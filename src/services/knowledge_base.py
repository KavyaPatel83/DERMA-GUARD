"""
website/rag.py — Retrieval-augmented knowledge layer.

Two retrievers:
  1. KnowledgeBase  — hybrid (dense MiniLM + TF-IDF) retrieval over curated
     dermatology / hospital / system documents, fused with Reciprocal Rank Fusion.
  2. SimilarCases   — nearest neighbours among the 2,298 documented PAD-UFES-20
     records, using the structured patient features.

Nothing here is generative: it only retrieves, and every chunk carries its source
so downstream agents can cite it.
"""
from __future__ import annotations

import hashlib
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KB_DIR = ROOT / "docs" / "knowledge_base"
EXTRA_DOCS = [  # project documents the assistant may quote about the system itself
    (ROOT / "docs" / "limitations.md", "Project limitations"),
    (ROOT / "docs" / "what_did_not_work.md", "What did not work"),
]
CACHE = ROOT / "outputs" / "portal" / "kb_embeddings.npz"
STOP = set("a an the of and or to in on is are was were be for with as at by it this that from can may not".split())


def _tok(s: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def _chunk(text: str, title: str, max_words: int = 110) -> List[Dict[str, str]]:
    """Split markdown by headings, then by sentence groups of ~max_words."""
    out: List[Dict[str, str]] = []
    section = title
    buf: List[str] = []
    def flush():
        body = " ".join(buf).strip()
        if body:
            sents = re.split(r"(?<=[.!?])\s+", body)
            cur: List[str] = []
            n = 0
            for s in sents:
                w = len(s.split())
                if cur and n + w > max_words:
                    out.append({"title": title, "section": section, "text": " ".join(cur)})
                    cur, n = [], 0
                cur.append(s); n += w
            if cur:
                out.append({"title": title, "section": section, "text": " ".join(cur)})
        buf.clear()
    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            h = line.lstrip("#").strip()
            if line.startswith("# "):
                title = h
            section = h
        elif line.strip():
            buf.append(line.strip())
    flush()
    return out


class KnowledgeBase:
    def __init__(self) -> None:
        self.chunks: List[Dict[str, Any]] = []
        self.mode = "uninitialised"
        self._tfidf = None
        self._tf_mat = None
        self._emb: Optional[np.ndarray] = None
        self._tokenizer = None
        self._model = None
        self._lock = threading.Lock()

    # ---- build ---------------------------------------------------------- #
    def build(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        chunks: List[Dict[str, Any]] = []
        for p in sorted(KB_DIR.glob("*.md")):
            for c in _chunk(p.read_text(encoding="utf-8"), p.stem.replace("_", " ").title()):
                c["source"] = p.name
                chunks.append(c)
        for p, label in EXTRA_DOCS:
            if p.exists():
                for c in _chunk(p.read_text(encoding="utf-8"), label):
                    c["source"] = p.name
                    chunks.append(c)
        for i, c in enumerate(chunks):
            c["id"] = i
        self.chunks = chunks
        texts = [f"{c['section']}. {c['text']}" for c in chunks]
        self._tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english", min_df=1)
        self._tf_mat = self._tfidf.fit_transform(texts)
        self.mode = "keyword (TF-IDF)"
        try:
            self._load_dense(texts)
            self.mode = "hybrid (MiniLM dense + TF-IDF, RRF)"
        except Exception as exc:   # offline / model missing -> degrade gracefully
            self.mode = f"keyword (TF-IDF); dense unavailable: {type(exc).__name__}"

    def _encode(self, texts: List[str]) -> np.ndarray:
        import torch
        out = []
        for i in range(0, len(texts), 32):
            batch = self._tokenizer(texts[i:i + 32], padding=True, truncation=True, max_length=256, return_tensors="pt")
            with torch.no_grad():
                h = self._model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).float()
            v = (h * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            v = torch.nn.functional.normalize(v, dim=1)
            out.append(v.numpy())
        return np.vstack(out).astype(np.float32)

    def _load_dense(self, texts: List[str]) -> None:
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from transformers import AutoModel, AutoTokenizer
        name = "sentence-transformers/all-MiniLM-L6-v2"
        self._tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=True)
        self._model = AutoModel.from_pretrained(name, local_files_only=True).eval()
        key = hashlib.sha1("\n".join(texts).encode()).hexdigest()
        if CACHE.exists():
            z = np.load(CACHE, allow_pickle=False)
            if str(z["key"]) == key:
                self._emb = z["emb"]
                return
        self._emb = self._encode(texts)
        CACHE.parent.mkdir(exist_ok=True)
        np.savez(CACHE, key=np.array(key), emb=self._emb)

    # ---- query ---------------------------------------------------------- #
    def search(self, query: str, k: int = 4, min_score: float = 0.0) -> List[Dict[str, Any]]:
        if not self.chunks or not query.strip():
            return []
        with self._lock:
            sparse = (self._tf_mat @ self._tfidf.transform([query]).T).toarray().ravel()
            ranks: Dict[int, float] = {}
            for order in (np.argsort(-sparse)[:20],):
                for r, idx in enumerate(order):
                    if sparse[idx] > 0:
                        ranks[int(idx)] = ranks.get(int(idx), 0) + 1.0 / (60 + r)
            dense = None
            if self._emb is not None:
                q = self._encode([query])[0]
                dense = self._emb @ q
                for r, idx in enumerate(np.argsort(-dense)[:20]):
                    ranks[int(idx)] = ranks.get(int(idx), 0) + 1.0 / (60 + r)
        best = sorted(ranks.items(), key=lambda kv: -kv[1])[:k]
        out = []
        for idx, s in best:
            c = self.chunks[idx]
            out.append({
                "id": c["id"], "title": c["title"], "section": c["section"], "source": c["source"],
                "text": c["text"], "score": round(s * 60 / 2, 3),
                "keyword": round(float(sparse[idx]), 3),
                "semantic": round(float(dense[idx]), 3) if dense is not None else None,
            })
        # drop weak matches: require some lexical OR semantic support
        return [o for o in out if o["keyword"] > 0.02 or (o["semantic"] or 0) > 0.30]

    def stats(self) -> Dict[str, Any]:
        return {"mode": self.mode, "chunks": len(self.chunks),
                "documents": len({c["source"] for c in self.chunks})}


# --------------------------------------------------------------------------- #
class SimilarCases:
    """k-NN over the documented dataset using structured features only."""

    REGIONS = ["FACE", "NOSE", "EAR", "LIP", "SCALP", "NECK", "CHEST", "BACK", "ABDOMEN", "ARM", "FOREARM", "HAND", "THIGH", "FOOT"]
    FLAGS = ["itch", "grew", "hurt", "changed", "bleed", "elevation"]

    def __init__(self) -> None:
        self.df = None
        self.X = None

    def build(self, metadata_csv: Path) -> None:
        import pandas as pd
        df = pd.read_csv(metadata_csv)
        df = df[df["age"].notna() & df["region"].notna()].reset_index(drop=True)
        self.df = df
        self.X = np.vstack([self._vec(r) for r in df.to_dict("records")]).astype(np.float32)

    def _vec(self, m: Dict[str, Any]) -> np.ndarray:
        def f(x, default=0.0):
            try:
                v = float(x)
                return default if np.isnan(v) else v
            except (TypeError, ValueError):
                return default
        age = f(m.get("age"), 55) / 100.0
        d = max(f(m.get("diameter_1")), f(m.get("diameter_2"))) / 30.0
        sex = 1.0 if str(m.get("gender", "")).upper() == "MALE" else 0.0
        reg = [1.0 if str(m.get("region", "")).upper() == r else 0.0 for r in self.REGIONS]
        flags = [1.0 if str(m.get(k, "")).upper() == "TRUE" else 0.0 for k in self.FLAGS]
        fitz = f(m.get("fitspatrick"), 3) / 6.0
        v = np.array([age * 2.0, d * 2.0, sex * 0.5, fitz] + [x * 1.2 for x in reg] + [x * 0.8 for x in flags])
        n = np.linalg.norm(v)
        return v / n if n else v

    def query(self, metadata: Dict[str, Any], k: int = 8, exclude_img: Optional[str] = None) -> Dict[str, Any]:
        if self.df is None or not metadata:
            return {"cases": [], "distribution": {}, "k": 0}
        sims = self.X @ self._vec(metadata)
        order = np.argsort(-sims)
        cases = []
        for idx in order:
            row = self.df.iloc[int(idx)]
            if exclude_img and row["img_id"] == exclude_img:
                continue
            cases.append({
                "img_id": row["img_id"], "diagnosis": row["diagnostic"], "age": int(row["age"]),
                "sex": row["gender"] if isinstance(row["gender"], str) else None, "region": row["region"],
                "diameter": float(max(row["diameter_1"] or 0, row["diameter_2"] or 0)) if not (row["diameter_1"] != row["diameter_1"]) else None,
                "similarity": round(float(sims[idx]), 3),
            })
            if len(cases) >= k:
                break
        dist: Dict[str, int] = {}
        for c in cases:
            dist[c["diagnosis"]] = dist.get(c["diagnosis"], 0) + 1
        return {"cases": cases, "distribution": dist, "k": len(cases)}
