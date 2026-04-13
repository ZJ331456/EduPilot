"""EduPilot 后端包：统一 LLM、GraphRAG 与教育智能体。"""

__version__ = "0.1.0"

from edupilot.services.graphrag import GraphRAG, QueryParam
from edupilot.agents.base.agent import (
    BaseAgent,
    SingleTurnAgent,
    MultiTurnAgent,
    OrchestratorAgent,
)
