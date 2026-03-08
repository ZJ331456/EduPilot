#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — TeachingAgent

职责（合并 v3 DraftWriter + SocraticGuide + CurriculumDesigner）：
- mode=explain    → 整合知识上下文，生成清晰解释 + 示例（原 DraftWriter）
- mode=socratic   → 生成苏格拉底式引导问题，促进深度理解（原 SocraticGuide）
- mode=curriculum → 生成结构化学习路径（原 CurriculumDesigner）
- mode=direct     → 简短直接回答，不需要知识检索支撑

设计要点：
1. 单 Agent 覆盖所有教学模式，减少 LLM 调用链路
2. 基于 task_plan.strategy 动态选择 prompt 模板
3. 引入 revision_gate：若评估层要求修改，可循环至多 2 次
4. 多轮苏格拉底对话中，维护问题历史避免重复
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from .prompt import (
    EXPLAIN_SYSTEM,
    SOCRATIC_SYSTEM,
    CURRICULUM_SYSTEM,
    DIRECT_SYSTEM,
    QUESTION_TYPES,
    DIRECT_SMALLTALK_FALLBACK,
)

logger = logging.getLogger(__name__)


async def _llm_chat(
    llm_manager,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
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


# ---------------------------------------------------------------------------
# 教学模式实现（prompt 已迁移至 prompt.py）
# ---------------------------------------------------------------------------


class TeachingAgent:
    """EduPilot v4 统一教学 Agent

    通过 task_plan.strategy 动态选择教学模式，一个 Agent 覆盖全部教学场景。
    """

    MAX_REVISIONS = 2

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
        """执行教学，返回更新的 state 片段"""
        start_ts = time.time()

        task_plan: Dict[str, Any] = state.get("task_plan") or {}
        strategy: str = task_plan.get("strategy", "explain")
        revision_count: int = state.get("revision_count", 0)

        # 修改循环上限
        if revision_count >= self.MAX_REVISIONS:
            self.logger.info("[Teacher] 达到最大修改次数，强制通过")
            strategy = strategy  # 保持策略不变，但继续执行

        # 分发到对应教学模式
        dispatch = {
            "explain": self._teach_explain,
            "socratic": self._teach_socratic,
            "curriculum": self._teach_curriculum,
            "direct": self._teach_direct,
        }
        handler = dispatch.get(strategy, self._teach_explain)

        try:
            teaching_output = await handler(state, task_plan)
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"[Teacher] {strategy} 模式失败: {e}")
            teaching_output = {
                "mode": strategy,
                "content": f"抱歉，生成教学内容时出现问题：{str(e)[:100]}。请稍后重试。",
                "socratic_question": "",
                "curriculum": {},
                "follow_up_hints": [],
                "error": str(e),
            }

        self._call_count += 1
        elapsed_ms = (time.time() - start_ts) * 1000
        self.logger.info(f"[Teacher] mode={strategy} ({elapsed_ms:.0f}ms)")

        # 将主要教学内容添加到消息流
        content = teaching_output.get("content", "")
        socratic_q = teaching_output.get("socratic_question", "")

        messages = []
        if content:
            messages.append({"role": "assistant", "content": content})
        if socratic_q:
            messages.append({"role": "assistant", "content": socratic_q})

        # 同步 v3 兼容字段
        from src.core.workflow.state import sync_compat_fields
        partial_state = {**state, "teaching_output": teaching_output}
        sync_compat_fields(partial_state)

        return {
            "teaching_output": teaching_output,
            "draft_content": partial_state.get("draft_content", content),
            "socratic_question": partial_state.get("socratic_question", socratic_q),
            "socratic_questions": partial_state.get("socratic_questions", []),
            "socratic_guidance": teaching_output,
            "curriculum_plan": teaching_output.get("curriculum", {}),
            "messages": messages,
            "performance_data": {
                **state.get("performance_data", {}),
                "teacher_ms": elapsed_ms,
            },
        }

    # ── 教学模式实现 ────────────────────────────────────────────────────

    async def _teach_explain(
        self, state: Dict[str, Any], task_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解释型教学 — 整合知识库检索内容，生成结构化解释"""
        llm = self._get_llm_manager()
        if not llm:
            return self._fallback_output("explain", state.get("user_query", ""))

        user_query = state.get("user_query", "")
        skill_level = state.get("skill_level", "intermediate")
        knowledge_context = state.get("knowledge_context") or {}
        retrieved_chunks = knowledge_context.get("retrieved_chunks", [])
        student_profile = state.get("student_profile") or {}

        # 构建知识上下文文本
        knowledge_text = ""
        if retrieved_chunks:
            chunks_text = "\n\n".join(
                f"[来源: {c.get('source', '知识库')}]\n{c.get('content', '')}"
                for c in retrieved_chunks[:5]
            )
            knowledge_text = f"\n\n参考资料：\n{chunks_text}"

        # 工具结果补充
        tool_results = knowledge_context.get("tool_results", {})
        if tool_results:
            tool_text = "\n".join(f"- {k}: {v}" for k, v in tool_results.items() if v)
            if tool_text:
                knowledge_text += f"\n\n工具查询结果：\n{tool_text}"

        # 修改建议（若是修改轮次）
        critique = state.get("critique", "")
        revision_instruction = ""
        if critique and state.get("revision_count", 0) > 0:
            revision_instruction = f"\n\n⚠️ 上一版本的改进建议：{critique}\n请根据以上建议改进回复。"

        user_msg = f"""学生水平：{skill_level}
学习目标：{task_plan.get('learning_goal', user_query)}
核心概念：{', '.join(task_plan.get('core_concepts', []))}
{knowledge_text}
{revision_instruction}

学生问题：{user_query}

请生成教学回复："""

        content = await _llm_chat(
            llm,
            messages=[
                {"role": "system", "content": EXPLAIN_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return {
            "mode": "explain",
            "content": content,
            "socratic_question": "",
            "curriculum": {},
            "follow_up_hints": self._extract_follow_up(content),
        }

    async def _teach_socratic(
        self, state: Dict[str, Any], task_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """苏格拉底式引导教学"""
        llm = self._get_llm_manager()
        if not llm:
            return self._fallback_output("socratic", state.get("user_query", ""))

        user_query = state.get("user_query", "")
        user_response = state.get("user_response", "")
        dialogue_history = state.get("dialogue_history", [])
        existing_questions = state.get("socratic_questions", [])
        knowledge_context = state.get("knowledge_context") or {}
        retrieved_chunks = knowledge_context.get("retrieved_chunks", [])

        # 已用问题类型（避免重复）
        asked_types = [
            h.get("question_type", "")
            for h in dialogue_history[-5:]
            if h.get("question_type")
        ]
        available_types = [t for t in QUESTION_TYPES if t not in asked_types]
        preferred_type = available_types[0] if available_types else QUESTION_TYPES[0]

        # 对话历史文本
        history_text = ""
        if dialogue_history:
            history_text = "\n".join(
                f"问题: {h.get('question', '')}\n学生: {h.get('response', '')}"
                for h in dialogue_history[-3:]
            )

        # 知识参考
        knowledge_hint = ""
        if retrieved_chunks:
            knowledge_hint = f"\n参考知识点（内部使用，不要直接告诉学生）：{retrieved_chunks[0].get('content', '')[:300]}"

        user_msg = f"""主题：{task_plan.get('learning_goal', user_query)}
学生当前问题/回答：{user_response or user_query}
{f"对话历史：{history_text}" if history_text else ""}
{knowledge_hint}
已使用的问题类型：{asked_types}
本轮建议使用：{preferred_type} 类型问题

请生成苏格拉底引导问题："""

        content = await _llm_chat(
            llm,
            messages=[
                {"role": "system", "content": SOCRATIC_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.6,
            max_tokens=512,
        )

        # 提取苏格拉底问题（以💭开头的部分）
        socratic_q = content
        parts = content.split("💭")
        main_response = parts[0].strip() if len(parts) > 1 else ""
        question_part = ("💭" + parts[1]).strip() if len(parts) > 1 else content

        return {
            "mode": "socratic",
            "content": main_response or content,
            "socratic_question": question_part,
            "question_type": preferred_type,
            "curriculum": {},
            "follow_up_hints": [],
        }

    async def _teach_curriculum(
        self, state: Dict[str, Any], task_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """结构化学习路径生成"""
        llm = self._get_llm_manager()
        if not llm:
            return self._fallback_output("curriculum", state.get("user_query", ""))

        user_query = state.get("user_query", "")
        skill_level = state.get("skill_level", "beginner")
        knowledge_context = state.get("knowledge_context") or {}
        retrieved_chunks = knowledge_context.get("retrieved_chunks", [])

        knowledge_summary = ""
        if retrieved_chunks:
            knowledge_summary = "\n".join(
                c.get("content", "")[:200] for c in retrieved_chunks[:3]
            )

        user_msg = f"""学生水平：{skill_level}
学习目标：{task_plan.get('learning_goal', user_query)}
核心概念：{', '.join(task_plan.get('core_concepts', []))}
{f"相关知识参考：{knowledge_summary}" if knowledge_summary else ""}

学生请求：{user_query}

请生成结构化学习路径："""

        content = await _llm_chat(
            llm,
            messages=[
                {"role": "system", "content": CURRICULUM_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=1200,
        )

        # 尝试解析课程结构
        curriculum = self._parse_curriculum_structure(content)

        return {
            "mode": "curriculum",
            "content": content,
            "socratic_question": "",
            "curriculum": curriculum,
            "follow_up_hints": ["从第一阶段开始，我们可以深入探讨任何一个知识点"],
        }

    async def _teach_direct(
        self, state: Dict[str, Any], task_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """直接简洁回答"""
        llm = self._get_llm_manager()
        if not llm:
            intent = task_plan.get("intent", "")
            if intent == "smalltalk":
                return {
                    "mode": "direct",
                    "content": DIRECT_SMALLTALK_FALLBACK,
                    "socratic_question": "",
                    "curriculum": {},
                    "follow_up_hints": [],
                }
            return self._fallback_output("direct", state.get("user_query", ""))

        user_query = state.get("user_query", "")
        intent = task_plan.get("intent", "")
        knowledge_context = state.get("knowledge_context") or {}
        tool_results = knowledge_context.get("tool_results", {})

        tool_context = ""
        if tool_results:
            tool_context = "\n工具查询结果：" + "\n".join(
                f"- {k}: {v}" for k, v in tool_results.items() if v
            )

        user_msg = f"""意图：{intent}
{tool_context}

学生问题：{user_query}

请提供简洁直接的回答："""

        content = await _llm_chat(
            llm,
            messages=[
                {"role": "system", "content": DIRECT_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        return {
            "mode": "direct",
            "content": content,
            "socratic_question": "",
            "curriculum": {},
            "follow_up_hints": [],
        }

    # ── 工具方法 ─────────────────────────────────────────────────────────

    def _extract_content(self, response: Any) -> str:
        """从 LLM 响应中提取文本内容"""
        if isinstance(response, dict):
            return response.get("content", response.get("text", str(response)))
        return str(response)

    def _extract_follow_up(self, content: str) -> List[str]:
        """从回复中提取 follow-up 问题提示"""
        hints = []
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.endswith("？") and len(line) > 10:
                hints.append(line)
        return hints[:3]

    def _parse_curriculum_structure(self, content: str) -> Dict[str, Any]:
        """从 Markdown 文本中解析课程结构"""
        stages = []
        current_stage = None

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("##") or (line.startswith("**") and "阶段" in line):
                if current_stage:
                    stages.append(current_stage)
                current_stage = {"name": line.lstrip("#").strip(), "points": []}
            elif current_stage and (line.startswith("-") or line.startswith("*")):
                point = line.lstrip("-*").strip()
                if point:
                    current_stage["points"].append(point)

        if current_stage:
            stages.append(current_stage)

        return {
            "stages": stages,
            "total_stages": len(stages),
            "raw_content": content[:500],
        }

    def _fallback_output(self, mode: str, user_query: str) -> Dict[str, Any]:
        """LLM 不可用时的兜底输出"""
        return {
            "mode": mode,
            "content": f"关于「{user_query[:50]}」，系统正在处理中，请稍后再试。",
            "socratic_question": "",
            "curriculum": {},
            "follow_up_hints": [],
            "error": "llm_unavailable",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent": "TeachingAgent",
            "call_count": self._call_count,
            "error_count": self._error_count,
        }
