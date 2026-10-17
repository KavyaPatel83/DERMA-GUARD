"""
src/fusion/acquisition.py — Acquisition Policy (DERMA-GUARD v4.0)

Uses GradientBoostingRegressor (scikit-learn) to predict expected
uncertainty reduction / cost for each candidate acquisition action.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


ALL_MODALITIES = ["clinical_image", "dermoscopy_image", "metadata", "text"]

FOLLOW_UP_QUESTIONS = [
    "ask_growth",
    "ask_bleeding",
    "ask_color_change",
    "ask_duration",
    "ask_pain",
    "ask_itching",
]

CANDIDATE_ACTIONS = ALL_MODALITIES + FOLLOW_UP_QUESTIONS

# Cost (relative): acquiring a dermoscopy image >> clinical photo >> asking a question
ACTION_COSTS = {
    "clinical_image":    5.0,
    "dermoscopy_image":  8.0,
    "metadata":          2.0,
    "text":              1.0,
    "ask_growth":        0.5,
    "ask_bleeding":      0.5,
    "ask_color_change":  0.5,
    "ask_duration":      0.5,
    "ask_pain":          0.5,
    "ask_itching":       0.5,
}


def encode_case_features(
    case_features: Dict,
    action: str,
) -> np.ndarray:
    """Encode (case_features, action) as a feature vector for the policy model.

    case_features:
        current_entropy:        float — predictive entropy of current fusion
        missing_count:          int — number of missing modalities
        metadata_completeness:  float ∈ [0,1]
        ptis:                   float ∈ [0,1] — text informativeness
        ood_score:              float — Mahalanobis distance
        consistency:            float ∈ [0,1]

    Action is one-hot encoded within CANDIDATE_ACTIONS.
    """
    action_idx = CANDIDATE_ACTIONS.index(action) if action in CANDIDATE_ACTIONS else 0
    action_onehot = np.zeros(len(CANDIDATE_ACTIONS))
    action_onehot[action_idx] = 1.0

    feats = np.array([
        float(case_features.get("current_entropy", 0.5)),
        float(case_features.get("missing_count", 0)),
        float(case_features.get("metadata_completeness", 1.0)),
        float(case_features.get("ptis", 0.5)),
        float(case_features.get("ood_score", 0.0)) / 100.0,  # normalise
        float(case_features.get("consistency", 1.0)),
    ])
    return np.concatenate([feats, action_onehot])


class AcquisitionPolicy:
    """Selects the best acquisition action to reduce uncertainty.

    Uses GradientBoostingRegressor trained on validation data to predict
    expected uncertainty reduction for each candidate action.

    Acquisition value = expected_uncertainty_reduction / cost

    Actions:
        Modalities: clinical_image, dermoscopy_image, metadata, text
        Questions:  ask_growth, ask_bleeding, ask_color_change, ask_duration, ...
    """

    def __init__(self, model_path: Optional[str] = None):
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            self._model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )
        except ImportError:
            warnings.warn("[AcquisitionPolicy] scikit-learn not installed. Using random policy.")
            self._model = None

        self._fitted = False

        if model_path and Path(model_path).exists():
            self.load(model_path)

    def train(
        self,
        X: np.ndarray,   # (N, feature_dim)
        y: np.ndarray,   # (N,) expected uncertainty reductions
    ) -> "AcquisitionPolicy":
        """Train the policy on validation-set observations."""
        if self._model is None:
            return self
        self._model.fit(X, y)
        self._fitted = True
        return self

    def select_action(
        self,
        case_features: Dict,
        available_modalities: List[str],
    ) -> str:
        """Select the best acquisition action.

        Args:
            case_features: dict with entropy, missing_count, ptis, ood_score, etc.
            available_modalities: list of modalities already available

        Returns:
            action name (e.g. 'dermoscopy_image' or 'ask_growth')
        """
        # Candidates: unavailable modalities + follow-up questions
        candidates = [m for m in ALL_MODALITIES if m not in available_modalities]
        candidates += FOLLOW_UP_QUESTIONS

        if not candidates:
            return "ask_growth"  # fallback

        if self._model is None or not self._fitted:
            return self._random_policy(candidates, case_features)

        best_action = None
        best_value = float("-inf")

        for action in candidates:
            feat = encode_case_features(case_features, action).reshape(1, -1)
            expected_reduction = float(self._model.predict(feat)[0])
            cost = ACTION_COSTS.get(action, 1.0)
            value = expected_reduction / max(cost, 1e-8)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action or candidates[0]

    def _random_policy(self, candidates: List[str], case_features: Dict) -> str:
        """Fallback: prefer modality acquisition over questions, then random."""
        modality_candidates = [c for c in candidates if c in ALL_MODALITIES]
        if modality_candidates:
            # Prefer the cheapest modality
            return min(modality_candidates, key=lambda a: ACTION_COSTS.get(a, 99.0))
        return candidates[0]

    def save(self, path: str):
        """Save trained model to disk."""
        import pickle
        with open(path, "wb") as f:
            pickle.dump({"model": self._model, "fitted": self._fitted}, f)

    def load(self, path: str) -> "AcquisitionPolicy":
        """Load model from disk."""
        import pickle
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self._model = data["model"]
            self._fitted = data["fitted"]
        except Exception as e:
            warnings.warn(f"[AcquisitionPolicy] Could not load from {path}: {e}")
        return self
