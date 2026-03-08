#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EvaluationAgent（v4）独立测试

验证质量评估、安全过滤、测验生成（需 LLM）。可先测无 LLM 的通过/拒绝逻辑。
运行：conda activate studyagent && python test/test_evaluator_agent.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.agents.evaluator import EvaluationAgent
from test.agents.mock_state import make_v4_state, EVALUATOR_DRAFT_CONTENT, QUIZ_DRAFT_CONTENT


async def main():
    print("=== EvaluationAgent (v4) 测试 ===\n")
    agent = EvaluationAgent()

    # 有草稿、正常内容 → 走 LLM 评估（若 LLM 不可用则兜底通过）
    state = make_v4_state(
        user_query="请介绍大化改新",
        task_plan={"need_assessment": False, "difficulty": "intermediate"},
        teaching_output={"content": EVALUATOR_DRAFT_CONTENT, "mode": "explain"},
        draft_content=EVALUATOR_DRAFT_CONTENT,
    )
    print("[1] 输入: 正常草稿")
    out = await agent.execute(state)
    satisfactory = out.get("is_satisfactory", False)
    score = (out.get("evaluation_output") or {}).get("quality_score", 0)
    print(f"    通过: {satisfactory}, 质量分: {score}")

    # 内容为空 → 直接通过
    state2 = make_v4_state(
        teaching_output={"content": "", "mode": "explain"},
        draft_content="",
    )
    print("\n[2] 输入: 空内容")
    out2 = await agent.execute(state2)
    print(f"    通过: {out2.get('is_satisfactory')}")

    # 达到最大修改次数 → 强制通过
    state3 = make_v4_state(
        revision_count=2,
        teaching_output={"content": EVALUATOR_DRAFT_CONTENT, "mode": "explain"},
        draft_content=EVALUATOR_DRAFT_CONTENT,
    )
    print("\n[3] 输入: revision_count=2（强制通过）")
    out3 = await agent.execute(state3)
    print(f"    通过: {out3.get('is_satisfactory')}")

    print("\n=== 测试结束 ===")


if __name__ == "__main__":
    asyncio.run(main())
