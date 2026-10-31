"""
src/main.py — DERMA-GUARD backend + web portal (FastAPI).

One process serves everything:
  /                         the hospital web portal (static pages in app/static)
  /api/...                  portal API (auth, cases, appointments, assistant, admin)
  /api/v1/...               the API contract from the project specification
  /predict /case /metrics   legacy v4.0 endpoints (kept for the Streamlit apps)
  /api/docs                 OpenAPI docs

Run:  python src/main.py        ->  http://127.0.0.1:8000
"""
from __future__ import annotations

import io
import json
import os
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel, Field

from src.services import auth, db, scheduling
from src.services import inference as eng
from src.services import knowledge_base as rag
from src.services import care_agents as ag

STATIC = ROOT / "app" / "static"
UPLOADS = db.STORAGE / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
THUMBS = db.STORAGE / "thumbs"
THUMBS.mkdir(parents=True, exist_ok=True)
DOCS_DIR = ROOT / "docs"

engine = eng.Engine()
kb = rag.KnowledgeBase()
similar = rag.SimilarCases()
llm = ag.LLM()
orch = ag.Orchestrator(engine, kb, similar, llm)
chat_agent = ag.ChatAgent(kb, llm, orch.safety)
rag_state: Dict[str, Any] = {"state": "loading", "error": None}


def _build_rag() -> None:
    try:
        kb.build()
        similar.build(eng.RAW_DATA / "metadata.csv")
        rag_state["state"] = "ready"
    except Exception as exc:
        rag_state.update(state="error", error=f"{type(exc).__name__}: {exc}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    creds = auth.seed_demo()
    if creds:
        print("\n" + creds + f"(also saved to {db.STORAGE / 'DEMO_CREDENTIALS.txt'})\n")
    auth.purge_expired()
    engine.start()
    threading.Thread(target=_build_rag, daemon=True, name="rag-build").start()
    yield


app = FastAPI(
    title="DERMA-GUARD API + portal",
    description=("Agentic Evidence-Management Framework for Reliable Multimodal Dermatological Diagnosis.\n\n"
                 "**Important**: research system, not clinically validated."),
    version="4.1.0", lifespan=lifespan,
    docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    if request.url.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    elif request.url.path.startswith("/static/") or resp.headers.get("content-type", "").startswith("text/html"):
        resp.headers["Cache-Control"] = "no-cache"      # always revalidate so UI edits show up immediately
    return resp


User = Dict[str, Any]
Pat = auth.require("patient", "doctor")
Doc = auth.require("doctor")
Admin = auth.require("admin")
Staff = auth.require("doctor", "admin")
Any_ = Depends(auth.current_user)


def ip(request: Request) -> str:
    return auth.client_ip(request)


# =========================================================================== #
# System
# =========================================================================== #
def _system_status() -> Dict[str, Any]:
    return {**engine.status(), "rag": {**rag_state, **kb.stats()},
            "llm": {"available": llm.available(), "model": llm.model}}


@app.get("/api/status")
def status():
    return _system_status()


@app.get("/api/v1/health", tags=["Health"])
def health_v1():
    s = _system_status()
    return {"status": "ok" if s["state"] == "ready" else s["state"], "service": "DERMA-GUARD v4.0",
            "pipeline_loaded": s["state"] == "ready", "knowledge_base": s["rag"]["state"],
            "ollama_available": s["llm"]["available"], "device": s["device"]}


# =========================================================================== #
# Auth
# =========================================================================== #
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=120)
    password: str = Field(max_length=128)


class LoginIn(BaseModel):
    email: str = Field(max_length=120)
    password: str = Field(max_length=128)


@app.post("/api/auth/register")
def register(body: RegisterIn, request: Request, response: Response, _: None = Depends(auth.csrf_guard)):
    email = body.email.strip().lower()
    if not auth.EMAIL_RE.match(email):
        raise HTTPException(400, "Enter a valid email address.")
    problem = auth.password_problem(body.password)
    if problem:
        raise HTTPException(400, problem)
    if db.one("SELECT 1 AS x FROM users WHERE email=?", (email,)):
        raise HTTPException(409, "An account with that email already exists.")
    uid = db.run("INSERT INTO users(email,name,role,password_hash,created) VALUES (?,?,?,?,?)",
                 (email, body.name.strip(), "patient", auth.hash_password(body.password), time.time()))
    db.audit({"id": uid, "email": email}, "register", email, ip(request))
    return auth.login(email, body.password, request, response)


class JoinIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=120)


@app.post("/api/auth/join")
def join(body: JoinIn, request: Request, response: Response, _: None = Depends(auth.csrf_guard)):
    """Passwordless patient registration (the only sign-up route in the web UI)."""
    return auth.join(body.name, body.email, request, response)


class SwitchIn(BaseModel):
    role: str = Field(pattern="^(patient|doctor|admin)$")
    doctor_id: Optional[int] = None


@app.post("/api/auth/switch")
def switch(body: SwitchIn, request: Request, response: Response, _: None = Depends(auth.csrf_guard)):
    return {"user": auth.switch_role(request, response, body.role, body.doctor_id)}


@app.post("/api/auth/login")
def login(body: LoginIn, request: Request, response: Response, _: None = Depends(auth.csrf_guard)):
    return auth.login(body.email, body.password, request, response)


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, _: None = Depends(auth.csrf_guard)):
    auth.logout(request, response, auth.optional_user(request))
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request):
    u = auth.optional_user(request)
    if not u:
        return {"user": None, "switchable": False}
    sess = db.one("SELECT origin_id FROM sessions WHERE token_hash=?", (auth._hash(request.cookies.get(auth.COOKIE, "")),))
    origin = db.one("SELECT role,name FROM users WHERE id=?", (sess["origin_id"],)) if sess and sess.get("origin_id") else None
    return {"user": auth.public_user(u), "switchable": bool(origin and origin["role"] == "patient"),
            "origin_name": origin["name"] if origin else None}


class PasswordIn(BaseModel):
    current: str = Field(max_length=128)
    new: str = Field(max_length=128)


@app.post("/api/auth/password")
def change_password(body: PasswordIn, request: Request, user: User = Any_):
    if not auth.verify_password(body.current, user["password_hash"]):
        raise HTTPException(400, "Current password is incorrect.")
    problem = auth.password_problem(body.new)
    if problem:
        raise HTTPException(400, problem)
    db.run("UPDATE users SET password_hash=? WHERE id=?", (auth.hash_password(body.new), user["id"]))
    tok = request.cookies.get(auth.COOKIE)
    if tok:
        db.run("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (user["id"], auth._hash(tok)))
    db.audit(user, "password_change", user["email"], ip(request))
    return {"ok": True}


# =========================================================================== #
# Directory
# =========================================================================== #
@app.get("/api/doctors")
def doctor_directory():
    return scheduling.doctors()


@app.get("/api/slots")
def slots(doctor_id: int, user: User = Any_):
    if not db.one("SELECT id FROM users WHERE id=? AND role='doctor' AND active=1", (doctor_id,)):
        raise HTTPException(404, "Doctor not found.")
    by_day: Dict[str, List[str]] = {}
    for s in scheduling.free_slots(doctor_id):
        by_day.setdefault(s[:10], []).append(s[11:])
    return by_day


# =========================================================================== #
# Analysis helpers
# =========================================================================== #
MAX_IMAGE = 10 * 1024 * 1024          # spec: <10 MB
MIN_DIM, MAX_DIM = 32, 4096           # spec: 32x32 .. 4096x4096
_SIGS = (b"MZ", b"%PDF", b"<?php", b"<script", b"\x7fELF")


def _parse_metadata(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(400, "metadata must be a JSON object")
    return eng._clean_row({k: data.get(k) for k in eng.METADATA_FIELDS if data.get(k) not in (None, "", "UNK")})


def _open_image(upload: Optional[UploadFile], label: str = "image") -> Optional[Image.Image]:
    """Input sanitisation per spec: size, signature, real image decode, dimensions."""
    if upload is None or not upload.filename:
        return None
    data = upload.file.read(MAX_IMAGE + 1)
    if not data:
        return None
    if len(data) > MAX_IMAGE:
        raise HTTPException(413, f"{label} is larger than 10 MB.")
    if any(data[:1024].startswith(s) for s in _SIGS) or not (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(400, f"{label} must be a JPEG or PNG image.")
    try:
        img = eng.pil_from_bytes(data)
    except Exception:
        raise HTTPException(400, f"{label} is not a readable image.")
    if not (MIN_DIM <= img.width <= MAX_DIM and MIN_DIM <= img.height <= MAX_DIM):
        raise HTTPException(400, f"{label} dimensions must be between {MIN_DIM} and {MAX_DIM} px.")
    return img


def _pending_count(user_id: int) -> int:
    return db.one("SELECT COUNT(*) AS n FROM cases WHERE owner_id=? AND status='pending_review'", (user_id,))["n"]


def _run_case(user: User, request: Request, img: Optional[Image.Image], meta: Dict[str, Any], txt: str,
              auto_text: bool = False, model: Optional[str] = None, truth: Optional[str] = None,
              sample_img: Optional[str] = None, source: Optional[str] = None) -> Dict[str, Any]:
    if engine.state == "loading":
        raise HTTPException(503, "Models are still loading — please retry in a few seconds.")
    if engine.state == "error":
        raise HTTPException(500, f"Inference engine failed to start: {engine.error}")
    if img is None and not meta and not txt:
        raise HTTPException(400, "Provide at least one input: an image, patient details or a description.")
    if _pending_count(user["id"]) >= 5:
        raise HTTPException(429, "Too many pending cases (limit 5). Wait for a doctor's review first.")

    if model:
        model = model.strip().upper()
        needs = eng.MODEL_REQUIRES.get(model)
        if needs is None:
            raise HTTPException(400, "model must be one of A to G")
        have = {"image": img is not None, "metadata": bool(meta), "text": bool(txt) or (auto_text and bool(meta))}
        missing = [eng.MODALITY_LABEL[m].lower() for m in needs if not have[m]]
        if missing:
            raise HTTPException(400, f"Model {model} needs: {', '.join(missing)}. Add it or choose automatic.")

    try:
        bundle = orch.analyze(img, meta, txt, auto_text=auto_text and bool(meta), model=model, sample_img=sample_img)
    except Exception as exc:
        raise HTTPException(500, f"Analysis failed: {exc}")

    result = bundle["result"]
    truth = truth.upper() if truth and truth.upper() in eng.CLASS_INFO else None

    case_id = uuid.uuid4().hex[:10]
    has_img = False
    morph = None
    if img is not None:
        t = img.copy()
        t.thumbnail((640, 640))
        t.save(UPLOADS / f"{case_id}.jpg", quality=88)
        has_img = True
        morph = eng.morphology(t, save_overlay=UPLOADS / f"{case_id}_mask.png")
    inputs = {"metadata": bundle["metadata_used"], "text": result.get("generated_text") or txt,
              "has_image": has_img, "extracted_from_text": bundle["extracted"]}
    blob = {k: bundle[k] for k in ("agents", "flags", "retrieval", "referral", "report", "scores")}
    blob["morphology"] = morph
    blob["acquisition"] = eng.acquisition_plan(result, morph, engine.measured)
    db.run("INSERT INTO cases(id,owner_id,created,source,truth,has_image,status,inputs,result,agents) VALUES (?,?,?,?,?,?,?,?,?,?)",
           (case_id, user["id"], time.time(), source or ("sample" if truth else "upload"), truth, int(has_img), "ai_only",
            db.jdump(inputs), db.jdump(result), db.jdump(blob)))
    db.audit(user, "case_create", case_id, ip(request), f"{result['selected_model']} {result['triage']['action']}")
    return {"case_id": case_id, "result": result, **blob, "inputs": inputs}


def _read_case_inputs(clinical, dermoscopy, patient_text, metadata, auto_text=False):
    img = _open_image(clinical, "clinical_image") or _open_image(dermoscopy, "dermoscopy_image")
    return img, _parse_metadata(metadata), (patient_text or "").strip()[:2000]


@app.post("/api/quality")
def quality(image: UploadFile = File(...), user: User = Any_):
    img = _open_image(image)
    if img is None:
        raise HTTPException(400, "No image supplied.")
    return eng.image_quality(img)


@app.post("/api/generate-text")
def generate_text(metadata: str = Form(...), user: User = Any_):
    meta = _parse_metadata(metadata)
    if not meta:
        raise HTTPException(400, "Fill in at least a few patient details first.")
    proj = str(eng.MODEL_PROJECT)
    if proj not in sys.path:
        sys.path.insert(0, proj)
    from data.text_generator import compute_ptis, generate_clinical_text  # noqa: E402
    text = generate_clinical_text(meta, include_morphology=False)
    return {"text": text, "ptis": float(compute_ptis(text))}


_samples_cache: Optional[List[Dict[str, Any]]] = None


@app.get("/api/samples")
def samples(user: User = Any_):
    global _samples_cache
    if _samples_cache is None:
        _samples_cache = eng.build_samples()
    return _samples_cache


@app.get("/api/sample-image/{img_id}")
def sample_image(img_id: str, request: Request, thumb: bool = False):
    if auth.optional_user(request) is None:
        raise HTTPException(401, "Please register first.")
    path = eng.RAW_DATA / "images" / Path(img_id).name
    if not path.exists():
        raise HTTPException(404, "Unknown sample image.")
    if thumb:
        tp = THUMBS / (path.stem + ".jpg")
        if not tp.exists():
            with Image.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail((260, 260))
                im.save(tp, quality=84)
        return FileResponse(tp, headers={"Cache-Control": "private, max-age=86400"})
    return FileResponse(path)


@app.post("/api/analyze")
def analyze(
    request: Request,
    image: Optional[UploadFile] = File(None),
    metadata: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    auto_text: bool = Form(False),
    model: Optional[str] = Form(None),
    truth: Optional[str] = Form(None),
    sample_img: Optional[str] = Form(None),
    user: User = Depends(Pat),
):
    img = _open_image(image)
    meta = _parse_metadata(metadata)
    return _run_case(user, request, img, meta, (text or "").strip()[:2000], auto_text, model, truth,
                     Path(sample_img).name if sample_img else None)


# =========================================================================== #
# Cases
# =========================================================================== #
def _case_row(case_id: str) -> Dict[str, Any]:
    row = db.one("SELECT * FROM cases WHERE id=?", (Path(case_id).name,))
    if not row:
        raise HTTPException(404, "Case not found.")
    return row


def _can_view(user: User, row: Dict[str, Any]) -> bool:
    return row["owner_id"] == user["id"] or user["role"] == "doctor"      # doctors see every case in the hospital


def _full_case(row: Dict[str, Any]) -> Dict[str, Any]:
    owner = db.one("SELECT name FROM users WHERE id=?", (row["owner_id"],))
    doc = db.one("SELECT name,department FROM users WHERE id=?", (row["doctor_id"],)) if row["doctor_id"] else None
    return {
        "id": row["id"], "created": row["created"], "status": row["status"], "source": row["source"],
        "truth": row["truth"], "has_image": bool(row["has_image"]),
        "owner": owner["name"] if owner else None, "owner_id": row["owner_id"], "doctor": doc, "doctor_id": row["doctor_id"],
        "inputs": db.jload(row["inputs"], {}), "result": db.jload(row["result"], {}),
        "review": db.jload(row["review"]), "lesion_id": row.get("lesion_id"),
        "observed_at": row.get("observed_at"), "simulated": bool(row.get("simulated")),
        **db.jload(row["agents"], {}),
    }


def _summary(row: Dict[str, Any]) -> Dict[str, Any]:
    r = db.jload(row["result"], {})
    return {
        "id": row["id"], "created": row["created"], "source": row["source"], "truth": row["truth"],
        "has_image": bool(row["has_image"]), "status": row["status"], "owner": row.get("owner_name"),
        "doctor": row.get("doctor_name"), "diagnosis": r["diagnosis"]["code"], "diagnosis_name": r["diagnosis"]["name"],
        "group": r["diagnosis"]["group"], "confidence": r["diagnosis"]["confidence"],
        "action": r["triage"]["action"], "level": r["triage"]["level"],
        "modalities": r["active_modalities"], "model": r["selected_model"],
        "lesion_id": row.get("lesion_id"), "simulated": bool(row.get("simulated")),
    }


@app.get("/api/cases")
def list_cases(scope: str = "mine", user: User = Any_):
    base = ("SELECT c.*, o.name AS owner_name, d.name AS doctor_name FROM cases c "
            "JOIN users o ON o.id=c.owner_id LEFT JOIN users d ON d.id=c.doctor_id ")
    if scope == "assigned" and user["role"] == "doctor":
        rows = db.all_(base + "WHERE c.doctor_id=? ORDER BY (c.status='pending_review') DESC, c.created DESC", (user["id"],))
    elif scope == "all" and user["role"] == "doctor":
        rows = db.all_(base + "ORDER BY (c.status='pending_review') DESC, (c.status='ai_only') DESC, c.created DESC")
    elif user["role"] == "admin":
        raise HTTPException(403, "Administrators cannot view clinical cases.")
    else:
        rows = db.all_(base + "WHERE c.owner_id=? ORDER BY c.created DESC", (user["id"],))
    return [_summary(r) for r in rows]


@app.get("/api/cases/{case_id}")
def get_case(case_id: str, request: Request, user: User = Any_):
    row = _case_row(case_id)
    if not _can_view(user, row):
        db.audit(user, "case_denied", row["id"], ip(request))
        raise HTTPException(403, "You do not have access to this case.")
    if user["id"] != row["owner_id"]:
        db.audit(user, "case_view", row["id"], ip(request))
    return _full_case(row)


@app.get("/api/case-image/{case_id}")
def case_image(case_id: str, overlay: bool = False, user: User = Any_):
    row = _case_row(case_id)
    if not _can_view(user, row):
        raise HTTPException(403, "You do not have access to this image.")
    p = UPLOADS / (f"{row['id']}_mask.png" if overlay else f"{row['id']}.jpg")
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, headers={"Cache-Control": "private, max-age=300"})


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str, request: Request, user: User = Any_):
    row = _case_row(case_id)
    if row["owner_id"] != user["id"]:
        raise HTTPException(403, "Only the owner can delete a case.")
    db.run("UPDATE appointments SET case_id=NULL WHERE case_id=?", (row["id"],))
    db.run("DELETE FROM cases WHERE id=?", (row["id"],))
    for suffix in (".jpg", "_mask.png", "_audit.png"):
        (UPLOADS / f"{row['id']}{suffix}").unlink(missing_ok=True)
    db.audit(user, "case_delete", row["id"], ip(request))
    return {"deleted": row["id"]}


class ReviewRequestIn(BaseModel):
    doctor_id: int


@app.post("/api/cases/{case_id}/request-review")
def request_review(case_id: str, body: ReviewRequestIn, request: Request, user: User = Depends(auth.require("patient"))):
    row = _case_row(case_id)
    if row["owner_id"] != user["id"]:
        raise HTTPException(403, "Not your case.")
    if not db.one("SELECT 1 AS x FROM users WHERE id=? AND role='doctor' AND active=1", (body.doctor_id,)):
        raise HTTPException(404, "Doctor not found.")
    db.run("UPDATE cases SET doctor_id=?, status='pending_review', review=NULL WHERE id=?", (body.doctor_id, row["id"]))
    db.audit(user, "review_requested", row["id"], ip(request), f"doctor {body.doctor_id}")
    return {"ok": True}


class ReviewIn(BaseModel):
    decision: str = Field(pattern="^(agree|modify|refer_urgent|need_more)$")
    final_dx: Optional[str] = None
    notes: str = Field(min_length=3, max_length=2000)


def _save_review(row, user, decision, dx, notes, request):
    dx = dx.upper() if dx else None
    if dx and dx not in eng.CLASS_INFO:
        raise HTTPException(400, "Unknown diagnosis code.")
    ai = db.jload(row["result"], {}).get("diagnosis", {})
    review = {"doctor_id": user["id"], "doctor": user["name"], "decision": decision, "final_dx": dx,
              "final_dx_name": eng.CLASS_INFO[dx]["name"] if dx else None, "notes": notes.strip(), "ts": time.time(),
              "ai_dx": ai.get("code"), "ai_conf": ai.get("confidence"),
              "overrides_ai": bool(dx and ai.get("code") and dx != ai.get("code"))}
    db.run("UPDATE cases SET review=?, status='reviewed', doctor_id=? WHERE id=?", (db.jdump(review), user["id"], row["id"]))
    db.audit(user, "case_review", row["id"], ip(request), decision)
    return review


@app.post("/api/cases/{case_id}/review")
def submit_review(case_id: str, body: ReviewIn, request: Request, user: User = Depends(Doc)):
    row = _case_row(case_id)
    if row["owner_id"] == user["id"]:
        raise HTTPException(403, "You cannot review your own case.")
    return _save_review(row, user, body.decision, body.final_dx, body.notes, request)


# =========================================================================== #
# /api/v1 — contract from the project specification (sections 9.1-9.4)
# =========================================================================== #
STATE_MAP = {"ACCEPT": "RESOLVED", "ARBITRATE": "RESOLVED", "ACQUIRE": "EVIDENCE_COLLECTION", "ESCALATE": "HUMAN_REVIEW"}


def _v1_state(row: Dict[str, Any]) -> str:
    review = db.jload(row["review"])
    if review:
        return {"agree": "CARE_PLANNING", "refer_urgent": "CARE_PLANNING", "modify": "CARE_PLANNING",
                "need_more": "EVIDENCE_COLLECTION", "reject": "RESOLVED"}.get(review["decision"], "RESOLVED")
    if row["status"] == "pending_review":
        return "HUMAN_REVIEW"
    return STATE_MAP[db.jload(row["result"])["triage"]["action"]]


@app.post("/api/v1/cases", status_code=202, tags=["Cases"])
def v1_submit_case(
    request: Request,
    clinical_image: Optional[UploadFile] = File(None),
    dermoscopy_image: Optional[UploadFile] = File(None),
    patient_text: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    user: User = Depends(Pat),
):
    """Submit a diagnostic case. Limits per spec: JPEG/PNG, <10 MB, 32-4096 px, text <=2000 chars,
    at most 5 pending cases per patient (429)."""
    if patient_text and len(patient_text) > 2000:
        raise HTTPException(400, "patient_text is limited to 2000 characters.")
    img, meta, txt = _read_case_inputs(clinical_image, dermoscopy_image, patient_text, metadata)
    out = _run_case(user, request, img, meta, txt)
    row = _case_row(out["case_id"])
    return {"case_id": out["case_id"], "status": _v1_state(row), "message": "Case accepted and processed",
            "estimated_time": "30 seconds"}


@app.get("/api/v1/cases/{case_id}", tags=["Cases"])
def v1_get_case(case_id: str, request: Request, user: User = Any_):
    row = _case_row(case_id)
    if not _can_view(user, row):
        raise HTTPException(403, "You do not have access to this case.")
    r = db.jload(row["result"], {})
    ag_blob = db.jload(row["agents"], {})
    ev, rep = r["evidence"], ag_blob.get("report") or {}
    names = {"image": "clinical_image", "metadata": "metadata", "text": "patient_text"}
    evidence = {names[m]: {"quality": ev["quality"].get(m), "reliability": ev["reliability"].get(m)} for m in r["active_modalities"]}
    missing = [names[m] for m in names if m not in r["active_modalities"]] + ["dermoscopy_image"]
    acq = (ag_blob.get("acquisition") or {}).get("recommended")
    return {
        "case_id": row["id"], "patient_id": row["owner_id"], "status": _v1_state(row), "evidence": evidence,
        "prediction": {"diagnosis": r["diagnosis"]["name"], "code": r["diagnosis"]["code"], "confidence": r["diagnosis"]["confidence"],
                       "consensus_level": r["triage"]["level"], "action": r["triage"]["action"],
                       "fusion_weights": ev["weights"], "conformal_set": r["conformal"]["set"]},
        "report": {"summary": rep.get("patient_summary"), "clinician_summary": rep.get("clinician_summary"),
                   "evidence_used": [names[m] for m in r["active_modalities"]], "evidence_missing": missing,
                   "conflicts": [f["label"] for f in ag_blob.get("flags", []) if f["level"] != "info"],
                   "acquisition_recommendation": acq},
        "created_at": datetime.fromtimestamp(row["created"]).astimezone().isoformat(timespec="seconds"),
        "updated_at": datetime.fromtimestamp(db.jload(row["review"], {}).get("ts", row["created"])).astimezone().isoformat(timespec="seconds"),
    }


@app.get("/api/v1/cases/{case_id}/trace", tags=["Cases"])
def v1_trace(case_id: str, user: User = Any_):
    """Append-only evidence trace: the agent steps plus every audited action touching the case."""
    row = _case_row(case_id)
    if not _can_view(user, row):
        raise HTTPException(403, "You do not have access to this case.")
    steps = (db.jload(row["agents"], {}) or {}).get("agents", [])
    events = db.all_("SELECT ts, email, action, detail FROM audit WHERE target=? ORDER BY id", (row["id"],))
    return {"case_id": row["id"], "agent_steps": steps, "events": events}


class ClinicianAction(BaseModel):
    action: str = Field(pattern="^(approve|reject|request_evidence)$")
    comment: str = Field(default="", max_length=2000)
    evidence_request: Optional[str] = None


@app.post("/api/v1/cases/{case_id}/clinician-action", tags=["Clinician"])
def v1_clinician_action(case_id: str, body: ClinicianAction, request: Request, user: User = Depends(Doc)):
    row = _case_row(case_id)
    if row["owner_id"] == user["id"]:
        raise HTTPException(403, "You cannot review your own case.")
    if row["status"] == "reviewed":
        raise HTTPException(409, "Case already has a final clinician decision.")
    if body.action != "approve" and len(body.comment.strip()) < 3:
        raise HTTPException(400, "A comment is required for reject / request_evidence.")
    decision = {"approve": "agree", "reject": "reject", "request_evidence": "need_more"}[body.action]
    notes = body.comment or "Approved."
    if body.evidence_request:
        notes += f" (requested: {body.evidence_request})"
    review = _save_review(row, user, decision, None, notes, request)
    new_row = _case_row(case_id)
    return {"case_id": case_id, "new_status": _v1_state(new_row), "action": body.action, "comment": body.comment,
            "timestamp": datetime.fromtimestamp(review["ts"]).astimezone().isoformat(timespec="seconds")}


# =========================================================================== #
# Appointments
# =========================================================================== #
class BookIn(BaseModel):
    doctor_id: int
    slot: str
    reason: str = Field(default="", max_length=300)
    case_id: Optional[str] = None


@app.get("/api/appointments")
def list_appointments(user: User = Any_):
    if user["role"] == "admin":
        raise HTTPException(403, "Not available for administrators.")
    col = "a.doctor_id" if user["role"] == "doctor" else "a.patient_id"
    return db.all_(
        "SELECT a.*, p.name AS patient_name, d.name AS doctor_name, d.department AS department "
        "FROM appointments a JOIN users p ON p.id=a.patient_id JOIN users d ON d.id=a.doctor_id "
        f"WHERE {col}=? ORDER BY a.slot", (user["id"],))


@app.post("/api/appointments")
def book(body: BookIn, request: Request, user: User = Depends(auth.require("patient"))):
    if not db.one("SELECT 1 AS x FROM users WHERE id=? AND role='doctor' AND active=1", (body.doctor_id,)):
        raise HTTPException(404, "Doctor not found.")
    if not scheduling.valid_slot(body.slot):
        raise HTTPException(400, "That is not a valid appointment time.")
    if body.case_id:
        if _case_row(body.case_id)["owner_id"] != user["id"]:
            raise HTTPException(403, "Not your case.")
    try:
        aid = db.run("INSERT INTO appointments(patient_id,doctor_id,slot,reason,case_id,status,created) VALUES (?,?,?,?,?,?,?)",
                     (user["id"], body.doctor_id, body.slot, body.reason.strip(), body.case_id, "booked", time.time()))
    except Exception:
        raise HTTPException(409, "That slot was just taken. Please choose another.")
    if body.case_id:
        db.run("UPDATE cases SET doctor_id=?, status=CASE WHEN status='reviewed' THEN status ELSE 'pending_review' END WHERE id=?",
               (body.doctor_id, body.case_id))
    db.audit(user, "appointment_book", str(aid), ip(request), body.slot)
    return {"id": aid}


class ApptPatch(BaseModel):
    status: str = Field(pattern="^(cancelled|confirmed|completed)$")
    note: Optional[str] = Field(default=None, max_length=500)


@app.patch("/api/appointments/{aid}")
def update_appointment(aid: int, body: ApptPatch, request: Request, user: User = Any_):
    a = db.one("SELECT * FROM appointments WHERE id=?", (aid,))
    if not a:
        raise HTTPException(404, "Appointment not found.")
    is_patient, is_doc = a["patient_id"] == user["id"], a["doctor_id"] == user["id"]
    if not (is_patient or is_doc):
        raise HTTPException(403, "Not your appointment.")
    if is_patient and not is_doc and body.status != "cancelled":
        raise HTTPException(403, "Patients can only cancel.")
    if a["status"] in ("cancelled", "completed"):
        raise HTTPException(409, f"Appointment already {a['status']}.")
    db.run("UPDATE appointments SET status=?, doctor_note=COALESCE(?, doctor_note) WHERE id=?", (body.status, body.note, aid))
    db.audit(user, "appointment_" + body.status, str(aid), ip(request))
    return {"ok": True}


# =========================================================================== #
# Assistant (RAG chat)
# =========================================================================== #
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=600)


@app.post("/api/chat")
def chat(body: ChatIn, user: User = Any_):
    if rag_state["state"] != "ready":
        return {"text": "My knowledge base is still loading — try again in a few seconds.", "sources": [],
                "mode": "loading", "actions": []}
    db.run("INSERT INTO chat(user_id,ts,role,content) VALUES (?,?,?,?)", (user["id"], time.time(), "user", body.message))
    out = chat_agent.reply(user, body.message)
    db.run("INSERT INTO chat(user_id,ts,role,content,meta) VALUES (?,?,?,?,?)",
           (user["id"], time.time(), "assistant", out["text"], db.jdump({k: out.get(k) for k in ("sources", "mode", "actions", "level")})))
    return out


@app.get("/api/chat/history")
def chat_history(user: User = Any_):
    rows = db.all_("SELECT role,content,meta,ts FROM chat WHERE user_id=? ORDER BY id DESC LIMIT 30", (user["id"],))
    return [{"role": r["role"], "text": r["content"], **(db.jload(r["meta"], {}) or {})} for r in reversed(rows)]


@app.delete("/api/chat/history")
def clear_chat(user: User = Any_):
    db.run("DELETE FROM chat WHERE user_id=?", (user["id"],))
    return {"ok": True}


# =========================================================================== #
# Dashboard + admin
# =========================================================================== #
@app.get("/api/dashboard")
def dashboard(user: User = Any_):
    now = time.time()
    today = datetime.now().strftime("%Y-%m-%d")
    if user["role"] == "patient":
        cases = db.all_("SELECT status, result FROM cases WHERE owner_id=?", (user["id"],))
        appts = db.all_("SELECT a.id,a.slot,a.status,a.reason,d.name AS doctor_name FROM appointments a JOIN users d ON d.id=a.doctor_id "
                        "WHERE a.patient_id=? AND a.status IN ('booked','confirmed') AND a.slot>=? ORDER BY a.slot LIMIT 5",
                        (user["id"], datetime.now().strftime("%Y-%m-%dT%H:%M")))
        latest = db.one("SELECT id,result,created FROM cases WHERE owner_id=? ORDER BY created DESC LIMIT 1", (user["id"],))
        return {"role": "patient", "cases": len(cases),
                "pending": sum(c["status"] == "pending_review" for c in cases),
                "reviewed": sum(c["status"] == "reviewed" for c in cases), "upcoming": appts,
                "latest": ({"id": latest["id"], "created": latest["created"],
                            **{k: db.jload(latest["result"])[k] for k in ("diagnosis", "triage")}} if latest else None)}
    if user["role"] == "doctor":
        queue = db.all_("SELECT c.id,c.created,c.result,c.doctor_id,o.name AS owner FROM cases c JOIN users o ON o.id=c.owner_id "
                        "WHERE c.status='pending_review' ORDER BY c.created")
        queue.sort(key=lambda r: (r["doctor_id"] != user["id"], -db.jload(r["result"])["triage"]["level"]))
        total_cases = db.one("SELECT COUNT(*) AS n FROM cases")["n"]
        unreviewed = db.one("SELECT COUNT(*) AS n FROM cases WHERE status='ai_only'")["n"]
        todays = db.all_("SELECT a.id,a.slot,a.status,a.reason,a.case_id,p.name AS patient_name FROM appointments a "
                         "JOIN users p ON p.id=a.patient_id WHERE a.doctor_id=? AND a.slot LIKE ? AND a.status IN ('booked','confirmed') ORDER BY a.slot",
                         (user["id"], today + "%"))
        reviewed = db.one("SELECT COUNT(*) AS n FROM cases WHERE doctor_id=? AND status='reviewed'", (user["id"],))["n"]
        return {"role": "doctor", "pending": len(queue), "reviewed": reviewed, "today": todays,
                "total_cases": total_cases, "unreviewed": unreviewed,
                "queue": [{"id": r["id"], "created": r["created"], "owner": r["owner"], "mine": r["doctor_id"] == user["id"],
                           "action": db.jload(r["result"])["triage"]["action"],
                           "diagnosis": db.jload(r["result"])["diagnosis"]["name"],
                           "group": db.jload(r["result"])["diagnosis"]["group"]} for r in queue[:10]]}
    roles = {r["role"]: r["n"] for r in db.all_("SELECT role, COUNT(*) AS n FROM users GROUP BY role")}
    case_actions: Dict[str, int] = {}
    for r in db.all_("SELECT result FROM cases"):
        a = db.jload(r["result"])["triage"]["action"]
        case_actions[a] = case_actions.get(a, 0) + 1
    return {
        "role": "admin", "users": roles, "cases": sum(case_actions.values()), "actions": case_actions,
        "appointments": db.one("SELECT COUNT(*) AS n FROM appointments")["n"],
        "logins_24h": db.one("SELECT COUNT(*) AS n FROM audit WHERE action='login' AND ts>?", (now - 86400,))["n"],
        "failed_24h": db.one("SELECT COUNT(*) AS n FROM audit WHERE action='login_failed' AND ts>?", (now - 86400,))["n"],
        "system": _system_status(),
    }


@app.get("/api/admin/users")
def admin_users(user: User = Depends(Admin)):
    return db.all_("SELECT id,email,name,role,department,specialty,active,created,last_login,failed_attempts,locked_until FROM users ORDER BY role, name")


class NewUserIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=120)
    password: str = Field(max_length=128)
    role: str = Field(pattern="^(doctor|admin|patient)$")
    department: Optional[str] = Field(default=None, max_length=80)
    specialty: Optional[str] = Field(default=None, max_length=120)


@app.post("/api/admin/users")
def admin_create_user(body: NewUserIn, request: Request, user: User = Depends(Admin)):
    email = body.email.strip().lower()
    if not auth.EMAIL_RE.match(email):
        raise HTTPException(400, "Invalid email.")
    problem = auth.password_problem(body.password)
    if problem:
        raise HTTPException(400, problem)
    if db.one("SELECT 1 AS x FROM users WHERE email=?", (email,)):
        raise HTTPException(409, "Email already in use.")
    uid = db.run("INSERT INTO users(email,name,role,password_hash,department,specialty,created) VALUES (?,?,?,?,?,?,?)",
                 (email, body.name.strip(), body.role, auth.hash_password(body.password), body.department, body.specialty, time.time()))
    db.audit(user, "user_create", email, ip(request), body.role)
    return {"id": uid}


class UserPatch(BaseModel):
    active: Optional[bool] = None
    role: Optional[str] = Field(default=None, pattern="^(patient|doctor|admin)$")
    unlock: Optional[bool] = None


@app.patch("/api/admin/users/{uid}")
def admin_patch_user(uid: int, body: UserPatch, request: Request, user: User = Depends(Admin)):
    target = db.one("SELECT * FROM users WHERE id=?", (uid,))
    if not target:
        raise HTTPException(404, "User not found.")
    if uid == user["id"] and (body.active is False or (body.role and body.role != "admin")):
        raise HTTPException(400, "You cannot demote or deactivate your own account.")
    if body.active is not None:
        db.run("UPDATE users SET active=? WHERE id=?", (int(body.active), uid))
        if not body.active:
            db.run("DELETE FROM sessions WHERE user_id=?", (uid,))
        db.audit(user, "user_active" if body.active else "user_deactivate", target["email"], ip(request))
    if body.role:
        db.run("UPDATE users SET role=? WHERE id=?", (body.role, uid))
        db.audit(user, "user_role", target["email"], ip(request), body.role)
    if body.unlock:
        db.run("UPDATE users SET failed_attempts=0, locked_until=0 WHERE id=?", (uid,))
        db.audit(user, "user_unlock", target["email"], ip(request))
    return {"ok": True}


@app.get("/api/admin/audit")
def admin_audit(limit: int = 100, user: User = Depends(Admin)):
    return db.all_("SELECT ts,email,action,target,ip,detail FROM audit ORDER BY id DESC LIMIT ?", (min(max(limit, 1), 500),))


# =========================================================================== #
# Reference data (public)
# =========================================================================== #
@app.get("/api/benchmarks")
def benchmarks():
    return eng.load_benchmarks()


@app.get("/api/dataset")
def dataset():
    if not hasattr(dataset, "_cache"):
        dataset._cache = eng.load_dataset_stats()
    return dataset._cache


@app.get("/api/evaluation")
def evaluation():
    """Honest re-evaluation on rows never used for training (see src/services/honest_eval.py)."""
    from src.services import honest_eval
    res = honest_eval.load()
    if res is None:
        raise HTTPException(503, "Evaluation not computed yet — models are still loading.")
    return res


@app.get("/api/artifact/{model}/{name}")
def artifact(model: str, name: str):
    if model.upper() not in list("ABCDEFG") or Path(name).name != name:
        raise HTTPException(404)
    p = eng.SAVED_MODELS / f"model_{model.upper()}" / name
    if not p.exists() or p.suffix.lower() not in (".png", ".jpg"):
        raise HTTPException(404)
    return FileResponse(p)


# project documentation (rendered by the Documentation page)
DOC_FILES = {
    "readme": ("Project overview", ROOT / "README.md"),
    "limitations": ("Limitations", DOCS_DIR / "limitations.md"),
    "what-did-not-work": ("What did not work", DOCS_DIR / "what_did_not_work.md"),
    "reproducibility": ("Reproducibility statement", DOCS_DIR / "repro_statement.md"),
    "running-guide": ("Running guide", DOCS_DIR / "running_guide.md"),
    "benchmarks-guide": ("Benchmarks & execution guide", DOCS_DIR / "benchmarks_and_execution_guide.md"),
    "evaluation-audit": ("Evaluation audit", DOCS_DIR / "evaluation_audit.md"),
    "architecture-v5": ("v5.0 extension notes", DOCS_DIR / "v5_extension_notes.md"),
    "project-context": ("Project context", ROOT / "project_context" / "PROJECT_CONTEXT.md"),
}


@app.get("/api/docs-index")
def docs_index():
    return [{"id": k, "title": t, "available": p.exists()} for k, (t, p) in DOC_FILES.items() if p.exists()]


@app.get("/api/docs-content/{doc_id}")
def docs_content(doc_id: str):
    item = DOC_FILES.get(doc_id)
    if not item or not item[1].exists():
        raise HTTPException(404, "Unknown document.")
    return {"id": doc_id, "title": item[0], "markdown": item[1].read_text(encoding="utf-8", errors="replace")}


# =========================================================================== #
# v5.0 modules: explanation audit, longitudinal lesion tracking, DERMA-STRESS
# =========================================================================== #
@app.post("/api/cases/{case_id}/explanation-audit")
def explanation_audit(case_id: str, request: Request, user: User = Depends(Pat)):
    """Occlusion-sensitivity audit of the image model for one case (about 5-10 s)."""
    from src.services import explain_audit
    row = _case_row(case_id)
    if not _can_view(user, row):
        raise HTTPException(403, "You do not have access to this case.")
    thumb = UPLOADS / f"{row['id']}.jpg"
    if not thumb.exists():
        raise HTTPException(400, "This case has no image to audit.")
    if engine.state != "ready":
        raise HTTPException(503, "Models are still loading.")
    result = db.jload(row["result"], {})
    mask = eng.lesion_mask(Image.open(thumb).convert("RGB"))
    out = explain_audit.audit_image(engine, thumb, result["diagnosis"]["code"], mask, UPLOADS / f"{row['id']}_audit.png")
    blob = db.jload(row["agents"], {})
    blob["explanation_audit"] = out
    db.run("UPDATE cases SET agents=? WHERE id=?", (db.jdump(blob), row["id"]))
    db.audit(user, "explanation_audit", row["id"], ip(request), out["status"])
    return out


@app.get("/api/case-audit-image/{case_id}")
def case_audit_image(case_id: str, user: User = Any_):
    row = _case_row(case_id)
    if not _can_view(user, row):
        raise HTTPException(403)
    p = UPLOADS / f"{row['id']}_audit.png"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


class LesionIn(BaseModel):
    label: str = Field(min_length=1, max_length=60)
    body_site: Optional[str] = Field(default=None, max_length=40)


@app.get("/api/lesions")
def list_lesions(user: User = Depends(Pat)):
    rows = db.all_("SELECT l.*, (SELECT COUNT(*) FROM cases c WHERE c.lesion_id=l.id) AS n_obs "
                   "FROM lesions l WHERE l.owner_id=? ORDER BY l.created DESC", (user["id"],))
    return rows


@app.post("/api/lesions")
def create_lesion(body: LesionIn, user: User = Depends(Pat)):
    lid = uuid.uuid4().hex[:8]
    db.run("INSERT INTO lesions(id,owner_id,label,body_site,created) VALUES (?,?,?,?,?)",
           (lid, user["id"], body.label.strip(), body.body_site, time.time()))
    return {"id": lid}


class LinkIn(BaseModel):
    lesion_id: Optional[str] = None
    observed_at: Optional[float] = None


@app.post("/api/cases/{case_id}/lesion")
def link_case_to_lesion(case_id: str, body: LinkIn, user: User = Depends(Pat)):
    row = _case_row(case_id)
    if row["owner_id"] != user["id"]:
        raise HTTPException(403, "Not your case.")
    if body.lesion_id and not db.one("SELECT 1 AS x FROM lesions WHERE id=? AND owner_id=?", (body.lesion_id, user["id"])):
        raise HTTPException(404, "Lesion not found.")
    db.run("UPDATE cases SET lesion_id=?, observed_at=? WHERE id=?", (body.lesion_id, body.observed_at or row["created"], row["id"]))
    return {"ok": True}


def _timeline(lesion_id: str) -> List[Dict[str, Any]]:
    rows = db.all_("SELECT id, created, observed_at, simulated, result, agents, doctor_id, status FROM cases "
                   "WHERE lesion_id=? ORDER BY COALESCE(observed_at, created)", (lesion_id,))
    out = []
    for r in rows:
        res, blob = db.jload(r["result"], {}), db.jload(r["agents"], {})
        m = blob.get("morphology") or {}
        out.append({"case_id": r["id"], "observed_at": r["observed_at"] or r["created"], "simulated": bool(r["simulated"]),
                    "diagnosis": res["diagnosis"]["code"], "confidence": res["diagnosis"]["confidence"],
                    "action": res["triage"]["action"], "area_px": m.get("area_px"), "area_fraction": m.get("area_fraction"),
                    "circularity": m.get("circularity"), "asymmetry": m.get("asymmetry"),
                    "colour_variation": m.get("colour_variation"), "seg_quality": m.get("segmentation_quality"),
                    "has_image": True})
    return out


@app.get("/api/lesions/{lesion_id}/timeline")
def lesion_timeline(lesion_id: str, user: User = Depends(Pat)):
    les = db.one("SELECT * FROM lesions WHERE id=? AND owner_id=?", (lesion_id, user["id"]))
    if not les:
        raise HTTPException(404, "Lesion not found.")
    obs = _timeline(lesion_id)
    deltas = []
    for a, b in zip(obs, obs[1:]):
        days = max((b["observed_at"] - a["observed_at"]) / 86400.0, 1e-6)
        rel = None
        if a["area_px"] and b["area_px"]:
            rel = (b["area_px"] - a["area_px"]) / a["area_px"]
        reliable = (a["seg_quality"] or 0) >= 0.5 and (b["seg_quality"] or 0) >= 0.5
        alert = None
        if rel is not None and reliable and abs(rel) >= 0.25:
            alert = "area_change"
        deltas.append({"from": a["case_id"], "to": b["case_id"], "days": round(days, 2), "relative_area_change": rel,
                       "area_rate_per_day": (rel / days) if rel is not None else None,
                       "circularity_change": None if None in (a["circularity"], b["circularity"]) else round(b["circularity"] - a["circularity"], 3),
                       "asymmetry_change": None if None in (a["asymmetry"], b["asymmetry"]) else round(b["asymmetry"] - a["asymmetry"], 3),
                       "colour_variation_change": None if None in (a["colour_variation"], b["colour_variation"]) else round(b["colour_variation"] - a["colour_variation"], 2),
                       "prediction_changed": a["diagnosis"] != b["diagnosis"], "segmentation_reliable": reliable,
                       "alert": alert, "involves_simulated": a["simulated"] or b["simulated"]})
    return {"lesion": les, "observations": obs, "changes": deltas,
            "caveats": ["Pixel area depends on camera distance and angle; no physical scale or image alignment is available, "
                        "so area change is a screening hint only.",
                        "Measurement noise: in an internal check on 24 images, a simulated +60% growth was recovered as a median "
                        "x1.42 (IQR 1.20-1.55, range 0.80-1.86 across lesions; large lesions touching the frame are under-measured). "
                        "Treat changes below about 25% as noise and compare photos taken at the same distance.",
                        "Observations marked simulated are synthetic and are not clinical evidence."]}


class SimIn(BaseModel):
    growth_pct: float = Field(default=30, ge=-50, le=300)
    days: int = Field(default=60, ge=1, le=730)


@app.post("/api/lesions/{lesion_id}/simulate-followup")
def simulate_followup(lesion_id: str, body: SimIn, request: Request, user: User = Depends(Pat)):
    """Create a clearly-labelled SIMULATED follow-up by magnifying the lesion region of the latest photo."""
    les = db.one("SELECT * FROM lesions WHERE id=? AND owner_id=?", (lesion_id, user["id"]))
    if not les:
        raise HTTPException(404, "Lesion not found.")
    last = db.one("SELECT * FROM cases WHERE lesion_id=? AND has_image=1 ORDER BY COALESCE(observed_at, created) DESC LIMIT 1", (lesion_id,))
    if not last:
        raise HTTPException(400, "Add at least one real observation with a photo first.")
    base = Image.open(UPLOADS / f"{last['id']}.jpg").convert("RGB")
    mask = eng.lesion_mask(base)
    sim = eng.simulate_growth(base, mask, body.growth_pct / 100.0)
    meta = db.jload(last["inputs"], {}).get("metadata", {})
    out = _run_case(user, request, sim, meta, "", source="simulated")
    t = (last["observed_at"] or last["created"]) + body.days * 86400
    db.run("UPDATE cases SET lesion_id=?, observed_at=?, simulated=1 WHERE id=?", (lesion_id, t, out["case_id"]))
    return {"case_id": out["case_id"]}


class StressIn(BaseModel):
    n_cases: int = Field(default=24, ge=6, le=60)
    conditions: Optional[List[str]] = None


@app.post("/api/v1/benchmarks/stress", status_code=202, tags=["Benchmarks"])
def start_stress(body: StressIn, request: Request, user: User = Depends(Staff)):
    from src.services import stress_runner
    if engine.state != "ready":
        raise HTTPException(503, "Models are still loading.")
    running = db.one("SELECT COUNT(*) AS n FROM stress_runs WHERE status='running'")["n"]
    if running:
        raise HTTPException(409, "A benchmark is already running.")
    jid = stress_runner.start(engine, user["id"], body.n_cases, body.conditions)
    db.audit(user, "stress_start", jid, ip(request), f"n={body.n_cases}")
    return {"benchmark_id": jid, "status": "running", "estimated_time": f"{max(1, body.n_cases // 8)} minutes"}


@app.get("/api/v1/benchmarks", tags=["Benchmarks"])
def list_stress(user: User = Depends(Staff)):
    return db.all_("SELECT id, created, status, progress, params FROM stress_runs ORDER BY created DESC LIMIT 20")


@app.get("/api/v1/benchmarks/{benchmark_id}", tags=["Benchmarks"])
def get_stress(benchmark_id: str, user: User = Depends(Staff)):
    r = db.one("SELECT * FROM stress_runs WHERE id=?", (Path(benchmark_id).name,))
    if not r:
        raise HTTPException(404, "Benchmark not found.")
    return {"benchmark_id": r["id"], "status": r["status"], "progress": r["progress"], "created": r["created"],
            "error": r["error"], "params": db.jload(r["params"]), **(db.jload(r["results"], {}) or {})}


# =========================================================================== #
# Legacy v4.0 endpoints (unchanged behaviour; used by app/*.py Streamlit apps)
# =========================================================================== #
_result_store: Dict[str, Dict] = {}
_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from src.agents.orchestrator import OrchestratorAgent
            from src.fusion.acquisition import AcquisitionPolicy
            from src.fusion.adaptive_fusion import DiagnosisAdaptiveFusion
            from src.llm.client import OllamaClient
            client = OllamaClient()
            _pipeline = OrchestratorAgent(
                fusion_model=DiagnosisAdaptiveFusion(), acquisition_policy=AcquisitionPolicy(),
                llm_client=client if client.is_available() else None,
                class_names=["nevus", "melanoma", "bcc", "scc", "seborrheic_keratosis", "dermatofibroma", "vascular_lesion"],
                model_version="4.0.0")
        except Exception as e:
            print(f"[API] Pipeline initialization failed: {e}")
    return _pipeline


class CaseResult(BaseModel):
    case_id: str
    action: str
    diagnosis: Optional[int]
    confidence: Optional[float]
    consensus_level: Optional[int]
    report: Optional[str]
    evidence_used: List[str]
    evidence_missing: List[str]
    processing_time_s: float


@app.get("/health", tags=["Legacy"])
def health():
    pipeline = get_pipeline()
    s = _system_status()
    try:
        import torch
        gpu = torch.cuda.is_available()
    except Exception:
        gpu = False
    return {"status": "ok", "pipeline_loaded": pipeline is not None, "ollama_available": s["llm"]["available"],
            "ollama_model_available": s["llm"]["available"], "gpu_available": gpu}


@app.post("/predict", response_model=CaseResult, tags=["Legacy"])
async def predict(
    clinical_image: Optional[UploadFile] = File(None),
    dermoscopy_image: Optional[UploadFile] = File(None),
    patient_text: Optional[str] = Form(None),
):
    """Legacy v4.0 endpoint (research pipeline in src/agents). Prefer /api/v1/cases."""
    from torchvision import transforms
    case_id = str(uuid.uuid4())[:8]
    tf = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
                             transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    tensors = []
    for up, label in ((clinical_image, "clinical"), (dermoscopy_image, "dermoscopy")):
        if up is None:
            tensors.append(None)
            continue
        try:
            tensors.append(tf(Image.open(io.BytesIO(await up.read())).convert("RGB")).unsqueeze(0))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid {label} image: {e}")
    if tensors[0] is None and tensors[1] is None and not patient_text:
        raise HTTPException(status_code=400, detail="At least one input is required.")
    from src.agents.orchestrator import PatientCase
    case = PatientCase(case_id=case_id, clinical_images=tensors[0], dermo_images=tensors[1], patient_text=patient_text,
                       clinical_available=tensors[0] is not None, dermo_available=tensors[1] is not None,
                       meta_available=False, text_available=bool(patient_text))
    pipeline = get_pipeline()
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not available. Check server logs.")
    try:
        result = pipeline.process_case(case)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")
    _result_store[case_id] = result.to_dict()
    return CaseResult(case_id=case_id, action=result.action, diagnosis=result.diagnosis, confidence=result.confidence,
                      consensus_level=result.consensus_level, report=result.report, evidence_used=result.evidence_used,
                      evidence_missing=result.evidence_missing, processing_time_s=result.processing_time_s)


@app.get("/case/{case_id}", tags=["Legacy"])
def legacy_get_case(case_id: str):
    if case_id not in _result_store:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return _result_store[case_id]


@app.get("/cases", tags=["Legacy"])
def legacy_list_cases():
    return {"case_ids": list(_result_store.keys()), "total": len(_result_store)}


@app.get("/metrics", tags=["Legacy"])
def system_metrics():
    c = lambda a: sum(1 for r in _result_store.values() if r.get("action") == a)  # noqa: E731
    return {"total_cases_processed": len(_result_store), "accept_count": c("ACCEPT"), "arbitrate_count": c("ARBITRATE"),
            "acquire_count": c("ACQUIRE"), "escalate_count": c("ESCALATE"), "abstain_count": c("ABSTAIN")}


# =========================================================================== #
# Pages + static
# =========================================================================== #
PAGES = {"": "index.html", "diagnose": "diagnose.html", "performance": "performance.html",
         "how-it-works": "how-it-works.html", "history": "history.html", "report": "report.html",
         "safety": "safety.html", "login": "login.html", "register": "register.html",
         "dashboard": "dashboard.html", "appointments": "appointments.html", "doctors": "doctors.html",
         "admin": "admin.html", "account": "account.html", "documentation": "documentation.html",
         "lesions": "lesions.html", "stress": "stress.html"}


def _page(name: str):
    def handler():
        p = STATIC / name
        if not p.exists():
            raise HTTPException(404)
        return FileResponse(p, headers={"Cache-Control": "no-cache"})
    return handler


for route, file in PAGES.items():
    app.add_api_route("/" + route, _page(file), methods=["GET"], include_in_schema=False)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.exception_handler(404)
async def not_found(request, exc):
    if request.url.path.startswith("/api/") or request.url.path in ("/predict",):
        return JSONResponse({"detail": getattr(exc, "detail", "Not found")}, status_code=404)
    return FileResponse(STATIC / "index.html", status_code=404)


def main():
    import uvicorn
    host = os.environ.get("DG_HOST", "127.0.0.1")
    port = int(os.environ.get("DG_PORT", "8000"))
    print(f"\n  DERMA-GUARD -> http://{host}:{port}\n  (models + knowledge base load in the background, ~40 s)\n")
    uvicorn.run("src.main:app", host=host, port=port, reload=os.environ.get("DG_RELOAD") == "1", log_level="warning")


if __name__ == "__main__":
    main()
