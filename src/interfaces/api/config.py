#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 层配置集中管理
用于统一控制缓存、限流、超时等后端运行参数，便于按环境调整。
"""

import os
from functools import lru_cache
from typing import List


class APISettings:
    """API 运行时配置"""

    def __init__(
        self,
        *,
        cache_ttl_seconds: int = 30,
        cache_max_entries: int = 256,
        cache_enabled: bool = True,
        rate_limit_per_minute: int = 120,
        cors_origins: List[str] | None = None,
        workflow_timeout_seconds: int = 240,
        session_ttl_hours: int = 12,
        slow_request_ms: int = 1500,
    ):
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_max_entries = cache_max_entries
        self.cache_enabled = cache_enabled
        self.rate_limit_per_minute = rate_limit_per_minute
        self.cors_origins = cors_origins or ["*"]
        self.workflow_timeout_seconds = workflow_timeout_seconds
        self.session_ttl_hours = session_ttl_hours
        self.slow_request_ms = slow_request_ms


def _parse_bool(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "y", "on"}


@lru_cache()
def get_settings() -> APISettings:
    """读取环境变量并生成只读配置实例"""
    cache_ttl = int(os.getenv("API_CACHE_TTL", "30"))
    cache_size = int(os.getenv("API_CACHE_MAX_ENTRIES", "256"))
    cache_enabled = _parse_bool(os.getenv("API_CACHE_ENABLED"), True)
    rate_limit = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "120"))
    timeout_seconds = int(os.getenv("API_WORKFLOW_TIMEOUT", "240"))
    session_ttl_hours = int(os.getenv("API_SESSION_TTL_HOURS", "12"))
    slow_request_ms = int(os.getenv("API_SLOW_REQUEST_MS", "1500"))

    cors_env = os.getenv("CORS_ORIGINS", "*")
    cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] or ["*"]

    return APISettings(
        cache_ttl_seconds=cache_ttl,
        cache_max_entries=cache_size,
        cache_enabled=cache_enabled,
        rate_limit_per_minute=rate_limit,
        cors_origins=cors_origins,
        workflow_timeout_seconds=timeout_seconds,
        session_ttl_hours=session_ttl_hours,
        slow_request_ms=slow_request_ms,
    )

