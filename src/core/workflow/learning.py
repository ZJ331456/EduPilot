#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — LangGraph 学习工作流引擎

v4 架构图（精简版）：

         ┌─────────────────────────────┐
         │        User Query            │
         └──────────────┬──────────────┘
                        ↓
              ┌─────────────────┐
              │  planner_node   │  ← LLM 0~1 次（启发式 + 精准规划）
              └────────┬────────┘
                       ↓
          ┌────────────┴────────────┐
          ↓ need_retrieval=True     ↓ need_retrieval=False
  ┌──────────────┐        ┌──────────────┐
  │knowledge_node│        │              │
  │ (no LLM)     │        │              │
  └──────┬───────┘        │              │
         └────────────────┤              │
                          ↓              ↓
              ┌─────────────────────────┐
              │     teaching_node       │  ← LLM 1 次（explain/socratic/curriculum/direct）
              └──────────┬──────────────┘
                         ↓
            ┌────────────┴────────────┐
            ↓ need_evaluation=True    ↓ socratic/direct → 直接结束
   ┌──────────────────┐      ┌────────────────┐
   │  evaluation_node │      │   memory_node  │  ← no LLM（IO 写入）
   │  LLM 1 次        │      └────────┬───────┘
   └────────┬─────────┘               ↓
            ↓ 通过                    END
   ┌────────────────┐
   │  memory_node   │
   └────────┬───────┘
            ↓
           END

平均 LLM 调用次数：2~3 次（v3：5~7 次）
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from .state import LearningWorkflowState, create_initial_state, sync_compat_fields
from .prompt import (
    NEXT_SUGGESTIONS_BY_INTENT,
    NEXT_SUGGESTIONS_BY_STRATEGY,
    NEXT_SUGGESTIONS_DEFAULT,
)
from .nodes import LearningWorkflowNodes
from .routing import (
    route_after_planning,
    route_after_teaching,
    route_after_evaluation,
)
from src.infrastructure.utils.enums import QueryType


class LangGraphLearningWorkflow:
    """EduPilot v4 LangGraph 学习工作流

    v4 核心改进：
    - 5 节点替代 12 节点（58% 精简）
    - 平均 2~3 次 LLM 调用（v3 为 5~7 次）
    - 无双状态转换（AgentState ↔ LearningWorkflowState 开销清零）
    - 条件路由更清晰：规划 → 知识? → 教学 → 评估? → 记忆
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

        self.feature_flags = {
            "enable_knowledge_engine": True,
            "enable_evaluation": True,
            "enable_memory": True,
            "enable_llm_planner": True,
        }
        if "feature_flags" in self.config:
            self.feature_flags.update(self.config["feature_flags"] or {})

        self.workflow_config = {
            "max_iterations": self.config.get("max_iterations", 5),
            "timeout_seconds": self.config.get("timeout_seconds", 120),
            "enable_socratic": self.config.get("enable_socratic", True),
            "feature_flags": self.feature_flags,
        }

        self.nodes = LearningWorkflowNodes(self.feature_flags)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.system_stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "average_session_duration": 0.0,
            "total_queries_processed": 0,
        }

        self.graph = self._build_graph()
        self.logger.info("[v4] LangGraphLearningWorkflow initialized")

    def _build_graph(self) -> StateGraph:
        """构建 v4 精简 LangGraph 图（5 个有效节点）"""
        workflow = StateGraph(LearningWorkflowState)

        # ── 注册节点 ─────────────────────────────────────────────────────
        workflow.add_node("planner", self.nodes.planner_node)
        workflow.add_node("knowledge", self.nodes.knowledge_node)
        workflow.add_node("teaching", self.nodes.teaching_node)
        workflow.add_node("evaluation", self.nodes.evaluation_node)
        workflow.add_node("memory", self.nodes.memory_node)
        workflow.add_node("error_handler", self.nodes.error_handler_node)

        # ── 入口 ─────────────────────────────────────────────────────────
        workflow.set_entry_point("planner")

        # ── 条件边 ───────────────────────────────────────────────────────
        # 1. planner → knowledge | teaching | error_handler
        workflow.add_conditional_edges(
            "planner",
            route_after_planning,
            {
                "knowledge": "knowledge",
                "teaching": "teaching",
                "error_handler": "error_handler",
            },
        )

        # 2. knowledge → teaching（固定，无条件）
        workflow.add_edge("knowledge", "teaching")

        # 3. teaching → evaluation | memory | error_handler
        workflow.add_conditional_edges(
            "teaching",
            route_after_teaching,
            {
                "evaluation": "evaluation",
                "memory": "memory",
                "error_handler": "error_handler",
            },
        )

        # 4. evaluation → teaching（需修改）| memory（通过）
        workflow.add_conditional_edges(
            "evaluation",
            route_after_evaluation,
            {
                "teaching": "teaching",
                "memory": "memory",
            },
        )

        # 5. 终止
        workflow.add_edge("memory", END)
        workflow.add_edge("error_handler", END)

        graph = workflow.compile()
        self.logger.info("[v4] Graph compiled: planner→(knowledge?)→teaching→(evaluation?)→memory→END")
        return graph

    # ── 公共接口 ─────────────────────────────────────────────────────────

    async def process_query(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        workflow_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """处理新查询"""
        try:
            effective_config = {**self.workflow_config, **(workflow_config or {})}
            if "feature_flags" in effective_config:
                self.feature_flags.update(effective_config["feature_flags"])
                self.nodes.set_feature_flags(self.feature_flags)

            # 新话题检测：检测到则重置会话
            if session_id and self._detect_new_topic(user_query, session_id):
                self.logger.info(f"[v4] 新话题检测，重置会话 {session_id[:8]}...")
                self.active_sessions.pop(session_id, None)
                session_id = None

            session_id = session_id or str(uuid.uuid4())

            uc = user_context or {}
            if user_id:
                uc["user_id"] = user_id
            effective_user_id = user_id or uc.get("user_id")

            initial_state = create_initial_state(
                user_query=user_query,
                session_id=session_id,
                user_id=effective_user_id,
                user_context=uc,
            )

            start_time = datetime.now()
            timeout = effective_config.get("timeout_seconds", 120)
            result = await asyncio.wait_for(
                self._execute_graph(initial_state),
                timeout=timeout,
            )

            self.active_sessions[session_id] = {
                "state": result.get("final_state", initial_state),
                "start_time": start_time,
                "last_activity": datetime.now(),
            }
            self._update_stats(session_id, start_time, result.get("success", False))
            return result

        except asyncio.TimeoutError:
            self.logger.error("[v4] 工作流超时")
            return {
                "success": False,
                "error": "处理超时，请缩短输入或稍后重试",
                "session_id": session_id,
            }
        except Exception as e:
            self.logger.error(f"[v4] process_query 失败: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    async def continue_session(
        self,
        session_id: str,
        user_id: str,
        user_response: str,
    ) -> Dict[str, Any]:
        """继续多轮对话"""
        try:
            current_state = (
                self.active_sessions[session_id]["state"]
                if session_id in self.active_sessions
                else await self._load_session_from_storage(session_id, user_id)
            )

            if not current_state:
                self.logger.info(f"[v4] 会话 {session_id[:8]} 不存在，作为新查询处理")
                return await self.process_query(
                    user_query=user_response,
                    session_id=session_id,
                    user_id=user_id,
                )

            # 更新对话状态
            current_state = dict(current_state)
            current_state["user_response"] = user_response
            current_state["user_responses"] = (
                list(current_state.get("user_responses", [])) + [user_response]
            )
            current_state["conversation_round"] = current_state.get("conversation_round", 0) + 1
            current_state["user_context"] = {
                **current_state.get("user_context", {}),
                "user_id": user_id,
            }
            current_state["user_id"] = user_id
            current_state["workflow_complete"] = False
            current_state["waiting_for_user"] = False

            # 更新对话历史：将用户回应填入最后一条未完成记录
            dialogue_history = list(current_state.get("dialogue_history", []))
            if dialogue_history:
                last = dict(dialogue_history[-1])
                if "response" not in last or not last["response"]:
                    last["response"] = user_response
                    last["response_timestamp"] = datetime.now().isoformat()
                    dialogue_history[-1] = last
            current_state["dialogue_history"] = dialogue_history

            start_time = datetime.now()
            timeout = self.workflow_config.get("timeout_seconds", 120)
            result = await asyncio.wait_for(
                self._execute_graph(current_state),
                timeout=timeout,
            )

            if session_id in self.active_sessions:
                self.active_sessions[session_id]["state"] = result.get(
                    "final_state", current_state
                )
                self.active_sessions[session_id]["last_activity"] = datetime.now()

            self._update_stats(session_id, start_time, result.get("success", False))
            return result

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "处理超时，请稍后重试",
                "session_id": session_id,
            }
        except Exception as e:
            self.logger.error(f"[v4] continue_session 失败: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    # ── 内部执行 ─────────────────────────────────────────────────────────

    async def _execute_graph(self, state: LearningWorkflowState) -> Dict[str, Any]:
        """执行 LangGraph 图并格式化输出"""
        try:
            result = await self.graph.ainvoke(state)

            # 提取最终响应：从 messages 中找到教学内容和苏格拉底问题
            messages = result.get("messages", [])
            final_response = ""
            socratic_question = None

            for m in messages:
                if m.get("role") != "assistant":
                    continue
                content = m.get("content", "")
                if content.startswith("💭"):
                    socratic_question = content
                elif content:
                    final_response = content  # 取最后一条有效内容

            # 汇总性能数据
            perf = result.get("performance_data", {})
            total_llm_ms = sum(
                perf.get(k, 0)
                for k in ["planner_ms", "teaching_ms", "evaluation_ms"]
            )

            execution_summary = {
                "tool_outputs": result.get("tool_outputs", {}),
                "curriculum_plan": result.get("curriculum_plan", {}),
                "draft_content": result.get("draft_content", ""),
                "critique": result.get("critique", ""),
                "teaching_output": result.get("teaching_output"),
                "evaluation_output": result.get("evaluation_output"),
                "duration_ms": total_llm_ms,
            }

            return {
                "success": True,
                "session_id": result.get("session_id"),
                "response": final_response,
                "conversation_complete": (
                    result.get("workflow_complete", False)
                    and not result.get("waiting_for_user", False)
                ),
                "waiting_for_user": result.get("waiting_for_user", False),
                "conversation_stage": result.get("conversation_stage", ""),
                "understanding_level": result.get("understanding_level", ""),
                "round": result.get("conversation_round", 0),
                "socratic_question": socratic_question,
                "socratic_questions": result.get("socratic_questions", []),
                "socratic_guidance": result.get("socratic_guidance", {}),
                "messages": messages,
                "analysis": result.get("task_plan") or result.get("interpretation", {}),
                "plan": result.get("task_plan") or result.get("plan", {}),
                "execution_summary": execution_summary,
                "next_suggestions": self._generate_next_suggestions(result),
                "performance_data": perf,
                "final_state": result,
                "current_step": result.get("next_step"),
            }

        except Exception as e:
            self.logger.error(f"[v4] Graph 执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": state.get("session_id"),
                "response": "工作流执行出现错误，请稍后重试。",
                "conversation_complete": True,
                "waiting_for_user": False,
            }

    # ── 辅助方法 ─────────────────────────────────────────────────────────

    def _detect_new_topic(self, user_query: str, session_id: str) -> bool:
        """检测是否是新话题（适配中文字符级相似度判断）"""
        if session_id not in self.active_sessions:
            return True

        # 明确的重置类关键词
        reset_kws = [
            "你好", "您好", "hi", "hello", "开始", "重新",
            "换个话题", "新问题", "换一个",
        ]
        q_lower = user_query.lower()
        if any(kw in q_lower for kw in reset_kws):
            return True

        session_state = self.active_sessions[session_id]["state"]

        # 对话轮次较少时，不急于重置
        if session_state.get("conversation_round", 0) <= 3:
            return False

        # 中文字符级重叠度检测（比 split() 词袋更适合中文）
        prev_query = session_state.get("user_query", "")
        if not prev_query:
            return False

        prev_chars = set(prev_query)
        curr_chars = set(user_query)
        if not prev_chars or not curr_chars:
            return False

        overlap = len(prev_chars & curr_chars) / min(len(prev_chars), len(curr_chars))
        # 字符重叠度低于 15% 认为话题已切换
        return overlap < 0.15

    def _generate_next_suggestions(self, state: Dict[str, Any]) -> List[str]:
        """生成后续学习建议"""
        task_plan = state.get("task_plan") or {}
        intent = task_plan.get("intent", "")
        strategy = task_plan.get("strategy", "")

        if intent in NEXT_SUGGESTIONS_BY_INTENT:
            return NEXT_SUGGESTIONS_BY_INTENT[intent]
        if strategy in NEXT_SUGGESTIONS_BY_STRATEGY:
            return NEXT_SUGGESTIONS_BY_STRATEGY[strategy]
        return NEXT_SUGGESTIONS_DEFAULT

    def _update_stats(self, session_id: str, start_time: datetime, success: bool):
        """更新系统统计"""
        duration = (datetime.now() - start_time).total_seconds()
        self.system_stats["total_sessions"] += 1
        self.system_stats["total_queries_processed"] += 1
        if success:
            self.system_stats["successful_sessions"] += 1

        total = self.system_stats["total_sessions"]
        avg = self.system_stats["average_session_duration"]
        self.system_stats["average_session_duration"] = (
            (avg * (total - 1) + duration) / total
        )

    async def _load_session_from_storage(
        self, session_id: str, user_id: str
    ) -> Optional[LearningWorkflowState]:
        """从存储恢复会话"""
        try:
            storage = self.nodes.memory_system._get_storage()
            if not storage:
                return None

            session_data = storage.load_session_memory(session_id)
            if not session_data:
                return None

            state = create_initial_state(
                user_query=session_data.get("query", ""),
                session_id=session_id,
                user_id=user_id,
                user_context={"user_id": user_id},
            )

            # 恢复苏格拉底对话状态
            socratic = session_data.get("socratic_dialogue", {})
            state["socratic_questions"] = socratic.get("questions", [])
            state["socratic_question"] = socratic.get("current_question", "")
            state["user_responses"] = socratic.get("user_responses", [])

            # 恢复理解跟踪
            tracking = session_data.get("understanding_tracking", {})
            state["understanding_level"] = tracking.get("current_level", "no_understanding")
            state["conversation_stage"] = tracking.get("conversation_stage", "initial_query")
            state["conversation_round"] = tracking.get("conversation_round", 0)
            state["dialogue_history"] = session_data.get("dialogue_history", [])

            # 恢复规划和教学输出
            exec_details = session_data.get("execution_details", {})
            state["task_plan"] = exec_details.get("plan")
            state["teaching_output"] = exec_details.get("teaching_output")

            sync_compat_fields(state)
            self.logger.info(f"[v4] 从存储恢复会话 {session_id[:8]}...")
            return state

        except Exception as e:
            self.logger.error(f"[v4] 恢复会话失败: {e}")
            return None

    # ── 管理接口 ─────────────────────────────────────────────────────────

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        if session_id not in self.active_sessions:
            return {"exists": False, "message": "Session not found"}

        session_info = self.active_sessions[session_id]
        state = session_info["state"]
        task_plan = state.get("task_plan") or {}

        return {
            "exists": True,
            "session_id": session_id,
            "start_time": session_info["start_time"].isoformat(),
            "last_activity": session_info.get(
                "last_activity", session_info["start_time"]
            ).isoformat(),
            "waiting_for_response": state.get("waiting_for_user", False),
            "conversation_round": state.get("conversation_round", 0),
            "understanding_level": state.get("understanding_level", ""),
            "latest_question": state.get("socratic_question", ""),
            "current_strategy": task_plan.get("strategy", ""),
            "current_intent": task_plan.get("intent", ""),
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计（仅读取已实例化的组件，不触发懒加载）"""
        stats = dict(self.system_stats)
        stats["active_sessions_count"] = len(self.active_sessions)
        stats["success_rate"] = (
            self.system_stats["successful_sessions"]
            / max(self.system_stats["total_sessions"], 1)
        )
        stats["architecture_version"] = "v4"

        # 仅读取已实例化的组件统计，避免触发懒加载
        if self.nodes._planner is not None:
            stats["planner_stats"] = self.nodes._planner.get_stats()
        if self.nodes._teacher is not None:
            stats["teacher_stats"] = self.nodes._teacher.get_stats()
        if self.nodes._evaluator is not None:
            stats["evaluator_stats"] = self.nodes._evaluator.get_stats()
        if self.nodes._knowledge_engine is not None:
            stats["knowledge_stats"] = self.nodes._knowledge_engine.get_stats()
        if self.nodes._memory_system is not None:
            stats["memory_stats"] = self.nodes._memory_system.get_stats()

        return stats

    def get_workflow_config(self) -> Dict[str, Any]:
        return {**self.workflow_config, "version": "v4"}

    def update_workflow_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        valid_keys = set(self.workflow_config.keys())
        invalid_keys = set(config_updates.keys()) - valid_keys
        if invalid_keys:
            return {"success": False, "error": f"Invalid keys: {invalid_keys}"}
        self.workflow_config.update(config_updates)
        return {"success": True, "updated_config": dict(self.workflow_config)}

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """清理过期会话"""
        now = datetime.now()
        expired = [
            sid for sid, info in self.active_sessions.items()
            if (now - info["start_time"]).total_seconds() > max_age_hours * 3600
        ]
        for sid in expired:
            del self.active_sessions[sid]
        if expired:
            self.logger.info(f"[v4] 清理 {len(expired)} 个过期会话")

    def shutdown(self):
        self.active_sessions.clear()
        self.logger.info("[v4] Workflow shutdown completed")

    def get_graph_visualization(self) -> str:
        """返回 v4 架构的 Mermaid 图"""
        return """
graph TD
    A[planner] -->|need_retrieval=true| B[knowledge]
    A -->|need_retrieval=false| C[teaching]
    A -->|error| F[error_handler]
    B --> C
    C -->|socratic/direct| E[memory]
    C -->|explain/curriculum/assessment| D[evaluation]
    C -->|error| F
    D -->|is_satisfactory=true| E
    D -->|revision_needed| C
    E --> END
    F --> END

    style A fill:#4CAF50,color:#fff
    style C fill:#2196F3,color:#fff
    style D fill:#FF9800,color:#fff
    style E fill:#9C27B0,color:#fff
    style B fill:#00BCD4,color:#fff
    style F fill:#f44336,color:#fff
"""


# ── 全局单例 ─────────────────────────────────────────────────────────────

_global_workflow: Optional[LangGraphLearningWorkflow] = None


def get_langgraph_learning_workflow(
    config: Optional[Dict[str, Any]] = None,
) -> LangGraphLearningWorkflow:
    """获取全局工作流实例（单例）"""
    global _global_workflow
    if _global_workflow is None:
        _global_workflow = LangGraphLearningWorkflow(config)
    return _global_workflow


def initialize_langgraph_learning_workflow(
    config: Optional[Dict[str, Any]] = None,
) -> LangGraphLearningWorkflow:
    """强制重新初始化全局工作流实例"""
    global _global_workflow
    _global_workflow = LangGraphLearningWorkflow(config)
    return _global_workflow
