#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — LangGraph 节点定义

v4 架构：5 个精简节点（v3 原有 12 个节点）

执行流程：
  planner_node
      ↓ (need_retrieval?)
  knowledge_node  ← 可选，仅在需要知识检索时执行
      ↓
  teaching_node
      ↓ (need_evaluation?)
  evaluation_node ← 可选，仅在需要评估时执行（socratic/direct 模式跳过）
      ↓
  memory_node     ← 对话结束时写入记忆
      ↓
  error_handler_node（仅在节点出错时到达）

核心改进：
1. 所有节点直接操作 LearningWorkflowState 字典（消除双状态转换）
2. 节点数量 12 → 5，减少 58%
3. LLM 调用链路 5~7 次 → 2~3 次，减少约 55%
4. 每个节点职责单一清晰
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .state import LearningWorkflowState, sync_compat_fields
from .prompt import (
    SUMMARY_LABEL,
    NEXT_SUGGESTION_LABEL,
    QUALITY_HIGH_PHRASE,
    QUALITY_MEDIUM_PHRASE,
    ERROR_MESSAGE_TEMPLATE,
    ERROR_MESSAGE_FALLBACK,
)
from src.core.agents.planner import LearningPlannerAgent
from src.core.agents.teacher import TeachingAgent
from src.core.agents.evaluator import EvaluationAgent
from src.core.services.knowledge_engine import KnowledgeEngineService
from src.core.services.memory_system import MemorySystemService

logger = logging.getLogger(__name__)

_NODE_TIMEOUT = 30      # 单节点超时（秒）
_KNOWLEDGE_TIMEOUT = 20  # 知识检索专用超时（网络 IO 可能较慢）
_MEMORY_TIMEOUT = 10     # 记忆写入专用超时


class LearningWorkflowNodes:
    """EduPilot v4 精简节点集合

    3 Agents + 2 Services，直接操作 LearningWorkflowState。
    """

    def __init__(self, feature_flags: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.feature_flags = {
            "enable_knowledge_engine": True,
            "enable_evaluation": True,
            "enable_memory": True,
            "enable_llm_planner": True,
        }
        if feature_flags:
            self.feature_flags.update(feature_flags)

        # v4：3 Agents + 2 Services（懒加载）
        self._planner: Optional[LearningPlannerAgent] = None
        self._teacher: Optional[TeachingAgent] = None
        self._evaluator: Optional[EvaluationAgent] = None
        self._knowledge_engine: Optional[KnowledgeEngineService] = None
        self._memory_system: Optional[MemorySystemService] = None

        self.logger.info(f"[v4] Nodes initialized | flags={self.feature_flags}")

    # ── 懒加载 ────────────────────────────────────────────────────────────

    @property
    def planner(self) -> LearningPlannerAgent:
        if self._planner is None:
            self._planner = LearningPlannerAgent(
                enable_llm=self.feature_flags.get("enable_llm_planner", True)
            )
        return self._planner

    @property
    def teacher(self) -> TeachingAgent:
        if self._teacher is None:
            self._teacher = TeachingAgent()
        return self._teacher

    @property
    def evaluator(self) -> EvaluationAgent:
        if self._evaluator is None:
            self._evaluator = EvaluationAgent()
        return self._evaluator

    @property
    def knowledge_engine(self) -> KnowledgeEngineService:
        if self._knowledge_engine is None:
            self._knowledge_engine = KnowledgeEngineService()
        return self._knowledge_engine

    @property
    def memory_system(self) -> MemorySystemService:
        if self._memory_system is None:
            self._memory_system = MemorySystemService()
        return self._memory_system

    def set_feature_flags(self, flags: Dict[str, Any]):
        """运行时更新特征开关（用于消融实验）"""
        self.feature_flags.update(flags or {})

    # ── 通用执行封装 ──────────────────────────────────────────────────────

    async def _run(
        self,
        coro,
        node_name: str,
        timeout: int = _NODE_TIMEOUT,
    ) -> Any:
        """带超时保护的协程执行封装。

        超时和异常均向上抛出，由各节点的 try/except 统一兜底。
        注意：协程超时取消后不可复用，调用方不得重试同一 coro 对象。
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"[{node_name}] 超时 ({timeout}s)")
            raise

    # ── v4 节点实现 ───────────────────────────────────────────────────────

    async def planner_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """
        节点一：学习规划
        输入：user_query, user_context, student_profile, dialogue_history
        输出：task_plan（intent + strategy + routing 决策）
        LLM 调用：0~1 次（启发式快速路由 / LLM 精准规划）
        """
        node_start = datetime.now()
        try:
            self.logger.info("[Node:Planner] 开始规划")

            # 首轮时从存储预加载学生画像，填充 skill_level 等字段
            if state.get("student_profile") is None and self.feature_flags.get("enable_memory"):
                user_id = state.get("user_id") or state.get("user_context", {}).get("user_id")
                if user_id:
                    profile = await self.memory_system.load_student_profile(user_id)
                    if profile:
                        state = {**state, "student_profile": profile}
                        state["skill_level"] = profile.get(
                            "knowledge_level", state.get("skill_level", "unknown")
                        )

            updates = await self._run(
                self.planner.execute(state),
                node_name="Planner",
            )
            state = {**state, **updates}
            self.logger.info(
                f"[Node:Planner] intent={state.get('task_plan', {}).get('intent')} "
                f"next={state.get('next_step')}"
            )

        except Exception as e:
            # 规划失败时使用默认 explain 策略兜底，不设 error_info（对话仍可继续）
            self.logger.error(f"[Node:Planner] 失败，使用默认规划兜底: {e}")
            fallback_plan = {
                "intent": "concept_explanation",
                "strategy": "explain",
                "need_retrieval": False,
                "need_assessment": False,
                "core_concepts": [],
                "difficulty": "intermediate",
                "learning_goal": state.get("user_query", "")[:80],
                "routing": "teaching",
                "reasoning": f"fallback due to error: {str(e)[:50]}",
            }
            state = {**state, "task_plan": fallback_plan, "next_step": "teaching"}
            sync_compat_fields(state)

        ms = (datetime.now() - node_start).total_seconds() * 1000
        state.setdefault("performance_data", {})["planner_ms"] = ms
        return state

    async def knowledge_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """
        节点二：知识检索（条件执行）
        仅在 task_plan.need_retrieval=True 时执行（routing.py 已过滤，此处为防御性校验）
        输入：task_plan, user_query
        输出：knowledge_context（retrieved_chunks + tool_results）
        LLM 调用：0 次
        """
        node_start = datetime.now()

        if not self.feature_flags.get("enable_knowledge_engine", True):
            self.logger.info("[Node:Knowledge] 已禁用，跳过")
            return {**state, "next_step": "teaching"}

        task_plan = state.get("task_plan") or {}
        if not task_plan.get("need_retrieval", False):
            self.logger.info("[Node:Knowledge] task_plan 未要求检索，跳过")
            return {**state, "next_step": "teaching"}

        try:
            self.logger.info("[Node:Knowledge] 开始知识检索")
            updates = await self._run(
                self.knowledge_engine.execute(state),
                node_name="KnowledgeEngine",
                timeout=_KNOWLEDGE_TIMEOUT,
            )
            state = {**state, **updates}
            state["next_step"] = "teaching"
            chunks = (state.get("knowledge_context") or {}).get("retrieved_chunks", [])
            self.logger.info(f"[Node:Knowledge] 检索完成，chunks={len(chunks)}")

        except Exception as e:
            # 检索失败不影响主流程，降级为无知识上下文的直接教学
            self.logger.error(f"[Node:Knowledge] 失败（降级继续）: {e}")
            state = {**state, "next_step": "teaching"}

        ms = (datetime.now() - node_start).total_seconds() * 1000
        state.setdefault("performance_data", {})["knowledge_ms"] = ms
        return state

    async def teaching_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """
        节点三：教学输出（核心节点）
        输入：task_plan, knowledge_context, student_profile, dialogue_history
        输出：teaching_output（content + socratic_question + curriculum）
        LLM 调用：1 次
        模式：explain / socratic / curriculum / direct

        路由决策：
        - socratic  → memory（等待用户回应，waiting_for_user=True）
        - direct（无 assessment）→ memory（直接结束）
        - explain / curriculum / direct（有 assessment）→ evaluation
        """
        node_start = datetime.now()
        try:
            task_plan = state.get("task_plan") or {}
            strategy = task_plan.get("strategy", "explain")
            need_assessment = task_plan.get("need_assessment", False)

            self.logger.info(f"[Node:Teaching] mode={strategy} assessment={need_assessment}")
            updates = await self._run(
                self.teacher.execute(state),
                node_name="TeachingAgent",
            )
            state = {**state, **updates}

            # ── 路由决策 ────────────────────────────────────────────────
            if strategy == "socratic":
                # 苏格拉底：本轮输出问题，等待学生回应再继续
                # workflow_complete=False 表示对话未结束，仅本轮暂停
                state["next_step"] = "memory"
                state["workflow_complete"] = False
                state["waiting_for_user"] = True
            elif strategy == "direct" and not need_assessment:
                # 直接回答且无测验需求：跳过评估
                state["next_step"] = "memory"
            else:
                # explain / curriculum / direct+assessment → 质量评估（+ 可选测验生成）
                state["next_step"] = "evaluation"

            content = (state.get("teaching_output") or {}).get("content", "")
            self.logger.info(
                f"[Node:Teaching] content_len={len(content)} next={state['next_step']}"
            )

        except Exception as e:
            self.logger.error(f"[Node:Teaching] 失败: {e}")
            state = {
                **state,
                "error_info": {"type": "teaching_error", "message": str(e)},
                "next_step": "error_handler",
            }

        ms = (datetime.now() - node_start).total_seconds() * 1000
        state.setdefault("performance_data", {})["teaching_ms"] = ms
        return state

    async def evaluation_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """
        节点四：质量评估（条件执行）
        输入：teaching_output, task_plan
        输出：evaluation_output（quality_score + is_satisfactory + quiz）
        LLM 调用：1 次（review + 可选 quiz 生成，合并为单次调用）

        路由决策：
        - is_satisfactory=True  → memory（流程结束）
        - is_satisfactory=False + revision_count < MAX → teaching（修改重写）
        - is_satisfactory=False + revision_count >= MAX → memory（强制通过）
        """
        node_start = datetime.now()

        if not self.feature_flags.get("enable_evaluation", True):
            self.logger.info("[Node:Evaluation] 已禁用，跳过")
            return {
                **state,
                "is_satisfactory": True,
                "next_step": "memory",
            }

        try:
            self.logger.info("[Node:Evaluation] 开始评估")
            updates = await self._run(
                self.evaluator.execute(state),
                node_name="EvaluationAgent",
            )
            state = {**state, **updates}

            is_satisfactory = state.get("is_satisfactory", True)
            revision_count = state.get("revision_count", 0)
            from src.core.agents.evaluator.prompt import MAX_REVISIONS

            if is_satisfactory or revision_count >= MAX_REVISIONS:
                state["next_step"] = "memory"
            else:
                state["next_step"] = "teaching"

            self.logger.info(
                f"[Node:Evaluation] pass={is_satisfactory} "
                f"revision={revision_count} next={state['next_step']}"
            )

        except Exception as e:
            self.logger.error(f"[Node:Evaluation] 失败（强制通过）: {e}")
            state = {
                **state,
                "is_satisfactory": True,
                "next_step": "memory",
            }

        ms = (datetime.now() - node_start).total_seconds() * 1000
        state.setdefault("performance_data", {})["evaluation_ms"] = ms
        return state

    async def memory_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """
        节点五：记忆更新
        输入：session_id, user_id, 完整 state
        输出：memory_analysis（供 API 层使用）
        LLM 调用：0 次

        注意：整个 graph 是 await ainvoke，memory 写入在响应前完成。
        保持超时短（10s）以减少用户等待。
        """
        node_start = datetime.now()

        if not self.feature_flags.get("enable_memory", True):
            self.logger.info("[Node:Memory] 已禁用，跳过")
            return {
                **state,
                "memory_updated": False,
                "workflow_complete": True,
                "next_step": None,
            }

        try:
            self.logger.info("[Node:Memory] 写入记忆")
            updates = await self._run(
                self.memory_system.execute(state),
                node_name="MemorySystem",
                timeout=_MEMORY_TIMEOUT,
            )
            state = {**state, **updates}

        except Exception as e:
            self.logger.warning(f"[Node:Memory] 失败（不影响响应）: {e}")
            state["memory_updated"] = False

        state["workflow_complete"] = True
        state["next_step"] = None
        ms = (datetime.now() - node_start).total_seconds() * 1000
        state.setdefault("performance_data", {})["memory_ms"] = ms
        return state

    async def error_handler_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """错误处理节点：仅在教学节点报告致命错误时到达"""
        error_info = state.get("error_info") or {}
        error_msg = error_info.get("message", "未知错误")

        self.logger.error(f"[Node:ErrorHandler] {error_msg}")

        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": ERROR_MESSAGE_TEMPLATE.format(error_msg=error_msg),
        })
        state["workflow_complete"] = True
        state["waiting_for_user"] = False
        state["next_step"] = None
        return state

    async def conclusion_node(
        self, state: LearningWorkflowState
    ) -> LearningWorkflowState:
        """结论节点：汇总对话并生成结束语（当前 v4 图中未接入常规流程）"""
        teaching_output = state.get("teaching_output") or {}
        evaluation_output = state.get("evaluation_output") or {}
        memory_analysis = state.get("memory_analysis") or {}

        conclusion_parts = []

        summary = memory_analysis.get("summary", "")
        if summary:
            conclusion_parts.append(f"{SUMMARY_LABEL}{summary}")

        quality = evaluation_output.get("quality_score", 0)
        if quality >= 0.8:
            conclusion_parts.append(QUALITY_HIGH_PHRASE)
        elif quality >= 0.6:
            conclusion_parts.append(QUALITY_MEDIUM_PHRASE)

        recommendations = memory_analysis.get("recommendations", [])
        if recommendations:
            conclusion_parts.append(NEXT_SUGGESTION_LABEL + "；".join(recommendations[:2]))

        conclusion_text = "\n".join(conclusion_parts)
        if conclusion_text:
            state.setdefault("messages", []).append({
                "role": "assistant",
                "content": conclusion_text,
            })

        state["workflow_complete"] = True
        state["waiting_for_user"] = False
        state["next_step"] = None
        return state
