"""用户画像与学习计划的 JSON 持久化。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from edupilot.config.settings import get_settings


class ProfileStore:
    def __init__(self) -> None:
        self._root = get_settings().data_dir / "users"

    def _user(self, user_id: str) -> Path:
        d = self._root / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_profile(self, user_id: str, doc: Dict[str, Any]) -> None:
        p = self._user(user_id) / "profile.json"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_profile(self, user_id: str) -> Dict[str, Any]:
        p = self._user(user_id) / "profile.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def save_plan(self, user_id: str, doc: Dict[str, Any]) -> None:
        p = self._user(user_id) / "learning_plan.json"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_plan(self, user_id: str) -> Dict[str, Any]:
        p = self._user(user_id) / "learning_plan.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))
