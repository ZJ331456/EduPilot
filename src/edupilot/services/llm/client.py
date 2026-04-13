"""统一 OpenAI 兼容客户端：对话与向量嵌入，支持流式响应。"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional

import numpy as np
from openai import AsyncOpenAI
from openai._models import FinalRequestOptions

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

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        **extra: Any,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话接口。

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            文本片段字符串
        """
        m = model or self._settings.chat_model
        stream = await self._client.chat.completions.create(
            model=m,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **extra,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        **extra: Any,
    ) -> str:
        """
        带工具调用的对话接口。

        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            模型响应文本
        """
        m = model or self._settings.chat_model
        resp = await self._client.chat.completions.create(
            model=m,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
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
