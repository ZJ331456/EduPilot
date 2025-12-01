#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习模式检测器 - 负责识别用户的学习偏好和模式
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from src.infrastructure.utils import AgentState, LearningPattern


class LearningPatternDetector:
    """学习模式检测器
    
    职责：
    1. 基于词汇的学习模式识别
    2. 基于上下文的模式推理
    3. 基于查询类型的模式推断
    4. 模式合并和排序
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pattern_keywords = self._init_pattern_keywords()
    
    def detect(self, state: AgentState) -> List[Dict[str, Any]]:
        """检测学习模式
        
        Args:
            state: 当前状态
            
        Returns:
            学习模式列表（按置信度排序）
        """
        text = state.user_query.lower()
        patterns = []
        
        # 1. 基础词汇匹配
        for pattern_type, words in self.pattern_keywords.items():
            matches = []
            total_score = 0
            
            for word in words:
                if word in text:
                    weight = self._get_pattern_weight(word, pattern_type)
                    total_score += weight
                    matches.append(word)
            
            if total_score > 0:
                max_possible_score = len(words) * 2.0
                confidence = min(total_score / max_possible_score, 1.0)
                
                patterns.append({
                    'pattern': pattern_type,
                    'score': total_score,
                    'confidence': confidence,
                    'indicators': matches,
                    'timestamp': datetime.now().isoformat()
                })
        
        # 2. 上下文学习模式推理
        context_patterns = self._infer_from_context(state)
        patterns.extend(context_patterns)
        
        # 3. 查询类型学习模式推理
        query_patterns = self._infer_from_query_type(text)
        patterns.extend(query_patterns)
        
        # 4. 合并重复模式
        merged_patterns = self._merge_patterns(patterns)
        
        return sorted(merged_patterns, key=lambda x: x['confidence'], reverse=True)
    
    def _init_pattern_keywords(self) -> Dict[str, List[str]]:
        """初始化学习模式关键词"""
        return {
            LearningPattern.VISUAL: [
                "图表", "图片", "视频", "可视化", "看", "观察", "展示", "演示",
                "画图", "图解", "示意图", "流程图", "图像", "颜色", "形状",
                "直观", "清晰", "明确", "视觉", "看起来", "显示"
            ],
            LearningPattern.AUDITORY: [
                "听", "说", "讨论", "音频", "对话", "交流", "沟通", "讲解",
                "讲述", "复述", "朗读", "背诵", "听讲", "声音", "语音",
                "口头", "听起来", "声音", "解释", "说明"
            ],
            LearningPattern.KINESTHETIC: [
                "动手", "实践", "操作", "体验", "互动", "练习", "做", "尝试",
                "实验", "实际", "亲自", "操作", "触摸", "感受", "体会",
                "实战", "练习", "模拟", "演练", "实操"
            ],
            LearningPattern.READING: [
                "阅读", "文字", "文档", "书籍", "资料", "文本", "读", "文章",
                "笔记", "记录", "写", "文献", "材料", "内容", "信息",
                "详细", "仔细", "研读", "学习资料"
            ],
        }
    
    def _get_pattern_weight(self, word: str, pattern_type: str) -> float:
        """获取学习模式词汇权重"""
        high_weight_words = {
            LearningPattern.VISUAL: ['可视化', '图解', '演示', '展示'],
            LearningPattern.AUDITORY: ['讲解', '讨论', '交流', '沟通'],
            LearningPattern.KINESTHETIC: ['实践', '动手', '操作', '体验'],
            LearningPattern.READING: ['阅读', '研读', '文献', '资料']
        }
        
        if word in high_weight_words.get(pattern_type, []):
            return 2.0
        else:
            return 1.0
    
    def _infer_from_context(self, state: AgentState) -> List[Dict[str, Any]]:
        """从上下文推理学习模式"""
        patterns = []
        
        # 检查是否有知识检索结果
        if hasattr(state, 'retrieved_knowledge') and state.retrieved_knowledge:
            total_text_length = sum(
                len(str(item)) for item in state.retrieved_knowledge.get('results', [])
            )
            if total_text_length > 1000:
                patterns.append({
                    'pattern': LearningPattern.READING,
                    'score': min(total_text_length / 2000, 2.0),
                    'confidence': 0.6,
                    'indicators': ['长文本内容检索'],
                    'source': 'context_inference',
                    'timestamp': datetime.now().isoformat()
                })
        
        return patterns
    
    def _infer_from_query_type(self, text: str) -> List[Dict[str, Any]]:
        """从查询类型推理学习模式"""
        patterns = []
        
        # 询问操作步骤 -> 动觉学习
        if any(phrase in text for phrase in ['怎么做', '如何操作', '步骤', '方法']):
            patterns.append({
                'pattern': LearningPattern.KINESTHETIC,
                'score': 1.5,
                'confidence': 0.7,
                'indicators': ['操作询问'],
                'source': 'query_type_inference',
                'timestamp': datetime.now().isoformat()
            })
        
        # 询问概念解释 -> 阅读学习
        if any(phrase in text for phrase in ['是什么', '定义', '概念', '含义']):
            patterns.append({
                'pattern': LearningPattern.READING,
                'score': 1.5,
                'confidence': 0.6,
                'indicators': ['概念询问'],
                'source': 'query_type_inference',
                'timestamp': datetime.now().isoformat()
            })
        
        return patterns
    
    def _merge_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并重复的学习模式"""
        merged = {}
        
        for pattern in patterns:
            pattern_type = pattern['pattern']
            if pattern_type in merged:
                merged[pattern_type]['score'] += pattern['score']
                merged[pattern_type]['confidence'] = max(
                    merged[pattern_type]['confidence'], 
                    pattern['confidence']
                )
                if 'indicators' in pattern:
                    merged[pattern_type].setdefault('indicators', []).extend(pattern['indicators'])
            else:
                merged[pattern_type] = pattern.copy()
                if 'indicators' not in merged[pattern_type]:
                    merged[pattern_type]['indicators'] = []
        
        return list(merged.values())

