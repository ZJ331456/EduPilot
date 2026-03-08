#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — LangGraph 路由函数

v4 精简路由（v3 原有 6 个路由函数，v4 保留 3 个核心路由）：

planner → knowledge | teaching    (route_after_planning)
teaching → evaluation | memory    (route_after_teaching)
evaluation → teaching | memory    (route_after_evaluation)
"""

import logging
from typing import Literal

from .state import LearningWorkflowState

logger = logging.getLogger(__name__)


def route_after_planning(
    state: LearningWorkflowState,
) -> Literal["knowledge", "teaching", "error_handler"]:
    """规划后路由：需要检索 → knowledge，否则 → teaching"""
    if state.get("error_info") and state.get("next_step") == "error_handler":
        return "error_handler"

    task_plan = state.get("task_plan") or {}
    need_retrieval = task_plan.get("need_retrieval", False)
    routing = task_plan.get("routing", "teaching")

    # 双重确认：task_plan.routing 和 need_retrieval 标志
    if need_retrieval or routing == "knowledge":
        logger.debug("[Route:Planning] → knowledge")
        return "knowledge"

    logger.debug("[Route:Planning] → teaching")
    return "teaching"


def route_after_teaching(
    state: LearningWorkflowState,
) -> Literal["evaluation", "memory", "error_handler"]:
    """教学后路由：需要评估 → evaluation，苏格拉底/direct → memory"""
    if state.get("next_step") == "error_handler":
        return "error_handler"

    next_step = state.get("next_step", "memory")

    if next_step == "evaluation":
        logger.debug("[Route:Teaching] → evaluation")
        return "evaluation"

    logger.debug("[Route:Teaching] → memory")
    return "memory"


def route_after_evaluation(
    state: LearningWorkflowState,
) -> Literal["teaching", "memory"]:
    """评估后路由：不满意且可修改 → teaching（重写），否则 → memory"""
    next_step = state.get("next_step", "memory")

    if next_step == "teaching":
        logger.debug("[Route:Evaluation] → teaching (revision)")
        return "teaching"

    logger.debug("[Route:Evaluation] → memory")
    return "memory"


# ── 向后兼容（v3 API 层可能引用）────────────────────────────────────────

def route_after_query_analysis(state: LearningWorkflowState) -> str:
    """v3 兼容别名 → 直接路由到规划"""
    return "planner" if not state.get("error_info") else "error_handler"


def route_after_planning_v3(state: LearningWorkflowState) -> str:
    """v3 兼容别名"""
    return route_after_planning(state)


def route_after_reviewer(state: LearningWorkflowState) -> str:
    """v3 兼容别名 → 评估路由"""
    return route_after_evaluation(state)


def route_error_handler(state: LearningWorkflowState) -> str:
    return "error_handler"


def route_conclusion(state: LearningWorkflowState) -> str:
    return "conclusion"


def route_wait_for_user(state: LearningWorkflowState) -> str:
    return "conclusion"


def route_after_quiz_master(state: LearningWorkflowState) -> str:
    return "conclusion"


__all__ = [
    "route_after_planning",
    "route_after_teaching",
    "route_after_evaluation",
    "route_after_query_analysis",
    "route_error_handler",
    "route_conclusion",
    "route_wait_for_user",
    "route_after_reviewer",
    "route_after_quiz_master",
]
