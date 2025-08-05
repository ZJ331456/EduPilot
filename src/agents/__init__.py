#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多智能体系统模块（整合版）
已整合查询相关智能体和用户画像智能体
"""

from .base import BaseAgent, AgentState, AgentRegistry
from .query_interpreter_integrated import QueryInterpreterAgent
from .knowledge_retriever import KnowledgeRetrieverAgent
from .socratic_guide import SocraticGuideAgent
from .planner import PlannerAgent
from .executor import ExecutorAgent
from .learner import LearnerAgent
from .user_profile_integrated import UserProfileAgent
from .multi_agent_system import MultiAgentSystem, get_multi_agent_system, initialize_multi_agent_system

__all__ = [
    "BaseAgent",
    "AgentState", 
    "AgentRegistry",
    "QueryInterpreterAgent",
    "KnowledgeRetrieverAgent",
    "SocraticGuideAgent",
    "PlannerAgent",
    "ExecutorAgent",
    "LearnerAgent",
    "UserProfileAgent",
    "MultiAgentSystem",
    "get_multi_agent_system",
    "initialize_multi_agent_system"
]