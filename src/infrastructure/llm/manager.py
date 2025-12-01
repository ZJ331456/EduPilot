"""Manager responsible for orchestrating multiple LLM providers."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import BaseLLMClient, LLMClientError, Message
from .ollama_client import OllamaLLMClient
from .qwen_client import QwenLLMClient
from .settings import OllamaSettings, QwenSettings


class LLMManager:
    """Registry of named LLM clients with optional default selection."""

    def __init__(self, *, auto_register: bool = True) -> None:
        self._clients: Dict[str, BaseLLMClient] = {}
        self._default_client: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)

        if auto_register:
            self._auto_register_from_env()

    # ------------------------------------------------------------------
    # Registration & lookup
    # ------------------------------------------------------------------
    def add_client(self, name: str, client: BaseLLMClient, *, set_as_default: bool = False) -> None:
        self._clients[name] = client
        if set_as_default or self._default_client is None:
            self._default_client = name
        self.logger.info("Registered LLM client '%s' (model=%s)", name, client.model)

    def remove_client(self, name: str) -> None:
        self._clients.pop(name, None)
        if self._default_client == name:
            self._default_client = next(iter(self._clients), None)

    def get_client(self, name: Optional[str] = None) -> Optional[BaseLLMClient]:
        if name is None:
            name = self._default_client
        return self._clients.get(name) if name is not None else None

    def require_client(self, name: Optional[str] = None) -> BaseLLMClient:
        client = self.get_client(name)
        if client is None:
            available = ", ".join(self.list_clients()) or "<none>"
            raise LLMClientError(f"LLM client '{name}' not found. Available: {available}")
        return client

    def list_clients(self) -> List[str]:
        return list(self._clients.keys())

    def set_default_client(self, name: str) -> None:
        if name not in self._clients:
            raise LLMClientError(f"Cannot set unknown client '{name}' as default")
        self._default_client = name

    # ------------------------------------------------------------------
    # High level interaction helpers
    # ------------------------------------------------------------------
    def generate_response(
        self,
        user_input: str,
        *,
        client_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        context: Optional[List[Message]] = None,
        **kwargs: Any,
    ) -> str:
        client = self.require_client(client_name)
        return client.generate_response(user_input, system_prompt=system_prompt, context=context, **kwargs)

    async def async_generate_response(
        self,
        user_input: str,
        *,
        client_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        context: Optional[List[Message]] = None,
        **kwargs: Any,
    ) -> str:
        client = self.require_client(client_name)
        return await client.async_generate_response(user_input, system_prompt=system_prompt, context=context, **kwargs)

    def generate_embeddings(
        self,
        texts: List[str],
        *,
        client_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> Any:  # noqa: ANN401
        client = self.require_client(client_name)
        if hasattr(client, "generate_embeddings"):
            return client.generate_embeddings(texts, embedding_model=embedding_model)  # type: ignore[arg-type]
        raise LLMClientError(f"Client '{client_name or self._default_client}' does not support embeddings")

    async def async_generate_embeddings(
        self,
        texts: List[str],
        *,
        client_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> Any:  # noqa: ANN401
        client = self.require_client(client_name)
        if hasattr(client, "async_generate_embeddings"):
            return await client.async_generate_embeddings(texts, embedding_model=embedding_model)  # type: ignore[arg-type]
        if hasattr(client, "generate_embeddings"):
            return client.generate_embeddings(texts, embedding_model=embedding_model)  # type: ignore[arg-type]
        raise LLMClientError(f"Client '{client_name or self._default_client}' does not support embeddings")

    def chat_completion(self, messages: List[Message], *, client_name: Optional[str] = None, **kwargs: Any):
        client = self.require_client(client_name)
        return client.chat_completion(messages, **kwargs)

    async def async_chat_completion(self, messages: List[Message], *, client_name: Optional[str] = None, **kwargs: Any):
        client = self.require_client(client_name)
        return await client.async_chat_completion(messages, **kwargs)

    def test_all_clients(self) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for name, client in self._clients.items():
            try:
                results[name] = client.test_connection()
            except Exception as exc:  # pragma: no cover - diagnostic path
                results[name] = {"success": False, "error": str(exc)}
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _auto_register_from_env(self) -> None:
        # Ollama
        ollama_settings = OllamaSettings.from_env()
        if ollama_settings.enabled:
            try:
                self.add_client("ollama", OllamaLLMClient(settings=ollama_settings), set_as_default=True)
            except Exception as exc:
                self.logger.warning("Failed to register Ollama client: %s", exc)

        # Qwen
        qwen_settings = QwenSettings.from_env()
        if qwen_settings.enabled and qwen_settings.api_key:
            try:
                self.add_client("qwen", QwenLLMClient(settings=qwen_settings), set_as_default=self._default_client is None)
            except Exception as exc:
                self.logger.warning("Failed to register Qwen client: %s", exc)
        elif qwen_settings.enabled:
            self.logger.debug("Qwen client enabled but API key missing; skipping auto registration")

    # Convenience wrappers for GraphRAG style integrations -----------------
    def get_llm_function(
        self,
        *,
        client_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        force_chinese: bool = True,
    ) -> Callable[[str], Any]:  # noqa: ANN401
        client = self.require_client(client_name)

        async def llm_func(prompt: str, **kwargs: Any) -> str:
            if force_chinese:
                prompt_to_send = f"请使用中文回答以下内容：\n{prompt}"
            else:
                prompt_to_send = prompt
            return await client.async_generate_response(prompt_to_send, system_prompt=system_prompt, **kwargs)

        return llm_func

    def get_embedding_function(
        self,
        *,
        client_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> Callable[[List[str]], Any]:  # noqa: ANN401
        client = self.require_client(client_name)

        async def embedding_func(texts: List[str]) -> Any:  # noqa: ANN401
            return await self.async_generate_embeddings(texts, client_name=client_name, embedding_model=embedding_model)

        return embedding_func


# ----------------------------------------------------------------------
# Module level helpers
# ----------------------------------------------------------------------

_global_manager: Optional[LLMManager] = None


def get_llm_manager(*, auto_register: bool = True) -> LLMManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = LLMManager(auto_register=auto_register)
    return _global_manager


def reset_llm_manager() -> None:
    global _global_manager
    _global_manager = None


def create_unified_processor_functions(
    *,
    llm_client_name: Optional[str] = None,
    embedding_client_name: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> Tuple[Callable[[str], Any], Callable[[List[str]], Any]]:  # noqa: ANN401
    manager = get_llm_manager()
    llm_func = manager.get_llm_function(client_name=llm_client_name)
    embedding_func = manager.get_embedding_function(client_name=embedding_client_name, embedding_model=embedding_model)
    return llm_func, embedding_func
