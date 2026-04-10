"""用户画像：基于会话与图谱摘要输出 JSON 画像。"""

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


async def analyze(
    user_id: str,
    summary: str,
    graph_summary: str,
) -> Dict[str, Any]:
    p = load_agent_prompt("user_profile")
    system = p.get("system", "")
    user = (p.get("user") or "").format(
        user_id=user_id,
        summary=summary,
        graph_summary=graph_summary,
    )
    llm = get_llm_client()
    raw = await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
    )
    return _parse_json(raw)
