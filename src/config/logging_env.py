#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志环境变量配置
定义和管理日志相关的环境变量
"""

import os
from typing import Dict, Any

class LoggingEnvConfig:
    """日志环境变量配置类"""
    
    # 日志级别配置
    LOG_LEVEL_CONSOLE = os.getenv('LOG_LEVEL_CONSOLE', 'INFO')
    LOG_LEVEL_FILE = os.getenv('LOG_LEVEL_FILE', 'DEBUG')
    LOG_LEVEL_ERROR = os.getenv('LOG_LEVEL_ERROR', 'ERROR')
    
    # 日志格式配置
    LOG_JSON_FORMAT = os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
    LOG_ENABLE_COLORS = os.getenv('LOG_ENABLE_COLORS', 'true').lower() == 'true'
    
    # 日志文件配置
    LOG_MAX_BYTES = os.getenv('LOG_MAX_BYTES', '10MB')
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    LOG_ENABLE_DEBUG_FILE = os.getenv('LOG_ENABLE_DEBUG_FILE', 'false').lower() == 'true'
    
    # 日志目录配置
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # 特定模块的日志级别
    LOG_LEVEL_AGENT = os.getenv('LOG_LEVEL_AGENT', 'INFO')
    LOG_LEVEL_LLM = os.getenv('LOG_LEVEL_LLM', 'INFO')
    LOG_LEVEL_API = os.getenv('LOG_LEVEL_API', 'INFO')
    LOG_LEVEL_DATABASE = os.getenv('LOG_LEVEL_DATABASE', 'INFO')
    LOG_LEVEL_USER_PROFILE = os.getenv('LOG_LEVEL_USER_PROFILE', 'INFO')
    LOG_LEVEL_KNOWLEDGE = os.getenv('LOG_LEVEL_KNOWLEDGE', 'INFO')
    LOG_LEVEL_CONVERSATION = os.getenv('LOG_LEVEL_CONVERSATION', 'INFO')
    
    # 第三方库日志级别
    LOG_LEVEL_HTTPX = os.getenv('LOG_LEVEL_HTTPX', 'WARNING')
    LOG_LEVEL_URLLIB3 = os.getenv('LOG_LEVEL_URLLIB3', 'WARNING')
    LOG_LEVEL_ASYNCIO = os.getenv('LOG_LEVEL_ASYNCIO', 'WARNING')
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有日志配置"""
        return {
            'console_level': cls.LOG_LEVEL_CONSOLE,
            'file_level': cls.LOG_LEVEL_FILE,
            'error_level': cls.LOG_LEVEL_ERROR,
            'json_format': cls.LOG_JSON_FORMAT,
            'enable_colors': cls.LOG_ENABLE_COLORS,
            'max_bytes': cls.LOG_MAX_BYTES,
            'backup_count': cls.LOG_BACKUP_COUNT,
            'enable_debug_file': cls.LOG_ENABLE_DEBUG_FILE,
            'log_dir': cls.LOG_DIR,
            'module_levels': {
                'agent': cls.LOG_LEVEL_AGENT,
                'llm': cls.LOG_LEVEL_LLM,
                'api': cls.LOG_LEVEL_API,
                'database': cls.LOG_LEVEL_DATABASE,
                'user_profile': cls.LOG_LEVEL_USER_PROFILE,
                'knowledge': cls.LOG_LEVEL_KNOWLEDGE,
                'conversation': cls.LOG_LEVEL_CONVERSATION,
            },
            'third_party_levels': {
                'httpx': cls.LOG_LEVEL_HTTPX,
                'urllib3': cls.LOG_LEVEL_URLLIB3,
                'asyncio': cls.LOG_LEVEL_ASYNCIO,
            }
        }
    
    @classmethod
    def print_config(cls):
        """打印当前日志配置"""
        config = cls.get_all_config()
        print("=== 日志配置 ===")
        for key, value in config.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")

# 环境变量示例
ENV_EXAMPLE = """
# 日志配置环境变量示例
# 复制以下内容到 .env 文件中

# 日志级别配置
LOG_LEVEL_CONSOLE=INFO
LOG_LEVEL_FILE=DEBUG
LOG_LEVEL_ERROR=ERROR

# 日志格式配置
LOG_JSON_FORMAT=false
LOG_ENABLE_COLORS=true

# 日志文件配置
LOG_MAX_BYTES=10MB
LOG_BACKUP_COUNT=5
LOG_ENABLE_DEBUG_FILE=false

# 日志目录
LOG_DIR=logs

# 模块日志级别
LOG_LEVEL_AGENT=INFO
LOG_LEVEL_LLM=INFO
LOG_LEVEL_API=INFO
LOG_LEVEL_DATABASE=INFO
LOG_LEVEL_USER_PROFILE=INFO
LOG_LEVEL_KNOWLEDGE=INFO
LOG_LEVEL_CONVERSATION=INFO

# 第三方库日志级别
LOG_LEVEL_HTTPX=WARNING
LOG_LEVEL_URLLIB3=WARNING
LOG_LEVEL_ASYNCIO=WARNING
"""

if __name__ == "__main__":
    LoggingEnvConfig.print_config()
    print("\n" + ENV_EXAMPLE) 