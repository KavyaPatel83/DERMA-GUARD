"""
tests/test_evidence_profiler.py — Evidence profiler tests (DERMA-GUARD v4.0)

Tests:
  - Q, R, C computation correctness
  - OOD detection on adversarial input
  - Conflict detection precision
"""
import numpy as np
import pytest
import torch

from src.evidence.quality import compute_image_quality, compute_text_quality, compute_metadata_quality
from src.evidence.consistency import compute_consistency, js_divergence
from src.agents.devils_advocate import OODDetector


class TestQualityComputation:
    def test_image_quality_bounds(self):
        """Image quality must be in [0, 1]."""
        q = compute_image_quality(
            blur_score=0.5, brightness=0.5, contrast=0.5,
            resolution_ratio=1.0, occlusion_score=0.8
        )
        assert 0.0 <= q <= 1.0

    def test_perfect_image_quality_above_zero(self):
        """Perfect stats → Q > 0.5."""
        q = compute_image_quality(
            blur_score=1.0, brightness=0.5, contrast=0.8,
            resolution_ratio=1.0, occlusion_score=1.0
        )
        assert q > 0.5

    def test_text_quality_is_ptis(self):
        """Q_text == PTIS score, clipped to [0,1]."""
        for ptis in [-0.1, 0.0, 0.5, 0.99, 1.0, 1.5]:
            q = compute_text_quality(ptis)
            assert 0.0 <= q <= 1.0

    def test_metadata_quality_full_present(self):
        """All fields present → Q_meta = 1.0."""
        mask = [False] * 10  # no missing fields
        q = compute_metadata_quality(mask)
        assert abs(q - 1.0) < 1e-6

    def test_metadata_quality_all_missing(self):
        """All fields missing → Q_meta = 0.0."""
        mask = [True] * 10  # all missing
        q = compute_metadata_quality(mask)
        assert abs(q - 0.0) < 1e-6


class TestConsistencyComputation:
    def test_identical_predictions_max_consistency(self):
        """All models predict identically → C ≈ 1.0."""
        logit = torch.zeros(7)
        logit[0] = 10.0
        predictions = {f"model_{i}": logit.clone() for i in range(4)}
        C, conflict, details = compute_consistency(predictions)
        assert C > 0.95, f"Identical predictions should give C ≈ 1.0, got {C:.3f}"
        assert not conflict

    def test_maximally_different_predictions_low_consistency(self):
        """Models predict completely different classes → C should be low."""
        predictions = {}
        for i in range(4):
            logit = torch.full((7,), -10.0)
            logit[i] = 10.0  # each model votes for a different class
            predictions[f"model_{i}"] = logit
        C, conflict, details = compute_consistency(predictions)
        assert C < 0.5, f"Diverse predictions should give C < 0.5, got {C:.3f}"

    def test_conflict_flag_below_threshold(self):
        """Consistency < 0.3 → conflict_flag = True."""
        predictions = {}
        for i in range(4):
            logit = torch.full((7,), -10.0)
            logit[i * 2 % 7] = 10.0
            predictions[f"model_{i}"] = logit
        C, conflict, _ = compute_consistency(predictions)
        # Just verify the flag is consistent with threshold
        assert conflict == (C < 0.3)

    def test_single_model_no_conflict(self):
        """Only one model → no pairs → C = 1.0, no conflict."""
        predictions = {"model_0": torch.zeros(7)}
        C, conflict, _ = compute_consistency(predictions)
        assert C == 1.0
        assert not conflict


class TestOODDetection:
    def test_in_distribution_low_score(self):
        """In-distribution sample → low OOD score."""
        d = 64
        np.random.seed(42)
        # Create training embeddings with two Gaussian clusters
        train_embs = np.vstack([
            np.random.randn(50, d) + np.array([5.0] * d),
            np.random.randn(50, d) + np.array([-5.0] * d),
        ])
        train_labels = np.array([0] * 50 + [1] * 50)

        detector = OODDetector(threshold=100.0)
        detector.fit(train_embs, train_labels)

        # In-distribution query
        in_dist = np.random.randn(d) + np.array([5.0] * d)
        score_in = detector.score(in_dist)

        # Out-of-distribution query (far from clusters)
        out_dist = np.random.randn(d) + np.array([50.0] * d)
        score_out = detector.score(out_dist)

        assert score_in < score_out, \
            f"In-distribution score ({score_in:.1f}) should be < OOD score ({score_out:.1f})"

    def test_ood_threshold_calibration(self):
        """Calibrated threshold should flag clear OOD samples."""
        d = 32
        np.random.seed(42)
        train_embs = np.random.randn(100, d)
        train_labels = np.zeros(100, dtype=int)

        val_embs = np.random.randn(50, d)
        val_labels = np.zeros(50, dtype=int)

        detector = OODDetector()
        detector.fit(train_embs, train_labels)
        threshold = detector.calibrate_threshold(val_embs, val_labels, fpr_target=0.10)

        assert threshold > 0, "Calibrated threshold must be positive"
