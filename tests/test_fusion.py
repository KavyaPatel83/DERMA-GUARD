"""
tests/test_fusion.py — Fusion module tests (DERMA-GUARD v4.0)

Tests:
  - Convergence in ≤3 iterations
  - Weight sum = 1.0 (after renormalization)
  - Missing modality masking (zero weights for missing)
  - Zero-division guard on all-missing input
"""
import pytest
import torch
import numpy as np

from src.fusion.adaptive_fusion import DiagnosisAdaptiveFusion, InsufficientEvidenceError


NUM_CLASSES = 7
NUM_MODALITIES = 5
D_COMMON = 64   # smaller for tests


@pytest.fixture
def fusion_model():
    """Small fusion model for testing."""
    return DiagnosisAdaptiveFusion(
        num_modalities=NUM_MODALITIES,
        num_classes=NUM_CLASSES,
        d_common=D_COMMON,
        max_iterations=3,
        convergence_threshold=0.05,
    )


def make_dummy_embeddings(num_modalities=5, d_common=64):
    """Create dummy projected embeddings (already d_common dim for simplicity)."""
    names = [
        "dermlip_panderm", "panderm", "swin_tiny_clinical",
        "swin_tiny_dermoscopy", "resnet152"
    ]
    embs = {name: torch.randn(1, d_common) for name in names[:num_modalities]}
    return embs


def make_quality_reliability_utility(n=5):
    q = {f"model_{i}": 0.7 for i in range(n)}
    r = {f"model_{i}": 0.8 for i in range(n)}
    u = {f"model_{i}": 0.5 for i in range(n)}
    return q, r, u


class TestFusionConvergence:
    def test_converges_within_max_iterations(self, fusion_model):
        """Fusion must converge in ≤ max_iterations=3."""
        # Override projector to accept d_common input directly
        embeddings = make_dummy_embeddings(d_common=D_COMMON)
        # Patch projector to be identity for testing
        fusion_model.projector.projectors = torch.nn.ModuleDict({
            k: torch.nn.Identity() for k in embeddings.keys()
        })
        # Also fix embedding dims
        for k in embeddings:
            fusion_model.EMBEDDING_DIMS[k] = D_COMMON

        missing_mask = torch.ones(NUM_MODALITIES)
        quality = {"clinical": 0.8, "dermoscopy": 0.7, **{k: 0.7 for k in embeddings}}
        reliability = {k: 0.8 for k in embeddings}
        utility = {k: 0.5 for k in embeddings}

        result = fusion_model.fuse(
            embeddings=embeddings,
            quality=quality,
            reliability=reliability,
            utility=utility,
            consistency=0.9,
            missing_mask=missing_mask,
        )

        assert result.iterations_used <= fusion_model.max_iterations, \
            f"Took {result.iterations_used} > {fusion_model.max_iterations} iterations"


class TestWeightNormalization:
    def test_weights_sum_to_one(self, fusion_model):
        """Weight vector must sum to 1.0 after renormalization."""
        embeddings = make_dummy_embeddings(d_common=D_COMMON)
        for k in embeddings:
            fusion_model.EMBEDDING_DIMS[k] = D_COMMON
        fusion_model.projector.projectors = torch.nn.ModuleDict({
            k: torch.nn.Identity() for k in embeddings.keys()
        })
        missing_mask = torch.ones(NUM_MODALITIES)
        result = fusion_model.fuse(
            embeddings=embeddings,
            quality={"clinical": 0.7, **{k: 0.7 for k in embeddings}},
            reliability={k: 0.8 for k in embeddings},
            utility={k: 0.5 for k in embeddings},
            consistency=0.9,
            missing_mask=missing_mask,
        )
        # Weights of available modalities must sum to 1.0
        weight_sum = result.weights[missing_mask.bool()].sum().item()
        assert abs(weight_sum - 1.0) < 0.02, f"Weights sum = {weight_sum}, expected 1.0"

    def test_missing_modality_weight_is_zero(self, fusion_model):
        """Missing modalities (mask=0) must receive zero weight."""
        embeddings = make_dummy_embeddings(d_common=D_COMMON)
        for k in embeddings:
            fusion_model.EMBEDDING_DIMS[k] = D_COMMON
        fusion_model.projector.projectors = torch.nn.ModuleDict({
            k: torch.nn.Identity() for k in embeddings.keys()
        })
        # Mask out first modality
        missing_mask = torch.ones(NUM_MODALITIES)
        missing_mask[0] = 0.0  # first modality missing

        result = fusion_model.fuse(
            embeddings=embeddings,
            quality={"clinical": 0.7, **{k: 0.7 for k in embeddings}},
            reliability={k: 0.8 for k in embeddings},
            utility={k: 0.5 for k in embeddings},
            consistency=0.9,
            missing_mask=missing_mask,
        )
        assert result.weights[0].item() < 1e-6, \
            f"Missing modality weight = {result.weights[0].item()}, expected ≈ 0"


class TestZeroDivisionGuard:
    def test_all_missing_raises_insufficient_evidence(self, fusion_model):
        """All modalities missing → InsufficientEvidenceError must be raised."""
        embeddings = make_dummy_embeddings(d_common=D_COMMON)
        missing_mask = torch.zeros(NUM_MODALITIES)  # ALL missing

        with pytest.raises(InsufficientEvidenceError):
            fusion_model.fuse(
                embeddings=embeddings,
                quality={},
                reliability={},
                utility={},
                consistency=1.0,
                missing_mask=missing_mask,
            )

    def test_single_modality_available(self, fusion_model):
        """Only one modality available → fusion should still work."""
        embeddings = make_dummy_embeddings(d_common=D_COMMON)
        for k in embeddings:
            fusion_model.EMBEDDING_DIMS[k] = D_COMMON
        fusion_model.projector.projectors = torch.nn.ModuleDict({
            k: torch.nn.Identity() for k in embeddings.keys()
        })
        missing_mask = torch.zeros(NUM_MODALITIES)
        missing_mask[0] = 1.0  # only first available

        result = fusion_model.fuse(
            embeddings=embeddings,
            quality={"clinical": 0.7, **{k: 0.7 for k in embeddings}},
            reliability={k: 0.8 for k in embeddings},
            utility={k: 0.5 for k in embeddings},
            consistency=1.0,
            missing_mask=missing_mask,
        )
        assert result.weights[0].item() > 0.99, "Single available modality should get weight ≈ 1"
