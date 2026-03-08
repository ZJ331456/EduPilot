#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — Agent 模块

3 个核心 Agent：
  LearningPlannerAgent — 意图识别 + 教学路由（单次 LLM 调用）
  TeachingAgent        — 多模态教学：explain / socratic / curriculum / direct
  EvaluationAgent      — 质量评估 + 测验生成（合并评估周期）

配套 2 个 Service（位于 src.core.services）：
  KnowledgeEngineService — GraphRAG 检索 + 工具调用
  MemorySystemService    — 学生画像持久化 + 记忆更新
"""

from .planner import LearningPlannerAgent
from .teacher import TeachingAgent
from .evaluator import EvaluationAgent

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

__all__ = [
    # v4 核心 Agents
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
]
