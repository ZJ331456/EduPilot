#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — Workflow 提示词与模板

存储结论节点、错误处理节点及「下一步建议」的展示文案。
"""

# ---------------------------------------------------------------------------
# 结论节点（conclusion_node）
# ---------------------------------------------------------------------------

SUMMARY_LABEL = "学习总结："
NEXT_SUGGESTION_LABEL = "下一步建议："

# 根据质量分数展示的进步反馈
QUALITY_HIGH_PHRASE = "回答质量很好，掌握得不错！"
QUALITY_MEDIUM_PHRASE = "理解在加深，继续保持！"

# ---------------------------------------------------------------------------
# 错误处理节点（error_handler_node）
# ---------------------------------------------------------------------------

ERROR_MESSAGE_TEMPLATE = "抱歉，处理过程中出现了问题：{error_msg}。请稍后重试或换一种方式提问。"
ERROR_MESSAGE_FALLBACK = "系统出现严重错误，请重新开始对话。"

# ---------------------------------------------------------------------------
# 下一步建议（_generate_next_suggestions，按 intent 优先匹配，strategy 次之）
# ---------------------------------------------------------------------------

NEXT_SUGGESTIONS_BY_INTENT: dict = {
    "concept_explanation": [
        "可以询问相关的应用示例",
        "可以要求更深入的原理解析",
        "可以比较相关概念的异同",
    ],
    "socratic_dialogue": [
        "继续探讨这个问题的深层逻辑",
        "从不同角度重新思考",
        "尝试用自己的话总结理解",
    ],
    "knowledge_retrieval": [
        "可以进一步追问细节",
        "可以要求代码示例实践",
        "可以了解相关知识点",
    ],
    "learning_guidance": [
        "从第一个阶段开始学习",
        "深入探讨某个具体知识点",
        "要求推荐具体的学习资源",
    ],
    "practice": [
        "检验答案并请求解析",
        "尝试下一组练习题",
        "针对薄弱点深入学习",
    ],
    "direct_answer": [
        "可以继续深入探讨",
        "可以换个角度提问",
        "可以请求更多示例",
    ],
    "smalltalk": [
        "告诉我你想学什么",
        "可以直接提问任何知识点",
        "可以让我帮你规划学习路径",
    ],
    "meta_question": [
        "可以直接提问任何问题",
        "告诉我你目前在学习什么",
        "可以让我帮你制定学习计划",
    ],
}

NEXT_SUGGESTIONS_BY_STRATEGY: dict = {
    "explain": [
        "可以深入追问某个细节",
        "可以要求更多代码示例",
        "可以了解实际应用场景",
    ],
    "socratic": [
        "继续探讨，尝试自主推导",
        "从反例角度思考验证",
        "尝试用自己的话解释原理",
    ],
    "curriculum": [
        "从第一个阶段开始学习",
        "了解某个具体知识点",
        "要求推荐学习资源",
    ],
    "direct": [
        "可以继续深入探讨",
        "可以换个角度提问",
        "可以请求更多示例",
    ],
}

NEXT_SUGGESTIONS_DEFAULT = [
    "可以继续深入探讨",
    "可以换个角度提问",
    "可以请求更多示例",
]

__all__ = [
    "SUMMARY_LABEL",
    "NEXT_SUGGESTION_LABEL",
    "QUALITY_HIGH_PHRASE",
    "QUALITY_MEDIUM_PHRASE",
    "ERROR_MESSAGE_TEMPLATE",
    "ERROR_MESSAGE_FALLBACK",
    "NEXT_SUGGESTIONS_BY_INTENT",
    "NEXT_SUGGESTIONS_BY_STRATEGY",
    "NEXT_SUGGESTIONS_DEFAULT",
]
