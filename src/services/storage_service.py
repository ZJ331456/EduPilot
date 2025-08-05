#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据存储服务
负责对话记录和用户画像的MongoDB存储
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.database_models import (
    ConversationSession, ConversationTurn, UserProfile, 
    KnowledgeQuery, SystemMetrics, QueryType, ConversationStage,
    LearningPattern, TopicMastery, LearningInsight
)
from config.database import get_database

logger = logging.getLogger(__name__)


class ConversationStorageService:
    """对话存储服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def initialize(self):
        """初始化服务"""
        self.db = await get_database()
        self.logger.info("Conversation storage service initialized")
    
    async def create_session(self, session_id: str, user_id: Optional[str] = None) -> ConversationSession:
        """创建新的对话会话"""
        try:
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                turns=[],
                total_turns=0,
                topics=[],
                learning_objectives=[],
                success_metrics={}
            )
            
            await session.create()
            self.logger.info(f"Created conversation session: {session_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create session {session_id}: {e}")
            raise
    
    async def add_conversation_turn(self, session_id: str, user_input: str, 
                                 system_response: str, query_type: QueryType,
                                 stage: ConversationStage, **kwargs) -> bool:
        """添加对话轮次"""
        try:
            session = await ConversationSession.find_one(
                ConversationSession.session_id == session_id
            )
            
            if not session:
                self.logger.error(f"Session not found: {session_id}")
                return False
            
            turn = ConversationTurn(
                user_input=user_input,
                system_response=system_response,
                query_type=query_type,
                timestamp=datetime.now(),
                stage=stage,
                retrieved_context=kwargs.get('retrieved_context'),
                confidence_score=kwargs.get('confidence_score'),
                understanding_level=kwargs.get('understanding_level')
            )
            
            session.turns.append(turn)
            session.total_turns += 1
            
            # 更新主题
            if 'topics' in kwargs:
                new_topics = kwargs['topics']
                session.topics.extend([t for t in new_topics if t not in session.topics])
            
            await session.save()
            self.logger.debug(f"Added turn to session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add turn to session {session_id}: {e}")
            return False
    
    async def end_session(self, session_id: str, success_metrics: Dict[str, Any],
                         final_understanding_level: Optional[str] = None,
                         session_summary: Optional[str] = None) -> bool:
        """结束对话会话"""
        try:
            session = await ConversationSession.find_one(
                ConversationSession.session_id == session_id
            )
            
            if not session:
                return False
            
            session.end_time = datetime.now()
            session.success_metrics = success_metrics
            session.final_understanding_level = final_understanding_level
            session.session_summary = session_summary
            
            await session.save()
            self.logger.info(f"Ended session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """获取对话会话"""
        try:
            return await ConversationSession.find_one(
                ConversationSession.session_id == session_id
            )
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[ConversationSession]:
        """获取用户的对话会话"""
        try:
            sessions = await ConversationSession.find(
                ConversationSession.user_id == user_id
            ).sort(-ConversationSession.start_time).limit(limit).to_list()
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []


class UserProfileStorageService:
    """用户画像存储服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def initialize(self):
        """初始化服务"""
        self.db = await get_database()
        self.logger.info("User profile storage service initialized")
    
    async def create_or_get_profile(self, user_id: str) -> UserProfile:
        """创建或获取用户画像"""
        try:
            # 尝试获取现有画像
            profile = await UserProfile.find_one(UserProfile.user_id == user_id)
            
            if profile:
                return profile
            
            # 创建新画像
            profile = UserProfile(
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                learning_preferences={},
                learning_patterns=[],
                topic_mastery=[],
                current_insights=[],
                current_recommendations=[]
            )
            
            await profile.create()
            self.logger.info(f"Created user profile: {user_id}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to create/get profile for {user_id}: {e}")
            raise
    
    async def update_learning_pattern(self, user_id: str, pattern_type: str, 
                                    confidence: float, evidence_count: int) -> bool:
        """更新学习模式"""
        try:
            profile = await self.create_or_get_profile(user_id)
            
            # 查找现有模式
            existing_pattern = None
            for pattern in profile.learning_patterns:
                if pattern.pattern_type == pattern_type:
                    existing_pattern = pattern
                    break
            
            if existing_pattern:
                # 更新现有模式
                existing_pattern.confidence = confidence
                existing_pattern.evidence_count = evidence_count
                existing_pattern.last_updated = datetime.now()
            else:
                # 添加新模式
                new_pattern = LearningPattern(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    evidence_count=evidence_count,
                    last_updated=datetime.now()
                )
                profile.learning_patterns.append(new_pattern)
            
            profile.updated_at = datetime.now()
            await profile.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update learning pattern for {user_id}: {e}")
            return False
    
    async def update_topic_mastery(self, user_id: str, topic: str, 
                                 mastery_level: str, confidence: float) -> bool:
        """更新主题掌握程度"""
        try:
            profile = await self.create_or_get_profile(user_id)
            
            # 查找现有主题
            existing_mastery = None
            for mastery in profile.topic_mastery:
                if mastery.topic == topic:
                    existing_mastery = mastery
                    break
            
            if existing_mastery:
                # 更新现有掌握度
                old_level = existing_mastery.mastery_level
                existing_mastery.mastery_level = mastery_level
                existing_mastery.confidence = confidence
                existing_mastery.interaction_count += 1
                existing_mastery.last_interaction = datetime.now()
                
                # 记录进展历史
                existing_mastery.progression_history.append({
                    "timestamp": datetime.now(),
                    "old_level": old_level,
                    "new_level": mastery_level,
                    "confidence": confidence
                })
            else:
                # 添加新主题
                new_mastery = TopicMastery(
                    topic=topic,
                    mastery_level=mastery_level,
                    confidence=confidence,
                    interaction_count=1,
                    last_interaction=datetime.now(),
                    progression_history=[{
                        "timestamp": datetime.now(),
                        "level": mastery_level,
                        "confidence": confidence
                    }]
                )
                profile.topic_mastery.append(new_mastery)
            
            profile.updated_at = datetime.now()
            await profile.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update topic mastery for {user_id}: {e}")
            return False
    
    async def add_learning_insight(self, user_id: str, insight_type: str,
                                 description: str, confidence: float,
                                 evidence: List[str], recommendations: List[str]) -> bool:
        """添加学习洞察"""
        try:
            profile = await self.create_or_get_profile(user_id)
            
            insight = LearningInsight(
                insight_type=insight_type,
                description=description,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                created_at=datetime.now()
            )
            
            # 限制洞察数量
            profile.current_insights.append(insight)
            if len(profile.current_insights) > 10:
                profile.current_insights = profile.current_insights[-10:]
            
            profile.updated_at = datetime.now()
            await profile.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add insight for {user_id}: {e}")
            return False
    
    async def update_conversation_stats(self, user_id: str, session_duration: float,
                                      query_types: List[str]) -> bool:
        """更新对话统计"""
        try:
            profile = await self.create_or_get_profile(user_id)
            
            # 更新统计信息
            profile.total_conversations += 1
            profile.total_questions += len(query_types)
            
            # 更新平均会话时长
            total_duration = profile.average_session_duration * (profile.total_conversations - 1) + session_duration
            profile.average_session_duration = total_duration / profile.total_conversations
            
            # 更新苏格拉底偏好分数
            socratic_count = query_types.count('socratic')
            total_count = len(query_types)
            session_socratic_ratio = socratic_count / total_count if total_count > 0 else 0
            
            # 指数移动平均
            alpha = 0.2
            profile.socratic_preference_score = (
                alpha * session_socratic_ratio + 
                (1 - alpha) * profile.socratic_preference_score
            )
            
            profile.updated_at = datetime.now()
            await profile.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation stats for {user_id}: {e}")
            return False
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        try:
            profile = await UserProfile.find_one(UserProfile.user_id == user_id)
            return profile
        except Exception as e:
            self.logger.error(f"Failed to get profile for user {user_id}: {e}")
            return None
    
    async def clear_user_profile(self, user_id: str) -> bool:
        """清空用户画像"""
        try:
            profile = await UserProfile.find_one(UserProfile.user_id == user_id)
            if profile:
                # 重置用户画像数据
                profile.learning_patterns = []
                profile.topic_mastery = []
                profile.current_insights = []
                profile.current_recommendations = []
                profile.total_conversations = 0
                profile.total_questions = 0
                profile.average_session_duration = 0.0
                profile.socratic_preference_score = 0.5
                profile.learning_velocity = 0.0
                profile.knowledge_retention = 0.0
                profile.conceptual_connection_ability = 0.0
                profile.learning_preferences = {}
                profile.updated_at = datetime.now()
                await profile.save()
                self.logger.info(f"Cleared user profile for {user_id}")
                return True
            else:
                self.logger.warning(f"User profile not found for {user_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to clear profile for user {user_id}: {e}")
            return False


class KnowledgeQueryStorageService:
    """知识查询存储服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def initialize(self):
        """初始化服务"""
        self.db = await get_database()
        self.logger.info("Knowledge query storage service initialized")
    
    async def save_query(self, query_data: Dict[str, Any]) -> bool:
        """保存知识查询记录"""
        try:
            query = KnowledgeQuery(**query_data)
            await query.create()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save knowledge query: {e}")
            return False
    
    async def get_query_statistics(self, start_date: datetime, 
                                 end_date: datetime) -> Dict[str, Any]:
        """获取查询统计"""
        try:
            queries = await KnowledgeQuery.find(
                KnowledgeQuery.timestamp >= start_date,
                KnowledgeQuery.timestamp <= end_date
            ).to_list()
            
            total_queries = len(queries)
            normal_queries = len([q for q in queries if q.query_type == QueryType.NORMAL])
            socratic_queries = len([q for q in queries if q.query_type == QueryType.SOCRATIC])
            
            avg_generation_time = sum(q.generation_time for q in queries) / total_queries if total_queries > 0 else 0
            
            # 主题分析
            all_topics = []
            for query in queries:
                all_topics.extend(query.detected_topics)
            
            topic_counts = {}
            for topic in all_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            return {
                "total_queries": total_queries,
                "normal_queries": normal_queries,
                "socratic_queries": socratic_queries,
                "avg_generation_time": avg_generation_time,
                "top_topics": sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get query statistics: {e}")
            return {}


class StorageService:
    """统一存储服务"""
    
    def __init__(self):
        self.conversation_service = ConversationStorageService()
        self.profile_service = UserProfileStorageService()
        self.query_service = KnowledgeQueryStorageService()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def initialize(self):
        """初始化所有服务"""
        await self.conversation_service.initialize()
        await self.profile_service.initialize()
        await self.query_service.initialize()
        self.logger.info("Storage service initialized")
    
    # 代理方法
    async def create_session(self, *args, **kwargs):
        return await self.conversation_service.create_session(*args, **kwargs)
    
    async def add_conversation_turn(self, *args, **kwargs):
        return await self.conversation_service.add_conversation_turn(*args, **kwargs)
    
    async def end_session(self, *args, **kwargs):
        return await self.conversation_service.end_session(*args, **kwargs)
    
    async def create_or_get_profile(self, *args, **kwargs):
        return await self.profile_service.create_or_get_profile(*args, **kwargs)
    
    async def update_learning_pattern(self, *args, **kwargs):
        return await self.profile_service.update_learning_pattern(*args, **kwargs)
    
    async def update_topic_mastery(self, *args, **kwargs):
        return await self.profile_service.update_topic_mastery(*args, **kwargs)
    
    async def update_conversation_stats(self, *args, **kwargs):
        return await self.profile_service.update_conversation_stats(*args, **kwargs)
    
    async def save_query(self, *args, **kwargs):
        return await self.query_service.save_query(*args, **kwargs)
    
    async def clear_user_profile(self, *args, **kwargs):
        return await self.profile_service.clear_user_profile(*args, **kwargs)

    async def get_user_sessions(self, *args, **kwargs):
        return await self.conversation_service.get_user_sessions(*args, **kwargs)


# 全局存储服务实例
storage_service = StorageService()
