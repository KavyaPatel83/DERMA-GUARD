"""
src/fusion/adaptive_fusion.py — Iterative EM-Style DiagnosisAdaptiveFusion.

DERMA-GUARD v4.0 core algorithm.

CRITICAL FIXES implemented:
1. Missing modality masking: softmax weights × binary mask, then renormalize.
   If all modalities missing → raise INSUFFICIENT_EVIDENCE (never divide by zero).
2. Class imbalance: Focal Loss (gamma=2.0) + class weights = N / (n_classes * n_c)
3. Gradient clipping: torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
4. Mixed precision: torch.cuda.amp autocast (enabled in training loop)
5. Early stopping: on validation macro-F1 (NOT loss), patience=10
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Feature projector — harmonise heterogeneous embedding dimensions
# ---------------------------------------------------------------------------

class ModalityProjector(nn.Module):
    """Project modality-specific embeddings to a common d_common dimension."""

    def __init__(self, input_dims: Dict[str, int], d_common: int = 768):
        super().__init__()
        self.projectors = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(dim, d_common),
                nn.LayerNorm(d_common),
                nn.ReLU(),
            )
            for name, dim in input_dims.items()
        })
        self.d_common = d_common

    def forward(self, embeddings: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Project all available embeddings to d_common dimension."""
        projected = {}
        for name, emb in embeddings.items():
            if name in self.projectors:
                projected[name] = self.projectors[name](emb)
        return projected


# ---------------------------------------------------------------------------
# Weight computation MLP: [Q, R, U, C] → weight logit per modality
# ---------------------------------------------------------------------------

class WeightLogitNetwork(nn.Module):
    """MLP: [Q_agg, R_agg, U_agg, C] (4 inputs) → (num_modalities,) weight logits.

    Per spec Part 5: f maps 4 aggregate evidence scalars to a logit vector
    over all modalities — NOT called once per modality with a scalar output.
    """

    def __init__(self, num_modalities: int = 5):
        super().__init__()
        self.num_modalities = num_modalities
        self.net = nn.Sequential(
            nn.Linear(4, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_modalities),  # output: logit per modality
        )

    def forward(self, evidence_vector: torch.Tensor) -> torch.Tensor:
        """evidence_vector: (4,) = [Q_agg, R_agg, U_agg, C] → (num_modalities,) logits."""
        return self.net(evidence_vector.unsqueeze(0)).squeeze(0)  # (M,)


# ---------------------------------------------------------------------------
# Focal Loss with class weights
# ---------------------------------------------------------------------------

class FocalLossWithWeights(nn.Module):
    """Focal Loss (gamma=2.0) + inverse-frequency class weights.

    weight_c = N / (n_classes * n_c)
    """

    def __init__(self, gamma: float = 2.0, weight: Optional[torch.Tensor] = None):
        super().__init__()
        self.gamma = gamma
        self.register_buffer("weight", weight)

    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """logits: (B, K), labels: (B,) → scalar loss."""
        ce = F.cross_entropy(logits, labels, weight=self.weight, reduction="none")
        pt = torch.exp(-ce)
        focal = ((1 - pt) ** self.gamma) * ce
        return focal.mean()

    @staticmethod
    def compute_class_weights(labels: torch.Tensor, num_classes: int) -> torch.Tensor:
        """Compute inverse-frequency weights: N / (num_classes × n_c)."""
        N = len(labels)
        weights = torch.zeros(num_classes)
        for c in range(num_classes):
            n_c = (labels == c).sum().item()
            weights[c] = N / (num_classes * max(n_c, 1))
        return weights


# ---------------------------------------------------------------------------
# DiagnosisAdaptiveFusion
# ---------------------------------------------------------------------------

class InsufficientEvidenceError(Exception):
    """Raised when ALL modalities are missing — pipeline should ABSTAIN."""
    pass


@dataclass
class FusionResult:
    """Output of DiagnosisAdaptiveFusion.fuse()."""
    prediction: torch.Tensor       # (K,) logits
    diagnosis: int                 # argmax of final prediction
    confidence: float              # max(softmax(prediction))
    weights: torch.Tensor          # (M,) per-modality weights
    fused_embedding: torch.Tensor  # (d_common,) fused embedding
    iterations_used: int           # how many EM iterations ran
    converged: bool                # whether convergence was achieved


class DiagnosisAdaptiveFusion(nn.Module):
    """Iterative EM-style diagnosis-adaptive fusion.

    Architecture:
        f:         WeightLogitNetwork — computes weight logits from [Q, R, U, C]
        W_prior:   (num_classes, num_modalities) — diagnosis-adaptive prior
        alpha:     learnable scalar for f contribution
        beta:      learnable scalar for W_prior contribution
        gamma:     learnable scalar for conflict penalty contribution
        projector: ModalityProjector — harmonise heterogeneous dims
        classifier: Linear(d_common, num_classes) — final prediction

    Training notes:
        - Use FocalLossWithWeights (gamma=2.0)
        - Gradient clip max_norm=1.0
        - Mixed precision (torch.cuda.amp)
        - Early stop on val macro-F1, patience=10
    """

    # Canonical modality ordering
    MODALITY_NAMES = [
        "dermlip_panderm",
        "panderm",
        "swin_tiny_clinical",
        "swin_tiny_dermoscopy",
        "resnet152",
    ]

    EMBEDDING_DIMS = {
        "dermlip_panderm":    768,
        "panderm":            768,
        "swin_tiny_clinical": 768,
        "swin_tiny_dermoscopy": 768,
        "resnet152":          2048,
    }

    def __init__(
        self,
        num_modalities: int = 5,
        num_classes: int = 7,
        d_common: int = 768,
        max_iterations: int = 3,
        convergence_threshold: float = 0.05,
    ):
        super().__init__()
        self.num_modalities = num_modalities
        self.num_classes = num_classes
        self.d_common = d_common
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

        # Weight logit network: [Q_agg, R_agg, U_agg, C] → (num_modalities,) logits
        self.f = WeightLogitNetwork(num_modalities)

        # Diagnosis-adaptive prior: (K, M)
        self.W_prior = nn.Parameter(torch.randn(num_classes, num_modalities) * 0.01)

        # Learnable scalars (initialised as in spec)
        self.alpha = nn.Parameter(torch.tensor(1.0))
        self.beta = nn.Parameter(torch.tensor(1.0))
        self.gamma_param = nn.Parameter(torch.tensor(0.5))

        # Projector for heterogeneous embedding dims
        self.projector = ModalityProjector(self.EMBEDDING_DIMS, d_common)

        # Final classification head
        self.classifier = nn.Linear(d_common, num_classes)

    def compute_conflict_penalty(
        self,
        available_embeddings: Dict[str, torch.Tensor],
        diag: int,
    ) -> torch.Tensor:
        """Penalise modalities that conflict with the current diagnosis.

        For each modality m, penalty_m = 1 - probability_of_diag_under_m.
        Returns (M,) tensor.
        """
        penalties = []
        for name in self.MODALITY_NAMES:
            if name in available_embeddings:
                emb = available_embeddings[name]           # (B, d_common)
                logits_m = self.classifier(emb)            # (B, K)
                prob_diag = F.softmax(logits_m, dim=-1)[:, diag].mean()
                penalties.append(float(1.0 - prob_diag.item()))
            else:
                penalties.append(0.0)  # missing → no penalty
        return torch.tensor(penalties, dtype=torch.float32)

    def fuse(
        self,
        embeddings: Dict[str, torch.Tensor],    # modality → (B, embed_dim)
        quality: Dict[str, float],              # modality → Q
        reliability: Dict[str, float],          # modality → R
        utility: Dict[str, float],              # modality → U (approx)
        consistency: float,                     # global consistency C
        missing_mask: torch.Tensor,             # (M,) binary [0,1] (1=available)
    ) -> FusionResult:
        """Execute iterative EM-style fusion.

        Args:
            embeddings:   per-modality tensors (heterogeneous dims, pre-projection)
            quality:      Q per modality
            reliability:  R per modality
            utility:      U per modality (approximate)
            consistency:  global consistency C
            missing_mask: (M,) binary tensor, same order as MODALITY_NAMES

        Returns:
            FusionResult

        Raises:
            InsufficientEvidenceError: if ALL modalities are missing.
        """
        # Guard: all-missing
        if missing_mask.sum() == 0:
            raise InsufficientEvidenceError(
                "All modalities are missing. Cannot perform fusion. Pipeline should ABSTAIN."
            )

        device = next(self.parameters()).device
        missing_mask = missing_mask.to(device)

        # Project all available embeddings to d_common
        available_projected = self.projector(embeddings)  # name → (B, d_common)

        # ---- Iteration 0: No diagnosis prior ---------------------------------
        w_logits = self._compute_weight_logits(quality, reliability, utility, consistency)  # (M,)
        w = F.softmax(self.alpha * w_logits, dim=-1) * missing_mask
        # Renormalize (guard against zero sum)
        w_sum = w.sum()
        if w_sum < 1e-8:
            w = missing_mask / missing_mask.sum().clamp(min=1e-8)
        else:
            w = w / w_sum

        z_fused = self._weighted_sum(available_projected, w)          # (B, d_common)
        pred = self.classifier(z_fused)                               # (B, K)
        diag = pred.argmax(dim=-1).mode().values.item()               # scalar int

        # ---- Iterations 1..max_iterations ------------------------------------
        k = 0
        for k in range(self.max_iterations):
            # E-step: diagnosis-adaptive prior
            pi = self.W_prior[int(diag)]  # (M,) prior weights for predicted diagnosis

            # M-step: conflict penalty
            conflict_penalty = self.compute_conflict_penalty(available_projected, int(diag)).to(device)

            w_logits_new = (
                self.alpha * self._compute_weight_logits(quality, reliability, utility, consistency)
                + self.beta * pi
                + self.gamma_param * torch.log(conflict_penalty + 1e-8)
            )

            w_new = F.softmax(w_logits_new, dim=-1) * missing_mask
            w_new_sum = w_new.sum()
            if w_new_sum < 1e-8:
                w_new = missing_mask / missing_mask.sum().clamp(min=1e-8)
            else:
                w_new = w_new / w_new_sum

            z_fused_new = self._weighted_sum(available_projected, w_new)
            pred_new = self.classifier(z_fused_new)
            diag_new = pred_new.argmax(dim=-1).mode().values.item()

            # Convergence check
            converged = (
                diag_new == diag
                and torch.max(torch.abs(w_new - w)).item() < self.convergence_threshold
            )
            w, z_fused, pred, diag = w_new, z_fused_new, pred_new, diag_new

            if converged:
                break

        confidence = float(F.softmax(pred, dim=-1).max(dim=-1).values.mean().item())

        return FusionResult(
            prediction=pred,
            diagnosis=int(diag),
            confidence=confidence,
            weights=w.detach(),
            fused_embedding=z_fused.mean(dim=0).detach(),  # (d_common,) batch-mean
            iterations_used=k + 1,
            converged=(k < self.max_iterations - 1) or converged,
        )

    def _compute_weight_logits(
        self,
        quality: Dict[str, float],
        reliability: Dict[str, float],
        utility: Dict[str, float],
        consistency: float,
    ) -> torch.Tensor:
        """Compute (M,) weight logit vector via single f([Q_agg, R_agg, U_agg, C]) call.

        Per spec: f takes 4 aggregate evidence scalars → num_modalities logit vector.
        Aggregate Q/R/U as mean across available modalities.
        """
        device = next(self.f.parameters()).device
        Q_vals = [quality.get(n, quality.get("clinical", 0.5)) for n in self.MODALITY_NAMES]
        R_vals = [reliability.get(n, 0.5) for n in self.MODALITY_NAMES]
        U_vals = [utility.get(n, 0.5) for n in self.MODALITY_NAMES]

        Q_agg = float(sum(Q_vals) / len(Q_vals))
        R_agg = float(sum(R_vals) / len(R_vals))
        U_agg = float(sum(U_vals) / len(U_vals))
        C = float(consistency)

        evidence_vec = torch.tensor([Q_agg, R_agg, U_agg, C], dtype=torch.float32, device=device)
        return self.f(evidence_vec)  # (M,)

    def _weighted_sum(
        self,
        projected: Dict[str, torch.Tensor],
        weights: torch.Tensor,
    ) -> torch.Tensor:
        """Compute weighted sum of projected embeddings.

        Args:
            projected: modality → (B, d_common)
            weights:   (M,) weight per modality in MODALITY_NAMES order

        Returns:
            (B, d_common) weighted fused embedding
        """
        # Determine batch size from first available
        B = next(iter(projected.values())).shape[0] if projected else 1
        device = weights.device
        z_sum = torch.zeros(B, self.d_common, device=device)
        w_sum_check = torch.zeros(1, device=device)

        for i, name in enumerate(self.MODALITY_NAMES):
            if name in projected and weights[i] > 1e-8:
                z_sum = z_sum + weights[i] * projected[name].to(device)
                w_sum_check = w_sum_check + weights[i]

        # Renormalize to handle floating point
        if w_sum_check.item() > 1e-8:
            z_sum = z_sum / w_sum_check
        return z_sum

    def forward(
        self,
        embeddings: Dict[str, torch.Tensor],
        quality: Dict[str, float],
        reliability: Dict[str, float],
        utility: Dict[str, float],
        consistency: float,
        missing_mask: torch.Tensor,
    ) -> Dict:
        """Forward pass (for training). Returns prediction logits and weights."""
        result = self.fuse(embeddings, quality, reliability, utility, consistency, missing_mask)
        return {
            "logits": result.prediction,
            "weights": result.weights,
            "fused_embedding": result.fused_embedding,
            "iterations": result.iterations_used,
        }
