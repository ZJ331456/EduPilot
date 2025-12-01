#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像管理器 - 负责用户画像的维护和更新
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from src.infrastructure.utils import AgentState


class ProfileManager:
    """用户画像管理器
    
    职责：
    1. 维护用户画像缓存
    2. 更新用户三元组
    3. 管理实体关系图谱
    4. 提供画像查询接口
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.profiles_cache = {}  # 用户画像缓存
        self.triples_store = defaultdict(list)  # 三元组存储
        self.entity_set = set()  # 实体集合
    
    def get_or_create_profile(self, user_id: str) -> Dict[str, Any]:
        """获取或创建用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户画像数据
        """
        if user_id not in self.profiles_cache:
            self.profiles_cache[user_id] = self._create_new_profile()
        
        return self.profiles_cache[user_id]
    
    def update_profile(
        self, 
        user_id: str, 
        triples: List[Dict], 
        emotion: Dict, 
        patterns: List[Dict],
        insights: List[Dict]
    ):
        """更新用户画像
        
        Args:
            user_id: 用户ID
            triples: 新增的三元组
            emotion: 情感分析结果
            patterns: 学习模式
            insights: 画像洞察
        """
        profile = self.get_or_create_profile(user_id)
        
        # 更新三元组
        profile['triples'].extend(triples)
        
        # 更新情感历史
        profile['emotions'].append(emotion)
        
        # 更新学习模式
        profile['learning_patterns'].extend(patterns)
        
        # 更新洞察
        profile['insights'].extend(insights)
        
        # 更新时间戳
        profile['updated_at'] = datetime.now().isoformat()
        
        # 更新图谱存储
        for triple in triples:
            self._add_triple_to_graph(user_id, triple)
    
    def _create_new_profile(self) -> Dict[str, Any]:
        """创建新的用户画像"""
        return {
            'created_at': datetime.now().isoformat(),
            'triples': [],
            'emotions': [],
            'learning_patterns': [],
            'insights': []
        }
    
    def _add_triple_to_graph(self, user_id: str, triple: Dict[str, Any]):
        """添加三元组到图谱"""
        key = f"{user_id}:{triple['subject']}:{triple['predicate']}"
        self.triples_store[key].append(triple)
        
        # 更新实体集合
        self.entity_set.add(triple['subject'])
        self.entity_set.add(triple['object'])
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        return self.profiles_cache.get(user_id)
    
    def get_user_triples(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有三元组"""
        profile = self.get_profile(user_id)
        if profile:
            return profile.get('triples', [])
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_users': len(self.profiles_cache),
            'total_entities': len(self.entity_set),
            'total_triples': sum(len(v) for v in self.triples_store.values())
        }

