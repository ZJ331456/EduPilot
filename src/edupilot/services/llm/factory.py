"""全局 LLM 客户端单例（按配置一种在线或本地兼容端点）。"""

from __future__ import annotations

from functools import lru_cache

from edupilot.config.settings import get_settings
from edupilot.services.llm.client import UnifiedOpenAIClient


@lru_cache
def get_llm_client() -> UnifiedOpenAIClient:
    return UnifiedOpenAIClient(get_settings())
