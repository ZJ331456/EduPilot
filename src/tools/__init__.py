#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
提供各种通用工具函数和类
"""

from .text_processor import (
    extract_keywords,
    calculate_similarity,
    normalize_text,
    split_text_into_chunks
)

from .cache_manager import (
    CacheManager,
    get_cache_manager
)

from .file_utils import (
    load_json_file,
    save_json_file,
    ensure_directory,
    get_file_extension
)

__all__ = [
    # 文本处理
    'extract_keywords',
    'calculate_similarity', 
    'normalize_text',
    'split_text_into_chunks',
    
    # 缓存管理
    'CacheManager',
    'get_cache_manager',
    
    # 文件工具
    'load_json_file',
    'save_json_file',
    'ensure_directory',
    'get_file_extension'
] 