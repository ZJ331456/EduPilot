#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — 核心模块

3 Agents + 2 Services + LangGraph Workflow
"""

# ── v4 Agents ──────────────────────────────────────────────────────────────
from .agents import (
    LearningPlannerAgent,
    TeachingAgent,
    EvaluationAgent,
    # 基础设施
    BaseAgent,
    AgentState,
    AgentRegistry,
    ConversationStage,
    UnderstandingLevel,
    ExecutionStatus,
    QueryType,
    ActionType,
    PlanType,
    ProfileDimension,
    EmotionType,
    LearningPattern,
    get_global_agent_registry,
    register_agent,
    get_agent,
)

# ── v4 Services ────────────────────────────────────────────────────────────
from .services import KnowledgeEngineService, MemorySystemService

# ── Workflow ───────────────────────────────────────────────────────────────
from .workflow import (
    LangGraphLearningWorkflow,
    get_langgraph_learning_workflow,
    initialize_langgraph_learning_workflow,
    get_workflow_info,
    LearningWorkflowNodes,
    LearningWorkflowRouter,
    LearningWorkflowState,
    create_initial_state,
)

__all__ = [
    # v4 Agents
    "LearningPlannerAgent",
    "TeachingAgent",
    "EvaluationAgent",
    # 基础设施
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
    # v4 Services
    "KnowledgeEngineService",
    "MemorySystemService",
    # Workflow
    "LangGraphLearningWorkflow",
    "get_langgraph_learning_workflow",
    "initialize_langgraph_learning_workflow",
    "get_workflow_info",
    "LearningWorkflowNodes",
    "LearningWorkflowRouter",
    "LearningWorkflowState",
    "create_initial_state",
]
