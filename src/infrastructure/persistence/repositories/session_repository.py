#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话仓储
管理学习会话数据的持久化
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..base import BaseRepository, BaseEntity, EntityNotFoundError
from ..adapters import StorageAdapter


@dataclass
class Session(BaseEntity):
    """会话实体"""
    session_id: str
    user_id: str
    
    # 对话信息
    query: str
    dialogue_history: List[Dict[str, str]] = field(default_factory=list)
    
    # 会话状态
    conversation_stage: str = "initial_query"
    understanding_level: str = "no_understanding"
    conversation_round: int = 0
    
    # 检索和执行结果
    query_analysis: Dict[str, Any] = field(default_factory=dict)
    knowledge_retrieval: Dict[str, Any] = field(default_factory=dict)
    socratic_dialogue: Dict[str, Any] = field(default_factory=dict)
    understanding_tracking: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query": self.query,
            "dialogue_history": self.dialogue_history,
            "conversation_stage": self.conversation_stage,
            "understanding_level": self.understanding_level,
            "conversation_round": self.conversation_round,
            "query_analysis": self.query_analysis,
            "knowledge_retrieval": self.knowledge_retrieval,
            "socratic_dialogue": self.socratic_dialogue,
            "understanding_tracking": self.understanding_tracking,
            "metadata": self.metadata,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建实体"""
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            session_id=data["session_id"],
            user_id=data["user_id"],
            query=data.get("query", ""),
            dialogue_history=data.get("dialogue_history", []),
            conversation_stage=data.get("conversation_stage", "initial_query"),
            understanding_level=data.get("understanding_level", "no_understanding"),
            conversation_round=data.get("conversation_round", 0),
            query_analysis=data.get("query_analysis", {}),
            knowledge_retrieval=data.get("knowledge_retrieval", {}),
            socratic_dialogue=data.get("socratic_dialogue", {}),
            understanding_tracking=data.get("understanding_tracking", {}),
            metadata=data.get("metadata", {}),
        )


class SessionRepository(BaseRepository[Session]):
    """会话仓储"""
    
    def __init__(self, storage_adapter: StorageAdapter):
        """初始化仓储"""
        self.storage = storage_adapter
        self.logger = logging.getLogger(self.__class__.__name__)
        self._key_prefix = "session:"
    
    def _make_key(self, session_id: str) -> str:
        """生成存储键"""
        return f"{self._key_prefix}{session_id}"
    
    async def save(self, entity: Session) -> Session:
        """保存会话"""
        entity.updated_at = datetime.now()
        key = self._make_key(entity.session_id)
        
        success = await self.storage.save_data(key, entity.to_dict())
        if not success:
            raise Exception(f"保存会话失败: {entity.session_id}")
        
        return entity
    
    async def find_by_id(self, entity_id: str) -> Optional[Session]:
        """根据 ID 查找会话"""
        key = self._make_key(entity_id)
        data = await self.storage.load_data(key)
        
        if data:
            return Session.from_dict(data)
        
        return None
    
    async def find_by_user_id(self, user_id: str, limit: int = 10) -> List[Session]:
        """查找用户的所有会话"""
        all_keys = await self.storage.list_keys(self._key_prefix)
        user_sessions = []
        
        for key in all_keys:
            data = await self.storage.load_data(key)
            if data and data.get("user_id") == user_id:
                user_sessions.append(Session.from_dict(data))
                if len(user_sessions) >= limit:
                    break
        
        return user_sessions
    
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters
    ) -> List[Session]:
        """查找所有会话"""
        keys = await self.storage.list_keys(self._key_prefix)
        sessions = []
        
        for key in keys[offset:offset + limit] if limit else keys[offset:]:
            data = await self.storage.load_data(key)
            if data:
                sessions.append(Session.from_dict(data))
        
        return sessions
    
    async def update(self, entity: Session) -> Session:
        """更新会话"""
        if not await self.exists(entity.session_id):
            raise EntityNotFoundError(f"会话不存在: {entity.session_id}")
        
        return await self.save(entity)
    
    async def delete(self, entity_id: str) -> bool:
        """删除会话"""
        key = self._make_key(entity_id)
        return await self.storage.delete_data(key)
    
    async def exists(self, entity_id: str) -> bool:
        """检查会话是否存在"""
        key = self._make_key(entity_id)
        return await self.storage.exists_data(key)
    
    async def count(self, **filters) -> int:
        """统计会话数量"""
        keys = await self.storage.list_keys(self._key_prefix)
        return len(keys)

