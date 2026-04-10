"""从各 Agent 子目录加载中文 YAML 提示词。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from edupilot.paths import project_root


def _agents_base() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "agents"


def load_agent_prompt(agent_folder: str, filename: str = "prompts.yaml") -> Dict[str, Any]:
    """agent_folder 为 agents 下目录名，例如 chat_direct。"""
    path = _agents_base() / agent_folder / "prompts" / "zh" / filename
    if not path.exists():
        raise FileNotFoundError(f"未找到提示词文件: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"提示词 YAML 根必须是字典: {path}")
    return data


def format_prompt(template: str, **kwargs: Any) -> str:
    return template.format(**kwargs)
