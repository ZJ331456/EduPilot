#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph 状态定义
基于现有 AgentState 重构为 LangGraph 兼容的状态
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, TYPE_CHECKING
from datetime import datetime
import operator

from src.infrastructure.utils.enums import (
    QueryType, ExecutionStatus, ConversationStage, UnderstandingLevel
)

if TYPE_CHECKING:
    from src.infrastructure.utils.data_models import AgentState


class LearningWorkflowState(TypedDict):
    """学习工作流状态 - LangGraph 兼容
    
    统一的工作流状态定义，用于整个系统。
    之前的 WorkflowState 和 LearningWorkflowState 已合并为此类。
    """
    
    # 基础信息
    session_id: str
    timestamp: float
    
    # 用户输入和查询信息
    user_query: str
    interpretation: Optional[Dict[str, Any]]
    query_type: Optional[str]  # QueryType enum as string
    
    # 知识检索相关
    retrieved_knowledge: Optional[Dict[str, Any]]
    knowledge_sources: List[str]
    retrieval_decision: Optional[Dict[str, Any]]
    
    # 苏格拉底对话相关
    socratic_question: str
    socratic_questions: List[str]
    user_response: str
    user_responses: List[str]
    dialogue_history: List[Dict[str, str]]
    socratic_guidance: Dict[str, Any]
    
    # 对话状态管理
    conversation_stage: str  # ConversationStage enum as string
    understanding_level: str  # UnderstandingLevel enum as string
    conversation_round: int
    max_conversation_rounds: int
    target_understanding_level: str  # UnderstandingLevel enum as string
    conversation_context: Dict[str, Any]
    user_context: Dict[str, Any]
    
    # 学习进度追踪
    learning_objectives: List[str]
    achieved_objectives: List[str]
    current_focus: str
    key_concepts_covered: List[str]
    goal_type: str
    skill_level: str
    difficulty_level: str
    
    # 规划和执行相关
    plan: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]
    execution_status: str  # ExecutionStatus enum as string
    
    # 学习和反馈相关
    learning_feedback: Optional[Dict[str, Any]]
    knowledge_updates: List[Dict[str, Any]]
    
    # 元数据
    metadata: Dict[str, Any]
    error_info: Optional[Dict[str, Any]]
    feature_flags: Dict[str, Any]
    experiment_tags: List[str]

    # 数据槽位
    retrieved_docs: List[Any]  # RAG结果
    validated_docs: List[Any]
    tool_outputs: Dict[str, Any]  # 工具运行结果
    curriculum_plan: Dict[str, Any]  # 课程结构
    evidence_used: List[Dict[str, Any]]
    quiz_stats: Dict[str, Any]
    
    # 审核槽位
    draft_content: str  # 初稿
    critique: str  # 批评意见
    is_satisfactory: bool  # 是否通过
    revision_count: int  # 修改次数
    
    # LangGraph 特定字段
    messages: Annotated[List[Dict[str, str]], operator.add]  # 消息历史
    next_step: Optional[str]  # 下一步节点
    workflow_complete: bool  # 工作流是否完成
    waiting_for_user: bool  # 是否等待用户输入
    
    # 性能优化字段
    cache: Dict[str, Any]
    performance_data: Dict[str, Any]
    execution_hints: Dict[str, Any]


def create_initial_state(
    user_query: str,
    session_id: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> LearningWorkflowState:
    """创建初始状态"""
    import uuid
    import time
    
    return LearningWorkflowState(
        # 基础信息
        session_id=session_id or str(uuid.uuid4()),
        timestamp=time.time(),
        
        # 用户输入和查询信息
        user_query=user_query,
        interpretation=None,
        query_type=None,
        
        # 知识检索相关
        retrieved_knowledge=None,
        knowledge_sources=[],
        retrieval_decision=None,
        
        # 苏格拉底对话相关
        socratic_question="",
        socratic_questions=[],
        user_response="",
        user_responses=[],
        dialogue_history=[],
        socratic_guidance={},
        
        # 对话状态管理
        conversation_stage=ConversationStage.INITIAL_QUERY.value,
        understanding_level=UnderstandingLevel.NO_UNDERSTANDING.value,
        conversation_round=0,
        max_conversation_rounds=10,
        target_understanding_level=UnderstandingLevel.GOOD_UNDERSTANDING.value,
        conversation_context={},
        user_context=user_context or {},
        
        # 学习进度追踪
        learning_objectives=[],
        achieved_objectives=[],
        current_focus="",
        key_concepts_covered=[],
        goal_type="general",
        skill_level="unknown",
        difficulty_level="medium",
        
        # 规划和执行相关
        plan=None,
        execution_result=None,
        execution_status=ExecutionStatus.PENDING.value,
        
        # 学习和反馈相关
        learning_feedback=None,
        knowledge_updates=[],
        
        # 元数据
        metadata={},
        error_info=None,
        feature_flags={},
        experiment_tags=[],

        # 数据槽位
        retrieved_docs=[],
        validated_docs=[],
        tool_outputs={},
        curriculum_plan={},
        evidence_used=[],
        quiz_stats={},
        
        # 审核槽位
        draft_content="",
        critique="",
        is_satisfactory=False,
        revision_count=0,
        
        # LangGraph 特定字段
        messages=[],
        next_step=None,
        workflow_complete=False,
        waiting_for_user=False,
        
        # 性能优化字段
        cache={},
        performance_data={},
        execution_hints={}
    )


def state_to_agent_state(state: LearningWorkflowState) -> 'AgentState':
    """将 LangGraph 状态转换为 AgentState"""
    from src.infrastructure.utils.data_models import AgentState
    
    agent_state = AgentState()
    
    # 基础信息
    agent_state.session_id = state["session_id"]
    agent_state.timestamp = state["timestamp"]
    
    # 用户输入和查询信息
    agent_state.user_query = state["user_query"]
    agent_state.interpretation = state["interpretation"]
    if state["query_type"]:
        agent_state.query_type = QueryType(state["query_type"])
    
    # 知识检索相关
    agent_state.retrieved_knowledge = state["retrieved_knowledge"]
    agent_state.knowledge_sources = state["knowledge_sources"]
    # 设置retrieval_decision属性
    if hasattr(agent_state, 'retrieval_decision'):
        agent_state.retrieval_decision = state.get("retrieval_decision")
    
    # 苏格拉底对话相关
    agent_state.socratic_question = state["socratic_question"]
    agent_state.socratic_questions = state["socratic_questions"]
    agent_state.user_response = state["user_response"]
    agent_state.user_responses = state["user_responses"]
    agent_state.dialogue_history = state["dialogue_history"]
    # 🔧 修复：添加 socratic_guidance 字段
    if hasattr(agent_state, 'socratic_guidance'):
        agent_state.socratic_guidance = state.get("socratic_guidance", {})
    
    # 对话状态管理
    agent_state.conversation_stage = ConversationStage(state["conversation_stage"])
    agent_state.understanding_level = UnderstandingLevel(state["understanding_level"])
    agent_state.conversation_round = state["conversation_round"]
    agent_state.max_conversation_rounds = state["max_conversation_rounds"]
    agent_state.target_understanding_level = UnderstandingLevel(state["target_understanding_level"])
    agent_state.conversation_context = state["conversation_context"]
    agent_state.user_context = state["user_context"]
    
    # 学习进度追踪
    agent_state.learning_objectives = state["learning_objectives"]
    agent_state.achieved_objectives = state["achieved_objectives"]
    agent_state.current_focus = state["current_focus"]
    agent_state.key_concepts_covered = state["key_concepts_covered"]
    agent_state.goal_type = state.get("goal_type", "general")
    agent_state.skill_level = state.get("skill_level", "unknown")
    agent_state.difficulty_level = state.get("difficulty_level", "medium")
    
    # 规划和执行相关
    agent_state.plan = state["plan"]
    agent_state.execution_result = state["execution_result"]
    agent_state.execution_status = ExecutionStatus(state["execution_status"])
    
    # 学习和反馈相关
    agent_state.learning_feedback = state["learning_feedback"]
    agent_state.knowledge_updates = state["knowledge_updates"]
    
    # 元数据
    agent_state.metadata = state["metadata"]
    agent_state.error_info = state["error_info"]
    agent_state.feature_flags = state.get("feature_flags", {})
    agent_state.experiment_tags = state.get("experiment_tags", [])
    
    # 数据槽位
    agent_state.retrieved_docs = state.get("retrieved_docs", [])
    agent_state.validated_docs = state.get("validated_docs", [])
    agent_state.tool_outputs = state.get("tool_outputs", {})
    agent_state.curriculum_plan = state.get("curriculum_plan", {})
    agent_state.evidence_used = state.get("evidence_used", [])
    agent_state.quiz_stats = state.get("quiz_stats", {})
    
    # 审核槽位
    agent_state.draft_content = state.get("draft_content", "")
    agent_state.critique = state.get("critique", "")
    agent_state.is_satisfactory = state.get("is_satisfactory", False)
    agent_state.revision_count = state.get("revision_count", 0)

    return agent_state


def agent_state_to_state(agent_state: 'AgentState') -> LearningWorkflowState:
    """将 AgentState 转换为 LangGraph 状态"""
    return LearningWorkflowState(
        # 基础信息
        session_id=agent_state.session_id,
        timestamp=agent_state.timestamp,
        
        # 用户输入和查询信息
        user_query=agent_state.user_query,
        interpretation=agent_state.interpretation,
        query_type=agent_state.query_type.value if agent_state.query_type else None,
        
        # 知识检索相关
        retrieved_knowledge=agent_state.retrieved_knowledge,
        knowledge_sources=agent_state.knowledge_sources,
        retrieval_decision=getattr(agent_state, 'retrieval_decision', None),
        
        # 苏格拉底对话相关
        socratic_question=agent_state.socratic_question,
        socratic_questions=agent_state.socratic_questions,
        user_response=agent_state.user_response,
        user_responses=agent_state.user_responses,
        dialogue_history=agent_state.dialogue_history,
        # 🔧 修复：添加 socratic_guidance 字段
        socratic_guidance=getattr(agent_state, 'socratic_guidance', {}),
        
        # 对话状态管理
        conversation_stage=agent_state.conversation_stage.value,
        understanding_level=agent_state.understanding_level.value,
        conversation_round=agent_state.conversation_round,
        max_conversation_rounds=agent_state.max_conversation_rounds,
        target_understanding_level=agent_state.target_understanding_level.value,
        conversation_context=agent_state.conversation_context,
        user_context=agent_state.user_context,
        
        # 学习进度追踪
        learning_objectives=agent_state.learning_objectives,
        achieved_objectives=agent_state.achieved_objectives,
        current_focus=agent_state.current_focus,
        key_concepts_covered=agent_state.key_concepts_covered,
        
        # 规划和执行相关
        plan=agent_state.plan,
        execution_result=agent_state.execution_result,
        execution_status=agent_state.execution_status.value,
        
        # 学习和反馈相关
        learning_feedback=agent_state.learning_feedback,
        knowledge_updates=agent_state.knowledge_updates,

        # 学习画像 / 难度
        goal_type=getattr(agent_state, "goal_type", "general"),
        skill_level=getattr(agent_state, "skill_level", "unknown"),
        difficulty_level=getattr(agent_state, "difficulty_level", "medium"),

        # 数据槽位
        retrieved_docs=getattr(agent_state, "retrieved_docs", []),
        validated_docs=getattr(agent_state, "validated_docs", []),
        tool_outputs=getattr(agent_state, "tool_outputs", {}),
        curriculum_plan=getattr(agent_state, "curriculum_plan", {}),
        evidence_used=getattr(agent_state, "evidence_used", []),
        quiz_stats=getattr(agent_state, "quiz_stats", {}),
        
        # 元数据
        metadata=agent_state.metadata,
        error_info=agent_state.error_info,
        feature_flags=getattr(agent_state, 'feature_flags', {}),
        experiment_tags=getattr(agent_state, 'experiment_tags', []),
        
        # LangGraph 特定字段
        messages=[],  # 从 dialogue_history 转换
        next_step=None,
        workflow_complete=False,
        waiting_for_user=False,
        
        # 性能优化字段
        cache=getattr(agent_state, '_cache', {}),
        performance_data=getattr(agent_state, '_performance_data', {}),
        execution_hints=getattr(agent_state, '_execution_hints', {})
    )


def update_state_from_agent_state(state: LearningWorkflowState, agent_state: 'AgentState') -> LearningWorkflowState:
    """从 AgentState 更新 LangGraph 状态"""
    # 更新所有字段
    state["session_id"] = agent_state.session_id
    state["timestamp"] = agent_state.timestamp
    state["user_query"] = agent_state.user_query
    state["interpretation"] = agent_state.interpretation
    state["query_type"] = agent_state.query_type.value if agent_state.query_type else None
    
    state["retrieved_knowledge"] = agent_state.retrieved_knowledge
    state["knowledge_sources"] = agent_state.knowledge_sources
    # 设置retrieval_decision
    state["retrieval_decision"] = getattr(agent_state, 'retrieval_decision', None)
    
    state["socratic_question"] = agent_state.socratic_question
    state["socratic_questions"] = agent_state.socratic_questions
    state["user_response"] = agent_state.user_response
    state["user_responses"] = agent_state.user_responses
    state["dialogue_history"] = agent_state.dialogue_history
    # 🔧 修复：添加 socratic_guidance 字段
    state["socratic_guidance"] = getattr(agent_state, 'socratic_guidance', {})
    
    state["conversation_stage"] = agent_state.conversation_stage.value
    state["understanding_level"] = agent_state.understanding_level.value
    state["conversation_round"] = agent_state.conversation_round
    state["max_conversation_rounds"] = agent_state.max_conversation_rounds
    state["target_understanding_level"] = agent_state.target_understanding_level.value
    state["conversation_context"] = agent_state.conversation_context
    state["user_context"] = agent_state.user_context
    
    state["learning_objectives"] = agent_state.learning_objectives
    state["achieved_objectives"] = agent_state.achieved_objectives
    state["current_focus"] = agent_state.current_focus
    state["key_concepts_covered"] = agent_state.key_concepts_covered
    state["goal_type"] = getattr(agent_state, "goal_type", "general")
    state["skill_level"] = getattr(agent_state, "skill_level", "unknown")
    state["difficulty_level"] = getattr(agent_state, "difficulty_level", "medium")
    
    state["plan"] = agent_state.plan
    state["execution_result"] = agent_state.execution_result
    state["execution_status"] = agent_state.execution_status.value
    
    state["learning_feedback"] = agent_state.learning_feedback
    state["knowledge_updates"] = agent_state.knowledge_updates
    
    state["metadata"] = agent_state.metadata
    state["error_info"] = agent_state.error_info
    state["feature_flags"] = getattr(agent_state, 'feature_flags', {})
    state["experiment_tags"] = getattr(agent_state, 'experiment_tags', [])
    
    # 数据槽位
    state["retrieved_docs"] = getattr(agent_state, 'retrieved_docs', [])
    state["validated_docs"] = getattr(agent_state, 'validated_docs', [])
    state["tool_outputs"] = getattr(agent_state, 'tool_outputs', {})
    state["curriculum_plan"] = getattr(agent_state, 'curriculum_plan', {})
    state["evidence_used"] = getattr(agent_state, 'evidence_used', [])
    state["quiz_stats"] = getattr(agent_state, 'quiz_stats', {})
    
    # 审核槽位
    state["draft_content"] = getattr(agent_state, 'draft_content', "")
    state["critique"] = getattr(agent_state, 'critique', "")
    state["is_satisfactory"] = getattr(agent_state, 'is_satisfactory', False)
    state["revision_count"] = getattr(agent_state, 'revision_count', 0)

    # 更新缓存和性能数据
    state["cache"] = getattr(agent_state, '_cache', {})
    state["performance_data"] = getattr(agent_state, '_performance_data', {})
    state["execution_hints"] = getattr(agent_state, '_execution_hints', {})
    
    return state


__all__ = [
    "LearningWorkflowState",
    "create_initial_state",
    "state_to_agent_state",
    "agent_state_to_state",
    "update_state_from_agent_state",
]
