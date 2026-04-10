"""对话：直接模式与苏格拉底模式，会话 JSON 与图谱更新。"""

from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from edupilot.agents import chat_direct as cd
from edupilot.agents import chat_socratic as cs
from edupilot.services.graph import DialogueGraphService
from edupilot.services.storage import SessionStore, UserGraphStore

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户标识")
    session_id: Optional[str] = None
    message: str
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
    store = SessionStore()
    dgraph = DialogueGraphService()
    ug = UserGraphStore()

    sid = req.session_id
    if not sid:
        sid = store.create(req.user_id, meta={"mode": req.mode})
    else:
        try:
            store.load(sid)
        except FileNotFoundError:
            sid = store.create(req.user_id, meta={"mode": req.mode})

    doc = store.load(sid)
    history: List[dict] = doc.get("messages") or []

    ctx = (
        cd.build_context(history, req.message)
        if req.mode == "direct"
        else cs.build_context(history, req.message)
    )

    if req.mode == "direct":
        assistant_text = await cd.reply(ctx)
    else:
        assistant_text = await cs.reply(ctx)

    store.append_message(sid, "user", req.message)
    store.append_message(sid, "assistant", assistant_text)

    nodes, edges = [], []
    if req.update_graph:
        tail = store.merge_messages_tail(sid, max_turns=16)
        try:
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
    store = SessionStore()
    try:
        store.mark_ended(session_id)
    except FileNotFoundError:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "session_id": session_id}
