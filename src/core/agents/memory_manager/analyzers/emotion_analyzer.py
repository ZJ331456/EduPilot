#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析器 - 负责用户情感识别和分析
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from src.infrastructure.utils import EmotionType


class EmotionAnalyzer:
    """情感分析器
    
    职责：
    1. 基于词典的情感识别
    2. 上下文情感推理
    3. 问句类型情感推断
    4. 情感强度分析
    5. 情感趋势追踪
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.emotion_lexicon = self._init_emotion_lexicon()
    
    def analyze(self, text: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析文本情感
        
        Args:
            text: 要分析的文本
            history: 历史情感数据（用于趋势分析）
            
        Returns:
            情感分析结果
        """
        emotion_scores = {}
        text_lower = text.lower()
        
        # 1. 基础词典匹配
        for emotion_type, words in self.emotion_lexicon.items():
            score = 0
            for word in words:
                if word in text_lower:
                    weight = self._get_emotion_word_weight(word, emotion_type)
                    score += weight
            emotion_scores[emotion_type] = score
        
        # 2. 上下文情感推理
        context_emotions = self._analyze_contextual_emotions(text_lower)
        for emotion_type, context_score in context_emotions.items():
            emotion_scores[emotion_type] = emotion_scores.get(emotion_type, 0) + context_score
        
        # 3. 问句类型情感推断
        question_emotions = self._analyze_question_emotions(text_lower)
        for emotion_type, question_score in question_emotions.items():
            emotion_scores[emotion_type] = emotion_scores.get(emotion_type, 0) + question_score
        
        # 4. 情感强度分析
        intensity_modifier = self._analyze_emotion_intensity(text_lower)
        
        # 5. 确定主要情感
        if not any(emotion_scores.values()):
            # 默认推断
            if '?' in text or any(q in text_lower for q in ['什么', '为什么', '怎么', '如何']):
                primary_emotion = EmotionType.CURIOUS
                confidence = 0.6
            else:
                primary_emotion = EmotionType.NEUTRAL
                confidence = 0.5
        else:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            total_score = sum(emotion_scores.values())
            base_confidence = emotion_scores[primary_emotion] / total_score if total_score > 0 else 0.5
            confidence = min(0.95, base_confidence * intensity_modifier)
        
        # 6. 情感趋势
        emotion_trend = self._get_emotion_trend(primary_emotion, history)
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': confidence,
            'emotion_scores': emotion_scores,
            'context_factors': context_emotions,
            'intensity_modifier': intensity_modifier,
            'emotion_trend': emotion_trend,
            'timestamp': datetime.now().isoformat()
        }
    
    def _init_emotion_lexicon(self) -> Dict[str, List[str]]:
        """初始化情感词典"""
        return {
            EmotionType.POSITIVE: [
                "喜欢", "开心", "满意", "兴奋", "好奇", "积极", "棒", "好", "很好", "不错",
                "有趣", "明白", "理解", "学会", "懂了", "清楚", "掌握", "知道了",
                "非常喜欢", "很开心", "太棒了", "很兴奋", "真好", "太好了",
                "想学", "希望", "期待", "愿意", "乐意", "感谢", "赞同"
            ],
            EmotionType.NEGATIVE: [
                "讨厌", "困惑", "担心", "焦虑", "沮丧", "消极", "差", "不好",
                "太难", "复杂", "不会", "记不住", "忘了", "烦", "麻烦",
                "很讨厌", "非常困惑", "很担心", "太难了", "真难", "好难",
                "不想", "拒绝", "无聊", "厌烦", "失望", "沮丧", "压力大"
            ],
            EmotionType.CURIOUS: [
                "好奇", "疑问", "探索", "想了解", "感兴趣", "为什么",
                "想知道", "想学", "如何", "怎样", "怎么", "什么", "哪个",
                "请教", "指导", "帮忙", "告诉我", "能否", "可以吗",
                "研究", "深入", "详细", "具体", "更多", "进一步"
            ],
            EmotionType.CONFUSED: [
                "困惑", "迷茫", "不解", "不清楚", "不懂", "不明白",
                "看不懂", "听不懂", "搞不清", "分不清", "理不清",
                "奇怪", "为什么", "怎么回事", "什么意思", "是什么",
                "模糊", "混乱", "乱", "晕", "蒙", "不确定"
            ],
            EmotionType.NEUTRAL: [
                "觉得", "认为", "知道", "了解", "学习", "思考",
                "是", "有", "存在", "包括", "属于", "关于",
                "事实", "情况", "现象", "问题", "方面", "内容"
            ]
        }
    
    def _get_emotion_word_weight(self, word: str, emotion_type: str) -> float:
        """获取情感词汇权重"""
        high_weight_words = {
            EmotionType.POSITIVE: ['非常喜欢', '很开心', '太棒了', '很兴奋'],
            EmotionType.NEGATIVE: ['很讨厌', '非常困惑', '很担心', '太难了'],
            EmotionType.CURIOUS: ['很好奇', '想知道', '感兴趣'],
            EmotionType.CONFUSED: ['不懂', '困惑', '不明白']
        }
        
        if word in high_weight_words.get(emotion_type, []):
            return 2.0
        else:
            return 1.0
    
    def _analyze_contextual_emotions(self, text: str) -> Dict[str, float]:
        """分析上下文情感"""
        context_emotions = {}
        
        if any(phrase in text for phrase in ['学习', '了解', '掌握']):
            context_emotions[EmotionType.CURIOUS] = 0.3
        
        if any(phrase in text for phrase in ['太难', '复杂', '不会']):
            context_emotions[EmotionType.CONFUSED] = 0.5
        
        if any(phrase in text for phrase in ['想学', '希望', '期待']):
            context_emotions[EmotionType.POSITIVE] = 0.4
        
        if any(phrase in text for phrase in ['帮忙', '请教', '指导']):
            context_emotions[EmotionType.CURIOUS] = 0.2
            
        return context_emotions
    
    def _analyze_question_emotions(self, text: str) -> Dict[str, float]:
        """分析问句类型对应的情感"""
        question_emotions = {}
        
        if any(q in text for q in ['什么是', '为什么', '如何', '怎样']):
            question_emotions[EmotionType.CURIOUS] = 0.6
        
        if any(q in text for q in ['是吗', '对吗', '真的吗']):
            question_emotions[EmotionType.CONFUSED] = 0.3
        
        if any(q in text for q in ['能否', '可以', '请问']):
            question_emotions[EmotionType.POSITIVE] = 0.2
            question_emotions[EmotionType.CURIOUS] = 0.4
            
        return question_emotions
    
    def _analyze_emotion_intensity(self, text: str) -> float:
        """分析情感强度修正因子"""
        base_intensity = 1.0
        
        intensifiers = ['非常', '很', '特别', '极其', '超级', '太', '真的']
        for intensifier in intensifiers:
            if intensifier in text:
                base_intensity += 0.2
        
        if '!!' in text or '？？' in text:
            base_intensity += 0.3
        
        if len(text) < 5:
            base_intensity *= 0.8
        elif len(text) > 50:
            base_intensity *= 1.1
            
        return min(1.5, base_intensity)
    
    def _get_emotion_trend(self, current_emotion: str, history: List[Dict[str, Any]] = None) -> str:
        """获取情感趋势"""
        if not history or len(history) < 2:
            return "stable"
        
        emotion_values = {
            EmotionType.POSITIVE: 1.0,
            EmotionType.CURIOUS: 0.5,
            EmotionType.NEUTRAL: 0.0,
            EmotionType.CONFUSED: -0.5,
            EmotionType.NEGATIVE: -1.0
        }
        
        recent = history[-5:]
        values = [emotion_values.get(e.get('primary_emotion', EmotionType.NEUTRAL), 0.0) for e in recent]
        
        if len(values) < 2:
            return "stable"
        
        avg_change = (values[-1] - values[0]) / len(values)
        
        if avg_change > 0.2:
            return "improving"
        elif avg_change < -0.2:
            return "declining"
        else:
            return "stable"

