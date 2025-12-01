#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储适配器模块
提供不同存储后端的实现
"""

from .file_storage import FileStorageAdapter
from .sqlite_adapter import SQLiteAdapter

from typing import Literal


def get_storage_adapter(
    adapter_type: Literal["file", "sqlite"] = "file",
    **config
):
    """获取存储适配器
    
    Args:
        adapter_type: 适配器类型
        **config: 配置参数
        
    Returns:
        StorageAdapter: 存储适配器实例
    """
    if adapter_type == "file":
        return FileStorageAdapter(**config)
    elif adapter_type == "sqlite":
        return SQLiteAdapter(**config)
    else:
        raise ValueError(f"不支持的存储适配器类型: {adapter_type}")


__all__ = [
    "FileStorageAdapter",
    "SQLiteAdapter",
    "get_storage_adapter",
]

