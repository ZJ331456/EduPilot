#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像仓储
管理用户画像数据的持久化
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ..base import BaseRepository, BaseEntity, EntityNotFoundError
from ..adapters import StorageAdapter


@dataclass
class UserProfile(BaseEntity):
    """用户画像实体"""
    user_id: str
    
    # 三元组知识图谱
    triples: List[Dict[str, Any]] = field(default_factory=list)
    
    # 情感历史
    emotions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 学习模式
    learning_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # 画像洞察
    insights: List[Dict[str, Any]] = field(default_factory=list)
    
    # 统计信息
    total_sessions: int = 0
    total_interactions: int = 0
    average_understanding_level: float = 0.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            "user_id": self.user_id,
            "triples": self.triples,
            "emotions": self.emotions,
            "learning_patterns": self.learning_patterns,
            "insights": self.insights,
            "total_sessions": self.total_sessions,
            "total_interactions": self.total_interactions,
            "average_understanding_level": self.average_understanding_level,
            "metadata": self.metadata,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """从字典创建实体"""
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            user_id=data["user_id"],
            triples=data.get("triples", []),
            emotions=data.get("emotions", []),
            learning_patterns=data.get("learning_patterns", []),
            insights=data.get("insights", []),
            total_sessions=data.get("total_sessions", 0),
            total_interactions=data.get("total_interactions", 0),
            average_understanding_level=data.get("average_understanding_level", 0.0),
            metadata=data.get("metadata", {}),
        )


class UserProfileRepository(BaseRepository[UserProfile]):
    """用户画像仓储"""
    
    def __init__(self, storage_adapter: StorageAdapter):
        """初始化仓储
        
        Args:
            storage_adapter: 存储适配器
        """
        self.storage = storage_adapter
        self.logger = logging.getLogger(self.__class__.__name__)
        self._key_prefix = "user_profile:"
    
    def _make_key(self, user_id: str) -> str:
        """生成存储键"""
        return f"{self._key_prefix}{user_id}"
    
    async def save(self, entity: UserProfile) -> UserProfile:
        """保存用户画像"""
        entity.updated_at = datetime.now()
        key = self._make_key(entity.user_id)
        
        success = await self.storage.save_data(key, entity.to_dict())
        
        if not success:
            raise Exception(f"保存用户画像失败: {entity.user_id}")
        
        return entity
    
    async def find_by_id(self, entity_id: str) -> Optional[UserProfile]:
        """根据 ID 查找用户画像"""
        return await self.find_by_user_id(entity_id)
    
    async def find_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """根据用户 ID 查找画像"""
        key = self._make_key(user_id)
        data = await self.storage.load_data(key)
        
        if data:
            return UserProfile.from_dict(data)
        
        return None
    
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters
    ) -> List[UserProfile]:
        """查找所有用户画像"""
        keys = await self.storage.list_keys(self._key_prefix)
        profiles = []
        
        for key in keys[offset:offset + limit] if limit else keys[offset:]:
            data = await self.storage.load_data(key)
            if data:
                profiles.append(UserProfile.from_dict(data))
        
        return profiles
    
    async def update(self, entity: UserProfile) -> UserProfile:
        """更新用户画像"""
        if not await self.exists(entity.user_id):
            raise EntityNotFoundError(f"用户画像不存在: {entity.user_id}")
        
        return await self.save(entity)
    
    async def delete(self, entity_id: str) -> bool:
        """删除用户画像"""
        key = self._make_key(entity_id)
        return await self.storage.delete_data(key)
    
    async def exists(self, entity_id: str) -> bool:
        """检查用户画像是否存在"""
        key = self._make_key(entity_id)
        return await self.storage.exists_data(key)
    
    async def count(self, **filters) -> int:
        """统计用户画像数量"""
        keys = await self.storage.list_keys(self._key_prefix)
        return len(keys)

