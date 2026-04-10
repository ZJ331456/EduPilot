"""苏格拉底式对话：以提问引导思考。"""

from __future__ import annotations

from typing import List

from edupilot.services.llm import get_llm_client
from edupilot.services.prompt.loader import load_agent_prompt


async def reply(context_block: str, temperature: float = 0.6) -> str:
    p = load_agent_prompt("chat_socratic")
    system = p.get("system", "你是苏格拉底式导师。")
    user = (p.get("user") or "{context}").format(context=context_block)
    llm = get_llm_client()
    return await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
    )


def build_context(history: List[dict], user_message: str, max_chars: int = 8000) -> str:
    lines = []
    for m in history[-24:]:
        role = m.get("role", "user")
        prefix = "用户" if role == "user" else "助手"
        lines.append(f"{prefix}: {m.get('content', '')}")
    lines.append(f"用户: {user_message}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        return text[-max_chars:]
    return text
