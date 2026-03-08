#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — LearningPlanner Agent

职责（合并 v3 QueryAnalyzer + Orchestrator）：
1. 意图识别 — 理解用户真正想要什么
2. 教学策略选择 — 选择最合适的教学方式
3. 检索决策 — 判断是否需要知识库支持
4. 评估决策 — 判断是否需要生成测验题
5. 难度/目标校准 — 结合学生画像调整参数

单次 LLM 调用输出 task_plan JSON，直接操作 LearningWorkflowState。
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from .prompt import (
    PLANNER_SYSTEM_PROMPT,
    INTENT_RULES,
    RETRIEVAL_INDICATORS,
)

logger = logging.getLogger(__name__)

# 不需要知识检索的意图集合（无论关键词如何均跳过检索）
_NO_RETRIEVAL_INTENTS = {"smalltalk", "meta_question", "practice"}

# 强制使用 direct 策略的意图（routing 不走 knowledge 节点）
_DIRECT_STRATEGY_INTENTS = {"smalltalk", "meta_question"}


def _heuristic_plan(user_query: str, user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """快速启发式规划（无 LLM 调用，用于简单意图）"""
    q = user_query.lower().strip()

    matched_intent = None
    matched_strategy = None

    for keywords, intent, strategy in INTENT_RULES:
        if any(kw in q for kw in keywords):
            matched_intent = intent
            matched_strategy = strategy
            break

    if not matched_intent:
        return None

    skill_level = user_context.get("skill_level", "unknown")

    # 简单意图：直接回答，无需 LLM
    if matched_intent in _DIRECT_STRATEGY_INTENTS:
        return {
            "intent": matched_intent,
            "strategy": "direct",
            "need_retrieval": False,
            "need_assessment": False,
            "core_concepts": [],
            "difficulty": skill_level if skill_level != "unknown" else "beginner",
            "learning_goal": user_query[:80],
            "routing": "teaching",
            "reasoning": "heuristic: simple intent detected",
        }

    # 其他意图：practice 不需要检索；直接策略也不检索；否则按关键词判断
    if matched_intent in _NO_RETRIEVAL_INTENTS or matched_strategy == "direct":
        need_retrieval = False
    else:
        need_retrieval = any(kw in q for kw in RETRIEVAL_INDICATORS)

    need_assessment = matched_intent == "practice" or any(
        kw in q for kw in ["练习", "题目", "测验", "quiz", "考考我", "出题"]
    )

    difficulty = user_context.get("difficulty_level") or (
        "beginner" if skill_level in ("beginner", "novice") else
        "advanced" if skill_level in ("advanced", "expert") else
        "intermediate"
    )

    return {
        "intent": matched_intent,
        "strategy": matched_strategy,
        "need_retrieval": need_retrieval,
        "need_assessment": need_assessment,
        "core_concepts": [],
        "difficulty": difficulty,
        "learning_goal": user_query[:80],
        "routing": "knowledge" if need_retrieval else "teaching",
        "reasoning": f"heuristic: matched intent={matched_intent}",
    }


async def _llm_chat(
    llm_manager,
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 600,
) -> str:
    """统一的 LLM 调用适配层

    将 dict 消息列表转换为 Message 对象，处理不同 LLM 客户端的返回格式。
    """
    from src.infrastructure.llm.base import Message

    msg_objects = [Message(role=m["role"], content=m["content"]) for m in messages]

    try:
        client = llm_manager.get_client()
        if client is None:
            return ""
        response = await client.async_chat_completion(
            msg_objects,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if hasattr(response, "content"):
            return response.content
        if hasattr(response, "to_dict"):
            return response.to_dict().get("content", "")
        if isinstance(response, dict):
            return response.get("content", response.get("text", str(response)))
        return str(response)
    except Exception as e:
        logger.warning(f"LLM 调用失败: {e}")
        return ""


class LearningPlannerAgent:
    """EduPilot v4 核心规划 Agent

    直接操作 LearningWorkflowState 字典，无需 AgentState 转换。
    优先使用启发式规则快速路由，对复杂意图使用单次 LLM 调用。
    """

    def __init__(self, enable_llm: bool = True):
        self.enable_llm = enable_llm
        self.logger = logging.getLogger(self.__class__.__name__)
        self._llm_manager = None
        self._call_count = 0
        self._error_count = 0

    def _get_llm_manager(self):
        """懒加载 LLM manager"""
        if self._llm_manager is None:
            try:
                from src.infrastructure.llm.manager import get_llm_manager
                self._llm_manager = get_llm_manager()
            except Exception as e:
                self.logger.warning(f"LLM manager not available: {e}")
        return self._llm_manager

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行规划，直接返回更新后的 state 片段"""
        start_ts = time.time()
        user_query: str = state.get("user_query", "")
        user_context: Dict[str, Any] = state.get("user_context", {})
        student_profile: Optional[Dict] = state.get("student_profile")
        conversation_round: int = state.get("conversation_round", 0)

        # 构建增强上下文（合并 state、user_context、student_profile，优先级递减）
        enriched_context = {
            "skill_level": (
                student_profile.get("knowledge_level")
                or state.get("skill_level")
                or user_context.get("skill_level")
                or "unknown"
            ),
            "difficulty_level": (
                state.get("difficulty_level")
                or user_context.get("difficulty_level")
                or "medium"
            ),
            "goal_type": state.get("goal_type", user_context.get("goal_type", "general")),
        }
        if student_profile:
            enriched_context["learning_objectives"] = student_profile.get("learning_objectives", [])
            enriched_context["key_concepts"] = student_profile.get("key_concepts_covered", [])

        task_plan: Optional[Dict[str, Any]] = None

        # 1. 优先启发式规划（快速、无开销）
        task_plan = _heuristic_plan(user_query, enriched_context)

        # 2. 复杂意图 → LLM 精准规划
        if task_plan is None and self.enable_llm:
            task_plan = await self._llm_plan(user_query, enriched_context, state)

        # 3. 兜底方案
        if task_plan is None:
            self.logger.warning("规划兜底：使用默认 explain 策略")
            task_plan = {
                "intent": "concept_explanation",
                "strategy": "explain",
                "need_retrieval": True,
                "need_assessment": False,
                "core_concepts": [],
                "difficulty": enriched_context.get("skill_level", "intermediate"),
                "learning_goal": user_query[:80],
                "routing": "knowledge",
                "reasoning": "fallback: heuristic and LLM both failed",
            }

        # 多轮对话：检测是否延续苏格拉底对话
        if conversation_round > 0 and task_plan.get("strategy") != "curriculum":
            task_plan = self._maybe_continue_socratic(task_plan, state)

        self._call_count += 1
        elapsed_ms = (time.time() - start_ts) * 1000
        self.logger.info(
            f"[Planner] intent={task_plan['intent']} strategy={task_plan['strategy']} "
            f"retrieval={task_plan['need_retrieval']} ({elapsed_ms:.0f}ms)"
        )

        # 同步 v3 兼容字段
        from src.core.workflow.state import sync_compat_fields
        merged = {**state, "task_plan": task_plan}
        sync_compat_fields(merged)

        return {
            "task_plan": task_plan,
            "interpretation": merged.get("interpretation"),
            "query_type": merged.get("query_type"),
            "plan": merged.get("plan"),
            "retrieval_decision": merged.get("retrieval_decision"),
            "difficulty_level": merged.get("difficulty_level", enriched_context.get("difficulty_level", "medium")),
            "goal_type": merged.get("goal_type", enriched_context.get("goal_type", "general")),
            "next_step": task_plan.get("routing", "teaching"),
            "performance_data": {
                **state.get("performance_data", {}),
                "planner_ms": elapsed_ms,
            },
        }

    def _maybe_continue_socratic(
        self, task_plan: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检测是否应延续苏格拉底对话。

        仅当上一轮是苏格拉底策略，且当前问题未切换话题时，
        才将策略覆盖为 socratic，避免用户换话题后被错误强制。
        """
        prev_plan = state.get("task_plan") or {}
        if prev_plan.get("strategy") != "socratic":
            return task_plan

        prev_concepts = set(prev_plan.get("core_concepts", []))
        curr_concepts = set(task_plan.get("core_concepts", []))

        # 若当前规划存在核心概念，且与上一轮毫无重叠 → 视为话题切换
        if curr_concepts and prev_concepts and curr_concepts.isdisjoint(prev_concepts):
            self.logger.debug("[Planner] 话题切换，不延续苏格拉底策略")
            return task_plan

        # 延续苏格拉底
        task_plan = {**task_plan}
        task_plan["strategy"] = "socratic"
        task_plan["routing"] = "teaching"
        task_plan["need_retrieval"] = False
        self.logger.debug("[Planner] 延续苏格拉底对话策略")
        return task_plan

    async def _llm_plan(
        self,
        user_query: str,
        user_context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """使用 LLM 进行精准意图规划"""
        llm = self._get_llm_manager()
        if not llm:
            return None

        try:
            skill_level = user_context.get("skill_level", "unknown")
            difficulty_level = user_context.get("difficulty_level", "medium")
            conversation_round = state.get("conversation_round", 0)

            # 构建学生信息摘要
            student_info_lines = []
            if skill_level != "unknown":
                student_info_lines.append(f"- 知识水平：{skill_level}")
            student_info_lines.append(f"- 当前难度：{difficulty_level}")

            # 上一轮规划信息（辅助多轮决策）
            prev_plan = state.get("task_plan") or {}
            if prev_plan:
                student_info_lines.append(
                    f"- 上一轮：意图={prev_plan.get('intent', '-')} / 策略={prev_plan.get('strategy', '-')}"
                )
                if prev_plan.get("core_concepts"):
                    student_info_lines.append(
                        f"- 上轮核心概念：{', '.join(prev_plan['core_concepts'])}"
                    )

            # 最近对话历史（最多3轮）
            history_text = ""
            dialogue_history = state.get("dialogue_history", [])
            if dialogue_history:
                recent = dialogue_history[-3:]
                history_text = "\n".join(
                    f"[Round {h.get('round', i+1)}] "
                    f"Q: {h.get('question', h.get('content', ''))[:150]} "
                    f"A: {h.get('response', h.get('answer', ''))[:150]}"
                    for i, h in enumerate(recent)
                )

            student_info = "\n".join(student_info_lines) if student_info_lines else "- 暂无"

            user_msg = (
                f"学生信息：\n{student_info}\n"
                f"对话轮次：{conversation_round}\n"
            )
            if history_text:
                user_msg += f"最近对话：\n{history_text}\n"
            user_msg += f"\n当前问题：{user_query}\n\n输出规划 JSON："

            content = await _llm_chat(
                llm,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            return self._parse_plan_json(content) if content else None

        except Exception as e:
            self._error_count += 1
            self.logger.error(f"LLM 规划失败: {e}")
            return None

    def _parse_plan_json(self, content: str) -> Optional[Dict[str, Any]]:
        """从 LLM 输出中解析 task_plan JSON（支持嵌套结构）"""
        try:
            # 提取最外层 JSON 对象（处理嵌套数组/对象）
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end > start:
                json_str = content[start:end + 1]
            else:
                json_str = content.strip()

            plan = json.loads(json_str)

            # 校验并修正 intent / strategy
            valid_intents = {
                "concept_explanation", "knowledge_retrieval", "socratic_dialogue",
                "learning_guidance", "practice", "direct_answer", "smalltalk", "meta_question",
            }
            valid_strategies = {"explain", "socratic", "curriculum", "direct"}

            if plan.get("intent") not in valid_intents:
                plan["intent"] = "concept_explanation"
            if plan.get("strategy") not in valid_strategies:
                plan["strategy"] = "explain"

            # 确保所有必要字段存在
            plan.setdefault("need_retrieval", False)
            plan.setdefault("need_assessment", False)
            plan.setdefault("core_concepts", [])
            plan.setdefault("difficulty", "intermediate")
            plan.setdefault("learning_goal", "")
            plan.setdefault("reasoning", "")

            # 强制保持 routing 与 need_retrieval 一致
            plan["routing"] = "knowledge" if plan["need_retrieval"] else "teaching"

            # core_concepts 类型保护
            if not isinstance(plan["core_concepts"], list):
                plan["core_concepts"] = []

            return plan

        except (json.JSONDecodeError, AttributeError) as e:
            self.logger.warning(f"解析规划 JSON 失败: {e}, content={content[:300]}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent": "LearningPlanner",
            "call_count": self._call_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._call_count, 1),
        }
