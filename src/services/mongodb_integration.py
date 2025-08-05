#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB集成服务
整合对话记录存储和用户画像管理
"""

import logging
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from config.database import db_manager
from services.storage_service import storage_service

logger = logging.getLogger(__name__)


class MongoDBIntegrationService:
    """MongoDB集成服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage = storage_service
        self.initialized = False
        
        # 设置本地文件存储路径 - 使用项目根目录
        project_root = Path(__file__).parent.parent.parent  # 从src/services/回到项目根目录
        self.data_dir = project_root / "data"
        self.user_profiles_dir = self.data_dir / "user_profiles"
        self.conversations_dir = self.data_dir / "conversations"
        self.sessions_dir = self.data_dir / "sessions"
        
        # 确保目录存在
        self.user_profiles_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """初始化服务"""
        try:
            await db_manager.connect()
            
            # 初始化 Beanie ODM
            from models.database_models import DOCUMENT_MODELS
            await db_manager.initialize_beanie(DOCUMENT_MODELS)
            
            await self.storage.initialize()
            self.initialized = True
            self.logger.info("MongoDB集成服务初始化成功")
        except Exception as e:
            self.logger.error(f"MongoDB集成服务初始化失败: {e}")
            raise
    
    async def save_conversation_turn(self, session_id: str, user_input: str, 
                                   system_response: str, metadata: Dict[str, Any]) -> bool:
        """保存对话轮次"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # 提取分类信息
            query_type = metadata.get('query_type', 'normal')
            classification = metadata.get('classification', {})
            stage = metadata.get('conversation_stage', 'initial')
            
            # 保存到对话记录
            success = await self.storage.add_conversation_turn(
                session_id=session_id,
                user_input=user_input,
                system_response=system_response,
                query_type=query_type,
                stage=stage,
                retrieved_context=metadata.get('retrieved_context'),
                confidence_score=classification.get('confidence'),
                understanding_level=metadata.get('understanding_level'),
                topics=metadata.get('topics', [])
            )
            
            # 更新用户画像
            if metadata.get('user_id'):
                await self._update_user_profile_from_interaction(
                    metadata['user_id'], user_input, system_response, metadata
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存对话轮次失败: {e}")
            return False
    
    async def create_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """创建新会话"""
        if not self.initialized:
            await self.initialize()
        
        try:
            session = await self.storage.create_session(session_id, user_id)
            return session is not None
        except Exception as e:
            self.logger.error(f"创建会话失败: {e}")
            return False
    
    async def end_session(self, session_id: str, metrics: Dict[str, Any]) -> bool:
        """结束会话"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.storage.end_session(
                session_id=session_id,
                success_metrics=metrics,
                final_understanding_level=metrics.get('final_understanding_level'),
                session_summary=metrics.get('session_summary')
            )
        except Exception as e:
            self.logger.error(f"结束会话失败: {e}")
            return False
    
    async def get_user_profile_context(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像上下文"""
        try:
            # 首先尝试从本地文件读取
            local_profile = await self._load_user_profile_from_file(user_id)
            if local_profile:
                self.logger.info(f"从本地文件获取用户画像: {user_id}")
                
                # 计算实体数量和关系数量
                triples = local_profile.get('triples', [])
                entity_count = len(set([t['subject'] for t in triples] + [t['object'] for t in triples]))
                relation_count = len(set([t['predicate'] for t in triples]))
                
                # 添加图统计信息
                context = {
                    'entity_count': entity_count,
                    'relation_count': relation_count,
                    'profile_completeness': local_profile.get('profile_completeness', 0.0),
                    'user_summary': local_profile.get('user_summary', '暂无用户画像信息'),
                    'user_entities': list(set([t['subject'] for t in triples] + [t['object'] for t in triples])),
                    'total_conversations': len(triples),
                    'learning_preferences': local_profile.get('learning_preferences', []),
                    'socratic_preference_score': local_profile.get('socratic_preference_score', 0.0),
                    'average_session_duration': local_profile.get('average_session_duration', 0.0),
                    'emotions': local_profile.get('emotions', []),
                    'learning_patterns': local_profile.get('learning_patterns', []),
                    'insights': local_profile.get('insights', [])
                }
                
                return context
            
            # 如果本地文件不存在，尝试从MongoDB读取
            if not self.initialized:
                await self.initialize()
            
            profile = await self.storage.create_or_get_profile(user_id)
            
            # 构建上下文
            context = {
                'entity_count': 0,
                'relation_count': 0,
                'socratic_preference_score': profile.socratic_preference_score,
                'learning_preferences': [pref.value for pref in profile.learning_preferences],
                'preferred_query_type': profile.preferred_query_type.value if profile.preferred_query_type else None,
                'total_conversations': profile.total_conversations,
                'average_session_duration': profile.average_session_duration,
                'learning_patterns': [
                    {
                        'type': pattern.pattern_type,
                        'confidence': pattern.confidence
                    } for pattern in profile.learning_patterns
                ],
                'topic_mastery': [
                    {
                        'topic': mastery.topic,
                        'level': mastery.mastery_level.value,
                        'confidence': mastery.confidence
                    } for mastery in profile.topic_mastery
                ],
                'current_recommendations': profile.current_recommendations
            }
            
            # 保存到本地文件作为备份
            await self._save_user_profile_to_file(user_id, context)
            
            return context
            
        except Exception as e:
            self.logger.error(f"获取用户画像上下文失败: {e}")
            return {
                'entity_count': 0,
                'relation_count': 0,
                'profile_completeness': 0.0,
                'user_summary': '暂无用户画像信息',
                'user_entities': [],
                'total_conversations': 0,
                'learning_preferences': [],
                'socratic_preference_score': 0.0,
                'average_session_duration': 0.0,
                'emotions': [],
                'learning_patterns': [],
                'insights': []
            }
    
    async def _update_user_profile_from_interaction(self, user_id: str, user_input: str, 
                                                   system_response: str, metadata: Dict[str, Any]):
        """从交互中更新用户画像"""
        try:
            # 更新对话统计
            session_duration = metadata.get('session_duration', 0)
            query_types = metadata.get('query_types', [])
            
            await self.storage.update_conversation_stats(
                user_id=user_id,
                session_duration=session_duration,
                query_types=query_types
            )
            
            # 更新学习模式
            if 'learning_pattern' in metadata:
                pattern = metadata['learning_pattern']
                await self.storage.update_learning_pattern(
                    user_id=user_id,
                    pattern_type=pattern['type'],
                    confidence=pattern['confidence'],
                    evidence_count=pattern.get('evidence_count', 1)
                )
            
            # 更新主题掌握
            if 'topics' in metadata and 'understanding_level' in metadata:
                for topic in metadata['topics']:
                    await self.storage.update_topic_mastery(
                        user_id=user_id,
                        topic=topic,
                        mastery_level=metadata['understanding_level'],
                        confidence=metadata.get('confidence_score', 0.5)
                    )
            
            # 添加学习洞察
            if 'insights' in metadata:
                for insight in metadata['insights']:
                    await self.storage.add_learning_insight(
                        user_id=user_id,
                        insight_type=insight['type'],
                        description=insight['description'],
                        confidence=insight['confidence'],
                        evidence=insight.get('evidence', []),
                        recommendations=insight.get('recommendations', [])
                    )
            
        except Exception as e:
            self.logger.error(f"更新用户画像失败: {e}")
    
    async def save_knowledge_query(self, query_data: Dict[str, Any]) -> bool:
        """保存知识查询记录"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.storage.save_query(query_data)
        except Exception as e:
            self.logger.error(f"保存知识查询失败: {e}")
            return False
    
    async def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话历史"""
        if not self.initialized:
            await self.initialize()
        
        try:
            session = await self.storage.conversation_service.get_session(session_id)
            if session:
                return {
                    'session_id': session.session_id,
                    'user_id': session.user_id,
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'total_turns': session.total_turns,
                    'topics': session.topics,
                    'success_metrics': session.success_metrics,
                    'turns': [
                        {
                            'user_input': turn.user_input,
                            'system_response': turn.system_response,
                            'query_type': turn.query_type.value,
                            'timestamp': turn.timestamp,
                            'stage': turn.stage.value
                        } for turn in session.turns
                    ]
                }
            return None
        except Exception as e:
            self.logger.error(f"获取会话历史失败: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户会话历史"""
        if not self.initialized:
            await self.initialize()
        
        try:
            sessions = await self.storage.get_user_sessions(user_id, limit)
            return sessions
        except Exception as e:
            self.logger.error(f"获取用户会话历史失败: {e}")
            return []
    
    async def clear_user_profile(self, user_id: str) -> bool:
        """清空用户画像"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # 清空用户画像数据
            success = await self.storage.clear_user_profile(user_id)
            self.logger.info(f"用户画像清空成功: {user_id}")
            return success
        except Exception as e:
            self.logger.error(f"清空用户画像失败: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            await db_manager.disconnect()
            self.initialized = False
            self.logger.info("MongoDB集成服务已清理")
        except Exception as e:
            self.logger.error(f"清理MongoDB集成服务失败: {e}")
    
    async def save_user_profile_to_file(self, user_id: str, profile_data: Dict[str, Any]):
        """保存用户画像到本地文件"""
        try:
            file_path = self.user_profiles_dir / f"user_profile_{user_id}.json"
            
            # 处理datetime对象
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2, default=datetime_handler)
            
            self.logger.info(f"用户画像已保存到本地文件: {file_path}")
        except Exception as e:
            self.logger.error(f"保存用户画像到本地文件失败: {e}")
    
    async def _save_user_profile_to_file(self, user_id: str, profile_data: Dict[str, Any]):
        """保存用户画像到本地文件（私有方法，保持向后兼容）"""
        return await self.save_user_profile_to_file(user_id, profile_data)
    
    async def _load_user_profile_from_file(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从本地文件加载用户画像"""
        try:
            file_path = self.user_profiles_dir / f"user_profile_{user_id}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                self.logger.info(f"从本地文件加载用户画像: {file_path}")
                return profile_data
            return None
        except Exception as e:
            self.logger.error(f"从本地文件加载用户画像失败: {e}")
            return None
    
    async def _save_conversation_to_file(self, session_id: str, conversation_data: Dict[str, Any]):
        """保存对话记录到本地文件"""
        try:
            file_path = self.conversations_dir / f"conversation_{session_id}.json"
            
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2, default=datetime_handler)
            
            self.logger.info(f"对话记录已保存到本地文件: {file_path}")
        except Exception as e:
            self.logger.error(f"保存对话记录到本地文件失败: {e}")


# 全局MongoDB集成服务实例
mongodb_service = MongoDBIntegrationService()
