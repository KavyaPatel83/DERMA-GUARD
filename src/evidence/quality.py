"""src/evidence/quality.py — Quality (Q) computation for DERMA-GUARD v4.0."""
import torch


def compute_image_quality(blur_score: float, brightness: float, contrast: float,
                           resolution_ratio: float, occlusion_score: float,
                           quality_mlp=None) -> float:
    """Compute Q_image ∈ [0,1] from image statistics.
    
    If quality_mlp provided, uses learned MLP. Else uses weighted average heuristic.
    """
    if quality_mlp is not None:
        feat = torch.tensor(
            [blur_score, brightness, contrast, resolution_ratio, occlusion_score],
            dtype=torch.float32,
        ).unsqueeze(0)
        with torch.no_grad():
            return float(quality_mlp(feat).item())
    # Heuristic fallback
    return float(0.25 * blur_score + 0.15 * brightness + 0.20 * contrast
                 + 0.25 * resolution_ratio + 0.15 * occlusion_score)


def compute_text_quality(ptis: float) -> float:
    """Q_text = PTIS score ∈ [0,1]."""
    return float(max(0.0, min(1.0, ptis)))


def compute_metadata_quality(missing_mask) -> float:
    """Q_meta = 1 - fraction_of_fields_missing.
    
    Args:
        missing_mask: iterable of booleans or a tensor (1=missing, 0=present)
    """
    import numpy as np
    arr = list(missing_mask) if not hasattr(missing_mask, 'mean') else missing_mask
    if hasattr(arr, 'float'):
        return float(1.0 - arr.float().mean().item())
    return float(1.0 - np.mean([bool(m) for m in arr]))
