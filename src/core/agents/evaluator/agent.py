#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — EvaluationAgent

职责（合并 v3 Reviewer + QuizMaster）：
- Phase 1 (Review)  → 评估 TeachingAgent 的输出质量，决定是否通过或需修改
- Phase 2 (Quiz)    → 当 task_plan.need_assessment=True 时，生成理解测验题
- 安全过滤          → 内容合规检查
- 修改决策          → 超出最大修改次数时强制通过

设计原则：
1. 一次 LLM 调用同时完成 Review + Quiz 生成（如需）
2. 低温度（0.2）保证评估的一致性和严谨性
3. 强制通过阈值：revision_count >= MAX_REVISIONS 或 quality_score >= 0.65
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from .prompt import (
    MAX_REVISIONS,
    QUALITY_THRESHOLD,
    BANNED_WORDS,
    EVALUATION_SYSTEM,
    QUIZ_SYSTEM,
)

logger = logging.getLogger(__name__)


async def _llm_chat(
    llm_manager,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> str:
    """统一 LLM 调用适配层（dict → Message 对象）"""
    from src.infrastructure.llm.base import Message

    msg_objects = [Message(role=m["role"], content=m["content"]) for m in messages]
    try:
        client = llm_manager.get_client()
        if client is None:
            return ""
        response = await client.async_chat_completion(
            msg_objects, temperature=temperature, max_tokens=max_tokens
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


class EvaluationAgent:
    """EduPilot v4 统一评估 Agent

    Review + Quiz 合并，减少 LLM 调用次数。
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._llm_client = None
        self._call_count = 0
        self._error_count = 0

    def _get_llm_manager(self):
        if self._llm_client is None:
            try:
                from src.infrastructure.llm.manager import get_llm_manager
                self._llm_client = get_llm_manager()
            except Exception as e:
                self.logger.warning(f"LLM manager not available: {e}")
        return self._llm_client

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行评估，返回更新的 state 片段"""
        start_ts = time.time()

        task_plan: Dict[str, Any] = state.get("task_plan") or {}
        teaching_output: Dict[str, Any] = state.get("teaching_output") or {}
        revision_count: int = state.get("revision_count", 0)
        need_assessment: bool = task_plan.get("need_assessment", False)

        content = teaching_output.get("content", state.get("draft_content", ""))

        # ── 安全过滤（无 LLM 开销）────────────────────────────────────
        safety_issue = self._safety_check(content)

        # ── 强制通过条件 ─────────────────────────────────────────────
        if revision_count >= MAX_REVISIONS:
            self.logger.info(f"[Evaluator] 已达最大修改次数 {MAX_REVISIONS}，强制通过")
            evaluation_output = {
                "quality_score": 0.70,
                "is_satisfactory": True,
                "critique": "",
                "strengths": ["已达修改上限，强制通过"],
                "revision_needed": False,
                "quiz": None,
                "feedback": "已达最大修改次数，内容强制通过。",
            }
            return self._build_result(evaluation_output, state, start_ts)

        if safety_issue:
            self.logger.warning(f"[Evaluator] 安全问题: {safety_issue}")
            evaluation_output = {
                "quality_score": 0.0,
                "is_satisfactory": False,
                "critique": f"内容包含不适当内容（{safety_issue}），请重新生成。",
                "strengths": [],
                "revision_needed": True,
                "quiz": None,
                "feedback": "安全检查未通过",
            }
            return self._build_result(evaluation_output, state, start_ts, increment_revision=True)

        if not content.strip():
            self.logger.warning("[Evaluator] 内容为空，直接通过")
            evaluation_output = {
                "quality_score": 0.5,
                "is_satisfactory": True,
                "critique": "",
                "strengths": [],
                "revision_needed": False,
                "quiz": None,
                "feedback": "内容为空，跳过评估",
            }
            return self._build_result(evaluation_output, state, start_ts)

        # ── LLM 评估 ──────────────────────────────────────────────────
        try:
            evaluation_output = await self._llm_evaluate(
                content=content,
                state=state,
                task_plan=task_plan,
                need_assessment=need_assessment,
            )
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"[Evaluator] LLM 评估失败: {e}")
            # 兜底：默认通过
            evaluation_output = {
                "quality_score": 0.70,
                "is_satisfactory": True,
                "critique": "",
                "strengths": [],
                "revision_needed": False,
                "quiz": None,
                "feedback": f"评估异常，默认通过: {str(e)[:100]}",
            }

        self._call_count += 1
        return self._build_result(
            evaluation_output, state, start_ts,
            increment_revision=not evaluation_output.get("is_satisfactory", True),
        )

    async def _llm_evaluate(
        self,
        content: str,
        state: Dict[str, Any],
        task_plan: Dict[str, Any],
        need_assessment: bool,
    ) -> Dict[str, Any]:
        """调用 LLM 进行质量评估 + 可选的测验生成"""
        llm = self._get_llm_manager()
        if not llm:
            return {
                "quality_score": 0.70,
                "is_satisfactory": True,
                "critique": "",
                "strengths": ["LLM 不可用，默认通过"],
                "revision_needed": False,
                "quiz": None,
                "feedback": "LLM 评估不可用",
            }

        user_query = state.get("user_query", "")
        skill_level = state.get("skill_level", "intermediate")
        teaching_mode = (state.get("teaching_output") or {}).get("mode", "explain")

        eval_user_msg = f"""学生水平：{skill_level}
教学模式：{teaching_mode}
学生问题：{user_query}

AI 导师的回复：
{content}

请进行质量评估（JSON 格式）："""

        eval_text = await _llm_chat(
            llm,
            messages=[
                {"role": "system", "content": EVALUATION_SYSTEM},
                {"role": "user", "content": eval_user_msg},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        evaluation = self._parse_json(eval_text)

        if evaluation is None:
            evaluation = {
                "quality_score": 0.70,
                "is_satisfactory": True,
                "critique": "",
                "strengths": [],
                "revision_needed": False,
            }

        # 确保字段完整
        score = float(evaluation.get("quality_score", 0.70))
        evaluation["quality_score"] = score
        evaluation["is_satisfactory"] = score >= QUALITY_THRESHOLD
        evaluation["revision_needed"] = not evaluation["is_satisfactory"]
        evaluation.setdefault("strengths", [])
        evaluation.setdefault("critique", "")

        # ── 测验生成（can_assessment 且内容质量足够时）─────────────────
        quiz_data = None
        if need_assessment and evaluation["is_satisfactory"]:
            try:
                quiz_data = await self._generate_quiz(content, task_plan, state, llm)
            except Exception as e:
                self.logger.warning(f"[Evaluator] 测验生成失败: {e}")

        evaluation["quiz"] = quiz_data
        evaluation["feedback"] = (
            evaluation.get("critique", "") or
            f"质量评分 {score:.2f}，{'通过' if evaluation['is_satisfactory'] else '需要改进'}"
        )

        return evaluation

    async def _generate_quiz(
        self,
        content: str,
        task_plan: Dict[str, Any],
        state: Dict[str, Any],
        llm: Any,  # LLMManager instance
    ) -> Optional[Dict[str, Any]]:
        """生成理解测验题"""
        difficulty = task_plan.get("difficulty", "intermediate")
        core_concepts = task_plan.get("core_concepts", [])

        quiz_user_msg = f"""基于以下学习内容，生成测验题：

难度等级：{difficulty}
核心概念：{', '.join(core_concepts)}

学习内容：
{content[:1500]}

请生成 3 道测验题（JSON 格式）："""

        quiz_text = await _llm_chat(
            llm,
            messages=[
                {"role": "system", "content": QUIZ_SYSTEM},
                {"role": "user", "content": quiz_user_msg},
            ],
            temperature=0.5,
            max_tokens=1024,
        )
        quiz_data = self._parse_json(quiz_text)

        if quiz_data and "questions" in quiz_data:
            return quiz_data

        return None

    # ── 安全检查 ─────────────────────────────────────────────────────────

    def _safety_check(self, content: str) -> Optional[str]:
        """返回第一个违规词，或 None（安全）"""
        for word in BANNED_WORDS:
            if word in content:
                return word
        return None

    # ── 工具方法 ─────────────────────────────────────────────────────────

    def _build_result(
        self,
        evaluation_output: Dict[str, Any],
        state: Dict[str, Any],
        start_ts: float,
        increment_revision: bool = False,
    ) -> Dict[str, Any]:
        """构建返回的 state 更新片段"""
        elapsed_ms = (time.time() - start_ts) * 1000
        is_satisfactory = evaluation_output.get("is_satisfactory", True)

        self.logger.info(
            f"[Evaluator] score={evaluation_output.get('quality_score', 0):.2f} "
            f"pass={is_satisfactory} ({elapsed_ms:.0f}ms)"
        )

        from src.core.workflow.state import sync_compat_fields
        partial_state = {**state, "evaluation_output": evaluation_output}
        sync_compat_fields(partial_state)

        result = {
            "evaluation_output": evaluation_output,
            "critique": evaluation_output.get("critique", ""),
            "is_satisfactory": is_satisfactory,
            "quiz_stats": evaluation_output.get("quiz") or {},
            "performance_data": {
                **state.get("performance_data", {}),
                "evaluator_ms": elapsed_ms,
            },
        }

        if increment_revision:
            result["revision_count"] = state.get("revision_count", 0) + 1

        # 测验结果追加到消息和 draft_content
        if evaluation_output.get("quiz") and is_satisfactory:
            quiz = evaluation_output["quiz"]
            quiz_text = self._format_quiz(quiz)
            if quiz_text:
                result["messages"] = [{"role": "assistant", "content": quiz_text}]
                draft = state.get("draft_content", "")
                result["draft_content"] = f"{draft}\n\n{quiz_text}" if draft else quiz_text

        return result

    def _format_quiz(self, quiz_data: Dict[str, Any]) -> str:
        """将测验数据格式化为文本"""
        if not quiz_data or "questions" not in quiz_data:
            return ""

        lines = ["\n\n---\n📝 **理解测验**\n"]
        for i, q in enumerate(quiz_data.get("questions", []), 1):
            lines.append(f"\n**{i}. {q.get('question', '')}**")
            for letter, option in q.get("options", {}).items():
                lines.append(f"   {letter}. {option}")

        lines.append("\n*请思考答案，回复你的选择，我会为你解析。*")
        return "\n".join(lines)

    def _extract_content(self, response: Any) -> str:
        if isinstance(response, dict):
            return response.get("content", response.get("text", str(response)))
        return str(response)

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(text.strip())
        except (json.JSONDecodeError, AttributeError):
            return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent": "EvaluationAgent",
            "call_count": self._call_count,
            "error_count": self._error_count,
        }
