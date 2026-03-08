#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LearningPlannerAgent（v4）独立测试

验证意图识别、策略选择、检索/评估决策。默认不启用 LLM，纯启发式。
运行：conda activate studyagent && python test/test_planner_agent.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.agents.planner import LearningPlannerAgent
from test.agents.mock_state import make_v4_state, PLANNER_SAMPLES


async def run_one(agent: LearningPlannerAgent, query: str) -> None:
    state = make_v4_state(user_query=query)
    updates = await agent.execute(state)
    task_plan = updates.get("task_plan") or {}
    intent = task_plan.get("intent", "?")
    strategy = task_plan.get("strategy", "?")
    need_retrieval = task_plan.get("need_retrieval", False)
    routing = task_plan.get("routing", "?")
    print(f"  意图: {intent}, 策略: {strategy}, 需检索: {need_retrieval}, 路由: {routing}")


async def main():
    print("=== LearningPlannerAgent (v4) 测试 ===\n")
    agent = LearningPlannerAgent(enable_llm=False)
    for i, query in enumerate(PLANNER_SAMPLES, 1):
        print(f"[{i}] 输入: {query}")
        await run_one(agent, query)
        print()
    print("=== 测试结束 ===")


if __name__ == "__main__":
    asyncio.run(main())
