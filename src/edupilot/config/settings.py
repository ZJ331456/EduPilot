"""应用配置：从环境变量读取，密钥绝不写入代码库。"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from edupilot.paths import project_root


class LLMProviderKind(str, Enum):
    """LLM 接入形态：与 OpenAI 兼容的 HTTP 端点统一用 AsyncOpenAI 客户端。"""

    siliconflow = "siliconflow"
    bailian = "bailian"
    local_vllm = "local_vllm"
    local_ollama = "local_ollama"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    llm_provider: LLMProviderKind = Field(default=LLMProviderKind.siliconflow, alias="LLM_PROVIDER")
    api_key: str = Field(default="", alias="LLM_API_KEY")
    base_url: str = Field(default="https://api.siliconflow.cn/v1", alias="LLM_BASE_URL")
    chat_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", alias="LLM_MODEL")
    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")
    request_timeout_sec: float = Field(default=120.0, alias="LLM_TIMEOUT")

    # --- GraphRAG 建索引：并发过高易触发 SiliconFlow 等平台的 TPM/RPM（见官方 Rate limits 说明）---
    graphrag_llm_max_async: int = Field(
        default=2,
        alias="GRAPHRAG_LLM_MAX_ASYNC",
        description="nano_graphrag 同时进行的 chat 请求数上限，免费档建议 1～2",
    )
    graphrag_embedding_max_async: int = Field(
        default=2,
        alias="GRAPHRAG_EMBEDDING_MAX_ASYNC",
        description="嵌入请求并发上限",
    )
    graphrag_embedding_batch_num: int = Field(
        default=8,
        alias="GRAPHRAG_EMBEDDING_BATCH_NUM",
        description="单次嵌入批大小，过大易瞬时占满 TPM",
    )

    # --- 兼容：百炼单独 key（可与 LLM_API_KEY 相同，由用户在 .env 填写）---
    dashscope_api_key: Optional[str] = Field(default=None, alias="DASHSCOPE_API_KEY")

    # --- 数据 ---
    data_dir: Path = Field(default_factory=lambda: project_root() / "data")

    # --- API ---
    api_cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173", alias="CORS_ORIGINS")

    def resolved_api_key(self) -> str:
        if self.llm_provider == LLMProviderKind.bailian and self.dashscope_api_key:
            return self.dashscope_api_key
        return self.api_key

    def resolved_base_url(self) -> str:
        if self.llm_provider == LLMProviderKind.bailian:
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        if self.llm_provider == LLMProviderKind.local_vllm:
            return self.base_url or "http://127.0.0.1:8000/v1"
        if self.llm_provider == LLMProviderKind.local_ollama:
            return self.base_url or "http://127.0.0.1:11434/v1"
        return self.base_url or "https://api.siliconflow.cn/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_data_subdirs() -> None:
    s = get_settings()
    root = s.data_dir
    for sub in (
        "metadata",
        "knowledge_bases",
        "sessions",
        "users",
        "indexes",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
