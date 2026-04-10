"""短期存储：单会话 JSON，位于 data/sessions。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from edupilot.config.settings import get_settings


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self) -> None:
        self._root = get_settings().data_dir / "sessions"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self._root / f"{session_id}.json"

    def create(self, user_id: str, meta: Optional[Dict[str, Any]] = None) -> str:
        sid = str(uuid.uuid4())
        doc = {
            "session_id": sid,
            "user_id": user_id,
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "messages": [],
            "dialogue_graph": {"nodes": [], "edges": []},
            "meta": meta or {},
        }
        self._write(sid, doc)
        return sid

    def _write(self, session_id: str, doc: Dict[str, Any]) -> None:
        doc["updated_at"] = _utc_now_iso()
        p = self._path(session_id)
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, session_id: str) -> Dict[str, Any]:
        p = self._path(session_id)
        if not p.exists():
            raise FileNotFoundError(session_id)
        return json.loads(p.read_text(encoding="utf-8"))

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        doc = self.load(session_id)
        doc["messages"].append(
            {
                "role": role,
                "content": content,
                "ts": _utc_now_iso(),
                **(extra or {}),
            }
        )
        self._write(session_id, doc)

    def update_dialogue_graph(self, session_id: str, nodes: List[Dict], edges: List[Dict]) -> None:
        doc = self.load(session_id)
        doc["dialogue_graph"] = {"nodes": nodes, "edges": edges}
        self._write(session_id, doc)

    def merge_messages_tail(self, session_id: str, max_turns: int = 12) -> str:
        doc = self.load(session_id)
        msgs = doc.get("messages") or []
        tail = msgs[-max_turns:]
        lines = []
        for m in tail:
            who = "用户" if m.get("role") == "user" else "助手"
            lines.append(f"{who}: {m.get('content', '')}")
        return "\n".join(lines)

    def mark_ended(self, session_id: str) -> None:
        doc = self.load(session_id)
        doc["ended"] = True
        self._write(session_id, doc)
