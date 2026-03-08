#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemorySystemService（v4）独立测试

验证记忆写入、画像加载、学习分析。依赖本地 data/memory_data 目录。
运行：conda activate studyagent && python test/test_memory_system.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.services.memory_system import MemorySystemService
from test.agents.mock_state import make_v4_state, MEMORY_USER_QUERY, MEMORY_DIALOGUE_HISTORY


async def main():
    print("=== MemorySystemService (v4) 测试 ===\n")
    service = MemorySystemService()

    # 加载画像（无则返回 None）
    profile = await service.load_student_profile("test_user_001")
    print(f"[1] load_student_profile('test_user_001'): {'有' if profile else '无'}")

    # 执行记忆更新（会异步写入）
    state = make_v4_state(
        user_query=MEMORY_USER_QUERY,
        user_id="test_user_001",
        session_id="test-session-001",
        task_plan={"intent": "concept_explanation", "strategy": "explain", "core_concepts": ["大化改新"]},
        teaching_output={"content": "大化改新是日本古代重要改革。", "mode": "explain"},
        evaluation_output={"quality_score": 0.75, "is_satisfactory": True},
        dialogue_history=MEMORY_DIALOGUE_HISTORY,
        conversation_round=1,
    )
    print("\n[2] execute() 记忆更新")
    out = await service.execute(state)
    print(f"    memory_updated: {out.get('memory_updated')}")
    analysis = out.get("memory_analysis") or {}
    print(f"    engagement_level: {analysis.get('engagement_level')}")
    print(f"    summary: {(analysis.get('summary') or '')[:60]}...")

    print("\n=== 测试结束 ===")


if __name__ == "__main__":
    asyncio.run(main())
