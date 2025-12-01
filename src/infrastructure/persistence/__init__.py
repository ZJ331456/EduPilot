#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化层模块
提供数据持久化的统一接口和实现
"""

from .base import (
    BaseRepository,
    BaseEntity,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError
)

from .repositories import (
    UserProfileRepository,
    SessionRepository,
    LearningRecordRepository
)

from .adapters import (
    FileStorageAdapter,
    SQLiteAdapter,
    get_storage_adapter
)

__all__ = [
    # 基础接口
    "BaseRepository",
    "BaseEntity",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    
    # 仓储实现
    "UserProfileRepository",
    "SessionRepository",
    "LearningRecordRepository",
    
    # 适配器
    "FileStorageAdapter",
    "SQLiteAdapter",
    "get_storage_adapter",
]

