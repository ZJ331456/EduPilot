#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer Prompt - 质量审核员提示词
负责生成内容审核的 Prompt。
"""


def build_review_prompt(draft: str, user_level: str) -> str:
    """构建审核 Prompt"""
    return f"""
作为 EduPilot 的质量审核员，请检查这篇教学草稿。

用户水平: {user_level}

草稿内容:
---
{draft}
---

请严格按照以下标准检查：
1. 准确性：是否存在明显的事实错误或幻觉？
2. 教学性：解释是否清晰？是否适合当前用户水平 ({user_level})？
3. 结构：是否分点清晰，逻辑顺畅？

输出格式要求：
- 如果内容合格，请只输出 "APPROVE"。
- 如果内容不合格，请输出 "REJECT"，然后换行给出具体的修改意见（Critique）。意见应具体、可执行。

请开始审核：
"""

