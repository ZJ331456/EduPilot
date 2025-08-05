#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体基类和状态管理
兼容性模块 - 重新导出utils中的内容
"""

# 重新导出所有内容以保持向后兼容性
from utils import (
    BaseAgent,
    AgentState,
    QueryType,
    ExecutionStatus,
    ConversationStage,
    UnderstandingLevel,
    PlanType,
    ActionType,
    ProfileDimension,
    EmotionType,
    LearningPattern,
    AgentRegistry,
    get_global_agent_registry,
    register_agent,
    get_agent
)

# 为了向后兼容，保留原有的导入路径
__all__ = [
    'BaseAgent',
    'AgentState',
    'QueryType',
    'ExecutionStatus',
    'ConversationStage',
    'UnderstandingLevel',
    'PlanType',
    'ActionType',
    'ProfileDimension',
    'EmotionType',
    'LearningPattern',
    'AgentRegistry',
    'get_global_agent_registry',
    'register_agent',
    'get_agent'
]