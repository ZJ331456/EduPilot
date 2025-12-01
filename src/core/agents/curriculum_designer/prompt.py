#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CurriculumDesigner Prompt - 课程设计师提示词
负责生成课程设计的 Prompt。
"""

from src.infrastructure.utils import AgentState


def build_curriculum_prompt(state: AgentState) -> str:
    """构建课程设计的 Prompt"""
    query = state.user_query
    
    return f"""
你是一个专业的课程设计师。用户想要系统地学习以下主题：

主题: "{query}"

请为该主题设计一个结构化的学习路径（思维导图）。

要求：
1. 结构清晰，包含根节点、一级子节点（主要模块）、二级子节点（具体知识点）。
2. 每个节点应包含 `name` (名称) 和 `description` (简短描述)。
3. 请输出标准的 JSON 格式。

JSON 结构示例：
{{
  "topic": "Python 基础",
  "modules": [
    {{
      "name": "环境搭建",
      "description": "安装 Python 和编辑器",
      "topics": [
        {{ "name": "Python 安装", "description": "Windows/Mac/Linux 安装指南" }},
        {{ "name": "VS Code 配置", "description": "推荐插件和设置" }}
      ]
    }},
    ...
  ]
}}

请生成 JSON：
"""

