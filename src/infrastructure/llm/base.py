"""Shared abstractions for LLM integrations.

This module defines the common data contracts used by the Ollama and
Alibaba Bailian (Qwen) clients as well as the abstract base class that
providers must implement.
"""

from __future__ import annotations

import abc
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class MessageRole(str, Enum):
    """Conversation role indicator compatible with OpenAI/Ollama."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(slots=True)
class Message:
    """Represents a single conversational turn."""

    role: MessageRole | str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:  # noqa: D401 - dataclass hook
        if isinstance(self.role, str):
            try:
                self.role = MessageRole(self.role)
            except ValueError as exc:  # pragma: no cover - defensive branch
                raise ValueError(f"Unsupported role: {self.role}") from exc

    def to_dict(self) -> Dict[str, Any]:
        """Serialise into provider friendly dictionary format."""

        payload: Dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.metadata:
            payload.update(self.metadata)
        return payload


@dataclass(slots=True)
class LLMResponse:
    """Unified response envelope returned by providers."""

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error,
        }


class SupportsEmbeddings(Protocol):
    """Protocol describing embedding capable clients."""

    def generate_embeddings(self, texts: List[str], *, embedding_model: Optional[str] = None) -> Any:  # noqa: ANN401
        ...

    async def async_generate_embeddings(
        self,
        texts: List[str],
        *,
        embedding_model: Optional[str] = None,
    ) -> Any:  # noqa: ANN401
        ...


class LLMClientError(RuntimeError):
    """Raised when a client level failure occurs."""


class BaseLLMClient(abc.ABC):
    """Abstract base class for concrete LLM providers."""

    def __init__(self, model: str, *, max_retries: int = 3, timeout: int = 30, logger: Optional[logging.Logger] = None) -> None:
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def chat_completion(self, messages: List[Message], **kwargs: Any) -> LLMResponse:
        """Execute a chat completion request."""

    async def async_chat_completion(self, messages: List[Message], **kwargs: Any) -> LLMResponse:
        """Asynchronous chat completion.

        Providers that do not have native async support fall back to the
        synchronous implementation executed in a default thread pool.
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.chat_completion(messages, **kwargs))

    @abc.abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Return provider specific connectivity diagnostics."""

    def generate_response(
        self,
        user_input: str,
        *,
        system_prompt: Optional[str] = None,
        context: Optional[List[Message]] = None,
        **kwargs: Any,
    ) -> str:
        """High level helper that prepares and dispatches a conversation."""

        conversation: List[Message] = []

        if system_prompt:
            conversation.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        if context:
            conversation.extend(context)

        conversation.append(Message(role=MessageRole.USER, content=user_input))

        response = self.chat_completion(conversation, **kwargs)
        if response.success:
            return response.content

        error = response.error or "Unknown error"
        self.logger.error("LLM generation failed: %s", error)
        raise LLMClientError(error)

    async def async_generate_response(
        self,
        user_input: str,
        *,
        system_prompt: Optional[str] = None,
        context: Optional[List[Message]] = None,
        **kwargs: Any,
    ) -> str:
        """Async equivalent of :meth:`generate_response`."""

        conversation: List[Message] = []
        if system_prompt:
            conversation.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
        if context:
            conversation.extend(context)
        conversation.append(Message(role=MessageRole.USER, content=user_input))

        response = await self.async_chat_completion(conversation, **kwargs)
        if response.success:
            return response.content

        error = response.error or "Unknown error"
        self.logger.error("Async LLM generation failed: %s", error)
        raise LLMClientError(error)
