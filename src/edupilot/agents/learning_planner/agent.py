"""学习计划：结合画像生成结构化周计划 JSON。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from edupilot.services.llm import get_llm_client
from edupilot.services.prompt.loader import load_agent_prompt


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("未解析到 JSON")
    return json.loads(m.group(0))


async def plan(profile: Dict[str, Any], goal_hint: str = "") -> Dict[str, Any]:
    p = load_agent_prompt("learning_planner")
    system = p.get("system", "")
    user = (p.get("user") or "").format(
        profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
        goal_hint=goal_hint or "无",
    )
    llm = get_llm_client()
    raw = await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
    )
    return _parse_json(raw)
