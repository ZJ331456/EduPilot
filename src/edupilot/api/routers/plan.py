"""学习计划。"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from edupilot.agents.learning_planner.agent import plan as generate_learning_plan
from edupilot.services.storage.profile_store import ProfileStore

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanBody(BaseModel):
    user_id: str
    goal_hint: str = ""


@router.post("/generate")
async def generate_plan(body: PlanBody):
    ps = ProfileStore()
    profile = ps.load_profile(body.user_id)
    if not profile:
        profile = {"learning_style": "未知", "strengths": [], "gaps": [], "interests": []}
    plan = await generate_learning_plan(profile, body.goal_hint)
    ps.save_plan(body.user_id, plan)
    return {"ok": True, "plan": plan}


@router.get("/{user_id}")
async def get_plan(user_id: str):
    return ProfileStore().load_plan(user_id)
