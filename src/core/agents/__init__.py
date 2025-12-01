#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""域内智能体模块导出。"""

from .base import (
    ActionType,
    AgentRegistry,
    AgentState,
    BaseAgent,
    ConversationStage,
    EmotionType,
    ExecutionStatus,
    LearningPattern,
    PlanType,
    ProfileDimension,
    QueryType,
    UnderstandingLevel,
    get_agent,
    get_global_agent_registry,
    register_agent,
)
from .knowledge_manager import KnowledgeManagerAgent
from .memory_manager import MemoryManagerAgent
from .orchestrator import OrchestratorAgent
from .query_analyzer import (
    IntentCandidate,
    QueryAnalyzerAgent,
    QueryAnalysisResult,
    RetrievalPlan,
)
from .socratic_guide import SocraticGuideAgent
from .draft_writer import DraftWriterAgent
from .reviewer import ReviewerAgent
from .curriculum_designer import CurriculumDesignerAgent
from .quiz_master import QuizMasterAgent
from .tool_specialist import ToolSpecialistAgent

__all__ = [
    "BaseAgent",
    "AgentState",
    "AgentRegistry",
    "ConversationStage",
    "UnderstandingLevel",
    "ExecutionStatus",
    "QueryType",
    "ActionType",
    "PlanType",
    "ProfileDimension",
    "EmotionType",
    "LearningPattern",
    "get_global_agent_registry",
    "register_agent",
    "get_agent",
    # Query Analyzer (新的统一模块)
    "IntentCandidate",
    "QueryAnalyzerAgent",
    "QueryAnalysisResult",
    "RetrievalPlan",
    # 其他 Agents
    "KnowledgeManagerAgent",
    "SocraticGuideAgent",
    "OrchestratorAgent",
    "MemoryManagerAgent",  # 统一记忆管理（替代LearnerAgent和UserProfileAgent）
    "DraftWriterAgent",
    "ReviewerAgent",
    "CurriculumDesignerAgent",
    "QuizMasterAgent",
    "ToolSpecialistAgent",
]