"""src/agents/__init__.py — Agent package for DERMA-GUARD v4.0."""
from src.agents.orchestrator import OrchestratorAgent, PatientCase, PipelineResult
from src.agents.vision_team import VisionSpecialistTeam
from src.agents.scribe import ScribeAgent
from src.agents.librarian import LibrarianAgent
from src.agents.devils_advocate import DevilsAdvocateAgent, EvidenceProfile

__all__ = [
    "OrchestratorAgent", "PatientCase", "PipelineResult",
    "VisionSpecialistTeam", "ScribeAgent", "LibrarianAgent",
    "DevilsAdvocateAgent", "EvidenceProfile",
]
