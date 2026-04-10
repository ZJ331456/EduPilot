"""学习评测。"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from edupilot.agents.evaluation.agent import evaluate as run_evaluate
from edupilot.services.storage import SessionStore

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvalBody(BaseModel):
    user_id: str
    session_id: str | None = None
    goals: str = ""
    extra_summary: str = ""


@router.post("/run")
async def run_evaluation(body: EvalBody):
    parts = []
    if body.extra_summary:
        parts.append(body.extra_summary)
    if body.session_id:
        try:
            doc = SessionStore().load(body.session_id)
            msgs = doc.get("messages") or []
            tail = "\n".join(
                f'{m.get("role")}: {m.get("content", "")}' for m in msgs[-50:]
            )
            parts.append("会话内容摘录：\n" + tail)
        except FileNotFoundError:
            pass
    summary = "\n\n".join(parts) or "无摘要，请结合目标评测。"
    result = await run_evaluate(summary, body.goals)
    return {"ok": True, "user_id": body.user_id, "evaluation": result}
