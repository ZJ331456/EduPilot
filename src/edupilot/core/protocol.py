"""核心协议定义：统一上下文与工具协议。"""

from __future__ import annotations

import abc
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from edupilot.core.stream import StreamBus, StreamEvent, ResponseBuilder


class AgentMode(str, Enum):
    """对话模式枚举。"""
    DIRECT = "direct"              # 直接回答模式
    SOCRATIC = "socratic"         # 苏格拉底式提问模式
    DEEP_SOLVE = "deep_solve"     # 深度问题解决模式
    RESEARCH = "research"          # 深度研究模式
    QUIZ = "quiz"                 # 测验生成模式


@dataclass
class ToolDefinition:
    """工具定义结构。"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema 格式
    is_async: bool = True


@dataclass
class ToolResult:
    """工具执行结果。"""
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class UnifiedContext:
    """统一上下文：贯穿所有 Agent 组件的单一数据对象。"""
    # 会话标识
    session_id: str
    user_id: str
    # 用户消息
    user_message: str
    # 对话历史
    history: List[Dict[str, str]] = field(default_factory=list)
    # 当前模式
    mode: AgentMode = AgentMode.DIRECT
    # 启用工具
    enabled_tools: List[str] = field(default_factory=list)
    # 知识库
    knowledge_bases: List[str] = field(default_factory=list)
    # 附件/上下文
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    # 配置覆盖
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_history(self, role: str, content: str) -> None:
        """添加历史消息。"""
        self.history.append({"role": role, "content": content, "ts": datetime.now(timezone.utc).isoformat()})

    def to_llm_messages(self) -> List[Dict[str, str]]:
        """转换为 LLM 消息格式。"""
        msgs = []
        for m in self.history[-24:]:  # 限制历史长度
            msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        msgs.append({"role": "user", "content": self.user_message})
        return msgs

    def get_context_summary(self, max_chars: int = 8000) -> str:
        """获取上下文摘要（用于提示词）。"""
        lines = []
        for m in self.history[-24:]:
            role = m.get("role", "user")
            prefix = "用户" if role == "user" else "助手"
            lines.append(f"{prefix}: {m.get('content', '')}")
        lines.append(f"用户: {self.user_message}")
        text = "\n".join(lines)
        if len(text) > max_chars:
            return text[-max_chars:]
        return text


@dataclass
class AgentResponse:
    """Agent 响应数据结构。"""
    content: str
    session_id: str
    mode: str
    # 可选字段
    analysis: Optional[Dict[str, Any]] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    graph_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(abc.ABC):
    """工具基类：所有工具必须继承此基类。"""

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """获取工具定义。"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具。"""
        pass

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数（可选实现）。"""
        return True
