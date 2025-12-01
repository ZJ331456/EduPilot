#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraftWriter Prompt - 内容撰稿人提示词
负责生成内容撰写的 Prompt。
"""

from src.infrastructure.utils import AgentState


def build_first_draft_prompt(state: AgentState, knowledge: str, tool_outputs: str, user_level: str) -> str:
    """构建初稿撰写的 Prompt"""
    query = state.user_query
    
    return f"""
你是一个专业的教育内容创作者。请根据以下信息为用户撰写一篇教学内容的草稿。

用户查询: {query}
用户水平: {user_level}

参考资料 (RAG):
{knowledge}

工具运行结果:
{tool_outputs}

要求：
1. 结构清晰，分点阐述。
2. 语言通俗易懂，适合用户水平。
3. 准确引用参考资料，不要编造。
4. 如果有代码或数学计算，请清晰展示。

请撰写草稿：
"""


def build_revision_prompt(state: AgentState, original_draft: str, critique: str) -> str:
    """构建修改草稿的 Prompt"""
    query = state.user_query
    
    return f"""
你是一个专业的教育内容创作者。之前的草稿未能通过审核，请根据审核意见进行修改。

用户查询: {query}

原草稿:
---
{original_draft}
---

审核意见 (Critique):
{critique}

请重写草稿，确保解决了上述所有问题。保持结构清晰，准确性高。
"""

