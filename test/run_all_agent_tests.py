#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — 一键运行所有 Agent/Service 测试（非 pytest）

请在项目根目录下执行，并先激活 conda 环境：
  conda activate studyagent
  python test/run_all_agent_tests.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 加载 .env，使 QWEN_API_KEY 等被 os.environ 读取，LLMManager 才能优先使用百炼
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# v4: 3 Agents + 2 Services
TESTS = [
    ("LearningPlanner", "test.test_planner_agent"),
    ("TeachingAgent", "test.test_teacher_agent"),
    ("EvaluationAgent", "test.test_evaluator_agent"),
    ("KnowledgeEngine", "test.test_knowledge_engine"),
    ("MemorySystem", "test.test_memory_system"),
]


def run_test(name: str, module_path: str) -> bool:
    try:
        import importlib
        mod = importlib.import_module(module_path)
        main = getattr(mod, "main", None)
        if main and asyncio.iscoroutinefunction(main):
            asyncio.run(main())
        else:
            print(f"  [skip] 无 async main(): {module_path}")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main_sync():
    print("EduPilot v4 测试 — 请在项目根目录执行并激活 conda 环境\n")
    success = 0
    for name, module_path in TESTS:
        print("\n" + "=" * 60)
        print(f" 运行: {name} ({module_path})")
        print("=" * 60)
        if run_test(name, module_path):
            success += 1
    print(f"\n完成: {success}/{len(TESTS)} 个测试已执行")


if __name__ == "__main__":
    main_sync()
