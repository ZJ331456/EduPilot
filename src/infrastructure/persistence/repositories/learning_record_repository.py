#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习记录仓储
管理学习记录数据的持久化
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..base import BaseRepository, BaseEntity, EntityNotFoundError
from ..adapters import StorageAdapter


@dataclass
class LearningRecord(BaseEntity):
    """学习记录实体"""
    record_id: str
    user_id: str
    session_id: str
    
    # 学习分析
    interaction_analysis: Dict[str, Any] = field(default_factory=dict)
    profile_update: Dict[str, Any] = field(default_factory=dict)
    learning_feedback: Dict[str, Any] = field(default_factory=dict)
    knowledge_gaps: List[Dict[str, Any]] = field(default_factory=list)
    
    # 效果评估
    quality_score: float = 0.0
    engagement_level: float = 0.0
    learning_value: float = 0.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            "record_id": self.record_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "interaction_analysis": self.interaction_analysis,
            "profile_update": self.profile_update,
            "learning_feedback": self.learning_feedback,
            "knowledge_gaps": self.knowledge_gaps,
            "quality_score": self.quality_score,
            "engagement_level": self.engagement_level,
            "learning_value": self.learning_value,
            "metadata": self.metadata,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningRecord':
        """从字典创建实体"""
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            record_id=data["record_id"],
            user_id=data["user_id"],
            session_id=data["session_id"],
            interaction_analysis=data.get("interaction_analysis", {}),
            profile_update=data.get("profile_update", {}),
            learning_feedback=data.get("learning_feedback", {}),
            knowledge_gaps=data.get("knowledge_gaps", []),
            quality_score=data.get("quality_score", 0.0),
            engagement_level=data.get("engagement_level", 0.0),
            learning_value=data.get("learning_value", 0.0),
            metadata=data.get("metadata", {}),
        )


class LearningRecordRepository(BaseRepository[LearningRecord]):
    """学习记录仓储"""
    
    def __init__(self, storage_adapter: StorageAdapter):
        """初始化仓储"""
        self.storage = storage_adapter
        self.logger = logging.getLogger(self.__class__.__name__)
        self._key_prefix = "learning_record:"
    
    def _make_key(self, record_id: str) -> str:
        """生成存储键"""
        return f"{self._key_prefix}{record_id}"
    
    async def save(self, entity: LearningRecord) -> LearningRecord:
        """保存学习记录"""
        entity.updated_at = datetime.now()
        key = self._make_key(entity.record_id)
        
        success = await self.storage.save_data(key, entity.to_dict())
        if not success:
            raise Exception(f"保存学习记录失败: {entity.record_id}")
        
        return entity
    
    async def find_by_id(self, entity_id: str) -> Optional[LearningRecord]:
        """根据 ID 查找学习记录"""
        key = self._make_key(entity_id)
        data = await self.storage.load_data(key)
        
        if data:
            return LearningRecord.from_dict(data)
        
        return None
    
    async def find_by_user_id(self, user_id: str, limit: int = 20) -> List[LearningRecord]:
        """查找用户的学习记录"""
        all_keys = await self.storage.list_keys(self._key_prefix)
        user_records = []
        
        for key in all_keys:
            data = await self.storage.load_data(key)
            if data and data.get("user_id") == user_id:
                user_records.append(LearningRecord.from_dict(data))
                if len(user_records) >= limit:
                    break
        
        return user_records
    
    async def find_by_session_id(self, session_id: str) -> Optional[LearningRecord]:
        """根据会话 ID 查找学习记录"""
        all_keys = await self.storage.list_keys(self._key_prefix)
        
        for key in all_keys:
            data = await self.storage.load_data(key)
            if data and data.get("session_id") == session_id:
                return LearningRecord.from_dict(data)
        
        return None
    
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters
    ) -> List[LearningRecord]:
        """查找所有学习记录"""
        keys = await self.storage.list_keys(self._key_prefix)
        records = []
        
        for key in keys[offset:offset + limit] if limit else keys[offset:]:
            data = await self.storage.load_data(key)
            if data:
                records.append(LearningRecord.from_dict(data))
        
        return records
    
    async def update(self, entity: LearningRecord) -> LearningRecord:
        """更新学习记录"""
        if not await self.exists(entity.record_id):
            raise EntityNotFoundError(f"学习记录不存在: {entity.record_id}")
        
        return await self.save(entity)
    
    async def delete(self, entity_id: str) -> bool:
        """删除学习记录"""
        key = self._make_key(entity_id)
        return await self.storage.delete_data(key)
    
    async def exists(self, entity_id: str) -> bool:
        """检查学习记录是否存在"""
        key = self._make_key(entity_id)
        return await self.storage.exists_data(key)
    
    async def count(self, **filters) -> int:
        """统计学习记录数量"""
        keys = await self.storage.list_keys(self._key_prefix)
        return len(keys)

