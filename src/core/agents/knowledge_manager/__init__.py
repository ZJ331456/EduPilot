#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识管理智能体模块

基于nano-graphrag实现的知识库管理和检索功能：
- 自动索引处理pipeline：检测并处理新的知识库文件
- 知识检索：从已索引的知识库中检索信息
- 知识库管理：管理知识库的完整生命周期
"""

from .knowledge_manager import KnowledgeManagerAgent

__all__ = [
    "KnowledgeManagerAgent",
]
