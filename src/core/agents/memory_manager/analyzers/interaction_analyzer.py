#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互分析器 - 负责分析用户交互质量
"""

import logging
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

from src.infrastructure.utils import AgentState


@dataclass
class InteractionAnalysis:
    """交互分析结果"""
    quality_score: float  # 总体质量分数
    engagement_level: float  # 参与度
    learning_value: float  # 学习价值
    knowledge_coverage: float  # 知识覆盖度
    response_effectiveness: float  # 响应效果
    areas_for_improvement: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class InteractionAnalyzer:
    """交互质量分析器
    
    职责：
    1. 评估用户参与度
    2. 评估知识覆盖度
    3. 评估响应效果
    4. 计算学习价值
    5. 识别改进领域
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze(self, state: AgentState) -> InteractionAnalysis:
        """分析交互质量
        
        Args:
            state: 当前状态
            
        Returns:
            交互分析结果
        """
        # 1. 评估用户参与度
        engagement_level = self._evaluate_user_engagement(state)
        
        # 2. 评估知识覆盖度
        knowledge_coverage = self._evaluate_knowledge_coverage(state)
        
        # 3. 评估响应效果
        response_effectiveness = self._evaluate_response_effectiveness(state)
        
        # 4. 计算学习价值
        learning_value = self._calculate_learning_value(state)
        
        # 5. 计算综合质量分数
        quality_score = (
            engagement_level * 0.25 +
            knowledge_coverage * 0.25 +
            response_effectiveness * 0.25 +
            learning_value * 0.25
        )
        
        # 6. 识别改进领域
        areas_for_improvement = self._identify_improvement_areas(
            engagement_level, knowledge_coverage, response_effectiveness, learning_value
        )
        
        return InteractionAnalysis(
            quality_score=quality_score,
            engagement_level=engagement_level,
            learning_value=learning_value,
            knowledge_coverage=knowledge_coverage,
            response_effectiveness=response_effectiveness,
            areas_for_improvement=areas_for_improvement
        )
    
    def _evaluate_user_engagement(self, state: AgentState) -> float:
        """评估用户参与度"""
        if not state.user_responses:
            return 0.3  # 基础分数
        
        response_count = len(state.user_responses)
        avg_length = sum(len(r) for r in state.user_responses) / response_count
        
        # 响应数量分数
        count_score = min(response_count / 5, 1.0)
        
        # 响应长度分数
        length_score = min(avg_length / 100, 1.0)
        
        return (count_score * 0.5 + length_score * 0.5)
    
    def _evaluate_knowledge_coverage(self, state: AgentState) -> float:
        """评估知识覆盖度"""
        factors = []
        
        # 检索知识的可用性
        if state.retrieved_knowledge:
            results = state.retrieved_knowledge.get("results", [])
            if results:
                avg_relevance = sum(r.get("relevance_score", 0) for r in results) / len(results)
                factors.append(avg_relevance)
            else:
                factors.append(0.1)
        else:
            factors.append(0.0)
        
        # 查询解释的完整性
        if state.interpretation:
            factors.append(0.8 if "keywords" in state.interpretation else 0.5)
        else:
            factors.append(0.2)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    def _evaluate_response_effectiveness(self, state: AgentState) -> float:
        """评估响应效果"""
        if not state.execution_result:
            return 0.0
        
        factors = []
        
        # 执行成功率
        execution_summary = state.execution_result.get("execution_summary", {})
        success_rate = execution_summary.get("success_rate", 0)
        factors.append(success_rate)
        
        # 行动完成度
        total_actions = execution_summary.get("total_actions", 0)
        successful_actions = execution_summary.get("successful_actions", 0)
        if total_actions > 0:
            factors.append(successful_actions / total_actions)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    def _calculate_learning_value(self, state: AgentState) -> float:
        """计算学习价值"""
        indicators = []
        
        # 苏格拉底式问答的价值
        if state.socratic_questions and state.user_responses:
            question_count = len(state.socratic_questions)
            response_count = len(state.user_responses)
            ratio = min(response_count / question_count, 1.0) if question_count > 0 else 0
            indicators.append(ratio)
        
        # 概念探索的深度
        if state.query_type and "explanation" in str(state.query_type).lower():
            indicators.append(0.8)
        
        # 知识连接的建立
        if state.retrieved_knowledge:
            sources = state.retrieved_knowledge.get("successful_sources", [])
            if len(sources) > 1:
                indicators.append(0.7)
        
        return sum(indicators) / len(indicators) if indicators else 0.3
    
    def _identify_improvement_areas(
        self, 
        engagement: float, 
        coverage: float, 
        effectiveness: float, 
        value: float
    ) -> List[str]:
        """识别需要改进的领域"""
        areas = []
        
        if engagement < 0.5:
            areas.append("提高用户参与度")
        if coverage < 0.6:
            areas.append("增强知识覆盖度")
        if effectiveness < 0.7:
            areas.append("优化响应效果")
        if value < 0.5:
            areas.append("增加学习价值")
        
        return areas

