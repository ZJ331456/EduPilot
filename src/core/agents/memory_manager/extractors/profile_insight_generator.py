#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画像洞察生成器 - 负责生成用户画像洞察
"""

import logging
from typing import Dict, Any, List
from datetime import datetime


class ProfileInsightGenerator:
    """画像洞察生成器
    
    职责：
    1. 基于三元组数量生成洞察
    2. 基于情感分析生成洞察
    3. 基于学习模式生成洞察
    4. 综合分析生成深度洞察
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate(
        self, 
        triples: List[Dict], 
        emotion: Dict, 
        patterns: List[Dict]
    ) -> List[Dict[str, Any]]:
        """生成画像洞察
        
        Args:
            triples: 提取的三元组
            emotion: 情感分析结果
            patterns: 学习模式列表
            
        Returns:
            洞察列表
        """
        insights = []
        
        # 1. 基于三元组数量的洞察
        if len(triples) > 0:
            insights.append({
                'type': 'information_richness',
                'description': f'用户在本次交互中提供了{len(triples)}条新信息',
                'confidence': 0.9,
                'timestamp': datetime.now().isoformat()
            })
        
        # 2. 基于情感的洞察
        if emotion.get('confidence', 0) > 0.7:
            insights.append({
                'type': 'emotional_state',
                'description': f'用户当前情感状态: {emotion.get("primary_emotion", "neutral")}',
                'confidence': emotion['confidence'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 3. 基于学习模式的洞察
        if patterns:
            dominant_pattern = patterns[0]
            insights.append({
                'type': 'learning_preference',
                'description': f'用户偏好{dominant_pattern.get("pattern", "unknown")}学习方式',
                'confidence': dominant_pattern.get('confidence', 0.5),
                'timestamp': datetime.now().isoformat()
            })
        
        # 4. 综合洞察
        comprehensive_insight = self._generate_comprehensive_insight(triples, emotion, patterns)
        if comprehensive_insight:
            insights.append(comprehensive_insight)
        
        return insights
    
    def _generate_comprehensive_insight(
        self, 
        triples: List[Dict], 
        emotion: Dict, 
        patterns: List[Dict]
    ) -> Dict[str, Any]:
        """生成综合洞察"""
        # 如果用户积极参与且有明确学习偏好
        if (len(triples) > 2 and 
            emotion.get('primary_emotion') in ['positive', 'curious'] and
            patterns):
            
            return {
                'type': 'comprehensive',
                'description': '用户表现出积极的学习态度和明确的学习偏好，建议提供更多个性化内容',
                'confidence': 0.8,
                'timestamp': datetime.now().isoformat()
            }
        
        return None

