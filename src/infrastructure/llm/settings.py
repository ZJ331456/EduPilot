"""Configuration helpers for LLM providers.

The settings objects are lightweight dataclasses that can be created
programmatically or populated from process environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_float(value: Optional[str], default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_int(value: Optional[str], default: Optional[int]) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(slots=True)
class OllamaSettings:
    """Settings used by the :class:`~llm.ollama_client.OllamaLLMClient`."""

    model: str = "qwen2.5:latest"
    embedding_model: str = "bge-m3:latest"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: Optional[int] = None
    enabled: bool = True
    debug: bool = False

    @classmethod
    def from_env(cls, prefix: str = "OLLAMA_") -> "OllamaSettings":
        # Create a default instance to get the actual default values
        default_instance = cls()
        return cls(
            model=_get_env(f"{prefix}MODEL", default_instance.model),
            embedding_model=_get_env(f"{prefix}EMBEDDING_MODEL", default_instance.embedding_model),
            base_url=_get_env(f"{prefix}BASE_URL", default_instance.base_url),
            temperature=_parse_float(_get_env(f"{prefix}TEMPERATURE"), default_instance.temperature),
            top_p=_parse_float(_get_env(f"{prefix}TOP_P"), default_instance.top_p),
            max_tokens=_parse_int(_get_env(f"{prefix}MAX_TOKENS"), default_instance.max_tokens),
            enabled=_parse_bool(_get_env(f"{prefix}ENABLED"), default_instance.enabled),
            debug=_parse_bool(_get_env(f"{prefix}DEBUG"), default_instance.debug),
        )


@dataclass(slots=True)
class QwenSettings:
    """Settings used by the :class:`~llm.qwen_client.QwenLLMClient`."""

    api_key: Optional[str] = None
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: Optional[int] = 2000
    embedding_model: Optional[str] = "text-embedding-v1"
    enabled: bool = True
    debug: bool = False

    @classmethod
    def from_env(cls, prefix: str = "QWEN_") -> "QwenSettings":
        api_key = _get_env(f"{prefix}API_KEY") or _get_env("DASHSCOPE_API_KEY")
        # Create a default instance to get the actual default values
        default_instance = cls()
        return cls(
            api_key=api_key,
            base_url=_get_env(f"{prefix}BASE_URL", default_instance.base_url),
            model=_get_env(f"{prefix}MODEL", default_instance.model),
            temperature=_parse_float(_get_env(f"{prefix}TEMPERATURE"), default_instance.temperature),
            top_p=_parse_float(_get_env(f"{prefix}TOP_P"), default_instance.top_p),
            max_tokens=_parse_int(_get_env(f"{prefix}MAX_TOKENS"), default_instance.max_tokens),
            embedding_model=_get_env(f"{prefix}EMBEDDING_MODEL", default_instance.embedding_model),
            enabled=_parse_bool(_get_env(f"{prefix}ENABLED"), default_instance.enabled),
            debug=_parse_bool(_get_env(f"{prefix}DEBUG"), default_instance.debug),
        )
