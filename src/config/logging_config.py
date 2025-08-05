#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置管理
提供项目级别的日志配置，支持不同环境、不同级别的日志输出
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class LoggingConfig:
    """日志配置类"""
    
    def __init__(self):
        # 项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        
        # 日志目录
        self.log_dir = self.project_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 日志文件配置
        self.log_files = {
            'app': self.log_dir / "hw_agent.log",
            'error': self.log_dir / "error.log",
            'debug': self.log_dir / "debug.log",
            'access': self.log_dir / "access.log"
        }
        
        # 日志级别配置
        self.log_levels = {
            'console': os.getenv('LOG_LEVEL_CONSOLE', 'INFO'),
            'file': os.getenv('LOG_LEVEL_FILE', 'DEBUG'),
            'error': os.getenv('LOG_LEVEL_ERROR', 'ERROR')
        }
        
        # 日志格式配置
        self.formats = {
            'detailed': logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
            ),
            'simple': logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ),
            'json': logging.Formatter(
                '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
            )
        }
        
        # 是否启用JSON格式
        self.use_json_format = os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
        
        # 日志轮转配置
        self.max_bytes = int(os.getenv('LOG_MAX_BYTES', '10MB').replace('MB', '000000'))
        self.backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # 是否启用彩色输出
        self.enable_colors = os.getenv('LOG_ENABLE_COLORS', 'true').lower() == 'true'
    
    def setup_logging(self, logger_name: str = 'hw_agent') -> logging.Logger:
        """设置日志配置"""
        
        # 获取根日志器
        logger = logging.getLogger(logger_name)
        
        # 避免重复配置
        if logger.handlers:
            return logger
        
        # 设置日志级别
        logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        logger.handlers.clear()
        
        # 添加处理器
        self._add_console_handler(logger)
        self._add_file_handlers(logger)
        
        # 设置传播
        logger.propagate = False
        
        return logger
    
    def _add_console_handler(self, logger: logging.Logger):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_levels['console']))
        
        # 选择格式器
        if self.use_json_format:
            formatter = self.formats['json']
        else:
            formatter = self.formats['simple']
        
        # 如果启用彩色输出，使用彩色格式器
        if self.enable_colors and not self.use_json_format:
            formatter = self._get_colored_formatter()
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handlers(self, logger: logging.Logger):
        """添加文件处理器"""
        
        # 主日志文件
        main_handler = logging.handlers.RotatingFileHandler(
            self.log_files['app'],
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        main_handler.setLevel(getattr(logging, self.log_levels['file']))
        main_handler.setFormatter(self.formats['detailed'])
        logger.addHandler(main_handler)
        
        # 错误日志文件
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_files['error'],
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(getattr(logging, self.log_levels['error']))
        error_handler.setFormatter(self.formats['detailed'])
        
        # 只记录错误级别的日志
        error_filter = logging.Filter()
        error_filter.filter = lambda record: record.levelno >= logging.ERROR
        error_handler.addFilter(error_filter)
        
        logger.addHandler(error_handler)
        
        # 调试日志文件（可选）
        if os.getenv('LOG_ENABLE_DEBUG_FILE', 'false').lower() == 'true':
            debug_handler = logging.handlers.RotatingFileHandler(
                self.log_files['debug'],
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(self.formats['detailed'])
            logger.addHandler(debug_handler)
    
    def _get_colored_formatter(self):
        """获取彩色格式器"""
        class ColoredFormatter(logging.Formatter):
            """彩色日志格式器"""
            
            COLORS = {
                'DEBUG': '\033[36m',    # 青色
                'INFO': '\033[32m',     # 绿色
                'WARNING': '\033[33m',  # 黄色
                'ERROR': '\033[31m',    # 红色
                'CRITICAL': '\033[35m', # 紫色
                'RESET': '\033[0m'      # 重置
            }
            
            def format(self, record):
                # 获取原始格式
                log_message = super().format(record)
                
                # 添加颜色
                if record.levelname in self.COLORS:
                    log_message = f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
                
                return log_message
        
        return ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        return logging.getLogger(name)
    
    def set_log_level(self, logger_name: str, level: str):
        """设置指定日志器的级别"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
    
    def add_file_handler(self, logger_name: str, file_path: str, level: str = 'INFO'):
        """为指定日志器添加文件处理器"""
        logger = logging.getLogger(logger_name)
        
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setLevel(getattr(logging, level.upper()))
        handler.setFormatter(self.formats['detailed'])
        
        logger.addHandler(handler)

class LoggerFactory:
    """日志器工厂类"""
    
    _config = LoggingConfig()
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """初始化日志配置"""
        if not cls._initialized:
            cls._config.setup_logging()
            cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取日志器"""
        if not cls._initialized:
            cls.initialize()
        return cls._config.get_logger(name)
    
    @classmethod
    def get_config(cls) -> LoggingConfig:
        """获取日志配置"""
        return cls._config

def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return LoggerFactory.get_logger(name)

def setup_logging(logger_name: str = 'hw_agent') -> logging.Logger:
    """设置日志配置的便捷函数"""
    return LoggerFactory.get_config().setup_logging(logger_name)

class LoggerNames:
    """预定义的日志器名称"""
    APP = 'hw_agent'
    AGENT = 'hw_agent.agent'
    LLM = 'hw_agent.llm'
    DATABASE = 'hw_agent.database'
    API = 'hw_agent.api'
    USER_PROFILE = 'hw_agent.user_profile'
    KNOWLEDGE = 'hw_agent.knowledge'
    CONVERSATION = 'hw_agent.conversation'
    CONFIG = 'hw_agent.config'


def initialize_default_logging():
    """初始化默认日志配置"""
    LoggerFactory.initialize()
    
    # 设置一些常用模块的日志级别
    config = LoggerFactory.get_config()
    
    # 设置第三方库的日志级别
    config.set_log_level('httpx', 'WARNING')
    config.set_log_level('urllib3', 'WARNING')
    config.set_log_level('asyncio', 'WARNING')
    
    # 设置项目模块的日志级别
    config.set_log_level(LoggerNames.LLM, 'INFO')
    config.set_log_level(LoggerNames.DATABASE, 'INFO')
    config.set_log_level(LoggerNames.API, 'INFO')


if __name__ != "__main__":
    initialize_default_logging() 