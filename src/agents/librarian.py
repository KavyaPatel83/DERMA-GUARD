"""src/agents/librarian.py — Librarian Agent wraps RAGIndex for similar-case retrieval."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from src.retrieval.rag_index import RAGIndex


class LibrarianAgent:
    """Manages the RAG index and serves similar-case queries to the Orchestrator.

    Wraps RAGIndex. The Orchestrator calls this via tool-calling.
    """

    def __init__(self, index_path: Optional[str] = None, k: int = 8):
        self.k = k
        self._index = RAGIndex()
        self._loaded = False

        if index_path and Path(index_path).with_suffix(".index").exists():
            try:
                self._index.load(index_path)
                self._loaded = True
            except Exception as e:
                import warnings
                warnings.warn(f"[Librarian] Could not load index: {e}")

    def retrieve(
        self,
        query_embeddings: Dict,
        predicted_diagnosis: Optional[int] = None,
    ) -> Dict:
        """Retrieve k similar training cases.

        Args:
            query_embeddings: dict with clinical_embedding, dermoscopy_embedding,
                              metadata_embedding, text_embedding
            predicted_diagnosis: for agreement rate computation

        Returns:
            dict with similar_cases and agreement_rate
        """
        if not self._loaded:
            return {"similar_cases": [], "agreement_rate": 0.0,
                    "note": "RAG index not loaded — run scripts to build index first."}

        return self._index.query(
            query_embeddings,
            k=self.k,
            predicted_diagnosis=predicted_diagnosis,
        )

    def build_from_cases(self, training_cases: List[Dict]) -> "LibrarianAgent":
        """Build index from training case list."""
        self._index.add_training_cases(training_cases)
        self._loaded = True
        return self

    def save(self, path: str):
        self._index.save(path)

    def load(self, path: str):
        self._index.load(path)
        self._loaded = True
