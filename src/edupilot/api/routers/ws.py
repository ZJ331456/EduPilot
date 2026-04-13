"""WebSocket 流式对话路由：使用统一的 ChatAgent，支持 SSE 和 WebSocket。"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sse_starlette.sse import EventSourceResponse

from edupilot.agents.chat.agent import ChatAgent
from edupilot.agents.base.agent import AgentConfig
from edupilot.core.protocol import AgentMode, UnifiedContext
from edupilot.core.stream import EventType, StreamBus, StreamEvent
from edupilot.services.graph import DialogueGraphService
from edupilot.services.storage import SessionStore, UserGraphStore

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器。"""

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._buses: Dict[str, StreamBus] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """接受 WebSocket 连接。"""
        await websocket.accept()
        self._connections[client_id] = websocket
        self._buses[client_id] = StreamBus()

    def disconnect(self, client_id: str) -> None:
        """断开连接。"""
        self._connections.pop(client_id, None)
        self._buses.pop(client_id, None)

    def get_bus(self, client_id: str) -> Optional[StreamBus]:
        """获取事件总线。"""
        return self._buses.get(client_id)

    async def send_json(self, client_id: str, data: Dict[str, Any]) -> None:
        """发送 JSON 数据。"""
        if client_id in self._connections:
            await self._connections[client_id].send_json(data)


manager = ConnectionManager()


@router.get("/chat/{client_id}")
async def chat_sse(client_id: str):
    """
    SSE 流式对话接口。

    使用 EventSourceResponse 实现服务器推送。
    """
    async def event_generator():
        bus = manager.get_bus(client_id)
        if not bus:
            return

        subscriber_id = f"sse_{client_id}"
        try:
            async for event in bus.subscribe(subscriber_id):
                yield {
                    "event": event.type.value,
                    "data": json.dumps(event.data, ensure_ascii=False)
                }
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator())


@router.websocket("/chat/ws/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket 流式对话接口。

    支持双向通信，可用于实时聊天场景。
    """
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)

    store = SessionStore()
    dgraph = DialogueGraphService()
    ug = UserGraphStore()

    try:
        # 发送连接成功消息
        await manager.send_json(client_id, {
            "type": "connected",
            "client_id": client_id,
            "user_id": user_id
        })

        while True:
            # 接收消息
            data = await websocket.receive_text()
            msg = json.loads(data)

            msg_type = msg.get("type", "chat")

            if msg_type == "chat":
                message = msg.get("message", "")
                mode = msg.get("mode", "direct")
                session_id = msg.get("session_id")
                update_graph = msg.get("update_graph", True)

                if not message:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": "消息内容不能为空"
                    })
                    continue

                # 创建或加载会话
                if not session_id:
                    session_id = store.create(user_id, meta={"mode": mode})
                else:
                    try:
                        store.load(session_id)
                    except FileNotFoundError:
                        session_id = store.create(user_id, meta={"mode": mode})

                doc = store.load(session_id)
                history = doc.get("messages") or []

                # 获取事件总线
                bus = manager.get_bus(client_id)

                # 发送消息开始事件
                await bus.publish(StreamEvent(
                    type=EventType.MESSAGE_START,
                    data={
                        "session_id": session_id,
                        "user_id": user_id,
                        "mode": mode
                    }
                ))

                # 构建统一上下文
                ctx = UnifiedContext(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=message,
                    mode=AgentMode.DIRECT if mode == "direct" else AgentMode.SOCRATIC,
                    metadata={"user_mode": mode}
                )
                ctx.history = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in history]

                # 使用统一的 ChatAgent
                agent = ChatAgent(AgentConfig(
                    name="ChatAgent",
                    streaming_enabled=True
                ))

                # 流式执行
                try:
                    async for event in agent.execute_stream(ctx):
                        await manager.send_json(client_id, event)

                    # 获取完整回复
                    full_content = ""
                    async for event in agent.execute_stream(ctx):
                        if event.get("type") == EventType.CONTENT.value and event.get("data", {}).get("is_final"):
                            full_content = event.get("data", {}).get("full_content", "")
                            break

                    # 如果流式执行没有返回完整内容，尝试其他方式获取
                    if not full_content:
                        # 重新执行获取完整回复
                        agent_sync = ChatAgent(AgentConfig(name="ChatAgent", streaming_enabled=False))
                        full_content = await agent_sync.execute(ctx, builder=None, stream=False)

                except Exception as e:
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": str(e)
                    })
                    continue

                # 保存消息
                store.append_message(session_id, "user", message)
                store.append_message(session_id, "assistant", full_content)

                # 更新图谱
                if update_graph:
                    try:
                        tail = store.merge_messages_tail(session_id, max_turns=16)
                        nodes, edges = await dgraph.extract(tail)
                        store.update_dialogue_graph(session_id, nodes, edges)
                        ug.merge_from_session(user_id, nodes, edges)

                        await manager.send_json(client_id, {
                            "type": "graph_updated",
                            "nodes_count": len(nodes),
                            "edges_count": len(edges)
                        })
                    except Exception:
                        pass

                # 发送完成事件
                await bus.publish(StreamEvent(
                    type=EventType.MESSAGE_END,
                    data={
                        "session_id": session_id,
                        "full_content": full_content
                    }
                ))

                await manager.send_json(client_id, {
                    "type": "message_complete",
                    "session_id": session_id,
                    "content": full_content
                })

            elif msg_type == "end_session":
                session_id = msg.get("session_id")
                if session_id:
                    try:
                        store.mark_ended(session_id)
                        await manager.send_json(client_id, {
                            "type": "session_ended",
                            "session_id": session_id
                        })
                    except FileNotFoundError:
                        await manager.send_json(client_id, {
                            "type": "error",
                            "error": "会话不存在"
                        })

            elif msg_type == "ping":
                await manager.send_json(client_id, {
                    "type": "pong"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        await manager.send_json(client_id, {
            "type": "error",
            "error": str(e)
        })
        manager.disconnect(client_id)
