#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — 本地存储管理器

从 v3 memory_manager/storage.py 迁移，作为独立存储工具供 MemorySystemService 使用。
只依赖标准库，无外部依赖。
"""

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StorageConfig:
    """存储配置"""

    base_dir: Path
    user_profiles_dir: Path
    session_memory_dir: Path
    learning_records_dir: Path
    max_file_age_days: int = 90
    backup_enabled: bool = True

    @classmethod
    def create_default(cls, base_dir: str = "data/memory_data") -> "StorageConfig":
        base_path = Path(base_dir)
        return cls(
            base_dir=base_path,
            user_profiles_dir=base_path / "user_profiles",
            session_memory_dir=base_path / "session_memory",
            learning_records_dir=base_path / "learning_records",
        )


class LocalStorageManager:
    """本地文件存储管理器（Repository 模式）

    职责：
    1. 用户画像的持久化存储
    2. 会话记忆的存储和检索
    3. 学习记录的归档管理
    4. 自动清理过期数据
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig.create_default()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ensure_directories()

    def _ensure_directories(self):
        for directory in [
            self.config.user_profiles_dir,
            self.config.session_memory_dir,
            self.config.learning_records_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    # ── 用户画像 ──────────────────────────────────────────────────────────

    def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        try:
            file_path = self.config.user_profiles_dir / f"{user_id}.json"
            if file_path.exists() and self.config.backup_enabled:
                self._backup_file(file_path)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"user_id": user_id, "data": profile_data,
                     "last_updated": datetime.now().isoformat(), "version": "1.0"},
                    f, ensure_ascii=False, indent=2,
                )
            self.logger.info(f"用户画像已保存: {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"保存用户画像失败: {user_id}, 错误: {e}")
            return False

    def load_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            file_path = self.config.user_profiles_dir / f"{user_id}.json"
            if not file_path.exists():
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f).get("data")
        except Exception as e:
            self.logger.error(f"加载用户画像失败: {user_id}, 错误: {e}")
            return None

    def list_user_profiles(self) -> List[str]:
        try:
            return [f.stem for f in self.config.user_profiles_dir.glob("*.json")]
        except Exception as e:
            self.logger.error(f"列出用户画像失败: {e}")
            return []

    # ── 会话记忆 ──────────────────────────────────────────────────────────

    def save_session_memory(self, session_id: str, memory_data: Dict[str, Any]) -> bool:
        try:
            file_path = self.config.session_memory_dir / f"session_{session_id}.json"

            # 合并对话历史（若文件已存在）
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing = json.load(f).get("data", {})
                    old_history = existing.get("dialogue_history", [])
                    new_history = memory_data.get("dialogue_history", [])
                    merged = list(old_history)
                    for item in new_history:
                        rn = item.get("round")
                        idx = next((i for i, h in enumerate(merged) if h.get("round") == rn), None)
                        if idx is None:
                            merged.append(item)
                        else:
                            merged[idx].update(item)
                    memory_data["dialogue_history"] = merged
                except Exception:
                    pass
                if self.config.backup_enabled:
                    self._backup_file(file_path)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"session_id": session_id, "timestamp": datetime.now().isoformat(),
                     "data": memory_data, "version": "1.0"},
                    f, ensure_ascii=False, indent=2,
                )
            self.logger.info(f"会话记忆已保存: {session_id}")
            return True
        except Exception as e:
            self.logger.error(f"保存会话记忆失败: {session_id}, 错误: {e}")
            return False

    def load_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            file_path = self.config.session_memory_dir / f"session_{session_id}.json"
            if not file_path.exists():
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f).get("data")
        except Exception as e:
            self.logger.error(f"加载会话记忆失败: {session_id}, 错误: {e}")
            return None

    def load_user_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            all_files = sorted(
                self.config.session_memory_dir.glob("session_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            sessions = []
            for fp in all_files:
                if len(sessions) >= limit:
                    break
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f).get("data", {})
                    if data.get("user_id") == user_id:
                        sessions.append(data)
                except Exception:
                    continue
            return sessions
        except Exception as e:
            self.logger.error(f"加载用户会话历史失败: {user_id}, 错误: {e}")
            return []

    # ── 学习记录 ──────────────────────────────────────────────────────────

    def save_learning_record(self, user_id: str, record_data: Dict[str, Any]) -> bool:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.config.learning_records_dir / f"learning_{user_id}_{ts}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"user_id": user_id, "timestamp": datetime.now().isoformat(),
                     "data": record_data, "version": "1.0"},
                    f, ensure_ascii=False, indent=2,
                )
            return True
        except Exception as e:
            self.logger.error(f"保存学习记录失败: {user_id}, 错误: {e}")
            return False

    def load_learning_records(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            files = sorted(
                self.config.learning_records_dir.glob(f"learning_{user_id}_*.json"),
                key=lambda f: f.stat().st_mtime, reverse=True,
            )
            records = []
            for fp in list(files)[:limit]:
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        records.append(json.load(f).get("data"))
                except Exception:
                    continue
            return records
        except Exception as e:
            self.logger.error(f"加载学习记录失败: {user_id}, 错误: {e}")
            return []

    # ── 维护 ─────────────────────────────────────────────────────────────

    def _backup_file(self, file_path: Path):
        try:
            backup_dir = file_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(file_path, backup_dir / f"{file_path.stem}_{ts}{file_path.suffix}")
        except Exception as e:
            self.logger.warning(f"文件备份失败: {e}")

    def cleanup_old_data(self, days: Optional[int] = None):
        try:
            days = days or self.config.max_file_age_days
            cutoff = datetime.now().timestamp() - days * 86400
            deleted = 0
            for directory in [self.config.session_memory_dir, self.config.learning_records_dir]:
                for fp in directory.glob("*.json"):
                    if fp.stat().st_mtime < cutoff:
                        fp.unlink()
                        deleted += 1
            self.logger.info(f"已清理 {deleted} 个过期文件")
        except Exception as e:
            self.logger.error(f"清理过期数据失败: {e}")

    def get_storage_statistics(self) -> Dict[str, Any]:
        try:
            total = sum(
                fp.stat().st_size
                for d in [self.config.user_profiles_dir,
                           self.config.session_memory_dir,
                           self.config.learning_records_dir]
                for fp in d.rglob("*.json")
            )
            return {
                "user_profiles_count": len(list(self.config.user_profiles_dir.glob("*.json"))),
                "session_memories_count": len(list(self.config.session_memory_dir.glob("*.json"))),
                "learning_records_count": len(list(self.config.learning_records_dir.glob("*.json"))),
                "total_size_mb": round(total / 1048576, 2),
            }
        except Exception as e:
            self.logger.error(f"获取存储统计失败: {e}")
            return {}
