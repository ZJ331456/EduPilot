#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuizMaster Prompt - 测评与出题官提示词
负责生成测试题的 Prompt。
"""

from src.infrastructure.utils import AgentState


def build_quiz_prompt(state: AgentState, content: str) -> str:
    """构建出题的 Prompt"""
    return f"""
你是一个专业的出题官。请根据以下教学内容，生成 3 道单项选择题，用于检测用户的掌握程度。

教学内容:
---
{content}
---

要求：
1. 题目难度适中，针对核心知识点。
2. 选项要有干扰性，但只有一个正确答案。
3. 请输出标准的 JSON 格式。

JSON 结构示例：
{{
  "questions": [
    {{
      "id": 1,
      "question": "Python 中用于输出的函数是？",
      "options": ["input()", "print()", "write()", "output()"],
      "correct_index": 1,
      "explanation": "print() 是 Python 的标准输出函数。"
    }}
  ]
}}

请生成 JSON：
"""

