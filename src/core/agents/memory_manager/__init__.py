#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理器智能体模块

负责用户画像管理、会话记忆和学习记录的持久化存储。
"""

from .agent import MemoryManagerAgent
from .storage import StorageConfig

__all__ = [
    "MemoryManagerAgent",
    "StorageConfig",  # 保留供测试使用
]

