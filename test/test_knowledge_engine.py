#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KnowledgeEngineService（v4）独立测试

验证知识检索流程（无 LLM）。无知识库时检索结果为空属正常。
运行：conda activate studyagent && python test/test_knowledge_engine.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.services.knowledge_engine import KnowledgeEngineService
from test.agents.mock_state import make_v4_state, KNOWLEDGE_ENGINE_QUERY


async def main():
    print("=== KnowledgeEngineService (v4) 测试 ===\n")
    service = KnowledgeEngineService()

    state = make_v4_state(
        user_query=KNOWLEDGE_ENGINE_QUERY,
        task_plan={
            "need_retrieval": True,
            "core_concepts": ["大化改新"],
            "strategy": "explain",
        },
    )
    print(f"输入: {KNOWLEDGE_ENGINE_QUERY}")
    out = await service.execute(state)
    kc = out.get("knowledge_context") or {}
    chunks = kc.get("retrieved_chunks", [])
    print(f"检索到 chunk 数: {len(chunks)}")
    if chunks:
        for i, c in enumerate(chunks[:3], 1):
            print(f"  [{i}] {c.get('content', '')[:80]}...")
    else:
        print("  (无知识库或未命中时为空，属正常)")
    print(f"next_step: {out.get('next_step')}")
    print("\n=== 测试结束 ===")


if __name__ == "__main__":
    asyncio.run(main())
