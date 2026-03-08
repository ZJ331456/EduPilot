#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — LangGraph 工作流状态定义

v4 架构核心改进：
- 消除双状态转换（AgentState ↔ LearningWorkflowState），所有 Agent 直接操作此字典
- 引入 task_plan 统一规划输出（替代 plan + interpretation + retrieval_decision 三字段）
- 引入 knowledge_context 汇总知识检索结果（替代 retrieved_docs + validated_docs + tool_outputs）
- teaching_output 承载教学内容（替代 draft_content + socratic_guidance + curriculum_plan）
- evaluation_output 承载评估结果（替代 critique + quiz_stats + is_satisfactory）
- 保留 API 兼容字段，通过节点内联写入确保前端无感升级
"""

from __future__ import annotations

import operator
import uuid
import time
from typing import Any, Annotated, Dict, List, Optional, TypedDict


# ---------------------------------------------------------------------------
# v4 核心状态（直接供所有 Agent/Service 节点读写，无需 AgentState 转换）
# ---------------------------------------------------------------------------

class LearningWorkflowState(TypedDict):
    """EduPilot v4 统一工作流状态

    设计原则：
    1. 扁平化 — 字段直接可读，无需 .get("xxx").get("yyy")
    2. 按阶段分区 — 规划 / 知识 / 教学 / 评估 / 记忆 / 系统
    3. API 向后兼容 — 保留 v3 中被 API 层读取的字段别名
    """

    # ── 基础 ──────────────────────────────────────────────────────────────
    session_id: str
    timestamp: float
    user_id: Optional[str]

    # ── 用户输入 ──────────────────────────────────────────────────────────
    user_query: str
    user_response: str                          # 多轮对话中用户的当前回复
    user_responses: List[str]                   # 历史回复列表
    user_context: Dict[str, Any]                # 前端传入的用户上下文

    # ── 对话历史 ──────────────────────────────────────────────────────────
    dialogue_history: List[Dict[str, Any]]      # [{role, content, timestamp, round}]
    conversation_round: int
    max_conversation_rounds: int

    # ══ v4 阶段一：规划层 ═════════════════════════════════════════════════
    # LearningPlanner 输出，替代 v3 的 plan + interpretation + retrieval_decision
    task_plan: Optional[Dict[str, Any]]
    # task_plan schema:
    # {
    #   "intent": str,           # concept_explanation|socratic_dialogue|practice|direct_answer|smalltalk
    #   "strategy": str,         # explain|socratic|curriculum|direct
    #   "need_retrieval": bool,
    #   "need_assessment": bool,
    #   "core_concepts": List[str],
    #   "difficulty": str,       # beginner|intermediate|advanced
    #   "learning_goal": str,
    #   "routing": str,          # "knowledge" | "teaching"（下一节点决策）
    #   "reasoning": str,        # 规划思路（调试用）
    # }

    # ══ v4 阶段二：知识层 ═════════════════════════════════════════════════
    # KnowledgeEngine service 输出，替代 retrieved_docs + validated_docs + tool_outputs
    knowledge_context: Optional[Dict[str, Any]]
    # knowledge_context schema:
    # {
    #   "retrieved_chunks": List[Dict],   # [{content, source, relevance_score}]
    #   "tool_results": Dict[str, Any],   # 工具调用结果
    #   "sources": List[str],
    #   "retrieval_strategy": str,
    #   "total_tokens": int,
    # }

    # ══ v4 阶段三：教学层 ═════════════════════════════════════════════════
    # TeachingAgent 输出，替代 draft_content + socratic_guidance + curriculum_plan
    teaching_output: Optional[Dict[str, Any]]
    # teaching_output schema:
    # {
    #   "mode": str,              # explain|socratic|curriculum|direct
    #   "content": str,           # 主要输出文本（对应 v3 draft_content）
    #   "socratic_question": str, # 苏格拉底问题（mode=socratic 时）
    #   "curriculum": Dict,       # 课程结构（mode=curriculum 时）
    #   "follow_up_hints": List[str],
    # }

    # ══ v4 阶段四：评估层 ═════════════════════════════════════════════════
    # EvaluationAgent 输出，替代 critique + quiz_stats + is_satisfactory
    evaluation_output: Optional[Dict[str, Any]]
    # evaluation_output schema:
    # {
    #   "quality_score": float,   # 0.0 ~ 1.0
    #   "is_satisfactory": bool,
    #   "critique": str,
    #   "revision_needed": bool,
    #   "quiz": Optional[Dict],   # 测验题目
    #   "feedback": str,
    # }

    # ══ v4 阶段五：记忆层 ════════════════════════════════════════════════
    memory_updated: bool                        # 是否已完成记忆写入
    student_profile: Optional[Dict[str, Any]]   # 读入的学生画像（供 Teacher 使用）
    memory_analysis: Optional[Dict[str, Any]]   # MemorySystem 分析结果

    # ── 系统控制 ──────────────────────────────────────────────────────────
    messages: Annotated[List[Dict[str, str]], operator.add]  # LangGraph 消息累加
    next_step: Optional[str]
    workflow_complete: bool
    waiting_for_user: bool
    error_info: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    performance_data: Dict[str, Any]

    # ── API 兼容别名（v3 → v4 映射，由节点同步写入）─────────────────────
    # 以下字段供 API 层 / 前端读取，由各节点在写 v4 字段后同步填充
    interpretation: Optional[Dict[str, Any]]    # ← task_plan
    query_type: Optional[str]                   # ← task_plan.intent
    plan: Optional[Dict[str, Any]]              # ← task_plan
    retrieval_decision: Optional[Dict[str, Any]] # ← task_plan.need_retrieval
    draft_content: str                           # ← teaching_output.content
    critique: str                                # ← evaluation_output.critique
    is_satisfactory: bool                        # ← evaluation_output.is_satisfactory
    revision_count: int
    socratic_question: str                       # ← teaching_output.socratic_question
    socratic_questions: List[str]
    socratic_guidance: Dict[str, Any]            # ← teaching_output
    curriculum_plan: Dict[str, Any]              # ← teaching_output.curriculum
    tool_outputs: Dict[str, Any]                 # ← knowledge_context.tool_results
    retrieved_docs: List[Any]                    # ← knowledge_context.retrieved_chunks
    validated_docs: List[Any]
    evidence_used: List[Dict[str, Any]]
    quiz_stats: Dict[str, Any]                   # ← evaluation_output.quiz
    execution_result: Optional[Dict[str, Any]]
    learning_feedback: Optional[Dict[str, Any]]  # ← memory_analysis
    conversation_stage: str
    understanding_level: str
    knowledge_sources: List[str]
    # 用户画像快照（规划时读入）
    skill_level: str
    difficulty_level: str
    goal_type: str
    key_concepts_covered: List[str]
    learning_objectives: List[str]
    achieved_objectives: List[str]
    current_focus: str


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def create_initial_state(
    user_query: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None,
) -> LearningWorkflowState:
    """创建 v4 初始状态"""
    return LearningWorkflowState(
        # 基础
        session_id=session_id or str(uuid.uuid4()),
        timestamp=time.time(),
        user_id=user_id,

        # 用户输入
        user_query=user_query,
        user_response="",
        user_responses=[],
        user_context=user_context or {},

        # 对话历史
        dialogue_history=[],
        conversation_round=0,
        max_conversation_rounds=10,

        # v4 阶段字段
        task_plan=None,
        knowledge_context=None,
        teaching_output=None,
        evaluation_output=None,

        # 记忆层
        memory_updated=False,
        student_profile=None,
        memory_analysis=None,

        # 系统控制
        messages=[],
        next_step=None,
        workflow_complete=False,
        waiting_for_user=False,
        error_info=None,
        metadata={},
        performance_data={},

        # API 兼容别名（v3 字段默认值）
        interpretation=None,
        query_type=None,
        plan=None,
        retrieval_decision=None,
        draft_content="",
        critique="",
        is_satisfactory=False,
        revision_count=0,
        socratic_question="",
        socratic_questions=[],
        socratic_guidance={},
        curriculum_plan={},
        tool_outputs={},
        retrieved_docs=[],
        validated_docs=[],
        evidence_used=[],
        quiz_stats={},
        execution_result=None,
        learning_feedback=None,
        conversation_stage="initial_query",
        understanding_level="no_understanding",
        knowledge_sources=[],
        skill_level="unknown",
        difficulty_level="medium",
        goal_type="general",
        key_concepts_covered=[],
        learning_objectives=[],
        achieved_objectives=[],
        current_focus="",
    )


def sync_compat_fields(state: LearningWorkflowState) -> None:
    """将 v4 字段同步到 v3 兼容别名（in-place）

    在每个主要节点末尾调用，保持 API 层无感升级。
    """
    # 规划层 → 兼容别名
    if task_plan := state.get("task_plan"):
        state["interpretation"] = task_plan
        state["query_type"] = task_plan.get("intent")
        state["plan"] = task_plan
        state["retrieval_decision"] = {
            "need_retrieval": task_plan.get("need_retrieval", False),
            "core_concepts": task_plan.get("core_concepts", []),
        }
        state["difficulty_level"] = task_plan.get("difficulty", state.get("difficulty_level", "medium"))
        state["goal_type"] = task_plan.get("intent", state.get("goal_type", "general"))

    # 知识层 → 兼容别名
    if kc := state.get("knowledge_context"):
        state["retrieved_docs"] = kc.get("retrieved_chunks", [])
        state["validated_docs"] = kc.get("retrieved_chunks", [])
        state["evidence_used"] = kc.get("retrieved_chunks", [])
        state["tool_outputs"] = kc.get("tool_results", {})
        state["knowledge_sources"] = kc.get("sources", [])

    # 教学层 → 兼容别名
    if to := state.get("teaching_output"):
        state["draft_content"] = to.get("content", "")
        state["socratic_question"] = to.get("socratic_question", "")
        if to.get("socratic_question"):
            qs = state.get("socratic_questions", [])
            if to["socratic_question"] not in qs:
                qs.append(to["socratic_question"])
            state["socratic_questions"] = qs
        state["socratic_guidance"] = to
        state["curriculum_plan"] = to.get("curriculum", {})

    # 评估层 → 兼容别名
    if eo := state.get("evaluation_output"):
        state["critique"] = eo.get("critique", "")
        state["is_satisfactory"] = eo.get("is_satisfactory", False)
        state["quiz_stats"] = eo.get("quiz", {})

    # 记忆层 → 兼容别名
    if ma := state.get("memory_analysis"):
        state["learning_feedback"] = ma


__all__ = [
    "LearningWorkflowState",
    "create_initial_state",
    "sync_compat_fields",
]
