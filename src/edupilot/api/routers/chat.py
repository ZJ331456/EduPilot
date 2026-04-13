"""对话路由：使用统一的 ChatAgent。"""

from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from edupilot.agents.chat.agent import ChatAgent, ChatMode
from edupilot.agents.base.agent import AgentConfig
from edupilot.core.protocol import AgentMode, UnifiedContext
from edupilot.agents.dialogue_graph import DialogueGraphAgent
from edupilot.services.storage import SessionStore, UserGraphStore, get_statistics_store

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户标识")
    session_id: Optional[str] = None
    message: str = Field(..., description="用户消息")
    mode: Literal["direct", "socratic"] = "direct"
    update_graph: bool = True


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    mode: str
    dialogue_nodes: int = 0
    dialogue_edges: int = 0


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    对话接口：使用统一的 ChatAgent。

    - mode=direct: 直接回答问题
    - mode=socratic: 苏格拉底式引导
    """
    import time
    store = SessionStore()
    dgraph = DialogueGraphAgent()
    ug = UserGraphStore()
    stats = get_statistics_store()

    # 记录开始时间
    start_time = time.time()

    # 记录用户活动
    stats.record_user_activity(req.user_id, "chat")

    # 创建或加载会话
    sid = req.session_id
    if not sid:
        sid = store.create(req.user_id, meta={"mode": req.mode})
        stats.increment_session_created()
    else:
        try:
            store.load(sid)
        except FileNotFoundError:
            sid = store.create(req.user_id, meta={"mode": req.mode})
            stats.increment_session_created()

    doc = store.load(sid)
    history: List[dict] = doc.get("messages") or []

    # 构建统一上下文
    ctx = UnifiedContext(
        session_id=sid,
        user_id=req.user_id,
        user_message=req.message,
        mode=AgentMode.DIRECT if req.mode == "direct" else AgentMode.SOCRATIC,
        metadata={"user_mode": req.mode}
    )
    ctx.history = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in history]

    # 执行 ChatAgent
    agent = ChatAgent(AgentConfig(
        name="ChatAgent",
        streaming_enabled=False  # REST API 使用非流式
    ))
    assistant_text = await agent.execute(ctx, builder=None, stream=False)

    # 记录 Agent 执行时间
    execution_time_ms = int((time.time() - start_time) * 1000)
    stats.increment_agent_execution("ChatAgent")
    stats.record_agent_execution("ChatAgent", execution_time_ms, True, req.mode)

    # 保存消息
    store.append_message(sid, "user", req.message)
    store.append_message(sid, "assistant", assistant_text)

    # 更新图谱
    nodes, edges = [], []
    if req.update_graph:
        try:
            tail = store.merge_messages_tail(sid, max_turns=16)
            nodes, edges = await dgraph.extract(tail)
            store.update_dialogue_graph(sid, nodes, edges)
            ug.merge_from_session(req.user_id, nodes, edges)
        except Exception:
            pass

    return ChatResponse(
        reply=assistant_text,
        session_id=sid,
        mode=req.mode,
        dialogue_nodes=len(nodes),
        dialogue_edges=len(edges),
    )


class EndSessionBody(BaseModel):
    user_id: str


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str, body: EndSessionBody):
    """结束会话。"""
    store = SessionStore()
    stats = get_statistics_store()
    try:
        store.mark_ended(session_id)
        stats.increment_session_ended()
    except FileNotFoundError:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "session_id": session_id}
