"""项目根路径解析，保证数据目录落在仓库根目录 data 下。"""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """edupilot/src/edupilot/... -> 仓库根 edupilot/"""
    return Path(__file__).resolve().parent.parent.parent


def data_dir() -> Path:
    root = project_root()
    d = root / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d
