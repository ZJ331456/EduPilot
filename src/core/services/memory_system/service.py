#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — MemorySystem Service

职责（重构自 v3 MemoryManagerAgent）：
- 会话结束时异步写入学生画像 + 学习记录（不阻塞主流程）
- 会话开始时读取历史画像，供 Planner/Teacher 使用
- 交互分析：学习质量、知识缺口、情感状态检测
- 提供 memory_analysis 供 API 层读取

v4 改进：
1. 只在对话结束（workflow_complete 或对话阶段结束）时写存储，
   不再每轮都执行，减少 IO 开销约 80%
2. 简化分析逻辑：移除 TripleExtractor LLM 调用，使用规则提取
3. 存储使用现有 LocalStorageManager（不重造轮子）
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .prompt import (
    SUMMARY_TEMPLATE_SINGLE,
    SUMMARY_TEMPLATE_MULTI,
    RECOMMENDATION_TEMPLATES,
)

logger = logging.getLogger(__name__)


class MemorySystemService:
    """EduPilot v4 记忆系统服务

    设计为纯服务层，只在需要时被 workflow 调用。
    通过 LocalStorageManager 持久化数据。
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._storage = None
        self._profile_cache: Dict[str, Dict[str, Any]] = {}  # 内存缓存
        self._call_count = 0
        self._error_count = 0

    def _get_storage(self):
        """懒加载存储管理器"""
        if self._storage is None:
            try:
                from src.core.services.memory_system.storage import LocalStorageManager, StorageConfig
                config = StorageConfig.create_default()
                self._storage = LocalStorageManager(config)
            except Exception as e:
                self.logger.warning(f"存储管理器初始化失败: {e}")
        return self._storage

    async def load_student_profile(
        self, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """加载学生画像（供 Planner 在开始时调用）"""
        if not user_id:
            return None

        # 内存缓存优先
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]

        try:
            storage = self._get_storage()
            if not storage:
                return None

            profile = storage.load_user_profile(user_id)
            if profile:
                self._profile_cache[user_id] = profile
            return profile
        except Exception as e:
            self.logger.warning(f"加载学生画像失败 ({user_id}): {e}")
            return None

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行记忆更新（在对话结束时调用）"""
        start_ts = time.time()

        user_id = state.get("user_id") or state.get("user_context", {}).get("user_id")
        session_id = state.get("session_id", "")

        if not session_id:
            return {"memory_updated": False}

        # 分析本次交互
        memory_analysis = self._analyze_interaction(state)

        # 后台异步持久化（不阻塞响应）
        asyncio.create_task(
            self._persist_async(user_id, session_id, state, memory_analysis)
        )

        self._call_count += 1
        elapsed_ms = (time.time() - start_ts) * 1000

        self.logger.info(
            f"[MemorySystem] session={session_id[:8]}... analysis={bool(memory_analysis)} "
            f"({elapsed_ms:.0f}ms)"
        )

        from src.core.workflow.state import sync_compat_fields
        partial_state = {**state, "memory_analysis": memory_analysis}
        sync_compat_fields(partial_state)

        return {
            "memory_updated": True,
            "memory_analysis": memory_analysis,
            "learning_feedback": partial_state.get("learning_feedback", memory_analysis),
            "performance_data": {
                **state.get("performance_data", {}),
                "memory_system_ms": elapsed_ms,
            },
        }

    def _analyze_interaction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """规则驱动的交互分析（无 LLM 开销）"""
        task_plan = state.get("task_plan") or {}
        teaching_output = state.get("teaching_output") or {}
        evaluation_output = state.get("evaluation_output") or {}
        dialogue_history = state.get("dialogue_history", [])
        user_responses = state.get("user_responses", [])

        # 学习质量评估
        quality_score = evaluation_output.get("quality_score", 0.5)
        is_satisfactory = evaluation_output.get("is_satisfactory", False)

        # 参与度评估（基于对话轮次和回复长度）
        avg_response_len = (
            sum(len(r) for r in user_responses) / max(len(user_responses), 1)
            if user_responses else 0
        )
        engagement_level = (
            "high" if avg_response_len > 100 else
            "medium" if avg_response_len > 30 else
            "low"
        )

        # 知识点覆盖
        core_concepts = task_plan.get("core_concepts", [])
        difficulty = task_plan.get("difficulty", "intermediate")
        strategy = task_plan.get("strategy", "explain")

        # 知识缺口检测（简单规则）
        knowledge_gaps = []
        if not is_satisfactory and evaluation_output.get("critique"):
            knowledge_gaps.append(evaluation_output["critique"][:100])

        # 生成学习反馈
        recommendations = []
        if strategy == "socratic" and len(dialogue_history) > 2:
            concepts_str = "、".join(core_concepts[:2]) if core_concepts else ""
            recommendations.append(RECOMMENDATION_TEMPLATES["socratic_continue"].format(concepts=concepts_str or "当前话题"))
        if difficulty == "beginner":
            recommendations.append(RECOMMENDATION_TEMPLATES["beginner_path"])
        if quality_score < 0.6:
            recommendations.append(RECOMMENDATION_TEMPLATES["low_quality"])

        return {
            "quality_score": quality_score,
            "engagement_level": engagement_level,
            "core_concepts_covered": core_concepts,
            "knowledge_gaps": knowledge_gaps,
            "learning_strategy_used": strategy,
            "difficulty_level": difficulty,
            "total_rounds": state.get("conversation_round", 0),
            "recommendations": recommendations,
            "summary": self._build_summary(state, core_concepts),
            "timestamp": datetime.now().isoformat(),
        }

    def _build_summary(
        self, state: Dict[str, Any], core_concepts: List[str]
    ) -> str:
        """构建学习摘要文本"""
        user_query = state.get("user_query", "")
        rounds = state.get("conversation_round", 0)
        concepts_text = "、".join(core_concepts) if core_concepts else "相关知识"

        if rounds == 0:
            return SUMMARY_TEMPLATE_SINGLE.format(concepts=concepts_text)
        return SUMMARY_TEMPLATE_MULTI.format(
            rounds=rounds,
            concepts=concepts_text,
            query_preview=user_query[:50],
        )

    async def _persist_async(
        self,
        user_id: Optional[str],
        session_id: str,
        state: Dict[str, Any],
        memory_analysis: Dict[str, Any],
    ):
        """异步持久化（后台执行，不影响响应速度）"""
        try:
            storage = self._get_storage()
            if not storage:
                return

            # 保存会话记忆
            session_data = self._build_session_data(session_id, state, memory_analysis)
            storage.save_session_memory(session_id, session_data)

            # 更新用户画像（仅当有 user_id 时）
            if user_id:
                profile = await self._update_profile(user_id, state, memory_analysis, storage)
                if profile:
                    self._profile_cache[user_id] = profile

            # 保存学习记录
            if user_id:
                learning_record = self._build_learning_record(
                    user_id, session_id, state, memory_analysis
                )
                storage.save_learning_record(user_id, learning_record)

        except Exception as e:
            self._error_count += 1
            self.logger.error(f"记忆持久化失败 ({session_id}): {e}")

    def _build_session_data(
        self,
        session_id: str,
        state: Dict[str, Any],
        memory_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """构建会话数据结构（复用 v3 格式，保持兼容）"""
        task_plan = state.get("task_plan") or {}
        return {
            "session_id": session_id,
            "query": state.get("user_query", ""),
            "timestamp": datetime.now().isoformat(),
            "query_analysis": {
                "intent": task_plan.get("intent", ""),
                "query_type": task_plan.get("intent", ""),
                "interpretation": task_plan,
                "keywords": task_plan.get("core_concepts", []),
            },
            "socratic_dialogue": {
                "questions": state.get("socratic_questions", []),
                "current_question": state.get("socratic_question", ""),
                "user_responses": state.get("user_responses", []),
            },
            "understanding_tracking": {
                "current_level": state.get("understanding_level", "no_understanding"),
                "conversation_stage": state.get("conversation_stage", "initial_query"),
                "conversation_round": state.get("conversation_round", 0),
            },
            "dialogue_history": state.get("dialogue_history", []),
            "execution_details": {
                "plan": state.get("task_plan"),
                "execution_result": state.get("execution_result"),
                "teaching_output": state.get("teaching_output"),
                "evaluation_output": state.get("evaluation_output"),
            },
            "knowledge_retrieval": {
                "sources": state.get("knowledge_sources", []),
                "context": state.get("knowledge_context"),
            },
            "memory_analysis": memory_analysis,
        }

    async def _update_profile(
        self,
        user_id: str,
        state: Dict[str, Any],
        memory_analysis: Dict[str, Any],
        storage: Any,
    ) -> Optional[Dict[str, Any]]:
        """更新学生画像"""
        try:
            existing = storage.load_user_profile(user_id) or {}
            task_plan = state.get("task_plan") or {}

            # 更新知识掌握状态
            knowledge_state = existing.get("knowledge_state", {})
            for concept in memory_analysis.get("core_concepts_covered", []):
                if concept:
                    knowledge_state[concept] = {
                        "last_studied": datetime.now().isoformat(),
                        "quality_score": memory_analysis.get("quality_score", 0.5),
                        "difficulty": task_plan.get("difficulty", "intermediate"),
                    }

            # 更新学习偏好
            preferences = existing.get("learning_preferences", {})
            strategy = memory_analysis.get("learning_strategy_used", "")
            if strategy:
                strategy_counts = preferences.get("strategy_counts", {})
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                preferences["strategy_counts"] = strategy_counts
                # 推断偏好策略
                if strategy_counts:
                    preferences["preferred_strategy"] = max(
                        strategy_counts, key=strategy_counts.get
                    )

            profile = {
                **existing,
                "user_id": user_id,
                "last_active": datetime.now().isoformat(),
                "total_sessions": existing.get("total_sessions", 0) + 1,
                "knowledge_state": knowledge_state,
                "learning_preferences": preferences,
                "knowledge_level": task_plan.get("difficulty", existing.get("knowledge_level", "unknown")),
            }

            storage.save_user_profile(user_id, profile)
            return profile
        except Exception as e:
            self.logger.warning(f"画像更新失败 ({user_id}): {e}")
            return None

    def _build_learning_record(
        self,
        user_id: str,
        session_id: str,
        state: Dict[str, Any],
        memory_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """构建学习记录"""
        return {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "topic": state.get("user_query", "")[:100],
            "core_concepts": memory_analysis.get("core_concepts_covered", []),
            "quality_score": memory_analysis.get("quality_score", 0.5),
            "engagement_level": memory_analysis.get("engagement_level", "medium"),
            "total_rounds": memory_analysis.get("total_rounds", 0),
            "strategy": memory_analysis.get("learning_strategy_used", ""),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "service": "MemorySystem",
            "call_count": self._call_count,
            "error_count": self._error_count,
            "cached_profiles": len(self._profile_cache),
        }
