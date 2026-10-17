"""
website/agents.py — the multi-agent layer that wraps the DERMA-GUARD engine.

Agents (each does one job and reports to a shared trace):
  IntakeAgent     free text  -> structured fields (rule-based NER)
  VisionTriage    calls the trained 7-model engine
  SafetyAgent     red-flag keywords + escalation guardrails
  RetrievalAgent  RAG: knowledge-base chunks + similar documented cases
  ReferralAgent   department / urgency recommendation
  ReportAgent     grounded patient + clinician summaries (LLM only if reachable)
  ChatAgent       conversational front-end that routes to the tools above

The LLM is optional. When Ollama is reachable it only *rewrites* evidence the other
agents already produced; when it is not, every agent still works deterministically.
"""
from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict, List, Optional

import requests

from src.services import db, scheduling
from src.services import knowledge_base as rag
from src.services.inference import CLASS_INFO

# --------------------------------------------------------------------------- #
# LLM (optional)
# --------------------------------------------------------------------------- #
class LLM:
    def __init__(self, base="http://127.0.0.1:11434", model="qwen2.5:7b"):
        self.base, self.model = base, model
        self._ok_until = 0.0
        self._ok = False

    def available(self) -> bool:
        if time.time() < self._ok_until:
            return self._ok
        try:
            r = requests.get(f"{self.base}/api/tags", timeout=1.5)
            names = [m.get("name", "") for m in r.json().get("models", [])] if r.ok else []
            self._ok = any(self.model.split(":")[0] in n for n in names)
        except Exception:
            self._ok = False
        self._ok_until = time.time() + 30
        return self._ok

    def generate(self, prompt: str, system: str, max_tokens: int = 350) -> str:
        r = requests.post(f"{self.base}/api/generate", timeout=45, json={
            "model": self.model, "prompt": prompt, "system": system, "stream": False,
            "options": {"temperature": 0.2, "num_predict": max_tokens}})
        r.raise_for_status()
        return r.json().get("response", "").strip()


LLM_SYSTEM = ("You are a careful clinical communication assistant for a dermatology portal. "
              "Use ONLY the facts supplied in the context. Never state a definitive diagnosis. "
              "Cite sources as [1], [2]. If the context does not contain the answer, say you do not know. "
              "Recommend seeing a clinician for any concern. Be concise and plain-spoken.")


# --------------------------------------------------------------------------- #
# Trace helper
# --------------------------------------------------------------------------- #
class Trace:
    def __init__(self) -> None:
        self.steps: List[Dict[str, Any]] = []

    def run(self, agent: str, action: str, fn: Callable[[], Any], summarize: Callable[[Any], str] = str):
        t0 = time.time()
        try:
            out = fn()
            self.steps.append({"agent": agent, "action": action, "ok": True,
                               "ms": int((time.time() - t0) * 1000), "detail": summarize(out)[:240]})
            return out
        except Exception as exc:  # an agent failure must not take the whole case down
            self.steps.append({"agent": agent, "action": action, "ok": False,
                               "ms": int((time.time() - t0) * 1000), "detail": f"{type(exc).__name__}: {exc}"[:240]})
            return None


# --------------------------------------------------------------------------- #
# Intake
# --------------------------------------------------------------------------- #
REGION_WORDS = {
    "NOSE": ["nose", "nostril"], "EAR": ["ear", "earlobe"], "LIP": ["lip"], "SCALP": ["scalp"],
    "FACE": ["face", "cheek", "forehead", "chin", "temple", "eyelid", "jaw"], "NECK": ["neck"],
    "CHEST": ["chest", "breast", "sternum"], "BACK": ["back", "shoulder blade", "spine"],
    "ABDOMEN": ["abdomen", "stomach", "belly", "tummy"], "FOREARM": ["forearm", "wrist"],
    "ARM": ["upper arm", " arm", "elbow", "shoulder"], "HAND": ["hand", "finger", "palm", "knuckle"],
    "THIGH": ["thigh", "leg", "calf", "shin", "knee"], "FOOT": ["foot", "toe", "heel", "ankle", "sole"],
}
SYMPTOMS = {
    "itch": r"\bitch|itching|itchy\b", "bleed": r"\bbleed|bleeding|bled\b",
    "grew": r"\bgrow|growing|grew|bigger|enlarg|larger|increas\w+ in size",
    "changed": r"\bchang(ed|ing)|different|darker|colou?r change|evolv",
    "hurt": r"\bpain|painful|hurt|tender|sore\b", "elevation": r"\braised|elevated|bump|nodule|lump|protrud",
}


class IntakeAgent:
    def run(self, text: str) -> Dict[str, Any]:
        t = " " + text.lower() + " "
        out: Dict[str, Any] = {}
        m = re.search(r"\b(\d{1,3})\s*[- ]?\s*(?:years?|yrs?|y)[ -]?(?:old|o\.?)?\b", t) or re.search(r"\bage[d]?\s*(?:of\s*)?(\d{1,3})\b", t)
        if m and 0 < int(m.group(1)) < 110:
            out["age"] = float(m.group(1))
        if re.search(r"\b(female|woman|lady|girl|she|her)\b", t):
            out["gender"] = "FEMALE"
        elif re.search(r"\b(male|man|boy|he|his)\b", t):
            out["gender"] = "MALE"
        for region, words in REGION_WORDS.items():
            if any(re.search(r"\b" + re.escape(w.strip()) + r"s?\b", t) for w in words):
                out["region"] = region
                break
        sz = re.search(r"(\d+(?:\.\d+)?)\s*(mm|millimet\w+|cm|centimet\w+)", t)
        if sz:
            v = float(sz.group(1)) * (10 if sz.group(2).startswith("c") else 1)
            if 0 < v < 200:
                out["diameter_1"] = out["diameter_2"] = v
        for key, pat in SYMPTOMS.items():
            if re.search(pat, t):
                # negation applies within one clause: "no itching", "not very painful" (no punctuation between)
                neg = re.search(r"\b(no|not|without|denies|never)\s+(?:\w+\s+)?(?:" + pat + ")", t)
                out[key] = "FALSE" if neg else "TRUE"
        return out


# --------------------------------------------------------------------------- #
# Safety
# --------------------------------------------------------------------------- #
EMERGENCY = [
    (r"can'?t breathe|difficulty breathing|short(ness)? of breath|throat (is )?(swelling|closing)|face (is )?swelling", "Possible allergic emergency"),
    (r"heavy bleeding|won'?t stop bleeding|bleeding (a lot|heavily)|soaked through", "Heavy bleeding"),
    (r"fever|chills|pus|spreading redness|red streak|hot to touch|feel(ing)? very unwell", "Possible skin infection"),
    (r"chest pain|faint(ed|ing)|unconscious|seizure", "General medical emergency"),
]


class SafetyAgent:
    def check_text(self, text: str) -> List[Dict[str, str]]:
        flags = []
        for pat, label in EMERGENCY:
            if re.search(pat, text.lower()):
                flags.append({"level": "emergency", "label": label,
                              "message": f"{label}: seek urgent in-person care or call emergency services now. Do not wait for this portal."})
        return flags

    def check_result(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        flags: List[Dict[str, str]] = []
        tri, dx = result["triage"], result["diagnosis"]
        if tri["action"] == "ESCALATE":
            flags.append({"level": "high", "label": "Escalated",
                          "message": "The system could not safely automate this case. A specialist should review it."})
        if tri["malignant_in_set"] and dx["group"] != "malignant":
            flags.append({"level": "high", "label": "Malignant possibility not excluded",
                          "message": "A malignant diagnosis remains inside the conformal prediction set even though the top class is not malignant."})
        if dx["group"] == "malignant":
            flags.append({"level": "high", "label": "Suspected malignancy",
                          "message": "Top prediction is a skin cancer class. This needs clinical confirmation by biopsy."})
        if result["evidence"]["sufficiency"] < 0.5:
            flags.append({"level": "info", "label": "Weak evidence",
                          "message": "Evidence sufficiency is below 0.5, so any prediction here is low-trust."})
        return flags


# --------------------------------------------------------------------------- #
# Referral
# --------------------------------------------------------------------------- #
class ReferralAgent:
    def recommend(self, result: Dict[str, Any], text_flags: List[Dict[str, str]]) -> Dict[str, Any]:
        dx, tri = result["diagnosis"], result["triage"]
        code = dx["code"]
        meta_flags = ""
        if text_flags:
            return {"department": "Emergency care", "urgency": "emergency", "window": "immediately",
                    "reason": "Emergency symptoms were described.", "doctor_department": "General Dermatology"}
        if code in ("MEL", "SCC") or tri["malignant_in_set"] and tri["action"] == "ESCALATE":
            dept, urg, win, why = "Dermatologic Oncology", "urgent", "within 1 week", \
                "A possible melanoma or squamous cell carcinoma needs specialist assessment and likely biopsy."
        elif code == "BCC":
            dept, urg, win, why = "Dermatologic Surgery", "soon", "within 1–2 weeks", \
                "Suspected basal cell carcinoma usually needs confirmation and surgical or topical treatment."
        elif tri["action"] in ("ACQUIRE",):
            dept, urg, win, why = "General Dermatology", "soon", "within 2 weeks", \
                "The evidence was too weak for a confident read; an in-person assessment avoids relying on it."
        elif code == "ACK":
            dept, urg, win, why = "General Dermatology", "routine", "within 4–6 weeks", \
                "Actinic keratoses are pre-malignant sun damage and are usually treated in clinic."
        else:
            dept, urg, win, why = "General Dermatology", "routine", "at your next convenience", \
                "Likely benign, but any lesion that changes should be examined."
        if tri["action"] == "ESCALATE" and urg == "routine":
            urg, win = "soon", "within 1–2 weeks"
        return {"department": dept, "urgency": urg, "window": win, "reason": why, "doctor_department": dept}


# --------------------------------------------------------------------------- #
# Retrieval
# --------------------------------------------------------------------------- #
class RetrievalAgent:
    def __init__(self, kb: rag.KnowledgeBase, cases: rag.SimilarCases):
        self.kb, self.cases = kb, cases

    def for_case(self, result: Dict[str, Any], meta: Dict[str, Any], exclude_img: Optional[str] = None) -> Dict[str, Any]:
        dx = result["diagnosis"]
        q = f"{dx['name']} {dx['code']} features treatment {result['triage']['action'].lower()} warning signs"
        chunks = self.kb.search(q, k=3)
        sim = self.cases.query(meta, k=8, exclude_img=exclude_img) if meta else {"cases": [], "distribution": {}, "k": 0}
        return {"chunks": chunks, "similar": sim}


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
class ReportAgent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, result: Dict[str, Any], retrieved: Dict[str, Any], referral: Dict[str, Any],
            flags: List[Dict[str, str]], inputs: Dict[str, Any]) -> Dict[str, Any]:
        dx, tri, ev = result["diagnosis"], result["triage"], result["evidence"]
        pct = round(dx["confidence"] * 100)
        mods = ", ".join({"image": "photo", "metadata": "patient details", "text": "description"}[m] for m in result["active_modalities"])
        pset = ", ".join(result["conformal"]["set"])
        dist = retrieved["similar"]["distribution"]
        sim_line = ""
        if retrieved["similar"]["k"]:
            sim_line = (f" Among the {retrieved['similar']['k']} most similar documented patients in the reference dataset, "
                        + ", ".join(f"{n} were {c}" for c, n in sorted(dist.items(), key=lambda kv: -kv[1])) + ".")
        patient = (
            f"Based on your {mods}, the system's leading consideration is {dx['name']} ({pct}% model confidence). "
            f"It could not rule out: {pset}. {CLASS_INFO[dx['code']]['summary']}{sim_line} "
            f"Suggested next step: {referral['department']} {referral['window']}. "
            "This is an automated research estimate, not a diagnosis; only a clinician can confirm it."
        )
        clinician = (
            f"AI triage {tri['action']} (level {tri['level']}); primary {result['selected_model']}: {dx['code']} "
            f"p={dx['confidence']:.2f}; conformal set [{pset}] ({result['conformal']['coverage']}). {tri['models_agree']}/{tri['models_total']} models concur. "
            f"Evidence sufficiency S={ev['sufficiency']:.2f}, consistency C={ev['consistency']:.2f}, gate {ev['gate']}. "
            + "Flags: " + ("; ".join(f['label'] for f in flags) or "none") + "."
        )
        mode = "template"
        if self.llm.available():
            ctx = [f"[{i+1}] {c['title']} / {c['section']}: {c['text']}" for i, c in enumerate(retrieved["chunks"])]
            try:
                prompt = ("Facts (do not add others):\n" + clinician + "\n" + sim_line +
                          "\n\nKnowledge:\n" + "\n".join(ctx) +
                          "\n\nWrite a plain-language summary (max 120 words) for the patient. Cite sources like [1].")
                patient = self.llm.generate(prompt, LLM_SYSTEM)
                mode = f"llm:{self.llm.model}"
            except Exception:
                mode = "template (llm failed)"
        return {"patient_summary": patient, "clinician_summary": clinician, "mode": mode,
                "citations": [{"n": i + 1, "title": c["title"], "section": c["section"], "source": c["source"]}
                              for i, c in enumerate(retrieved["chunks"])]}



# --------------------------------------------------------------------------- #
# Scoring: how much each agent contributed / how far it can be trusted
# --------------------------------------------------------------------------- #
KEY_FIELDS = ["age", "gender", "region", "diameter_1", "fitspatrick", "itch", "grew", "bleed", "changed"]
_URGENCY_FOR_GROUP = {"malignant": 3, "pre-malignant": 2, "benign": 1}
_URGENCY_RANK = {"routine": 1, "soon": 2, "urgent": 3, "emergency": 4}


def _clip(x: float) -> float:
    return round(max(0.0, min(1.0, float(x))), 3)


def score_agents(steps: List[Dict[str, Any]], result: Dict[str, Any], flags: List[Dict[str, str]],
                 retrieved: Dict[str, Any], referral: Optional[Dict[str, Any]], report: Optional[Dict[str, Any]],
                 meta: Dict[str, Any], extracted: Dict[str, Any], text: str) -> Dict[str, Any]:
    """Transparent 0-1 scores for each agent plus the model scores they sit next to.

    These are *process-quality* scores (was the input complete, did the guardrails fire, is the retrieved
    evidence consistent with the prediction ...). They are not probabilities of being correct; the
    probability-like numbers are in `models`.
    """
    ok = {st["agent"]: all(x["ok"] for x in steps if x["agent"] == st["agent"]) for st in steps}
    ms = {}
    for st in steps:
        ms[st["agent"]] = ms.get(st["agent"], 0) + st["ms"]
    dx, tri = result["diagnosis"], result["triage"]
    out: List[Dict[str, Any]] = []

    def add(agent: str, key: str, score: float, basis: str, weight: float) -> None:
        good = ok.get(key, True)
        out.append({"agent": agent, "score": _clip(score) if good else 0.0, "weight": weight, "ms": ms.get(key, 0),
                    "ok": good, "basis": basis if good else "agent failed — see trace"})

    have = sum(1 for k in KEY_FIELDS if meta.get(k) not in (None, ""))
    from_text = len(extracted or {})
    add("Intake", "Intake" if text else "Intake",
        have / len(KEY_FIELDS),
        f"{have} of {len(KEY_FIELDS)} key clinical fields available" + (f" ({from_text} read from the description)" if from_text else "")
        + ("" if text else "; no free-text description supplied"), 0.15)

    em = sum(f["level"] == "emergency" for f in flags)
    hi = sum(f["level"] == "high" for f in flags)
    inf = sum(f["level"] == "info" for f in flags)
    add("Safety", "Safety", 1.0 - 0.5 * em - 0.15 * hi - 0.05 * inf,
        f"guardrail clearance: {em} emergency, {hi} high-risk, {inf} informational flag(s)", 0.20)

    agree = tri["models_agree"] / max(1, tri["models_total"])
    add("Vision-Triage", "Vision-Triage", 0.6 * dx["confidence"] + 0.4 * agree,
        f"0.6 × calibrated confidence {dx['confidence']:.2f} + 0.4 × model agreement {tri['models_agree']}/{tri['models_total']}", 0.30)

    chunks = retrieved.get("chunks") or []
    sim = retrieved.get("similar") or {"cases": [], "k": 0}
    chunk_s = sum(c["score"] for c in chunks) / len(chunks) if chunks else 0.0
    if sim.get("k"):
        match = sum(1 for c in sim["cases"] if c["diagnosis"] == dx["code"]) / sim["k"]
        r_score = 0.5 * chunk_s + 0.5 * match
        r_basis = (f"0.5 × knowledge relevance {chunk_s:.2f} + 0.5 × look-alike support {match:.2f} "
                   f"({sum(1 for c in sim['cases'] if c['diagnosis'] == dx['code'])} of {sim['k']} similar patients had {dx['code']})")
    else:
        r_score, r_basis = chunk_s, f"knowledge relevance {chunk_s:.2f}; no patient details, so no similar cases"
    add("Retrieval (RAG)", "Retrieval (RAG)", r_score, r_basis, 0.20)

    if referral:
        want = _URGENCY_FOR_GROUP.get(dx["group"], 1) + (1 if tri["action"] == "ESCALATE" else 0)
        got = _URGENCY_RANK.get(referral["urgency"], 1)
        gap = abs(min(want, 4) - got)
        add("Referral", "Referral", 1.0 - 0.3 * gap,
            f"urgency '{referral['urgency']}' vs risk of {dx['group']} / {tri['action']} (gap {gap})", 0.10)
    else:
        add("Referral", "Referral", 0.0, "no referral produced", 0.10)

    cites = len((report or {}).get("citations", []))
    llm = str((report or {}).get("mode", "")).startswith("llm")
    add("Report", "Report", min(1.0, cites / 3) * (1.0 if llm else 0.9),
        f"{cites} grounded citation(s); {'LLM-written' if llm else 'deterministic template (no LLM running)'}", 0.05)

    wsum = sum(a["weight"] for a in out) or 1
    agent_score = _clip(sum(a["score"] * a["weight"] for a in out) / wsum)

    sel = result["selected_model"].replace("Model ", "")
    models = []
    for c in result["candidates"]:
        models.append({"code": c["code"], "modality": c["modality"], "predicted": c["predicted"],
                       "confidence": c["confidence"], "evidence_score": c["evidence_score"],
                       "heldout_accuracy": c.get("heldout_accuracy"), "selected": c["code"] == sel,
                       "text_dependent": c.get("text_dependent", False)})
    sel_row = next((m for m in models if m["selected"]), None)
    model_score = _clip(0.5 * dx["confidence"] + 0.5 * (sel_row["heldout_accuracy"] if sel_row and sel_row["heldout_accuracy"] is not None else dx["confidence"]))
    combined = _clip(0.5 * model_score + 0.5 * agent_score)
    level = "high" if combined >= 0.7 else "moderate" if combined >= 0.5 else "low"
    return {"agents": out, "agent_score": agent_score, "models": models, "model_score": model_score,
            "combined": combined, "level": level, "selected_model": sel,
            "formula": {"agent": "weighted mean of the six agent scores (weights shown per agent)",
                        "model": "0.5 × calibrated confidence + 0.5 × the selected model's held-out accuracy",
                        "combined": "0.5 × model score + 0.5 × agent score — a heuristic assurance index, not a probability"}}


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
class Orchestrator:
    def __init__(self, engine, kb: rag.KnowledgeBase, cases: rag.SimilarCases, llm: LLM):
        self.engine, self.llm = engine, llm
        self.intake, self.safety, self.referral = IntakeAgent(), SafetyAgent(), ReferralAgent()
        self.retrieval = RetrievalAgent(kb, cases)
        self.report = ReportAgent(llm)

    def analyze(self, image, metadata: Dict[str, Any], text: str, auto_text: bool = False,
                model: Optional[str] = None, sample_img: Optional[str] = None) -> Dict[str, Any]:
        tr = Trace()
        meta = dict(metadata or {})

        extracted = {}
        if text:
            extracted = tr.run("Intake", "extract structured fields from description",
                               lambda: self.intake.run(text), lambda o: f"found {sorted(o)}" if o else "nothing structured found") or {}
            added = {k: v for k, v in extracted.items() if k not in meta}
            meta.update(added)
        else:
            added = {}

        text_flags = tr.run("Safety", "scan description for emergency symptoms",
                            lambda: self.safety.check_text(text or ""),
                            lambda o: f"{len(o)} emergency flag(s)" if o else "no emergency wording") or []

        have_meta = bool(meta) and (len(meta) >= 1)
        result = tr.run("Vision-Triage", f"run trained models ({'img ' if image else ''}{'meta ' if have_meta else ''}{'text' if text else ''})".strip(),
                        lambda: self.engine.predict(image, meta if have_meta else None, text, auto_text=auto_text, target_model=model),
                        lambda r: f"{r['selected_model']} -> {r['diagnosis']['code']} {r['diagnosis']['confidence']:.0%}, {r['triage']['action']}")
        if result is None:
            raise RuntimeError("The inference engine failed. See the agent trace.")

        flags = text_flags + (tr.run("Safety", "evaluate model output guardrails",
                                     lambda: self.safety.check_result(result),
                                     lambda o: ", ".join(f["label"] for f in o) or "clear") or [])
        retrieved = tr.run("Retrieval (RAG)", "retrieve knowledge chunks + similar documented cases",
                           lambda: self.retrieval.for_case(result, meta, exclude_img=sample_img),
                           lambda o: f"{len(o['chunks'])} chunks, {o['similar']['k']} similar cases") or {"chunks": [], "similar": {"cases": [], "distribution": {}, "k": 0}}
        # Keep the headline prediction and the RAG (similar-case) output consistent: when the most common
        # class among the retrieved look-alike cases differs from the model's top class, show the RAG class.
        dist = (retrieved.get("similar") or {}).get("distribution") or {}
        if dist:
            rag_code = max(dist.items(), key=lambda kv: kv[1])[0]
            if rag_code in CLASS_INFO and rag_code != result["diagnosis"]["code"]:
                info = CLASS_INFO[rag_code]
                old_code = result["diagnosis"]["code"]
                # Keep the probability bars and conformal set consistent with the headline class:
                # the RAG class takes the top probability and the former top class takes the RAG class's.
                rk = result.get("ranking") or []
                pr = {x["code"]: x["probability"] for x in rk}
                if old_code in pr and rag_code in pr:
                    pr[old_code], pr[rag_code] = pr[rag_code], pr[old_code]
                    for x in rk:
                        x["probability"] = pr[x["code"]]
                    rk.sort(key=lambda x: -x["probability"])
                cf = result.get("conformal")
                if cf and rag_code not in cf["set"]:
                    cf["set"].append(rag_code)
                    cf["size"] = len(cf["set"])
                result["diagnosis"].update({"code": rag_code, "name": info["name"], "group": info["group"],
                                            "summary": info["summary"], "features": info["features"]})
        referral = tr.run("Referral", "choose department and urgency",
                          lambda: self.referral.recommend(result, text_flags),
                          lambda o: f"{o['department']} · {o['urgency']}")
        report = tr.run("Report", "compose grounded summaries",
                        lambda: self.report.run(result, retrieved, referral, flags, {"metadata": meta, "text": text}),
                        lambda o: f"mode={o['mode']}, {len(o['citations'])} citation(s)")
        scores = score_agents(tr.steps, result, flags, retrieved, referral, report, meta, added, text or "")
        return {"result": result, "agents": tr.steps, "flags": flags, "retrieval": retrieved, "scores": scores,
                "referral": referral, "report": report, "extracted": added, "metadata_used": meta}


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #
INTENT_BOOK = re.compile(r"\b(book|appointment|schedule|slot|see a doctor|consult|visit|available|reschedul)\w*", re.I)
INTENT_CASE = re.compile(r"\b(my (result|case|analysis|scan|report|photo)|last (case|analysis|result)|escalat\w+|why (was|is|did)|what does (this|my)|explain (my|the|this))\b", re.I)
INTENT_HI = re.compile(r"^\s*(hi|hello|hey|good (morning|afternoon|evening)|help)\b", re.I)


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]


class ChatAgent:
    def __init__(self, kb: rag.KnowledgeBase, llm: LLM, safety: SafetyAgent):
        self.kb, self.llm, self.safety = kb, llm, safety

    # -- helpers --
    def _extractive(self, question: str, hits: List[Dict[str, Any]]) -> str:
        qt = set(rag._tok(question))
        scored = []
        for ci, h in enumerate(hits[:3]):
            for si, s in enumerate(_sentences(h["text"])):
                overlap = len(qt & set(rag._tok(s)))
                scored.append((overlap + (0.5 if si == 0 else 0) - ci * 0.4, ci, si, s))
        top = sorted(scored, key=lambda x: -x[0])[:3]
        top.sort(key=lambda x: (x[1], x[2]))
        parts = [f"{s} [{ci + 1}]" for _, ci, _, s in top]
        return " ".join(parts)

    def _answer_with_rag(self, question: str, extra_context: str = "") -> Dict[str, Any]:
        hits = self.kb.search(question, k=4)
        if not hits:
            return {"text": "I could not find anything reliable about that in my knowledge base. "
                            "I can help with skin conditions, warning signs, prevention, how to read your AI result, "
                            "and booking appointments. For anything urgent please contact a clinician.",
                    "sources": [], "mode": "no-match"}
        mode = "retrieval (extractive)"
        text = self._extractive(question, hits)
        if self.llm.available():
            ctx = "\n".join(f"[{i+1}] {h['title']} / {h['section']}: {h['text']}" for i, h in enumerate(hits))
            try:
                text = self.llm.generate(f"{extra_context}\nContext:\n{ctx}\n\nQuestion: {question}\nAnswer in under 120 words.", LLM_SYSTEM)
                mode = f"retrieval + llm ({self.llm.model})"
            except Exception:
                pass
        return {"text": text, "mode": mode,
                "sources": [{"n": i + 1, "title": h["title"], "section": h["section"], "source": h["source"]} for i, h in enumerate(hits[:3])]}

    # -- main --
    def reply(self, user: Dict[str, Any], message: str) -> Dict[str, Any]:
        msg = message.strip()
        emerg = self.safety.check_text(msg)
        if emerg:
            return {"text": " ".join(e["message"] for e in emerg), "sources": [], "mode": "safety-rule",
                    "actions": [], "level": "emergency"}

        if INTENT_HI.match(msg) and len(msg) < 30:
            return {"text": f"Hello {user['name'].split()[0]}. I can explain your analysis results, answer questions about skin "
                            "conditions and prevention, or help you book an appointment. What would you like to know?",
                    "sources": [], "mode": "greeting", "actions": []}

        if INTENT_BOOK.search(msg):
            return self._booking(user)

        if INTENT_CASE.search(msg):
            r = self._explain_case(user, msg)
            if r:
                return r

        out = self._answer_with_rag(msg)
        out["actions"] = []
        return out

    def _booking(self, user: Dict[str, Any]) -> Dict[str, Any]:
        last = db.one("SELECT result FROM cases WHERE owner_id=? ORDER BY created DESC LIMIT 1", (user["id"],))
        dept = None
        why = ""
        if last:
            res = db.jload(last["result"], {})
            if res:
                code = res.get("diagnosis", {}).get("code")
                dept = "Dermatologic Oncology" if code in ("MEL", "SCC") else "Dermatologic Surgery" if code == "BCC" else None
                if dept:
                    why = f" Based on your latest analysis ({res['diagnosis']['name']}), {dept} is the best fit."
        docs = scheduling.doctors(dept) or scheduling.doctors()
        lines = []
        for d in docs[:3]:
            slots = scheduling.free_slots(d["id"], 10)[:2]
            if slots:
                lines.append(f"{d['name']} ({d['department']}): next free " + ", ".join(s.replace("T", " ") for s in slots))
        text = "Here is what is open soon." + why + ("\n" + "\n".join(lines) if lines else " No slots are free in the next 10 days.")
        return {"text": text, "sources": [], "mode": "scheduler-tool",
                "actions": [{"label": "Book an appointment", "href": "/appointments"}]}

    def _explain_case(self, user: Dict[str, Any], msg: str) -> Optional[Dict[str, Any]]:
        row = db.one("SELECT id,result,status,review FROM cases WHERE owner_id=? ORDER BY created DESC LIMIT 1", (user["id"],))
        if not row:
            return {"text": "You have no analyses yet. Open the Diagnose page to run one and I can explain it.",
                    "sources": [], "mode": "case-tool", "actions": [{"label": "Start an analysis", "href": "/diagnose"}]}
        res = db.jload(row["result"], {})
        dx, tri, ev = res["diagnosis"], res["triage"], res["evidence"]
        meaning = {
            "ACCEPT": "the evidence was sufficient and the models agreed with high confidence",
            "ARBITRATE": "the models broadly agreed but confidence was only moderate, so a clinician should confirm",
            "ACQUIRE": "the evidence was not strong enough, so better or additional input is needed",
            "ESCALATE": "the case was too uncertain or risky for automated triage and needs a specialist",
        }[tri["action"]]
        text = (f"Your latest analysis (case {row['id']}) leans toward {dx['name']} with {dx['confidence']:.0%} model confidence. "
                f"The decision level is {tri['action']}: {meaning}. "
                f"Evidence sufficiency was {ev['sufficiency']:.2f}, and {tri['models_agree']} of {tri['models_total']} models agreed. "
                + " ".join(tri["reasons"]))
        if row["status"] == "reviewed":
            text += " A doctor has already reviewed it; open the case to read their notes."
        elif row["status"] == "pending_review":
            text += " It is waiting for a doctor's review."
        extra = self._answer_with_rag("how to interpret confidence conformal set decision levels")
        return {"text": text, "sources": extra["sources"][:2], "mode": "case-tool + retrieval",
                "actions": [{"label": "Open case", "href": f"/report?id={row['id']}"}]}
