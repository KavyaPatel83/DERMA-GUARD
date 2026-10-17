"""src/evidence/__init__.py — Evidence profiling package."""
from src.evidence.quality import compute_image_quality, compute_text_quality, compute_metadata_quality
from src.evidence.reliability import ReliabilityMLP, compute_predictive_entropy, compute_reliability
from src.evidence.consistency import compute_consistency
from src.evidence.missingness import compute_missingness, ALL_MODALITIES
from src.evidence.utility import compute_utility_retrospective, approximate_utility_from_training

__all__ = [
    "compute_image_quality", "compute_text_quality", "compute_metadata_quality",
    "ReliabilityMLP", "compute_predictive_entropy", "compute_reliability",
    "compute_consistency", "compute_missingness", "ALL_MODALITIES",
    "compute_utility_retrospective", "approximate_utility_from_training",
]
