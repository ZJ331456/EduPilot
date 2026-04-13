"""核心事件流协议：支持 SSE 流式响应和统一事件类型。"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

import sse_starlette.sse as sse


class EventType(str, Enum):
    """事件类型枚举。"""
    # 内容事件
    CONTENT = "content"          # 主内容片段（流式）
    THINKING = "thinking"       # 思考过程
    TOOL_START = "tool_start"   # 工具开始执行
    TOOL_END = "tool_end"       # 工具执行完成
    TOOL_ERROR = "tool_error"   # 工具执行错误
    STEP_START = "step_start"   # 步骤开始
    STEP_END = "step_end"       # 步骤完成
    # 元事件
    MESSAGE_START = "message_start"    # 消息开始
    MESSAGE_END = "message_end"        # 消息结束
    ERROR = "error"                   # 错误
    HEARTBEAT = "heartbeat"           # 心跳保活
    # 分析事件
    ANALYSIS = "analysis"             # 查询分析结果


@dataclass
class StreamEvent:
    """流式事件数据结构。"""
    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp
        }

    def to_sse(self) -> str:
        """转换为 SSE 格式。"""
        return f"event: {self.type.value}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


class StreamBus:
    """异步事件流总线：支持多订阅者、事件发布与消费。"""

    def __init__(self) -> None:
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, subscriber_id: str) -> AsyncGenerator[StreamEvent, None]:
        """订阅事件流，返回异步生成器。"""
        queue: asyncio.Queue[Optional[StreamEvent]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[subscriber_id] = queue

        try:
            while True:
                event = await queue.get()
                if event is None:  # 收到终止信号
                    break
                yield event
        finally:
            async with self._lock:
                self._subscribers.pop(subscriber_id, None)

    async def publish(self, event: StreamEvent) -> None:
        """向所有订阅者发布事件。"""
        if not self._subscribers:
            return
        async with self._lock:
            for queue in list(self._subscribers.values()):
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass

    async def broadcast(self, event: StreamEvent) -> None:
        """广播事件（publish 的异步版本）。"""
        await self.publish(event)

    async def close(self, subscriber_id: str) -> None:
        """关闭订阅者的事件流。"""
        async with self._lock:
            if subscriber_id in self._subscribers:
                await self._subscribers[subscriber_id].put(None)


class ResponseBuilder:
    """响应构建器：逐步组装流式响应，支持多阶段事件。"""

    def __init__(
        self,
        bus: StreamBus,
        session_id: str,
        agent_name: str = "base"
    ) -> None:
        self._bus = bus
        self._session_id = session_id
        self._agent_name = agent_name
        self._content_chunks: List[str] = []
        self._steps: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []

    async def start_message(self, message_type: str = "chat") -> None:
        """开始一条消息。"""
        await self._bus.publish(StreamEvent(
            type=EventType.MESSAGE_START,
            data={
                "session_id": self._session_id,
                "agent": self._agent_name,
                "message_type": message_type
            }
        ))

    async def start_step(self, step_name: str, step_index: int = -1) -> None:
        """开始一个执行步骤。"""
        step = {
            "step_name": step_name,
            "step_index": step_index,
            "agent_name": self._agent_name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running"
        }
        self._steps.append(step)
        await self._bus.publish(StreamEvent(
            type=EventType.STEP_START,
            data=step
        ))

    async def end_step(self, step_name: str, result: Optional[Dict[str, Any]] = None) -> None:
        """结束一个执行步骤。"""
        for step in reversed(self._steps):
            if step["step_name"] == step_name and step.get("status") == "running":
                step["status"] = "completed"
                step["end_time"] = datetime.now(timezone.utc).isoformat()
                if result:
                    step["result"] = result
                await self._bus.publish(StreamEvent(
                    type=EventType.STEP_END,
                    data=step
                ))
                break

    async def start_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> None:
        """开始执行工具。"""
        tool = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running"
        }
        self._tools.append(tool)
        await self._bus.publish(StreamEvent(
            type=EventType.TOOL_START,
            data=tool
        ))

    async def end_tool(self, tool_name: str, tool_output: Any, error: Optional[str] = None) -> None:
        """结束工具执行。"""
        for tool in reversed(self._tools):
            if tool["tool_name"] == tool_name and tool.get("status") == "running":
                tool["status"] = "completed" if not error else "error"
                tool["end_time"] = datetime.now(timezone.utc).isoformat()
                tool["tool_output"] = str(tool_output)[:2000]
                if error:
                    tool["error"] = error
                event_type = EventType.TOOL_ERROR if error else EventType.TOOL_END
                await self._bus.publish(StreamEvent(
                    type=event_type,
                    data=tool
                ))
                break

    async def send_thinking(self, thought: str) -> None:
        """发送思考过程。"""
        await self._bus.publish(StreamEvent(
            type=EventType.THINKING,
            data={
                "thought": thought,
                "agent": self._agent_name
            }
        ))

    async def send_content(self, chunk: str, is_final: bool = False) -> None:
        """发送内容片段（流式）。"""
        self._content_chunks.append(chunk)
        await self._bus.publish(StreamEvent(
            type=EventType.CONTENT,
            data={
                "chunk": chunk,
                "is_final": is_final,
                "agent": self._agent_name,
                "full_content": "".join(self._content_chunks) if is_final else None
            }
        ))

    async def send_analysis(self, analysis: Dict[str, Any]) -> None:
        """发送分析结果。"""
        await self._bus.publish(StreamEvent(
            type=EventType.ANALYSIS,
            data=analysis
        ))

    async def end_message(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """结束一条消息。"""
        await self._bus.publish(StreamEvent(
            type=EventType.MESSAGE_END,
            data={
                "session_id": self._session_id,
                "agent": self._agent_name,
                "full_content": "".join(self._content_chunks),
                "steps_count": len(self._steps),
                "tools_count": len(self._tools),
                "metadata": metadata or {}
            }
        ))

    async def send_error(self, error: str, error_code: str = "UNKNOWN") -> None:
        """发送错误事件。"""
        await self._bus.publish(StreamEvent(
            type=EventType.ERROR,
            data={
                "error": error,
                "error_code": error_code,
                "agent": self._agent_name
            }
        ))

    @property
    def full_content(self) -> str:
        """获取完整内容。"""
        return "".join(self._content_chunks)

    @property
    def steps(self) -> List[Dict[str, Any]]:
        """获取所有步骤。"""
        return self._steps

    @property
    def tools(self) -> List[Dict[str, Any]]:
        """获取所有工具调用。"""
        return self._tools


def format_sse_response(event: StreamEvent) -> sse.Event:
    """将 StreamEvent 格式化为 SSE 响应。"""
    return sse.Event(
        event=event.type.value,
        data=json.dumps(event.data, ensure_ascii=False)
    )
