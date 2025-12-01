"""Client implementation for Alibaba Bailian (Qwen) models."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from typing import Any, Dict, List, Optional

from .base import BaseLLMClient, LLMResponse, Message
from .settings import QwenSettings

from importlib import import_module


def _load_openai_clients() -> tuple[Any, Any]:
    try:
        openai_module = import_module("openai")
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("The 'openai' package is required for Qwen client support") from exc

    OpenAI = getattr(openai_module, "OpenAI", None)
    AsyncOpenAI = getattr(openai_module, "AsyncOpenAI", None)

    if OpenAI is None:
        raise RuntimeError("Installed 'openai' package does not expose the OpenAI client class")

    return OpenAI, AsyncOpenAI


class QwenLLMClient(BaseLLMClient):
    """Wrapper speaking the OpenAI compatible Bailian API surface."""

    def __init__(
        self,
        *,
        settings: Optional[QwenSettings] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        embedding_model: Optional[str] = None,
        debug: Optional[bool] = None,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        settings = settings or QwenSettings.from_env()

        if api_key is not None:
            settings = replace(settings, api_key=api_key)
        if base_url is not None:
            settings = replace(settings, base_url=base_url)
        if model is not None:
            settings = replace(settings, model=model)
        if temperature is not None:
            settings = replace(settings, temperature=temperature)
        if top_p is not None:
            settings = replace(settings, top_p=top_p)
        if max_tokens is not None:
            settings = replace(settings, max_tokens=max_tokens)
        if embedding_model is not None:
            settings = replace(settings, embedding_model=embedding_model)
        if debug is not None:
            settings = replace(settings, debug=debug)

        if not settings.api_key:
            raise ValueError("An API key is required to initialise the Qwen client")

        super().__init__(model=settings.model, max_retries=max_retries, timeout=timeout)

        OpenAI, AsyncOpenAI = _load_openai_clients()
        self._async_client_cls = AsyncOpenAI

        self.client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
        self.api_key = settings.api_key
        self.base_url = settings.base_url
        self.temperature = settings.temperature
        self.top_p = settings.top_p
        self.max_tokens = settings.max_tokens
        self.embedding_model = settings.embedding_model
        self.debug = settings.debug
        self._timeout = timeout

        self._async_client = None
        if self._async_client_cls is not None:
            try:
                self._async_client = self._async_client_cls(api_key=settings.api_key, base_url=settings.base_url)
            except Exception as exc:  # pragma: no cover - dependency guard
                self.logger.warning("Failed to initialise AsyncOpenAI client: %s", exc)

        self.logger.info(
            "Qwen client initialised (model=%s, base_url=%s, debug=%s)",
            self.model,
            self.base_url,
            self.debug,
        )

    def chat_completion(self, messages: List[Message], **kwargs: Any) -> LLMResponse:
        openai_messages = [msg.to_dict() for msg in messages]
        params = {
            "model": kwargs.get("model", self.model),
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
        }
        params.update({k: v for k, v in kwargs.items() if k not in {"model", "messages", "max_tokens", "temperature", "top_p"}})

        if self.debug:
            self.logger.debug("Dispatching Qwen chat params: %s", params)

        try:
            response = self.client.chat.completions.create(**params)
        except Exception as exc:
            self.logger.error("Qwen chat request failed: %s", exc)
            return LLMResponse(content="", model=self.model, success=False, error=str(exc))

        content = response.choices[0].message.content if response.choices else ""
        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        metadata = {
            "finish_reason": response.choices[0].finish_reason if response.choices else None,
            "created": getattr(response, "created", None),
        }

        return LLMResponse(content=content, model=params["model"], usage=usage, metadata=metadata)

    async def async_chat_completion(self, messages: List[Message], **kwargs: Any) -> LLMResponse:
        if self._async_client is None:
            return await super().async_chat_completion(messages, **kwargs)

        openai_messages = [msg.to_dict() for msg in messages]
        params = {
            "model": kwargs.get("model", self.model),
            "messages": openai_messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
        }
        params.update({k: v for k, v in kwargs.items() if k not in {"model", "messages", "max_tokens", "temperature", "top_p"}})

        if self.debug:
            self.logger.debug("Dispatching async Qwen chat params: %s", params)

        try:
            response = await self._async_client.chat.completions.create(**params)
        except Exception as exc:
            self.logger.error("Qwen async chat request failed: %s", exc)
            return LLMResponse(content="", model=self.model, success=False, error=str(exc))

        content = response.choices[0].message.content if response.choices else ""
        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        metadata = {
            "finish_reason": response.choices[0].finish_reason if response.choices else None,
            "created": getattr(response, "created", None),
        }

        return LLMResponse(content=content, model=params["model"], usage=usage, metadata=metadata)

    def test_connection(self) -> Dict[str, Any]:
        probe = [Message(role="user", content="你好，请简单介绍一下你自己。")]
        try:
            response = self.chat_completion(probe)
            return {
                "success": response.success,
                "model": self.model,
                "response": response.content if response.success else response.error,
                "usage": response.usage,
                "base_url": self.base_url,
            }
        except Exception as exc:
            return {
                "success": False,
                "model": self.model,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    def generate_embeddings(self, texts: List[str], *, embedding_model: Optional[str] = None) -> Any:  # noqa: ANN401
        model_name = embedding_model or self.embedding_model
        if model_name is None:
            self.logger.error("Qwen embedding model not specified")
            return []

        embeddings_api = getattr(self.client, "embeddings", None)
        if embeddings_api is None:
            self.logger.error("Qwen client does not expose an embeddings API")
            return []

        try:
            response = embeddings_api.create(model=model_name, input=texts)
        except Exception as exc:
            self.logger.error("Qwen embeddings request failed: %s", exc)
            return []

        data = getattr(response, "data", [])
        results: List[Any] = []
        for item in data:
            if isinstance(item, dict):
                embedding = item.get("embedding")
            else:
                embedding = getattr(item, "embedding", None)
            if embedding is not None:
                results.append(embedding)
        return results

    async def async_generate_embeddings(
        self,
        texts: List[str],
        *,
        embedding_model: Optional[str] = None,
    ) -> Any:  # noqa: ANN401
        model_name = embedding_model or self.embedding_model
        if model_name is None:
            self.logger.error("Qwen embedding model not specified")
            return []

        if self._async_client is not None and hasattr(self._async_client, "embeddings"):
            try:
                response = await self._async_client.embeddings.create(model=model_name, input=texts)
            except Exception as exc:
                self.logger.error("Qwen async embeddings request failed: %s", exc)
                return []

            data = getattr(response, "data", [])
            results: List[Any] = []
            for item in data:
                if isinstance(item, dict):
                    embedding = item.get("embedding")
                else:
                    embedding = getattr(item, "embedding", None)
                if embedding is not None:
                    results.append(embedding)
            return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate_embeddings(texts, embedding_model=model_name))
