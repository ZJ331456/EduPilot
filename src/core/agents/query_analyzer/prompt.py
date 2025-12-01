#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QueryAnalyzer Prompt - 查询分析器提示词
负责生成查询分析的 Prompt。
"""


def build_intent_recognition_system_prompt() -> str:
    """构建意图识别的系统提示"""
    return (
        "你是一个多智能体系统的路由器，负责根据用户输入识别意图并返回 JSON。"
        "请严格输出 JSON，不要包含额外文本。"
    )

def build_question_validation_prompt(question: str, user_query: str, question_type: str, understanding_level: str) -> str:
    """构建问题验证的 Prompt"""
    return f"""请阅读以下教师提出的问题，判断该问题是否遵循苏格拉底式提问风格。

**问题内容**: {question}

**评估要点**：
1. 问题是否通过引导帮助学生思考，而不是直接要求学生回答或解释
2. 问题是否避免了"请解释"、"请说明"、"有什么"等直接要求的表达
3. 问题是否使用了引导性的表达，如"让我们想想"、"如果...会怎样"、"是什么让你..."
4. 问题是否只包含问题本身，没有给出答案或提示

**背景信息**（仅供参考）：
- 用户查询: {user_query}
- 问题类型: {question_type}
- 理解水平: {understanding_level}"""


def build_question_validation_system_prompt() -> str:
    """构建问题验证的系统提示"""
    return """你是一个评估者，负责判断给定任务的正确性。你的输出必须严格遵循以下规则：

1. 如果任务被判定为正确，只输出：
   [True]

2. 如果任务被判定为不正确，输出：
   [False]
   [suggestion: <不正确判定的原因>]
   
   将 `<不正确判定的原因>` 替换为清晰简洁的解释，说明为什么任务不正确。

不要包含任何额外的文本、评论或解释，超出指定格式之外的内容。"""


