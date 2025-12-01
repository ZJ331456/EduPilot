#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心模块
提供学习系统的核心功能，包括智能体和工作流
直接使用 LangGraph 实现
"""

# 智能体
from .agents import (
    BaseAgent,
    AgentState,
    AgentRegistry,
    # 枚举
    ConversationStage,
    UnderstandingLevel,
    ExecutionStatus,
    QueryType,
    ActionType,
    PlanType,
    ProfileDimension,
    EmotionType,
    LearningPattern,
    # 智能体注册
    get_global_agent_registry,
    register_agent,
    get_agent,
    # 具体智能体
    QueryAnalyzerAgent,
    KnowledgeManagerAgent,
    SocraticGuideAgent,
    OrchestratorAgent,
    MemoryManagerAgent,
    DraftWriterAgent,
    ReviewerAgent,
    CurriculumDesignerAgent,
    QuizMasterAgent,
    ToolSpecialistAgent,
)

# 工作流（LangGraph 实现）
from .workflow import (
    LangGraphLearningWorkflow,
    get_langgraph_learning_workflow,
    initialize_langgraph_learning_workflow,
    get_workflow_info,
    # LangGraph 组件
    LearningWorkflowNodes,
    LearningWorkflowRouter,
    LearningWorkflowState,
    create_initial_state,
)

__all__ = [
    # 智能体
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
    "QueryAnalyzerAgent",
    "KnowledgeManagerAgent",
    "SocraticGuideAgent",
    "OrchestratorAgent",
    "MemoryManagerAgent",
    "DraftWriterAgent",
    "ReviewerAgent",
    "CurriculumDesignerAgent",
    "QuizMasterAgent",
    "ToolSpecialistAgent",
    
    # 工作流（LangGraph 实现）
    "LangGraphLearningWorkflow",
    "get_langgraph_learning_workflow",
    "initialize_langgraph_learning_workflow",
    "get_workflow_info",
    
    # LangGraph 组件
    "LearningWorkflowNodes",
    "LearningWorkflowRouter",
    "LearningWorkflowState",
    "create_initial_state",
]
