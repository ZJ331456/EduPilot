"""从多轮对话中抽取实体与关系，写入会话级图谱并可选合并到用户长期图谱。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from edupilot.services.llm import get_llm_client
from edupilot.services.prompt.loader import load_agent_prompt


def _parse_json_block(text: str) -> Dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("模型未返回 JSON 对象")
    return json.loads(m.group(0))


class DialogueGraphAgent:
    def __init__(self) -> None:
        self._prompts = load_agent_prompt("dialogue_graph")
        self._llm = get_llm_client()

    async def extract(self, dialogue_text: str) -> Tuple[List[Dict], List[Dict]]:
        system = self._prompts.get("system", "你是知识图谱抽取助手。")
        user_tpl = self._prompts.get("user", "{dialogue}")
        user = user_tpl.format(dialogue=dialogue_text)
        reply = await self._llm.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        data = _parse_json_block(reply)
        nodes = data.get("nodes") or []
        edges = data.get("edges") or []
        norm_nodes = []
        for n in nodes:
            nid = str(n.get("id", n.get("name", "")))
            if not nid:
                continue
            norm_nodes.append({"id": nid, "label": n.get("label", nid)})
        norm_edges = []
        for e in edges:
            s, t = e.get("source"), e.get("target")
            if not s or not t:
                continue
            norm_edges.append(
                {
                    "source": str(s),
                    "target": str(t),
                    "relation": str(e.get("relation", "相关")),
                }
            )
        return norm_nodes, norm_edges
