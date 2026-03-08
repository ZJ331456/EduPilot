#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 测试用模拟状态与数据

v4 使用 LearningWorkflowState（dict），不再使用 AgentState。
运行测试时请在项目根目录执行，并激活对应 conda 环境。
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.workflow.state import create_initial_state


def make_v4_state(
    user_query: str = "",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None,
    **overrides,
) -> Dict[str, Any]:
    """构造 v4 LearningWorkflowState（dict），供 Planner/Teacher/Evaluator 测试复用。"""
    state = create_initial_state(
        user_query=user_query or "什么是机器学习？",
        session_id=session_id,
        user_id=user_id,
        user_context=user_context or {},
    )
    for k, v in overrides.items():
        if k in state:
            state[k] = v
    return state


# ---------- Planner 测试样本 ----------
PLANNER_SAMPLES = [
    "什么是大化改新？",
    "帮我制定一个学习计划",
    "为什么日本要推行大化改新？",
    "你好",
    "算一下 3.14 * 100",
]

# ---------- Teacher 测试数据 ----------
TEACHER_KNOWLEDGE_CONTEXT = {
    "retrieved_chunks": [
        {"content": "大化改新（645年）以中大兄皇子与中臣镰足为中心，颁布改新之诏，确立公地公民制。", "source": "知识库"},
        {"content": "改革借鉴唐朝律令制度，建立二官八省等中央官制。", "source": "知识库"},
    ],
    "tool_results": {},
    "sources": ["知识库"],
}

# ---------- Evaluator 测试数据 ----------
EVALUATOR_DRAFT_CONTENT = """
# 大化改新简介
大化改新是日本飞鸟时代的重大改革。改革仿效中国唐朝制度，确立了律令制国家基础。
"""

QUIZ_DRAFT_CONTENT = """
大化改新是日本历史上一次重要的政治改革，发生在公元645年。
主要内容包括：废除贵族私有土地和部民制，实行公地公民制；建立中央集权体制。
"""

# ---------- KnowledgeEngine 测试数据 ----------
KNOWLEDGE_ENGINE_QUERY = "大化改新的主要内容"

# ---------- MemorySystem 测试数据 ----------
MEMORY_USER_QUERY = "我想了解大化改新"
MEMORY_DIALOGUE_HISTORY = [
    {"question": "大化改新是什么", "response": "是一次古代日本的改革", "round": 1},
]

__all__ = [
    "make_v4_state",
    "PLANNER_SAMPLES",
    "TEACHER_KNOWLEDGE_CONTEXT",
    "EVALUATOR_DRAFT_CONTENT",
    "QUIZ_DRAFT_CONTENT",
    "KNOWLEDGE_ENGINE_QUERY",
    "MEMORY_USER_QUERY",
    "MEMORY_DIALOGUE_HISTORY",
]
