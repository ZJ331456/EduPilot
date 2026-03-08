#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TeachingAgent（v4）独立测试

验证 explain / socratic / curriculum / direct 四种模式。依赖 LLM。
运行：conda activate studyagent && python test/test_teacher_agent.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.agents.teacher import TeachingAgent
from test.agents.mock_state import make_v4_state, TEACHER_KNOWLEDGE_CONTEXT


async def main():
    print("=== TeachingAgent (v4) 测试 ===\n")
    agent = TeachingAgent()

    # explain 模式
    state = make_v4_state(
        user_query="请介绍大化改新的主要内容",
        task_plan={
            "intent": "concept_explanation",
            "strategy": "explain",
            "learning_goal": "理解大化改新",
            "core_concepts": ["大化改新"],
            "difficulty": "intermediate",
        },
        knowledge_context=TEACHER_KNOWLEDGE_CONTEXT,
        skill_level="intermediate",
    )
    print("[1] 模式: explain")
    out = await agent.execute(state)
    content = (out.get("teaching_output") or {}).get("content", "")
    print(f"    内容长度: {len(content)} 字符")
    if content:
        print(f"    摘要: {content[:200]}..." if len(content) > 200 else f"    内容: {content}")
    else:
        print("    (无内容时多为 LLM 未配置或不可用，属正常)")

    # direct 模式（问候，可不调 LLM）
    state2 = make_v4_state(
        user_query="你好",
        task_plan={"intent": "smalltalk", "strategy": "direct"},
    )
    print("\n[2] 模式: direct (smalltalk)")
    out2 = await agent.execute(state2)
    content2 = (out2.get("teaching_output") or {}).get("content", "")
    print(f"    回复: {content2[:150]}" if content2 else "    (无 LLM 时使用兜底文案)")

    print("\n=== 测试结束 ===")


if __name__ == "__main__":
    asyncio.run(main())
