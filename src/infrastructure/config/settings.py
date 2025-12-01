#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置管理
使用 Pydantic Settings 进行配置管理和验证
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # 兼容旧版本 pydantic
    from pydantic import BaseSettings

from pydantic import Field, validator


# ============================================================================
# 子配置类
# ============================================================================

class LLMConfig(BaseSettings):
    """LLM 配置"""
    
    # Ollama 配置
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama 服务地址"
    )
    ollama_model: str = Field(
        default="qwen2.5:latest",
        description="Ollama 默认模型"
    )
    ollama_embedding_model: str = Field(
        default="bge-m3:latest",
        description="Ollama 嵌入模型"
    )
    ollama_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    ollama_enabled: bool = Field(default=True)
    
    # Qwen 配置
    qwen_api_key: Optional[str] = Field(
        default=None,
        description="通义千问 API Key"
    )
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    qwen_model: str = Field(default="qwen-plus")
    qwen_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    qwen_max_tokens: int = Field(default=2000, ge=1)
    qwen_enabled: bool = Field(default=True)
    
    # 通用配置
    default_provider: str = Field(
        default="ollama",
        description="默认 LLM 提供商"
    )
    timeout: int = Field(default=60, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    
    class Config:
        env_prefix = "LLM_"
        case_sensitive = False


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    
    # 数据库类型: sqlite, postgresql, mysql
    db_type: str = Field(default="sqlite", description="数据库类型")
    
    # SQLite 配置
    sqlite_path: str = Field(
        default="data/edupilot.db",
        description="SQLite 数据库文件路径"
    )
    
    # PostgreSQL 配置
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="edupilot")
    postgres_password: str = Field(default="")
    postgres_database: str = Field(default="edupilot")
    
    # 连接池配置
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    pool_timeout: int = Field(default=30, ge=1)
    
    # 其他配置
    echo_sql: bool = Field(default=False, description="是否打印 SQL")
    auto_migrate: bool = Field(default=True, description="是否自动迁移")
    
    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        elif self.db_type == "postgresql":
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )
        else:
            return f"sqlite:///{self.sqlite_path}"
    
    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class KnowledgeBaseConfig(BaseSettings):
    """知识库配置"""
    
    root_dir: str = Field(
        default="concept_knowledge_bases",
        description="知识库根目录"
    )
    default_kb: str = Field(default="default", description="默认知识库")
    
    # GraphRAG 配置
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_db: str = Field(default="hnswlib", description="向量数据库类型")
    graph_db: str = Field(default="networkx", description="图数据库类型")
    
    # 检索配置
    max_concurrent_queries: int = Field(default=4, ge=1)
    top_k: int = Field(default=5, ge=1, description="返回前 K 个结果")
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="相似度阈值"
    )
    
    # 缓存配置
    cache_enabled: bool = Field(default=True)
    cache_dir: str = Field(default="data/retrieval_cache")
    cache_ttl_hours: int = Field(default=24, ge=1)
    max_cache_size: int = Field(default=1000, ge=1)
    
    class Config:
        env_prefix = "KB_"
        case_sensitive = False


class CacheConfig(BaseSettings):
    """缓存配置"""
    
    enabled: bool = Field(default=True)
    backend: str = Field(default="memory", description="缓存后端: memory, redis")
    
    # Redis 配置
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = None
    redis_db: int = Field(default=0, ge=0, le=15)
    
    # 缓存策略
    default_ttl: int = Field(default=3600, description="默认过期时间（秒）")
    max_size: int = Field(default=1000, description="内存缓存最大条目数")
    
    class Config:
        env_prefix = "CACHE_"
        case_sensitive = False


class APIConfig(BaseSettings):
    """API 配置"""
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    
    # CORS 配置
    cors_enabled: bool = Field(default=True)
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="允许的跨域来源"
    )
    
    # 限流配置
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    
    # 认证配置
    auth_enabled: bool = Field(default=False)
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60, ge=1)
    
    # API 文档
    docs_enabled: bool = Field(default=True)
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """日志配置"""
    
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 文件日志
    file_enabled: bool = Field(default=True)
    log_dir: str = Field(default="logs")
    log_file: str = Field(default="edupilot.log")
    max_bytes: int = Field(default=10485760, description="单个日志文件最大大小")
    backup_count: int = Field(default=5, description="保留的日志文件数量")
    
    # 控制台日志
    console_enabled: bool = Field(default=True)
    
    # JSON 日志
    json_logs: bool = Field(default=False, description="是否输出 JSON 格式日志")
    
    @validator("level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是: {valid_levels}")
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


# ============================================================================
# 主配置类
# ============================================================================

class AppConfig(BaseSettings):
    """应用主配置"""
    
    # 应用基本信息
    app_name: str = Field(default="EduPilot", description="应用名称")
    version: str = Field(default="3.0.0", description="应用版本")
    description: str = Field(
        default="AI-Powered Socratic Learning System",
        description="应用描述"
    )
    
    # 环境配置
    environment: str = Field(
        default="development",
        description="运行环境: development, testing, production"
    )
    debug: bool = Field(default=True, description="调试模式")
    
    # 项目路径
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent,
        description="项目根目录"
    )
    data_dir: str = Field(default="data", description="数据目录")
    
    # 工作流配置
    max_conversation_rounds: int = Field(default=10, ge=1)
    enable_socratic: bool = Field(default=True)
    enable_learning: bool = Field(default=True)
    workflow_timeout: int = Field(default=300, description="工作流超时时间（秒）")
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "testing", "production"]
        if v not in valid_envs:
            raise ValueError(f"环境必须是: {valid_envs}")
        return v
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


# ============================================================================
# 统一设置类
# ============================================================================

class Settings(BaseSettings):
    """统一配置管理器"""
    
    # 主配置
    app: AppConfig = Field(default_factory=AppConfig)
    
    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs_to_create = [
            self.app.data_dir,
            self.knowledge_base.cache_dir,
            self.logging.log_dir,
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "app": self.app.dict(),
            "llm": self.llm.dict(),
            "database": self.database.dict(),
            "knowledge_base": self.knowledge_base.dict(),
            "api": self.api.dict(),
            "logging": self.logging.dict(),
            "cache": self.cache.dict(),
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# ============================================================================
# 全局配置实例
# ============================================================================

_settings: Optional[Settings] = None


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置实例（单例模式）
    
    Returns:
        Settings: 配置实例
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """重新加载配置"""
    global _settings
    _settings = None
    get_settings.cache_clear()
    return get_settings()

