"""统一 OpenAI 兼容客户端：对话与向量嵌入。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from openai import AsyncOpenAI

from edupilot.config.settings import Settings


class UnifiedOpenAIClient:
    """封装 AsyncOpenAI，供业务 Agent 与 GraphRAG 注入使用。"""

    def __init__(self, settings: Settings) -> None:
        key = settings.resolved_api_key()
        if not key:
            raise ValueError("未配置 LLM_API_KEY 或 DASHSCOPE_API_KEY，请在 .env 中设置。")
        self._client = AsyncOpenAI(
            api_key=key,
            base_url=settings.resolved_base_url(),
            timeout=settings.request_timeout_sec,
        )
        self._settings = settings

    @property
    def async_client(self) -> AsyncOpenAI:
        return self._client

    @property
    def settings(self) -> Settings:
        return self._settings

    async def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        **extra: Any,
    ) -> str:
        m = model or self._settings.chat_model
        resp = await self._client.chat.completions.create(
            model=m,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra,
        )
        return (resp.choices[0].message.content or "").strip()

    async def embed(self, texts: List[str], *, model: Optional[str] = None) -> np.ndarray:
        em = model or self._settings.embedding_model
        r = await self._client.embeddings.create(
            model=em,
            input=texts,
            encoding_format="float",
        )
        return np.array([d.embedding for d in r.data], dtype=np.float32)
