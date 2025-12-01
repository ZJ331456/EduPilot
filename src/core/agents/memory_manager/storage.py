#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地存储管理器
负责记忆数据的持久化存储和检索
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import shutil


@dataclass
class StorageConfig:
    """存储配置"""
    base_dir: Path
    user_profiles_dir: Path
    session_memory_dir: Path
    learning_records_dir: Path
    max_file_age_days: int = 90  # 最大文件保留天数
    backup_enabled: bool = True
    
    @classmethod
    def create_default(cls, base_dir: str = "data/memory_data"):
        """创建默认配置
        
        Args:
            base_dir: 基础目录，默认为 data/memory_data
        """
        base_path = Path(base_dir)
        return cls(
            base_dir=base_path,
            user_profiles_dir=base_path / "user_profiles",
            session_memory_dir=base_path / "session_memory",
            learning_records_dir=base_path / "learning_records"
        )


class LocalStorageManager:
    """本地文件存储管理器
    
    职责:
    1. 用户画像的持久化存储
    2. 会话记忆的存储和检索
    3. 学习记录的归档管理
    4. 自动清理过期数据
    
    设计原则:
    - Repository模式: 封装数据访问逻辑
    - 单一职责: 只负责存储和检索
    - 错误容错: 存储失败不影响主流程
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        """初始化存储管理器"""
        self.config = config or StorageConfig.create_default()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保所有目录存在
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保所有存储目录存在"""
        for directory in [
            self.config.user_profiles_dir,
            self.config.session_memory_dir,
            self.config.learning_records_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            
    # ==================== 用户画像存储 ====================
    
    def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """保存用户画像
        
        Args:
            user_id: 用户ID
            profile_data: 画像数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            file_path = self.config.user_profiles_dir / f"{user_id}.json"
            
            # 添加元数据
            data_with_meta = {
                "user_id": user_id,
                "data": profile_data,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # 备份旧文件
            if file_path.exists() and self.config.backup_enabled:
                self._backup_file(file_path)
            
            # 保存新文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"用户画像已保存: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存用户画像失败: {user_id}, 错误: {e}")
            return False
    
    def load_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """加载用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict]: 画像数据，不存在返回None
        """
        try:
            file_path = self.config.user_profiles_dir / f"{user_id}.json"
            
            if not file_path.exists():
                self.logger.info(f"用户画像不存在: {user_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get("data")
            
        except Exception as e:
            self.logger.error(f"加载用户画像失败: {user_id}, 错误: {e}")
            return None
    
    def list_user_profiles(self) -> List[str]:
        """列出所有用户ID"""
        try:
            profile_files = self.config.user_profiles_dir.glob("*.json")
            return [f.stem for f in profile_files]
        except Exception as e:
            self.logger.error(f"列出用户画像失败: {e}")
            return []
    
    # ==================== 会话记忆存储 ====================
    
    def save_session_memory(self, session_id: str, memory_data: Dict[str, Any]) -> bool:
        """保存会话记忆
        
        🔧 修复：使用固定文件名，同一session_id更新同一个文件
        
        Args:
            session_id: 会话ID
            memory_data: 记忆数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 🔧 修复：移除时间戳，使用固定文件名
            filename = f"session_{session_id}.json"
            file_path = self.config.session_memory_dir / filename
            
            # 如果文件已存在，加载现有数据并合并对话历史
            existing_data = None
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_file = json.load(f)
                        existing_data = existing_file.get("data")
                except Exception as e:
                    self.logger.warning(f"加载现有会话数据失败: {e}")
            
            # 🔧 合并对话历史
            if existing_data and 'dialogue_history' in existing_data:
                # 保留旧的对话历史，追加新的
                old_history = existing_data.get('dialogue_history', [])
                new_history = memory_data.get('dialogue_history', [])
                
                # 合并历史，避免重复
                merged_history = old_history.copy()
                for item in new_history:
                    # 检查是否已存在相同轮次的记录
                    round_num = item.get('round')
                    exists = any(h.get('round') == round_num for h in merged_history)
                    if not exists:
                        merged_history.append(item)
                    else:
                        # 更新已存在的记录（比如添加response）
                        for h in merged_history:
                            if h.get('round') == round_num:
                                h.update(item)
                                break
                
                memory_data['dialogue_history'] = merged_history
                self.logger.info(f"合并对话历史: {len(merged_history)}轮")
            
            # 添加元数据
            data_with_meta = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "data": memory_data,
                "version": "1.0"
            }
            
            # 备份旧文件（如果启用备份）
            if file_path.exists() and self.config.backup_enabled:
                self._backup_file(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"会话记忆已保存: {session_id} (对话轮次: {len(memory_data.get('dialogue_history', []))})")
            return True
            
        except Exception as e:
            self.logger.error(f"保存会话记忆失败: {session_id}, 错误: {e}")
            return False
    
    def load_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话记忆
        
        🔧 修复：直接加载固定文件名的会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict]: 记忆数据，不存在返回None
        """
        try:
            # 🔧 修复：直接使用固定文件名
            filename = f"session_{session_id}.json"
            file_path = self.config.session_memory_dir / filename
            
            if not file_path.exists():
                self.logger.info(f"会话记忆不存在: {session_id}")
                return None
            
            # 加载文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            memory_data = data.get("data")
            if memory_data:
                self.logger.info(
                    f"已加载会话记忆: {session_id} (对话轮次: {len(memory_data.get('dialogue_history', []))})"
                )
            
            return memory_data
            
        except Exception as e:
            self.logger.error(f"加载会话记忆失败: {session_id}, 错误: {e}")
            return None
    
    def load_user_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """加载用户的会话历史
        
        Args:
            user_id: 用户ID
            limit: 最多返回的会话数
            
        Returns:
            List[Dict]: 会话记忆列表
        """
        try:
            # 查找所有会话文件，并按时间排序
            all_files = sorted(
                self.config.session_memory_dir.glob("session_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            user_sessions = []
            for file_path in all_files:
                if len(user_sessions) >= limit:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 检查是否属于该用户
                    if data.get("data", {}).get("user_id") == user_id:
                        user_sessions.append(data.get("data"))
                except:
                    continue
            
            return user_sessions
            
        except Exception as e:
            self.logger.error(f"加载用户会话历史失败: {user_id}, 错误: {e}")
            return []
    
    # ==================== 学习记录存储 ====================
    
    def save_learning_record(self, user_id: str, record_data: Dict[str, Any]) -> bool:
        """保存学习记录
        
        Args:
            user_id: 用户ID
            record_data: 记录数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"learning_{user_id}_{timestamp}.json"
            file_path = self.config.learning_records_dir / filename
            
            # 添加元数据
            data_with_meta = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "data": record_data,
                "version": "1.0"
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"学习记录已保存: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存学习记录失败: {user_id}, 错误: {e}")
            return False
    
    def load_learning_records(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """加载用户的学习记录
        
        Args:
            user_id: 用户ID
            limit: 最多返回的记录数
            
        Returns:
            List[Dict]: 学习记录列表
        """
        try:
            pattern = f"learning_{user_id}_*.json"
            record_files = sorted(
                self.config.learning_records_dir.glob(pattern),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            records = []
            for file_path in list(record_files)[:limit]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    records.append(data.get("data"))
                except:
                    continue
            
            return records
            
        except Exception as e:
            self.logger.error(f"加载学习记录失败: {user_id}, 错误: {e}")
            return []
    
    # ==================== 维护操作 ====================
    
    def _backup_file(self, file_path: Path):
        """备份文件"""
        try:
            backup_dir = file_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"文件已备份: {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"文件备份失败: {e}")
    
    def cleanup_old_data(self, days: Optional[int] = None):
        """清理过期数据
        
        Args:
            days: 保留天数，默认使用配置值
        """
        try:
            days = days or self.config.max_file_age_days
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            deleted_count = 0
            
            # 清理会话记忆和学习记录（用户画像不自动删除）
            for directory in [self.config.session_memory_dir, self.config.learning_records_dir]:
                for file_path in directory.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            self.logger.info(f"已清理 {deleted_count} 个过期文件")
            
        except Exception as e:
            self.logger.error(f"清理过期数据失败: {e}")
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            stats = {
                "user_profiles_count": len(list(self.config.user_profiles_dir.glob("*.json"))),
                "session_memories_count": len(list(self.config.session_memory_dir.glob("*.json"))),
                "learning_records_count": len(list(self.config.learning_records_dir.glob("*.json"))),
                "total_size_mb": 0.0
            }
            
            # 计算总大小
            total_size = 0
            for directory in [
                self.config.user_profiles_dir,
                self.config.session_memory_dir,
                self.config.learning_records_dir
            ]:
                for file_path in directory.rglob("*.json"):
                    total_size += file_path.stat().st_size
            
            stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取存储统计失败: {e}")
            return {}

