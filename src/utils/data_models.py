#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .enums import (
    QueryType, ExecutionStatus, ConversationStage, UnderstandingLevel,
    ProfileDimension, EmotionType, LearningPattern
)

@dataclass
class AgentState:
    """智能体状态对象，用于在智能体之间传递信息"""
    
    # 基础信息
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    # 用户输入和查询信息
    user_query: str = ""
    interpretation: Optional[Dict[str, Any]] = None  # 查询解释结果
    query_type: Optional[QueryType] = None
    
    # 知识检索相关
    retrieved_knowledge: Optional[Dict[str, Any]] = None
    knowledge_sources: List[str] = field(default_factory=list)
    
    # 苏格拉底对话相关
    socratic_question: str = ""
    socratic_questions: List[str] = field(default_factory=list)  # 苏格拉底问题列表
    user_response: str = ""
    user_responses: List[str] = field(default_factory=list)  # 用户响应列表
    dialogue_history: List[Dict[str, str]] = field(default_factory=list)
    
    # 对话状态管理
    conversation_stage: ConversationStage = ConversationStage.INITIAL_QUERY
    understanding_level: UnderstandingLevel = UnderstandingLevel.NO_UNDERSTANDING
    conversation_round: int = 0
    max_conversation_rounds: int = 10
    target_understanding_level: UnderstandingLevel = UnderstandingLevel.GOOD_UNDERSTANDING
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, Any] = field(default_factory=dict)  # 用户上下文信息
    
    # 学习进度追踪
    learning_objectives: List[str] = field(default_factory=list)
    achieved_objectives: List[str] = field(default_factory=list)
    current_focus: str = ""
    key_concepts_covered: List[str] = field(default_factory=list)
    
    # 规划和执行相关
    plan: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    execution_status: ExecutionStatus = ExecutionStatus.PENDING
    
    # 学习和反馈相关
    learning_feedback: Optional[Dict[str, Any]] = None
    knowledge_updates: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    
    def add_dialogue_turn(self, question: str, response: str):
        """添加对话轮次"""
        self.dialogue_history.append({
            "question": question,
            "response": response,
            "timestamp": time.time(),
            "round": self.conversation_round,
            "stage": self.conversation_stage.value
        })
        self.conversation_round += 1
    
    def advance_conversation_stage(self, new_stage: ConversationStage):
        """推进对话阶段"""
        self.conversation_stage = new_stage
        self.conversation_context[f"stage_{new_stage.value}_timestamp"] = time.time()
    
    def update_understanding_level(self, new_level: UnderstandingLevel):
        """更新理解水平"""
        self.understanding_level = new_level
        self.conversation_context["understanding_updated_at"] = time.time()
    
    def is_conversation_complete(self) -> bool:
        """检查对话是否完成"""
        # 达到目标理解水平或超过最大轮次
        return (
            self.understanding_level.level_value >= self.target_understanding_level.level_value or
            self.conversation_round >= self.max_conversation_rounds or
            self.conversation_stage == ConversationStage.CONCLUSION
        )
    
    def should_continue_socratic_questioning(self) -> bool:
        """判断是否应该继续苏格拉底式提问"""
        # 添加日志以便调试
        print(f"   检查是否继续提问:")
        print(f"   当前理解水平: {self.understanding_level.value}")
        print(f"   目标理解水平: {self.target_understanding_level.value}")
        print(f"   当前轮次: {self.conversation_round}")
        print(f"   最大轮次: {self.max_conversation_rounds}")
        print(f"   对话阶段: {self.conversation_stage.value}")
        
        if self.is_conversation_complete():
            print(f"对话已完成，停止提问")
            return False
        
        # 如果理解水平还不够，继续提问
        if self.understanding_level.level_value < self.target_understanding_level.level_value:
            print(f"理解水平不够，继续提问")
            return True
        
        # 如果最近几轮用户回答质量不高，继续提问
        if len(self.user_responses) >= 2:
            recent_responses = self.user_responses[-2:]
            if all(len(response.strip()) < 20 for response in recent_responses):
                return True
        
        return False
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        return {
            "session_id": self.session_id,
            "total_rounds": self.conversation_round,
            "current_stage": self.conversation_stage.value,
            "understanding_level": self.understanding_level.value,
            "progress": f"{self.conversation_round}/{self.max_conversation_rounds}",
            "objectives_achieved": len(self.achieved_objectives),
            "key_concepts": self.key_concepts_covered,
            "dialogue_turns": len(self.dialogue_history)
        }
    
    def set_error(self, error_type: str, error_message: str, details: Optional[Dict] = None):
        """设置错误信息"""
        self.error_info = {
            "type": error_type,
            "message": error_message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.execution_status = ExecutionStatus.FAILED
    
    def clear_error(self):
        """清除错误信息"""
        self.error_info = None
        if self.execution_status == ExecutionStatus.FAILED:
            self.execution_status = ExecutionStatus.PENDING
    
    def has_error(self) -> bool:
        """检查是否有错误
        
        Returns:
            是否存在错误信息
        """
        return self.error_info is not None
    
    def get_errors(self) -> List[str]:
        """获取错误信息列表
        
        Returns:
            错误信息列表
        """
        if self.error_info is None:
            return []
        return [f"{self.error_info.get('type', 'unknown')}: {self.error_info.get('message', 'No message')}"]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "user_query": self.user_query,
            "interpretation": self.interpretation,
            "query_type": self.query_type.value if self.query_type else None,
            "retrieved_knowledge": self.retrieved_knowledge,
            "knowledge_sources": self.knowledge_sources,
            "socratic_question": self.socratic_question,
            "socratic_questions": self.socratic_questions,
            "user_response": self.user_response,
            "user_responses": self.user_responses,
            "dialogue_history": self.dialogue_history,
            "plan": self.plan,
            "execution_result": self.execution_result,
            "execution_status": self.execution_status.value,
            "learning_feedback": self.learning_feedback,
            "knowledge_updates": self.knowledge_updates,
            "metadata": self.metadata,
            "error_info": self.error_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """从字典创建状态对象"""
        state = cls()
        state.session_id = data.get("session_id", state.session_id)
        state.timestamp = data.get("timestamp", state.timestamp)
        state.user_query = data.get("user_query", "")
        state.interpretation = data.get("interpretation")
        
        query_type_str = data.get("query_type")
        if query_type_str:
            state.query_type = QueryType(query_type_str)
        
        state.retrieved_knowledge = data.get("retrieved_knowledge")
        state.knowledge_sources = data.get("knowledge_sources", [])
        state.socratic_question = data.get("socratic_question", "")
        state.socratic_questions = data.get("socratic_questions", [])
        state.user_response = data.get("user_response", "")
        state.user_responses = data.get("user_responses", [])
        state.dialogue_history = data.get("dialogue_history", [])
        state.plan = data.get("plan")
        state.execution_result = data.get("execution_result")
        
        execution_status_str = data.get("execution_status", "pending")
        state.execution_status = ExecutionStatus(execution_status_str)
        
        state.learning_feedback = data.get("learning_feedback")
        state.knowledge_updates = data.get("knowledge_updates", [])
        state.metadata = data.get("metadata", {})
        state.error_info = data.get("error_info")
        
        return state

@dataclass
class ExtractionRule:
    """抽取规则配置"""
    pattern: str  # 正则表达式模式
    subject: str  # 主语模板
    predicate: str  # 谓语模板
    object_template: str  # 宾语模板
    dimension: ProfileDimension  # 所属维度
    confidence: float  # 基础置信度
    weight: float  # 权重
    description: str  # 规则描述

@dataclass
class DimensionConfig:
    """维度配置"""
    name: str  # 维度名称
    weight: float  # 权重
    patterns: List[str]  # 匹配模式
    extraction_rules: List[ExtractionRule]  # 抽取规则
    priority: int  # 优先级

@dataclass
class ProfileInsight:
    """画像洞察"""
    insight_type: str
    description: str
    confidence: float
    evidence: List[str]
    recommendations: List[str]
    created_at: datetime

@dataclass
class LearningProfile:
    """学习画像"""
    learning_style: str
    knowledge_level: str
    strengths: List[str]
    weaknesses: List[str]
    preferences: Dict[str, Any]

@dataclass
class PersonalityProfile:
    """性格画像"""
    traits: List[str]
    communication_style: str
    motivation_factors: List[str]
    stress_indicators: List[str] 