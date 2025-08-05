#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话存储管理器
整合MongoDB和本地文件存储，提供统一的历史记录管理
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from services.mongodb_integration import mongodb_service

logger = logging.getLogger(__name__)


class StorageType(str, Enum):
    """存储类型"""
    MONGODB = "mongodb"
    LOCAL_FILE = "local_file"
    BOTH = "both"


@dataclass
class ConversationTurn:
    """对话轮次"""
    turn_id: str
    session_id: str
    user_id: Optional[str]
    user_input: str
    system_response: str
    timestamp: datetime
    query_type: str
    stage: str
    retrieved_context: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    understanding_level: Optional[str] = None
    topics: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationStorageManager:
    """对话存储管理器"""
    
    def __init__(self, storage_type: StorageType = StorageType.BOTH):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage_type = storage_type
        
        # 设置本地文件存储路径
        project_root = Path(__file__).parent.parent.parent
        self.data_dir = project_root / "data"
        self.conversations_dir = self.data_dir / "conversations"
        self.sessions_dir = self.data_dir / "sessions"
        
        # 确保目录存在
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.initialized = False
    
    async def initialize(self):
        """初始化存储管理器"""
        try:
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                await mongodb_service.initialize()
            
            self.initialized = True
            self.logger.info("对话存储管理器初始化成功")
            
        except Exception as e:
            self.logger.error(f"对话存储管理器初始化失败: {e}")
            raise
    
    async def save_conversation_turn(self, session_id: str, user_input: str, 
                                   system_response: str, user_id: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """保存对话轮次"""
        try:
            # 创建对话轮次对象
            turn = ConversationTurn(
                turn_id=f"{session_id}_{int(datetime.now().timestamp())}",
                session_id=session_id,
                user_id=user_id,
                user_input=user_input,
                system_response=system_response,
                timestamp=datetime.now(),
                query_type=metadata.get('query_type', 'normal') if metadata else 'normal',
                stage=metadata.get('stage', 'initial') if metadata else 'initial',
                retrieved_context=metadata.get('retrieved_context'),
                confidence_score=metadata.get('confidence_score'),
                understanding_level=metadata.get('understanding_level'),
                topics=metadata.get('topics', []),
                metadata=metadata
            )
            
            # 根据存储类型保存
            success = True
            
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                try:
                    await mongodb_service.save_conversation_turn(
                        session_id=session_id,
                        user_input=user_input,
                        system_response=system_response,
                        metadata=metadata or {}
                    )
                except Exception as e:
                    self.logger.error(f"保存到MongoDB失败: {e}")
                    success = False
            
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                try:
                    await self._save_turn_to_local_file(turn)
                except Exception as e:
                    self.logger.error(f"保存到本地文件失败: {e}")
                    success = False
            
            if success:
                self.logger.info(f"对话轮次保存成功: {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存对话轮次失败: {e}")
            return False
    
    async def create_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """创建新会话"""
        try:
            success = True
            
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                try:
                    await mongodb_service.create_session(session_id, user_id)
                except Exception as e:
                    self.logger.error(f"在MongoDB中创建会话失败: {e}")
                    success = False
            
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                try:
                    await self._save_session_to_local_file(session_id, user_id)
                except Exception as e:
                    self.logger.error(f"保存会话到本地文件失败: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"创建会话失败: {e}")
            return False
    
    async def end_session(self, session_id: str, metrics: Dict[str, Any]) -> bool:
        """结束会话"""
        try:
            success = True
            
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                try:
                    await mongodb_service.end_session(session_id, metrics)
                except Exception as e:
                    self.logger.error(f"在MongoDB中结束会话失败: {e}")
                    success = False
            
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                try:
                    await self._update_session_in_local_file(session_id, metrics)
                except Exception as e:
                    self.logger.error(f"更新本地会话文件失败: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"结束会话失败: {e}")
            return False
    
    async def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话历史"""
        try:
            # 优先从MongoDB获取
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                try:
                    session_data = await mongodb_service.get_session_history(session_id)
                    if session_data:
                        return session_data
                except Exception as e:
                    self.logger.warning(f"从MongoDB获取会话历史失败: {e}")
            
            # 从本地文件获取
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                try:
                    return await self._load_session_from_local_file(session_id)
                except Exception as e:
                    self.logger.warning(f"从本地文件获取会话历史失败: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取会话历史失败: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户会话历史"""
        try:
            sessions = []
            
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                try:
                    # 修复：直接调用MongoDB服务的方法
                    mongodb_sessions = await mongodb_service.get_user_sessions(user_id, limit)
                    # 确保返回的是字典列表而不是Document对象
                    if mongodb_sessions:
                        for session in mongodb_sessions:
                            if hasattr(session, 'dict'):
                                # 如果是Document对象，转换为字典
                                sessions.append(session.dict())
                            else:
                                # 如果已经是字典，直接添加
                                sessions.append(session)
                except Exception as e:
                    self.logger.warning(f"从MongoDB获取用户会话失败: {e}")
            
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                try:
                    local_sessions = await self._get_user_sessions_from_local_files(user_id, limit)
                    sessions.extend(local_sessions)
                except Exception as e:
                    self.logger.warning(f"从本地文件获取用户会话失败: {e}")
            
            # 去重并按时间排序
            unique_sessions = {}
            for session in sessions:
                session_id = session.get('session_id')
                if session_id and session_id not in unique_sessions:
                    unique_sessions[session_id] = session
            
            # 修复排序问题：确保start_time是字符串格式
            def get_start_time(session):
                start_time = session.get('start_time', '')
                if hasattr(start_time, 'isoformat'):
                    # 如果是datetime对象，转换为字符串
                    return start_time.isoformat()
                return str(start_time)
            
            sorted_sessions = sorted(
                unique_sessions.values(),
                key=get_start_time,
                reverse=True
            )
            
            return sorted_sessions[:limit]
            
        except Exception as e:
            self.logger.error(f"获取用户会话历史失败: {e}")
            return []
    
    async def _save_turn_to_local_file(self, turn: ConversationTurn):
        """保存对话轮次到本地文件"""
        try:
            # 创建会话目录
            session_dir = self.conversations_dir / turn.session_id
            session_dir.mkdir(exist_ok=True)
            
            # 保存轮次文件
            turn_file = session_dir / f"turn_{turn.turn_id}.json"
            
            # 转换datetime对象
            turn_data = asdict(turn)
            turn_data['timestamp'] = turn.timestamp.isoformat()
            
            with open(turn_file, 'w', encoding='utf-8') as f:
                json.dump(turn_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"对话轮次已保存到本地文件: {turn_file}")
            
        except Exception as e:
            self.logger.error(f"保存对话轮次到本地文件失败: {e}")
            raise
    
    async def _save_session_to_local_file(self, session_id: str, user_id: Optional[str]):
        """保存会话到本地文件"""
        try:
            session_file = self.sessions_dir / f"session_{session_id}.json"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'start_time': datetime.now().isoformat(),
                'turns': [],
                'total_turns': 0,
                'topics': [],
                'learning_objectives': [],
                'success_metrics': {}
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"会话已保存到本地文件: {session_file}")
            
        except Exception as e:
            self.logger.error(f"保存会话到本地文件失败: {e}")
            raise
    
    async def _load_session_from_local_file(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从本地文件加载会话"""
        try:
            session_file = self.sessions_dir / f"session_{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"从本地文件加载会话失败: {e}")
            return None
    
    async def _update_session_in_local_file(self, session_id: str, metrics: Dict[str, Any]):
        """更新本地会话文件"""
        try:
            session_file = self.sessions_dir / f"session_{session_id}.json"
            
            if not session_file.exists():
                return
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 更新会话信息
            session_data['end_time'] = datetime.now().isoformat()
            session_data['success_metrics'] = metrics
            session_data['final_understanding_level'] = metrics.get('final_understanding_level')
            session_data['session_summary'] = metrics.get('session_summary')
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"会话文件已更新: {session_file}")
            
        except Exception as e:
            self.logger.error(f"更新本地会话文件失败: {e}")
            raise
    
    async def _get_user_sessions_from_local_files(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """从本地文件获取用户会话"""
        try:
            sessions = []
            
            # 遍历所有会话文件
            for session_file in self.sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 检查是否属于该用户
                    if session_data.get('user_id') == user_id:
                        sessions.append(session_data)
                        
                except Exception as e:
                    self.logger.warning(f"读取会话文件失败: {session_file}, 错误: {e}")
                    continue
            
            # 按时间排序
            sessions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            self.logger.error(f"从本地文件获取用户会话失败: {e}")
            return []

    async def cleanup_old_sessions(self, days: int = 30):
        """清理旧会话数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理本地文件
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                await self._cleanup_local_sessions(cutoff_date)
            
            # 清理MongoDB（需要MongoDB服务支持）
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                await self._cleanup_mongodb_sessions(cutoff_date)
            
            self.logger.info(f"已清理 {days} 天前的会话数据")
            
        except Exception as e:
            self.logger.error(f"清理旧会话失败: {e}")
    
    async def _cleanup_local_sessions(self, cutoff_date: datetime):
        """清理本地会话文件"""
        try:
            count = 0
            for session_file in self.sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    start_time_str = session_data.get('start_time')
                    if start_time_str:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time < cutoff_date:
                            session_file.unlink()
                            count += 1
                            
                except Exception as e:
                    self.logger.warning(f"处理会话文件失败: {session_file}, 错误: {e}")
                    continue
            
            self.logger.info(f"已清理 {count} 个本地会话文件")
            
        except Exception as e:
            self.logger.error(f"清理本地会话失败: {e}")
    
    async def _cleanup_mongodb_sessions(self, cutoff_date: datetime):
        """清理MongoDB会话"""
        try:
            # 这里需要MongoDB服务提供清理功能
            # 暂时跳过，等待MongoDB服务支持
            self.logger.info("MongoDB会话清理功能待实现")
            
        except Exception as e:
            self.logger.error(f"清理MongoDB会话失败: {e}")

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """导出用户所有数据"""
        try:
            # 获取用户会话历史
            sessions = await self.get_user_sessions(user_id, limit=1000)  # 获取更多历史记录
            
            # 获取用户画像
            profile_context = {}
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                try:
                    profile_context = await mongodb_service.get_user_profile_context(user_id)
                except Exception as e:
                    self.logger.warning(f"获取MongoDB用户画像失败: {e}")
            
            # 从本地文件获取用户画像
            local_profile = None
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                try:
                    profile_file = self.data_dir / "user_profiles" / f"user_profile_{user_id}.json"
                    if profile_file.exists():
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            local_profile = json.load(f)
                except Exception as e:
                    self.logger.warning(f"获取本地用户画像失败: {e}")
            
            # 获取用户的对话轮次
            user_turns = await self._get_user_turns_from_local_files(user_id)
            
            export_data = {
                "user_id": user_id,
                "export_timestamp": datetime.now().isoformat(),
                "sessions": sessions,
                "profile_context": profile_context,
                "local_profile": local_profile,
                "conversation_turns": user_turns,
                "summary": {
                    "total_sessions": len(sessions),
                    "total_turns": len(user_turns),
                    "has_profile": bool(profile_context or local_profile)
                }
            }
            
            self.logger.info(f"用户数据导出成功: {user_id}")
            return export_data
            
        except Exception as e:
            self.logger.error(f"导出用户数据失败: {e}")
            return {"error": str(e)}

    async def _get_user_turns_from_local_files(self, user_id: str) -> List[Dict[str, Any]]:
        """从本地文件获取用户的所有对话轮次"""
        try:
            turns = []
            
            # 遍历所有会话目录
            for session_dir in self.conversations_dir.iterdir():
                if session_dir.is_dir():
                    # 检查会话是否属于该用户
                    session_file = self.sessions_dir / f"session_{session_dir.name}.json"
                    if session_file.exists():
                        try:
                            with open(session_file, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                            
                            if session_data.get('user_id') == user_id:
                                # 获取该会话的所有轮次
                                for turn_file in session_dir.glob("turn_*.json"):
                                    try:
                                        with open(turn_file, 'r', encoding='utf-8') as f:
                                            turn_data = json.load(f)
                                        turns.append(turn_data)
                                    except Exception as e:
                                        self.logger.warning(f"读取轮次文件失败: {turn_file}, 错误: {e}")
                                        continue
                        except Exception as e:
                            self.logger.warning(f"读取会话文件失败: {session_file}, 错误: {e}")
                            continue
            
            # 按时间排序
            turns.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return turns
            
        except Exception as e:
            self.logger.error(f"获取用户对话轮次失败: {e}")
            return []

    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            stats = {
                "storage_type": self.storage_type.value,
                "timestamp": datetime.now().isoformat(),
                "local_files": {},
                "mongodb": {}
            }
            
            # 本地文件统计
            if self.storage_type in [StorageType.LOCAL_FILE, StorageType.BOTH]:
                local_stats = await self._get_local_storage_stats()
                stats["local_files"] = local_stats
            
            # MongoDB统计
            if self.storage_type in [StorageType.MONGODB, StorageType.BOTH]:
                mongodb_stats = await self._get_mongodb_stats()
                stats["mongodb"] = mongodb_stats
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取存储统计失败: {e}")
            return {"error": str(e)}

    async def _get_local_storage_stats(self) -> Dict[str, Any]:
        """获取本地存储统计"""
        try:
            # 统计会话文件
            session_files = list(self.sessions_dir.glob("session_*.json"))
            total_sessions = len(session_files)
            
            # 统计对话轮次
            total_turns = 0
            for session_dir in self.conversations_dir.iterdir():
                if session_dir.is_dir():
                    turn_files = list(session_dir.glob("turn_*.json"))
                    total_turns += len(turn_files)
            
            # 统计用户画像文件
            profile_files = list(self.data_dir.glob("user_profiles/user_profile_*.json"))
            total_users = len(profile_files)
            
            # 计算存储大小
            total_size = 0
            for file_path in session_files + profile_files:
                if file_path.exists():
                    total_size += file_path.stat().st_size
            
            # 计算对话轮次文件大小
            for session_dir in self.conversations_dir.iterdir():
                if session_dir.is_dir():
                    for turn_file in session_dir.glob("turn_*.json"):
                        if turn_file.exists():
                            total_size += turn_file.stat().st_size
            
            return {
                "total_sessions": total_sessions,
                "total_turns": total_turns,
                "total_users": total_users,
                "storage_size_bytes": total_size,
                "storage_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"获取本地存储统计失败: {e}")
            return {"error": str(e)}

    async def _get_mongodb_stats(self) -> Dict[str, Any]:
        """获取MongoDB统计"""
        try:
            # 这里需要MongoDB服务提供统计功能
            # 暂时返回基本信息
            return {
                "status": "connected" if mongodb_service.initialized else "disconnected",
                "note": "详细统计功能待实现"
            }
            
        except Exception as e:
            self.logger.error(f"获取MongoDB统计失败: {e}")
            return {"error": str(e)}

    async def backup_data(self, backup_dir: Optional[str] = None) -> str:
        """备份所有数据"""
        try:
            if backup_dir is None:
                backup_dir = self.data_dir / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 备份会话文件
            sessions_backup_dir = backup_path / "sessions"
            sessions_backup_dir.mkdir(exist_ok=True)
            
            for session_file in self.sessions_dir.glob("session_*.json"):
                backup_file = sessions_backup_dir / session_file.name
                import shutil
                shutil.copy2(session_file, backup_file)
            
            # 备份对话轮次
            conversations_backup_dir = backup_path / "conversations"
            conversations_backup_dir.mkdir(exist_ok=True)
            
            for session_dir in self.conversations_dir.iterdir():
                if session_dir.is_dir():
                    session_backup_dir = conversations_backup_dir / session_dir.name
                    session_backup_dir.mkdir(exist_ok=True)
                    
                    for turn_file in session_dir.glob("turn_*.json"):
                        backup_file = session_backup_dir / turn_file.name
                        import shutil
                        shutil.copy2(turn_file, backup_file)
            
            # 备份用户画像
            profiles_backup_dir = backup_path / "user_profiles"
            profiles_backup_dir.mkdir(exist_ok=True)
            
            for profile_file in self.data_dir.glob("user_profiles/user_profile_*.json"):
                backup_file = profiles_backup_dir / profile_file.name
                import shutil
                shutil.copy2(profile_file, backup_file)
            
            self.logger.info(f"数据备份完成: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"数据备份失败: {e}")
            raise

    async def restore_data(self, backup_dir: str) -> bool:
        """从备份恢复数据"""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                raise ValueError(f"备份目录不存在: {backup_dir}")
            
            # 恢复会话文件
            sessions_backup_dir = backup_path / "sessions"
            if sessions_backup_dir.exists():
                for backup_file in sessions_backup_dir.glob("session_*.json"):
                    restore_file = self.sessions_dir / backup_file.name
                    import shutil
                    shutil.copy2(backup_file, restore_file)
            
            # 恢复对话轮次
            conversations_backup_dir = backup_path / "conversations"
            if conversations_backup_dir.exists():
                for session_backup_dir in conversations_backup_dir.iterdir():
                    if session_backup_dir.is_dir():
                        session_restore_dir = self.conversations_dir / session_backup_dir.name
                        session_restore_dir.mkdir(exist_ok=True)
                        
                        for backup_file in session_backup_dir.glob("turn_*.json"):
                            restore_file = session_restore_dir / backup_file.name
                            import shutil
                            shutil.copy2(backup_file, restore_file)
            
            # 恢复用户画像
            profiles_backup_dir = backup_path / "user_profiles"
            if profiles_backup_dir.exists():
                for backup_file in profiles_backup_dir.glob("user_profile_*.json"):
                    restore_file = self.data_dir / "user_profiles" / backup_file.name
                    import shutil
                    shutil.copy2(backup_file, restore_file)
            
            self.logger.info(f"数据恢复完成: {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据恢复失败: {e}")
            return False


# 全局存储管理器实例
conversation_storage_manager = ConversationStorageManager(StorageType.BOTH) 