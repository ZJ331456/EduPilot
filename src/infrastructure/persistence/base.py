#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化层基础接口
定义 Repository 模式的抽象接口
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================================
# 异常定义
# ============================================================================

class RepositoryError(Exception):
    """仓储层基础异常"""
    pass


class EntityNotFoundError(RepositoryError):
    """实体未找到异常"""
    pass


class DuplicateEntityError(RepositoryError):
    """实体重复异常"""
    pass


# ============================================================================
# 基础实体
# ============================================================================

@dataclass
class BaseEntity:
    """基础实体类
    
    所有实体都应继承此类
    """
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """从字典创建实体"""
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


# ============================================================================
# Repository 抽象接口
# ============================================================================

T = TypeVar('T', bound=BaseEntity)


class BaseRepository(Generic[T], ABC):
    """Repository 抽象基类
    
    定义标准的 CRUD 操作接口
    采用 Repository 模式，将数据访问逻辑从业务逻辑中分离
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体
        
        Args:
            entity: 要保存的实体
            
        Returns:
            T: 保存后的实体
            
        Raises:
            RepositoryError: 保存失败
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[T]:
        """根据 ID 查找实体
        
        Args:
            entity_id: 实体 ID
            
        Returns:
            Optional[T]: 找到的实体，不存在返回 None
        """
        pass
    
    @abstractmethod
    async def find_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters
    ) -> List[T]:
        """查找所有实体
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            **filters: 过滤条件
            
        Returns:
            List[T]: 实体列表
        """
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新实体
        
        Args:
            entity: 要更新的实体
            
        Returns:
            T: 更新后的实体
            
        Raises:
            EntityNotFoundError: 实体不存在
            RepositoryError: 更新失败
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """删除实体
        
        Args:
            entity_id: 要删除的实体 ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """检查实体是否存在
        
        Args:
            entity_id: 实体 ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def count(self, **filters) -> int:
        """统计实体数量
        
        Args:
            **filters: 过滤条件
            
        Returns:
            int: 实体数量
        """
        pass


# ============================================================================
# 存储适配器接口
# ============================================================================

class StorageAdapter(ABC):
    """存储适配器抽象接口
    
    定义不同存储后端的统一接口
    """
    
    @abstractmethod
    async def connect(self):
        """连接存储"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开存储连接"""
        pass
    
    @abstractmethod
    async def save_data(self, key: str, data: Dict[str, Any]) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        pass
    
    @abstractmethod
    async def delete_data(self, key: str) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    async def exists_data(self, key: str) -> bool:
        """检查数据是否存在"""
        pass
    
    @abstractmethod
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """列出所有键"""
        pass

