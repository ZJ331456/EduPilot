#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识缺口检测器 - 负责识别学习中的知识缺口和改进领域
"""

import logging
from typing import Dict, Any, List

from src.infrastructure.utils import AgentState
from .interaction_analyzer import InteractionAnalysis


class KnowledgeGapDetector:
    """知识缺口检测器
    
    职责：
    1. 基于参与度识别缺口
    2. 基于知识覆盖度识别缺口
    3. 基于响应效果识别缺口
    4. 生成改进建议
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def detect(self, state: AgentState, interaction_analysis: InteractionAnalysis) -> List[Dict[str, Any]]:
        """检测知识缺口
        
        Args:
            state: 当前状态
            interaction_analysis: 交互分析结果
            
        Returns:
            知识缺口列表（按优先级排序）
        """
        gaps = []
        
        # 1. 基于参与度识别缺口
        if interaction_analysis.engagement_level < 0.4:
            gaps.append({
                'type': 'engagement_gap',
                'description': '用户参与度不足',
                'severity': 'high',
                'suggestions': ['简化问题', '提供更多引导', '增加互动元素'],
                'priority': 0.9
            })
        
        # 2. 基于知识覆盖度识别缺口
        if interaction_analysis.knowledge_coverage < 0.5:
            gaps.append({
                'type': 'knowledge_gap',
                'description': '知识库内容不足',
                'severity': 'medium',
                'suggestions': ['扩展知识库', '改进检索算法'],
                'priority': 0.7
            })
        
        # 3. 基于响应效果识别缺口
        if interaction_analysis.response_effectiveness < 0.5:
            gaps.append({
                'type': 'effectiveness_gap',
                'description': '响应效果有待提升',
                'severity': 'medium',
                'suggestions': ['优化响应策略', '增加个性化'],
                'priority': 0.6
            })
        
        # 4. 基于理解水平识别缺口
        if state.understanding_level and state.understanding_level.level_value < 2:
            gaps.append({
                'type': 'understanding_gap',
                'description': '理解水平较低，需要更多支持',
                'severity': 'high',
                'suggestions': ['提供更多示例', '降低概念难度', '增加交互引导'],
                'priority': 0.85
            })
        
        # 按优先级排序
        gaps.sort(key=lambda x: x['priority'], reverse=True)
        
        return gaps

