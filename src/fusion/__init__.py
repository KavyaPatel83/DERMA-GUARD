"""src/fusion/__init__.py — Dynamic Fusion package."""
from src.fusion.adaptive_fusion import DiagnosisAdaptiveFusion
from src.fusion.consensus import classify_consensus, ConsensusResult
from src.fusion.acquisition import AcquisitionPolicy

__all__ = ["DiagnosisAdaptiveFusion", "classify_consensus", "ConsensusResult", "AcquisitionPolicy"]
