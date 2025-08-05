#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from beanie import Document
from enum import Enum


class QueryType(str, Enum):
    """查询类型"""
    NORMAL = "normal"
    SOCRATIC = "socratic"


class ConversationStage(str, Enum):
    """对话阶段"""
    INITIAL = "initial"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    SOCRATIC_QUESTIONING = "socratic_questioning"
    COMPREHENSION_CHECK = "comprehension_check"
    CONCLUSION = "conclusion"


class LearningPreference(str, Enum):
    """学习偏好"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class DifficultyLevel(str, Enum):
    """难度级别"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# 对话记录模型
class ConversationTurn(BaseModel):
    """单轮对话"""
    user_input: str
    system_response: str
    query_type: QueryType
    timestamp: datetime = Field(default_factory=datetime.now)
    retrieved_context: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    stage: ConversationStage
    understanding_level: Optional[str] = None


class ConversationSession(Document):
    """对话会话"""
    session_id: str = Field(..., unique=True)
    user_id: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    turns: List[ConversationTurn] = Field(default_factory=list)
    total_turns: int = 0
    topics: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    success_metrics: Dict[str, Any] = Field(default_factory=dict)
    final_understanding_level: Optional[str] = None
    session_summary: Optional[str] = None
    
    class Settings:
        name = "conversations"
        indexes = [
            "session_id",
            "user_id",
            "start_time",
            "topics"
        ]


# 用户画像模型
class LearningPattern(BaseModel):
    """学习模式"""
    pattern_type: str  # 如：深度学习者、快速学习者、实践导向等
    confidence: float
    evidence_count: int
    last_updated: datetime = Field(default_factory=datetime.now)


class TopicMastery(BaseModel):
    """主题掌握程度"""
    topic: str
    mastery_level: DifficultyLevel
    confidence: float
    interaction_count: int
    last_interaction: datetime = Field(default_factory=datetime.now)
    progression_history: List[Dict[str, Any]] = Field(default_factory=list)


class LearningInsight(BaseModel):
    """学习洞察"""
    insight_type: str  # 如：学习速度、理解深度、知识关联能力等
    description: str
    confidence: float
    evidence: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class UserProfile(Document):
    """用户画像"""
    user_id: str = Field(..., unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 基本信息
    display_name: Optional[str] = None
    email: Optional[str] = None
    knowledge_level: Optional[str] = None  # 用户知识水平
    
    # 学习偏好
    learning_preferences: Dict[str, Any] = Field(default_factory=dict)
    preferred_query_type: Optional[QueryType] = None
    interaction_style: Optional[str] = None  # 如：详细解释、简洁回答、引导式学习等
    
    # 学习模式
    learning_patterns: List[LearningPattern] = Field(default_factory=list)
    
    # 主题掌握
    topic_mastery: List[TopicMastery] = Field(default_factory=list)
    
    # 对话统计
    total_conversations: int = 0
    total_questions: int = 0
    average_session_duration: float = 0.0
    socratic_preference_score: float = 0.5  # 0-1之间，越高越偏向苏格拉底模式
    
    # 学习进展
    learning_velocity: float = 0.0  # 学习速度评分
    knowledge_retention: float = 0.0  # 知识保持率
    conceptual_connection_ability: float = 0.0  # 概念关联能力
    
    # 动态洞察
    current_insights: List[LearningInsight] = Field(default_factory=list)
    
    # 个性化建议
    current_recommendations: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "user_profiles"
        indexes = [
            "user_id",
            "updated_at",
            "learning_preferences",
            "preferred_query_type"
        ]


# 知识查询记录
class KnowledgeQuery(Document):
    """知识查询记录"""
    query_id: str = Field(..., unique=True)
    session_id: str
    user_id: Optional[str] = None
    query_text: str
    query_type: QueryType
    
    # 检索信息
    retrieved_documents: List[str] = Field(default_factory=list)
    retrieval_scores: List[float] = Field(default_factory=list)
    knowledge_sources: List[str] = Field(default_factory=list)
    
    # 分类信息
    classification_confidence: float
    detected_topics: List[str] = Field(default_factory=list)
    difficulty_level: Optional[DifficultyLevel] = None
    
    # 响应信息
    response_text: str
    response_type: str  # direct_answer, socratic_question, etc.
    generation_time: float  # 响应生成时间（秒）
    
    # 用户反馈
    user_satisfaction: Optional[int] = None  # 1-5评分
    follow_up_questions: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Settings:
        name = "knowledge_queries"
        indexes = [
            "query_id",
            "session_id",
            "user_id",
            "query_type",
            "timestamp",
            "detected_topics"
        ]


# 系统指标
class SystemMetrics(Document):
    """系统性能指标"""
    metric_id: str = Field(..., unique=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 性能指标
    response_time_avg: float
    response_time_p95: float
    classification_accuracy: float
    retrieval_relevance_score: float
    
    # 使用统计
    total_queries: int
    normal_queries: int
    socratic_queries: int
    successful_sessions: int
    
    # 系统健康
    memory_usage: float
    cpu_usage: float
    database_connections: int
    error_rate: float
    
    # 业务指标
    user_satisfaction_avg: float
    learning_effectiveness_score: float
    knowledge_coverage: float
    
    class Settings:
        name = "system_metrics"
        indexes = [
            "timestamp",
            "metric_id"
        ]


# 所有文档模型列表（用于Beanie初始化）
DOCUMENT_MODELS = [
    ConversationSession,
    UserProfile,
    KnowledgeQuery,
    SystemMetrics
]
