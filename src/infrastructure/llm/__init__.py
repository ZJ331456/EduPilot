"""Unified LLM integrations for the EduPilot infrastructure layer."""

from .base import BaseLLMClient, LLMClientError, LLMResponse, Message, MessageRole
from .manager import (
    LLMManager,
    create_unified_processor_functions,
    get_llm_manager,
    reset_llm_manager,
)
from .ollama_client import OllamaLLMClient
from .qwen_client import QwenLLMClient
from .settings import OllamaSettings, QwenSettings

__all__ = [
    "BaseLLMClient",
    "LLMClientError",
    "LLMResponse",
    "Message",
    "MessageRole",
    "LLMManager",
    "create_unified_processor_functions",
    "get_llm_manager",
    "reset_llm_manager",
    "OllamaLLMClient",
    "QwenLLMClient",
    "OllamaSettings",
    "QwenSettings",
]
