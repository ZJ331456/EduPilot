"""学习评测：输出分数与建议 JSON。"""

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


async def evaluate(summary: str, goals: str = "") -> Dict[str, Any]:
    p = load_agent_prompt("evaluation")
    system = p.get("system", "")
    user = (p.get("user") or "").format(summary=summary, goals=goals or "未指定")
    llm = get_llm_client()
    raw = await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.35,
    )
    return _parse_json(raw)
