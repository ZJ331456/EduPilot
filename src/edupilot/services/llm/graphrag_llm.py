"""为 nano_graphrag 构造 best_model_func 与 embedding_func（签名与缓存兼容）。"""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np
from openai import AsyncOpenAI, APIConnectionError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from edupilot.config.settings import Settings
from nano_graphrag._utils import compute_args_hash, wrap_embedding_func_with_attrs
from nano_graphrag.base import BaseKVStorage


def build_graphrag_functions(settings: Settings, client: AsyncOpenAI):
    """返回 (best_model_func, embedding_func) 供 GraphRAG(...) 使用。"""

    chat_model = settings.chat_model
    embed_model = settings.embedding_model
    embed_dim = settings.embedding_dim

    # 与 nano_graphrag._llm.gpt_4o_complete 一致：首参为 prompt（见 _op.extract_entities 中 use_llm_func(hint_prompt)）
    @retry(
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=2, min=5, max=90),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
    )
    async def openai_compatible_complete_if_cache(
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> str:
        hashing_kv: Optional[BaseKVStorage] = kwargs.pop("hashing_kv", None)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history_messages:
            messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})

        use_model = chat_model
        if hashing_kv is not None:
            args_hash = compute_args_hash(use_model, messages)
            cached = await hashing_kv.get_by_id(args_hash)
            if cached is not None:
                return cached["return"]

        resp = await client.chat.completions.create(
            model=use_model,
            messages=messages,
            **kwargs,
        )
        text = resp.choices[0].message.content or ""

        if hashing_kv is not None:
            await hashing_kv.upsert(
                {args_hash: {"return": text, "model": use_model}}
            )
            await hashing_kv.index_done_callback()
        return text

    # wrap_embedding_func_with_attrs 是装饰器，只接受 keyword（与 _llm.openai_embedding 一致）
    @wrap_embedding_func_with_attrs(embedding_dim=embed_dim, max_token_size=8192)
    @retry(
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
    )
    async def embedding_func_inner(texts: list[str]) -> np.ndarray:
        r = await client.embeddings.create(
            model=embed_model,
            input=texts,
            encoding_format="float",
        )
        return np.array([d.embedding for d in r.data], dtype=np.float32)

    return openai_compatible_complete_if_cache, embedding_func_inner
