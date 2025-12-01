#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相关性评分器 - 负责计算检索结果的相关性分数
"""

import logging
from typing import List


class RelevanceScorer:
    """相关性评分器
    
    职责：
    1. 计算词汇匹配分数
    2. 计算语义相似度
    3. 计算结构化匹配分数
    4. 计算上下文相关性
    5. 计算内容质量分数
    6. 综合评分
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate_score(self, query: str, content: str) -> float:
        """计算相关性分数
        
        Args:
            query: 查询文本
            content: 内容文本
            
        Returns:
            相关性分数（0-1）
        """
        try:
            if not query or not content:
                return 0.0
            
            query_lower = query.lower()
            content_lower = content.lower()
            
            # 1. 词汇匹配分数
            word_match_score = self._calculate_word_match(query_lower, content_lower)
            
            # 2. 语义相似度分数
            semantic_score = self._calculate_semantic_similarity(query_lower, content_lower)
            
            # 3. 结构化匹配分数
            structural_score = self._calculate_structural_match(query_lower, content_lower)
            
            # 4. 上下文相关性分数
            context_score = self._calculate_context_relevance(query_lower, content_lower)
            
            # 5. 内容质量分数
            quality_score = self._calculate_content_quality(content)
            
            # 综合计算
            final_score = (
                word_match_score * 0.4 +
                semantic_score * 0.25 +
                structural_score * 0.15 +
                context_score * 0.15 +
                quality_score * 0.05
            )
            
            # 长度调整
            length_adjustment = self._calculate_length_adjustment(query, content)
            final_score = final_score * length_adjustment
            
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            self.logger.warning(f"相关性计算失败: {e}")
            return 0.1
    
    def _calculate_word_match(self, query: str, content: str) -> float:
        """计算词汇匹配分数"""
        query_words = set(query.split())
        content_words = set(content.split())
        
        if not query_words:
            return 0.0
        
        # 精确匹配
        exact_matches = query_words.intersection(content_words)
        exact_score = len(exact_matches) / len(query_words)
        
        # 部分匹配
        partial_matches = 0
        for q_word in query_words:
            if q_word not in exact_matches:
                for c_word in content_words:
                    if q_word in c_word or c_word in q_word:
                        partial_matches += 1
                        break
        
        partial_score = partial_matches / len(query_words) * 0.5
        
        return exact_score + partial_score
    
    def _calculate_semantic_similarity(self, query: str, content: str) -> float:
        """计算语义相似度（简化版）"""
        semantic_keywords = {
            '历史': ['古代', '朝代', '时期', '年代', '历史', '文化', '传统'],
            '政治': ['政治', '政府', '制度', '法律', '统治', '权力'],
            '文化': ['文化', '艺术', '文学', '思想', '哲学', '宗教'],
            '经济': ['经济', '贸易', '商业', '农业', '工业', '财政'],
            '社会': ['社会', '民族', '人民', '阶级', '等级', '身份']
        }
        
        query_themes = set()
        content_themes = set()
        
        for theme, keywords in semantic_keywords.items():
            if any(keyword in query for keyword in keywords):
                query_themes.add(theme)
            if any(keyword in content for keyword in keywords):
                content_themes.add(theme)
        
        if not query_themes:
            return 0.3
        
        theme_overlap = len(query_themes.intersection(content_themes))
        semantic_score = theme_overlap / len(query_themes)
        
        return semantic_score
    
    def _calculate_structural_match(self, query: str, content: str) -> float:
        """计算结构化匹配分数"""
        structural_score = 0.0
        
        # 检查完整短语
        query_phrases = self._extract_phrases(query)
        for phrase in query_phrases:
            if phrase in content:
                structural_score += 0.3
        
        # 检查定义性内容
        definition_patterns = ['是一', '指的是', '定义为', '含义', '概念']
        if any(pattern in content for pattern in definition_patterns):
            structural_score += 0.2
        
        # 检查详细说明
        explanation_patterns = ['因为', '所以', '由于', '原因', '影响', '作用']
        explanation_count = sum(1 for pattern in explanation_patterns if pattern in content)
        structural_score += min(explanation_count * 0.1, 0.3)
        
        return min(structural_score, 1.0)
    
    def _calculate_context_relevance(self, query: str, content: str) -> float:
        """计算上下文相关性"""
        context_score = 0.0
        
        # 内容长度合理性
        content_length = len(content)
        if 100 <= content_length <= 2000:
            context_score += 0.3
        elif content_length > 2000:
            context_score += 0.2
        
        # 信息密度
        info_density = self._calculate_information_density(content)
        context_score += info_density * 0.4
        
        # 具体信息
        concrete_patterns = ['时间', '地点', '人物', '数字', '年', '月']
        concrete_count = sum(1 for pattern in concrete_patterns if pattern in content)
        context_score += min(concrete_count * 0.05, 0.3)
        
        return min(context_score, 1.0)
    
    def _calculate_content_quality(self, content: str) -> float:
        """计算内容质量分数"""
        quality_score = 0.5
        
        # 内容完整性
        if '...' not in content and '更多' not in content:
            quality_score += 0.2
        
        # 信息来源
        if '来源:' in content or 'http' in content:
            quality_score += 0.2
        
        # 结构化程度
        if any(marker in content for marker in ['1.', '2.', '一、', '二、', '（1）', '（2）']):
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _calculate_information_density(self, content: str) -> float:
        """计算信息密度"""
        words = content.split()
        if not words:
            return 0.0
        
        meaningful_words = [word for word in words if len(word) > 1 and word not in ['的', '了', '是', '在', '有', '和']]
        density = len(meaningful_words) / len(words)
        
        return min(density, 1.0)
    
    def _extract_phrases(self, text: str) -> List[str]:
        """提取短语"""
        phrases = []
        words = text.split()
        
        for i in range(len(words) - 1):
            if i + 2 <= len(words):
                phrase2 = ' '.join(words[i:i+2])
                if len(phrase2) > 3:
                    phrases.append(phrase2)
            
            if i + 3 <= len(words):
                phrase3 = ' '.join(words[i:i+3])
                if len(phrase3) > 5:
                    phrases.append(phrase3)
        
        return phrases
    
    def _calculate_length_adjustment(self, query: str, content: str) -> float:
        """计算长度调整系数"""
        query_len = len(query)
        content_len = len(content)
        
        adjustment = 1.0
        
        if content_len < 50:
            adjustment *= 0.8
        elif 100 <= content_len <= 1000:
            adjustment *= 1.1
        elif content_len > 2000:
            adjustment *= 0.95
        
        if query_len > 10 and content_len > 200:
            adjustment *= 1.05
        
        return adjustment

