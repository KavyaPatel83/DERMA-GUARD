"""
src/retrieval/rag_index.py — RAG Index for DERMA-GUARD v4.0.

CRITICAL FIX: Index individual modality embedding CONCATENATIONS, not fused embeddings.
  - Training: concatenate [z_clinical, z_dermo, z_meta, z_text] per case
  - Inference: same concatenation for the test case
  - NEVER index fused embeddings (circular — fusion depends on RAG which depends on fusion)

Index type: FAISS IndexFlatIP (inner product = cosine after L2 normalisation).
Default k = 8 similar cases.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch


# Default individual embedding dims (must match VisionSpecialistTeam + ScribeAgent)
DEFAULT_EMBEDDING_DIMS = {
    "clinical_embedding":    768,   # Swin-Tiny or DermLIP
    "dermoscopy_embedding":  768,   # Swin-Tiny dermoscopy
    "metadata_embedding":    64,    # MetadataEncoder
    "text_embedding":        768,   # ClinicalBERT
}

TOTAL_DIM = sum(DEFAULT_EMBEDDING_DIMS.values())  # 768 + 768 + 64 + 768 = 2368


def l2_normalize(x: np.ndarray) -> np.ndarray:
    """L2 normalise rows of a 2D array (for cosine similarity via inner product)."""
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(norms, 1e-8)


def concat_modality_embeddings(case: Dict) -> np.ndarray:
    """Concatenate individual modality embeddings for indexing/querying.

    Args:
        case: dict with keys matching DEFAULT_EMBEDDING_DIMS

    Returns:
        1D numpy array of concatenated embeddings (TOTAL_DIM,)
    """
    parts = []
    for key, dim in DEFAULT_EMBEDDING_DIMS.items():
        emb = case.get(key)
        if emb is None:
            parts.append(np.zeros(dim, dtype=np.float32))
        elif isinstance(emb, torch.Tensor):
            parts.append(emb.detach().cpu().numpy().flatten()[:dim])
        else:
            arr = np.array(emb, dtype=np.float32).flatten()
            if len(arr) < dim:
                arr = np.pad(arr, (0, dim - len(arr)))
            parts.append(arr[:dim])
    return np.concatenate(parts, axis=0).astype(np.float32)


def proportion_sharing_predicted_diagnosis(
    similar_cases: List[Dict],
    predicted_diagnosis: Optional[int] = None,
) -> float:
    """Compute fraction of similar cases sharing the predicted diagnosis."""
    if not similar_cases:
        return 0.0
    if predicted_diagnosis is None:
        return 0.0
    matching = sum(
        1 for c in similar_cases
        if c.get("label") == predicted_diagnosis or c.get("diagnosis") == predicted_diagnosis
    )
    return matching / len(similar_cases)


class RAGIndex:
    """FAISS-based RAG index over individual modality embeddings.

    Usage:
        # Build at training time
        index = RAGIndex()
        index.add_training_cases(training_cases)
        index.save("outputs/rag_index")

        # Query at inference
        index.load("outputs/rag_index")
        result = index.query(test_case, k=8)
    """

    def __init__(self, total_dim: int = TOTAL_DIM):
        self.total_dim = total_dim
        self._index = None
        self._training_cases: List[Dict] = []

    def add_training_cases(self, cases: List[Dict]) -> "RAGIndex":
        """Build FAISS index from training cases.

        CRITICAL: uses individual modality concatenation, NOT fused embeddings.

        Args:
            cases: list of dicts, each with embedding keys and 'label'/'diagnosis'.
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")

        embeddings = []
        for case in cases:
            emb = concat_modality_embeddings(case)
            embeddings.append(emb)

        if not embeddings:
            print("[RAGIndex] No training cases provided. Index not built.")
            return self

        emb_matrix = np.stack(embeddings, axis=0).astype(np.float32)  # (N, D)
        # L2 normalise for cosine similarity via inner product
        emb_matrix = l2_normalize(emb_matrix)

        self._index = faiss.IndexFlatIP(self.total_dim)
        self._index.add(emb_matrix)
        self._training_cases = list(cases)
        print(f"[RAGIndex] Indexed {len(cases)} training cases (dim={self.total_dim})")
        return self

    def query(
        self,
        case: Dict,
        k: int = 8,
        predicted_diagnosis: Optional[int] = None,
    ) -> Dict:
        """Find k most similar training cases.

        CRITICAL: query uses individual modality concatenation (same as index).

        Args:
            case:                 dict with embedding keys
            k:                    number of neighbours to retrieve
            predicted_diagnosis:  if provided, computes agreement_rate

        Returns:
            dict with:
                similar_cases:  list of k case dicts with 'distance' added
                agreement_rate: fraction sharing predicted_diagnosis
        """
        if self._index is None or not self._training_cases:
            return {"similar_cases": [], "agreement_rate": 0.0}

        query_emb = concat_modality_embeddings(case).reshape(1, -1)
        query_emb = l2_normalize(query_emb)

        actual_k = min(k, self._index.ntotal)
        if actual_k == 0:
            return {"similar_cases": [], "agreement_rate": 0.0}

        distances, indices = self._index.search(query_emb, actual_k)

        similar_cases = []
        for i in range(actual_k):
            idx = int(indices[0][i])
            if 0 <= idx < len(self._training_cases):
                case_copy = dict(self._training_cases[idx])
                # Remove raw embedding tensors (too large for JSON / LLM context)
                for key in DEFAULT_EMBEDDING_DIMS:
                    case_copy.pop(key, None)
                case_copy["distance"] = float(distances[0][i])
                similar_cases.append(case_copy)

        agreement_rate = proportion_sharing_predicted_diagnosis(similar_cases, predicted_diagnosis)

        return {
            "similar_cases": similar_cases,
            "agreement_rate": agreement_rate,
        }

    def save(self, path: str) -> None:
        """Save index and metadata to disk."""
        import faiss
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path.with_suffix(".index")))
        meta_path = path.with_suffix(".json")
        # Save only non-tensor metadata
        safe_cases = []
        for c in self._training_cases:
            safe_c = {k: v for k, v in c.items() if not hasattr(v, "numpy")}
            safe_cases.append(safe_c)
        with open(meta_path, "w") as f:
            json.dump(safe_cases, f, default=str)
        print(f"[RAGIndex] Saved index → {path}.index + .json")

    def load(self, path: str) -> "RAGIndex":
        """Load index from disk."""
        import faiss
        path = Path(path)
        index_path = path.with_suffix(".index")
        meta_path = path.with_suffix(".json")
        if not index_path.exists():
            raise FileNotFoundError(f"RAG index not found at {index_path}")
        self._index = faiss.read_index(str(index_path))
        self.total_dim = self._index.d
        with open(meta_path) as f:
            self._training_cases = json.load(f)
        print(f"[RAGIndex] Loaded {len(self._training_cases)} cases (dim={self.total_dim})")
        return self
