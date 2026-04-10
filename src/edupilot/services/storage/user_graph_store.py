"""长期存储：用户级聚合图谱 JSON，位于 data/users/<id>/。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from edupilot.config.settings import get_settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserGraphStore:
    def __init__(self) -> None:
        self._root = get_settings().data_dir / "users"
        self._root.mkdir(parents=True, exist_ok=True)

    def user_dir(self, user_id: str) -> Path:
        d = self._root / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def long_term_graph_path(self, user_id: str) -> Path:
        return self.user_dir(user_id) / "long_term_graph.json"

    def load_graph(self, user_id: str) -> Dict[str, Any]:
        p = self.long_term_graph_path(user_id)
        if not p.exists():
            return {"nodes": [], "edges": [], "updated_at": _now()}
        return json.loads(p.read_text(encoding="utf-8"))

    def save_graph(self, user_id: str, nodes: List[Dict], edges: List[Dict]) -> None:
        p = self.long_term_graph_path(user_id)
        doc = {"nodes": nodes, "edges": edges, "updated_at": _now()}
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def merge_from_session(
        self,
        user_id: str,
        session_nodes: List[Dict],
        session_edges: List[Dict],
    ) -> Dict[str, Any]:
        cur = self.load_graph(user_id)
        nodes_by_id: Dict[str, Dict] = {}
        for n in cur.get("nodes", []):
            nid = str(n.get("id", ""))
            if nid:
                nodes_by_id[nid] = dict(n)

        for n in session_nodes:
            nid = str(n.get("id") or n.get("name") or "")
            if not nid:
                continue
            if nid not in nodes_by_id:
                nodes_by_id[nid] = {
                    "id": nid,
                    "label": n.get("label", nid),
                    "source": "session",
                }
            else:
                nodes_by_id[nid]["label"] = n.get("label", nodes_by_id[nid].get("label", nid))

        def ek(e: Dict) -> tuple:
            return (
                str(e.get("source", "")),
                str(e.get("target", "")),
                str(e.get("relation", "")),
            )

        seen = set()
        merged_edges: List[Dict] = []
        for e in cur.get("edges", []) + session_edges:
            k = ek(e)
            if k in seen or not k[0] or not k[1]:
                continue
            seen.add(k)
            merged_edges.append(e)

        nodes_out = list(nodes_by_id.values())
        self.save_graph(user_id, nodes_out, merged_edges)
        return self.load_graph(user_id)
