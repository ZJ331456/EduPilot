"""Implementation of an Ollama backed LLM client.

The client prefers the official ``ollama`` python package when available
and falls back to the HTTP API described in the Ollama documentation:
https://www.llamafactory.cn/ollama-docs/api.html
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from typing import Any, Dict, List, Optional

from .base import BaseLLMClient, LLMResponse, Message
from .settings import OllamaSettings

try:  # pragma: no cover - optional dependency
    import ollama  # type: ignore

    _OLLAMA_AVAILABLE = True
except Exception:  # pragma: no cover - import failure branch
    ollama = None  # type: ignore
    _OLLAMA_AVAILABLE = False


class _HTTPAdapter:
    """Very small wrapper around the Ollama REST API."""

    def __init__(self, base_url: str, timeout: int, logger: logging.Logger) -> None:
        import importlib

        try:
            self._requests = importlib.import_module("requests")
        except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("The 'requests' package is required for HTTP fallback") from exc
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._logger = logger

    def chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}/api/chat"
        response = self._requests.post(url, json=payload, timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    async def async_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.chat(payload))

    def embeddings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}/api/embeddings"
        response = self._requests.post(url, json=payload, timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    async def async_embeddings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.embeddings(payload))

    def list_models(self) -> Dict[str, Any]:
        url = f"{self._base_url}/api/tags"
        response = self._requests.get(url, timeout=self._timeout)
        response.raise_for_status()
        return response.json()


class OllamaLLMClient(BaseLLMClient):
    """Concrete implementation that communicates with an Ollama instance."""

    def __init__(
        self,
        *,
        settings: Optional[OllamaSettings] = None,
        model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        debug: Optional[bool] = None,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        settings = settings or OllamaSettings.from_env()

        if model is not None:
            settings = replace(settings, model=model)
        if embedding_model is not None:
            settings = replace(settings, embedding_model=embedding_model)
        if base_url is not None:
            settings = replace(settings, base_url=base_url)
        if temperature is not None:
            settings = replace(settings, temperature=temperature)
        if top_p is not None:
            settings = replace(settings, top_p=top_p)
        if max_tokens is not None:
            settings = replace(settings, max_tokens=max_tokens)
        if debug is not None:
            settings = replace(settings, debug=debug)

        super().__init__(
            model=settings.model,
            max_retries=max_retries,
            timeout=timeout,
        )

        self._settings = settings
        self.base_url = settings.base_url.rstrip("/")
        self.temperature = settings.temperature
        self.top_p = settings.top_p
        self.max_tokens = settings.max_tokens
        self.embedding_model = settings.embedding_model
        self.debug = settings.debug

        self._sync_client: Optional[Any] = None
        self._async_client: Optional[Any] = None

        if _OLLAMA_AVAILABLE:
            try:
                test_client = ollama.Client(host=self.base_url)
                # Test the connection by making a simple list request
                test_client.list()
                self._sync_client = test_client
                self._async_client = ollama.AsyncClient(host=self.base_url)
                self.logger.info("Ollama python client initialised (model=%s, base_url=%s)", self.model, self.base_url)
            except Exception as exc:  # pragma: no cover - rarely triggered
                self.logger.warning("Failed to initialise Ollama python client: %s. Falling back to HTTP adapter.", exc)
                self._sync_client = None
        else:
            self.logger.debug("ollama package not available; using HTTP fallback if possible")

        if self._sync_client is None:
            try:
                self._sync_client = _HTTPAdapter(self.base_url, timeout, self.logger)
                self.logger.info("Using HTTP fallback for Ollama (model=%s, base_url=%s)", self.model, self.base_url)
            except Exception as exc:
                self.logger.error("Unable to configure Ollama HTTP fallback: %s", exc)

    # ------------------------------------------------------------------
    # Core LLM operations
    # ------------------------------------------------------------------
    def chat_completion(self, messages: List[Message], **kwargs: Any) -> LLMResponse:
        if self._sync_client is None:
            return LLMResponse(content="", model=self.model, success=False, error="Ollama client not available")

        options: Dict[str, Any] = {
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
        }

        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [msg.to_dict() for msg in messages],
            "options": options,
            "stream": False,
        }

        if self.debug:
            self.logger.debug("Dispatching Ollama chat payload: %s", payload)

        try:
            if _OLLAMA_AVAILABLE and isinstance(self._sync_client, ollama.Client):
                response = self._sync_client.chat(**payload)
            elif isinstance(self._sync_client, _HTTPAdapter):
                response = self._sync_client.chat(payload)
            else:  # pragma: no cover - defensive branch
                response = self._sync_client.chat(**payload)
        except Exception as exc:
            self.logger.error("Ollama chat request failed: %s", exc)
            return LLMResponse(content="", model=self.model, success=False, error=str(exc))

        message = response.get("message", {})
        content = message.get("content", "")
        usage = {
            "prompt_tokens": response.get("prompt_eval_count", 0),
            "completion_tokens": response.get("eval_count", 0),
        }
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

        metadata = {
            "eval_duration": response.get("eval_duration", 0),
            "load_duration": response.get("load_duration", 0),
        }

        return LLMResponse(content=content, model=kwargs.get("model", self.model), usage=usage, metadata=metadata)

    async def async_chat_completion(self, messages: List[Message], **kwargs: Any) -> LLMResponse:
        if self._async_client is not None and _OLLAMA_AVAILABLE and isinstance(self._async_client, ollama.AsyncClient):
            options: Dict[str, Any] = {
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
            }
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            if max_tokens is not None:
                options["num_predict"] = max_tokens

            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [msg.to_dict() for msg in messages],
                "options": options,
                "stream": False,
            }

            try:
                response = await self._async_client.chat(**payload)
            except Exception as exc:
                self.logger.error("Ollama async chat failed: %s", exc)
                return LLMResponse(content="", model=self.model, success=False, error=str(exc))

            message = response.get("message", {})
            content = message.get("content", "")
            usage = {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            metadata = {
                "eval_duration": response.get("eval_duration", 0),
                "load_duration": response.get("load_duration", 0),
            }
            return LLMResponse(content=content, model=payload["model"], usage=usage, metadata=metadata)

        if isinstance(self._sync_client, _HTTPAdapter):
            options: Dict[str, Any] = {
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
            }
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            if max_tokens is not None:
                options["num_predict"] = max_tokens

            payload = {
                "model": kwargs.get("model", self.model),
                "messages": [msg.to_dict() for msg in messages],
                "options": options,
                "stream": False,
            }
            try:
                response = await self._sync_client.async_chat(payload)
            except Exception as exc:
                self.logger.error("Ollama HTTP async chat failed: %s", exc)
                return LLMResponse(content="", model=self.model, success=False, error=str(exc))

            message = response.get("message", {})
            content = message.get("content", "")
            usage = {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            metadata = {
                "eval_duration": response.get("eval_duration", 0),
                "load_duration": response.get("load_duration", 0),
            }
            return LLMResponse(content=content, model=payload["model"], usage=usage, metadata=metadata)

        return await super().async_chat_completion(messages, **kwargs)

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    def generate_embeddings(self, texts: List[str], *, embedding_model: Optional[str] = None) -> Any:  # noqa: ANN401
        if self._sync_client is None:
            self.logger.error("Ollama client not available for embeddings")
            return []

        model = embedding_model or self.embedding_model or "bge-m3:latest"
        embeddings: List[Any] = []

        for text in texts:
            try:
                if _OLLAMA_AVAILABLE and isinstance(self._sync_client, ollama.Client):
                    response = self._sync_client.embeddings(model=model, prompt=text)
                elif isinstance(self._sync_client, _HTTPAdapter):
                    payload = {"model": model, "prompt": text}
                    response = self._sync_client.embeddings(payload)
                else:  # pragma: no cover - defensive branch
                    response = self._sync_client.embeddings(model=model, prompt=text)
            except Exception as exc:
                self.logger.error("Failed to generate embedding via Ollama: %s", exc)
                continue

            embeddings.append(response.get("embedding", []))

        return embeddings

    async def async_generate_embeddings(
        self,
        texts: List[str],
        *,
        embedding_model: Optional[str] = None,
    ) -> Any:  # noqa: ANN401
        if self._async_client is not None and _OLLAMA_AVAILABLE and isinstance(self._async_client, ollama.AsyncClient):
            model = embedding_model or self.embedding_model or "bge-m3:latest"
            embeddings: List[Any] = []
            for text in texts:
                try:
                    response = await self._async_client.embeddings(model=model, prompt=text)
                except Exception as exc:
                    self.logger.error("Failed to generate async embedding via Ollama: %s", exc)
                    continue
                embeddings.append(response.get("embedding", []))
            return embeddings

        if isinstance(self._sync_client, _HTTPAdapter):
            model = embedding_model or self.embedding_model or "bge-m3:latest"
            payloads = [{"model": model, "prompt": text} for text in texts]
            results: List[Any] = []
            for payload in payloads:
                try:
                    response = await self._sync_client.async_embeddings(payload)
                except Exception as exc:
                    self.logger.error("Failed to generate async embedding via HTTP fallback: %s", exc)
                    continue
                results.append(response.get("embedding", []))
            return results

        self.logger.error("Ollama client does not support async embeddings in current configuration")
        return []

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def list_models(self) -> List[str]:
        if self._sync_client is None:
            return []

        try:
            if _OLLAMA_AVAILABLE and isinstance(self._sync_client, ollama.Client):
                data = self._sync_client.list()
            elif isinstance(self._sync_client, _HTTPAdapter):
                data = self._sync_client.list_models()
            else:  # pragma: no cover - defensive branch
                data = self._sync_client.list()
        except Exception as exc:
            self.logger.error("Failed to list Ollama models: %s", exc)
            return []

        models: List[str] = []
        items = data.get("models") if isinstance(data, dict) else getattr(data, "models", [])
        if isinstance(items, list):
            for entry in items:
                if isinstance(entry, dict):
                    name = entry.get("name") or entry.get("model") or entry.get("id")
                    if name:
                        models.append(name)
                elif hasattr(entry, "model"):
                    models.append(getattr(entry, "model"))
                elif isinstance(entry, str):
                    models.append(entry)
        return models

    def test_connection(self) -> Dict[str, Any]:
        if self._sync_client is None:
            return {
                "success": False,
                "model": self.model,
                "error": "Ollama client not available",
            }

        try:
            models = self.list_models()
            test_response = self.chat_completion([Message(role="user", content="你好，请简单介绍一下你自己。")])
            return {
                "success": test_response.success,
                "model": self.model,
                "available_models": models,
                "response": test_response.content if test_response.success else test_response.error,
                "usage": test_response.usage,
            }
        except Exception as exc:
            return {
                "success": False,
                "model": self.model,
                "error": str(exc),
            }
