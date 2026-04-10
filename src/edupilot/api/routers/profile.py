"""用户画像：调用 user_profile 智能体并写入 data。"""

from __future__ import annotations

import json

from fastapi import APIRouter
from pydantic import BaseModel, Field

from edupilot.agents.user_profile.agent import analyze as run_user_profile_llm
from edupilot.services.storage import SessionStore, UserGraphStore
from edupilot.services.storage.profile_store import ProfileStore

router = APIRouter(prefix="/profile", tags=["profile"])


class AnalyzeBody(BaseModel):
    user_id: str
    session_id: str | None = None
    extra_summary: str = ""


@router.post("/analyze")
async def analyze_profile(body: AnalyzeBody):
    ug = UserGraphStore()
    g = ug.load_graph(body.user_id)
    graph_summary = json.dumps(g, ensure_ascii=False)[:6000]

    summary_parts = []
    if body.extra_summary:
        summary_parts.append(body.extra_summary)
    if body.session_id:
        try:
            doc = SessionStore().load(body.session_id)
            msgs = doc.get("messages") or []
            tail = "\n".join(
                f'{m.get("role")}: {m.get("content", "")}' for m in msgs[-40:]
            )
            summary_parts.append("近期会话摘录：\n" + tail)
        except FileNotFoundError:
            pass

    summary = "\n\n".join(summary_parts) or "暂无会话摘要，仅根据图谱推断。"
    prof = await run_user_profile_llm(body.user_id, summary, graph_summary)
    ProfileStore().save_profile(body.user_id, prof)
    return {"ok": True, "profile": prof}


@router.get("/{user_id}")
async def get_profile(user_id: str):
    return ProfileStore().load_profile(user_id)
