#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — MemorySystem 提示词与模板

本服务以规则分析 + 持久化为主，无 LLM 生成类 prompt。
此处存放学习反馈、摘要、推荐语等模板文案，便于统一调整语气与风格。
"""

# ---------------------------------------------------------------------------
# 学习摘要模板（_build_summary 使用）
# ---------------------------------------------------------------------------

SUMMARY_TEMPLATE_SINGLE = "探讨了关于「{concepts}」的问题。"
SUMMARY_TEMPLATE_MULTI = "通过 {rounds} 轮对话，深入学习了「{concepts}」相关内容，初始问题：{query_preview}。"

# ---------------------------------------------------------------------------
# 结论/推荐短语（结论节点与记忆分析使用）
# ---------------------------------------------------------------------------

QUALITY_PHRASES = {
    "high": "学习效果很好！",
    "medium": "继续努力，你的理解在加深。",
}

NEXT_SUGGESTION_LABEL = "💡 下一步建议："
SUMMARY_LABEL = "📚 学习总结："

# ---------------------------------------------------------------------------
# 推荐语模板（memory_analysis.recommendations）
# ---------------------------------------------------------------------------

RECOMMENDATION_TEMPLATES = {
    "socratic_continue": "继续深入探讨 {concepts}",
    "beginner_path": "建议从基础概念开始，逐步深入",
    "low_quality": "建议换一个角度重新提问",
}

__all__ = [
    "SUMMARY_TEMPLATE_SINGLE",
    "SUMMARY_TEMPLATE_MULTI",
    "QUALITY_PHRASES",
    "NEXT_SUGGESTION_LABEL",
    "SUMMARY_LABEL",
    "RECOMMENDATION_TEMPLATES",
]
