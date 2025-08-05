#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像智能体（整合版）
整合了用户画像构建、分析和配置功能
合并了 user_profile_agent.py, user_profile_analyzer.py, user_profile_config.py 的功能
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

from utils import BaseAgent, AgentState

from utils import (
    ProfileDimension, EmotionType, LearningPattern,
    ExtractionRule, DimensionConfig, ProfileInsight,
    LearningProfile, PersonalityProfile
)

# 导入MongoDB服务（用于API兼容性）
try:
    from services.mongodb_integration import mongodb_service
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# 导入文件系统操作
import json
import os
from pathlib import Path

class UserProfileAgent(BaseAgent):
    """用户画像智能体（整合版）
    
    功能：
    1. 从用户对话中抽取多维度用户画像信息
    2. 维护用户知识图谱
    3. 分析用户画像数据，生成洞察和建议
    4. 为其他智能体提供个性化的用户上下文
    """
    
    def __init__(self):
        super().__init__("UserProfileAgent", "用户画像构建与分析")
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化配置
        self.config = self._init_config()
        
        # 内存存储结构
        self.triples_store = defaultdict(list)  # 用户三元组存储
        self.entity_relations = defaultdict(list)  # 实体关系
        self.entity_set = set()  # 实体集合
        self.user_profiles = {}  # 用户画像缓存
        
        # 维度权重（动态调整）
        self.dimension_weights = {dim: 1.0 for dim in ProfileDimension}
    
    def _init_config(self) -> Dict[str, Any]:
        """初始化配置"""
        return {
            'dimensions': self._init_dimensions(),
            'emotion_lexicon': self._init_emotion_lexicon(),
            'learning_patterns': self._init_learning_patterns(),
            'extraction_rules': self._init_extraction_rules(),
            'personalization_strategies': self._init_personalization_strategies()
        }
    
    def _init_dimensions(self) -> Dict[str, DimensionConfig]:
        """初始化维度配置"""
        return {
            ProfileDimension.BASIC_INFO: DimensionConfig("基本信息", 1.0, [r"我叫|我是|年龄|职业"], [], 1),
            ProfileDimension.INTERESTS: DimensionConfig("兴趣爱好", 1.2, [r"喜欢|爱好|感兴趣"], [], 2),
            ProfileDimension.LEARNING_STYLE: DimensionConfig("学习风格", 1.5, [r"学习|理解|习惯"], [], 3),
            ProfileDimension.KNOWLEDGE_LEVEL: DimensionConfig("知识水平", 1.3, [r"知道|了解|不懂"], [], 4),
            ProfileDimension.PERSONALITY: DimensionConfig("性格特征", 1.1, [r"性格|个性"], [], 5),
            ProfileDimension.GOALS: DimensionConfig("目标动机", 1.4, [r"想要|希望|目标"], [], 6),
            ProfileDimension.SKILLS: DimensionConfig("技能能力", 1.2, [r"会|擅长|技能"], [], 7),
            ProfileDimension.PREFERENCES: DimensionConfig("偏好设置", 1.0, [r"偏好|选择"], [], 8),
            ProfileDimension.SOCIAL: DimensionConfig("社交关系", 1.0, [r"朋友|同事"], [], 9),
            ProfileDimension.WORK: DimensionConfig("工作职业", 1.1, [r"工作|公司"], [], 10)
        }
    
    def _init_emotion_lexicon(self) -> Dict[str, List[str]]:
        """初始化情感词典"""
        return {
            EmotionType.POSITIVE: ["喜欢", "开心", "满意", "兴奋", "好奇", "积极"],
            EmotionType.NEGATIVE: ["讨厌", "困惑", "担心", "焦虑", "沮丧", "消极"],
            EmotionType.CURIOUS: ["好奇", "疑问", "探索", "想了解", "感兴趣"],
            EmotionType.CONFUSED: ["困惑", "迷茫", "不解", "不清楚", "不懂"],
            EmotionType.NEUTRAL: ["觉得", "认为", "知道", "了解", "学习", "思考"]
        }
    
    def _init_learning_patterns(self) -> Dict[str, List[str]]:
        """初始化学习模式词汇"""
        return {
            LearningPattern.VISUAL: ["图表", "图片", "视频", "可视化", "看"],
            LearningPattern.AUDITORY: ["听", "说", "讨论", "音频", "对话"],
            LearningPattern.KINESTHETIC: ["动手", "实践", "操作", "体验", "互动"],
            LearningPattern.READING: ["阅读", "文字", "文档", "书籍", "资料"],
            LearningPattern.SOCIAL: ["讨论", "合作", "团队", "分享", "交流"],
            LearningPattern.SOLITARY: ["独自", "独立", "个人", "安静", "专注"]
        }
    
    def _init_extraction_rules(self) -> List[ExtractionRule]:
        """初始化抽取规则"""
        return [
            ExtractionRule(r"我叫(.+?)(?:，|。|$)", "用户", "姓名", "{match}", 
                         ProfileDimension.BASIC_INFO, 0.9, 1.0, "提取用户姓名"),
            ExtractionRule(r"我喜欢(.+?)(?:，|。|$)", "用户", "喜欢", "{match}", 
                         ProfileDimension.INTERESTS, 0.85, 1.2, "提取用户喜好"),
            ExtractionRule(r"我爱(.+?)(?:，|。|$)", "用户", "喜欢", "{match}", 
                         ProfileDimension.INTERESTS, 0.85, 1.2, "提取用户喜好"),
            ExtractionRule(r"我爱吃(.+?)(?:，|。|$)", "用户", "喜欢", "{match}", 
                         ProfileDimension.INTERESTS, 0.85, 1.2, "提取用户喜好"),
            ExtractionRule(r"我还喜欢(.+?)(?:，|。|$)", "用户", "喜欢", "{match}", 
                         ProfileDimension.INTERESTS, 0.85, 1.2, "提取用户喜好"),
            ExtractionRule(r"我擅长(.+?)(?:，|。|$)", "用户", "擅长", "{match}", 
                         ProfileDimension.SKILLS, 0.8, 1.2, "提取擅长技能"),
            ExtractionRule(r"我习惯(.+?)学习", "用户", "学习习惯", "{match}", 
                         ProfileDimension.LEARNING_STYLE, 0.8, 1.5, "提取学习习惯"),
            ExtractionRule(r"我对(.+?)很熟悉", "用户", "熟悉领域", "{match}", 
                         ProfileDimension.KNOWLEDGE_LEVEL, 0.8, 1.3, "提取熟悉领域"),
            ExtractionRule(r"我想要(.+?)(?:，|。|$)", "用户", "目标", "{match}", 
                         ProfileDimension.GOALS, 0.8, 1.4, "提取用户目标")
        ]
    
    def _init_personalization_strategies(self) -> Dict[str, Dict[str, Any]]:
        """初始化个性化策略"""
        return {
            "learning_style_adaptation": {
                "visual": {"response_format": "图表化", "presentation_style": "结构化"},
                "auditory": {"response_format": "语音化", "presentation_style": "对话式"},
                "kinesthetic": {"response_format": "互动化", "presentation_style": "步骤化"},
                "reading": {"response_format": "文本化", "presentation_style": "详细化"}
            },
            "knowledge_level_adaptation": {
                "beginner": {"complexity": "简单", "explanation_depth": "基础"},
                "intermediate": {"complexity": "中等", "explanation_depth": "适中"},
                "advanced": {"complexity": "复杂", "explanation_depth": "深入"}
            }
        }
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return bool(state.user_query and state.user_query.strip())
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行用户画像分析"""
        try:
            self.logger.info("执行用户画像分析...")
            
            # 优先从metadata获取用户ID，然后从user_context获取
            user_id = state.metadata.get('user_id') or (state.user_context.get('user_id', 'anonymous') if state.user_context else 'anonymous')
            
            # 1. 提取用户信息
            triples = await self._extract_user_information(state)
            
            # 2. 情感分析
            emotion_analysis = self._analyze_emotion(state.user_query)
            
            # 3. 学习模式识别
            learning_patterns = self._identify_learning_patterns(state)
            
            # 4. 更新用户画像
            update_result = await self._update_user_profile(user_id, triples, emotion_analysis, learning_patterns)
            
            # 5. 构建用户上下文
            user_context = await self._build_user_context(user_id, state)
            
            # 6. 生成画像分析
            profile_analysis = self._analyze_user_profile(user_id)
            
            # 更新状态
            state.metadata.update({
                'user_profile_analysis': {
                    'triples': triples,
                    'extracted_triples': len(triples),
                    'emotion_analysis': emotion_analysis,
                    'learning_patterns': learning_patterns,
                    'update_result': update_result,
                    'profile_analysis': profile_analysis
                },
                'enhanced_user_context': user_context
            })
            
            state.status = "completed"
            self.logger.info(f"用户画像分析完成，提取 {len(triples)} 个三元组")
            
        except Exception as e:
            self.logger.error(f"用户画像分析失败: {e}")
            state.status = "failed"
            state.error = str(e)
            
        return state
    
    async def _extract_user_information(self, state: AgentState) -> List[Dict[str, Any]]:
        """提取用户信息"""
        text = state.user_query
        triples = []
        
        # 优先使用大模型抽取
        try:
            llm_triples = await self._extract_llm_triples(text)
            if llm_triples:
                triples.extend(llm_triples)
                self.logger.info(f"大模型抽取成功，获得 {len(llm_triples)} 个三元组")
                return triples
        except Exception as e:
            self.logger.warning(f"大模型抽取失败，回退到规则抽取: {e}")
        
        # 大模型抽取失败时，使用规则抽取作为备用
        rule_triples = self._extract_rule_based_triples(text)
        triples.extend(rule_triples)
        
        # 简单模式匹配抽取
        pattern_triples = self._extract_pattern_triples(text)
        triples.extend(pattern_triples)
        
        return triples
    
    async def _extract_llm_triples(self, text: str) -> List[Dict[str, Any]]:
        """使用大模型抽取三元组"""
        try:
            # 尝试导入LLM管理器
            try:
                from utils.llm import async_generate_response
                llm_available = True
            except ImportError:
                self.logger.warning("LLM模块不可用，跳过大模型抽取")
                return []
            
            if not llm_available:
                return []
            
            # 构建提示词
            prompt = self._build_triple_extraction_prompt(text)
            
            # 调用LLM
            response = await async_generate_response(prompt)
            
            if not response or not response.strip():
                return []
            
            # 解析LLM响应
            triples = self._parse_llm_triple_response(response)
            
            return triples
            
        except Exception as e:
            self.logger.error(f"大模型抽取失败: {e}")
            return []
    
    def _build_triple_extraction_prompt(self, text: str) -> str:
        """构建三元组抽取的提示词"""
        return f"""请从以下用户输入中抽取用户画像相关的三元组信息。

用户输入：{text}

请按照以下格式输出三元组，每个三元组占一行：
主体|谓语|客体|维度|置信度

维度说明：
- basic_info: 基本信息（姓名、年龄、职业等）
- interests: 兴趣爱好（喜欢、爱好等）
- skills: 技能能力（擅长、会等）
- learning_style: 学习风格（学习习惯、理解方式等）
- knowledge_level: 知识水平（熟悉、不懂等）
- goals: 目标动机（想要、希望等）
- personality: 性格特征（性格、个性等）
- preferences: 偏好设置（经常、需要等）

示例输出格式：
用户|喜欢|苹果|interests|0.9
用户|擅长|编程|skills|0.8

请只输出三元组，不要其他解释。如果无法抽取到有效信息，请输出空行。"""

    def _parse_llm_triple_response(self, response: str) -> List[Dict[str, Any]]:
        """解析LLM的三元组响应"""
        triples = []
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or '|' not in line:
                continue
            
            try:
                parts = line.split('|')
                if len(parts) >= 4:
                    subject = parts[0].strip()
                    predicate = parts[1].strip()
                    obj = parts[2].strip()
                    dimension = parts[3].strip()
                    confidence = float(parts[4].strip()) if len(parts) > 4 and parts[4].strip() else 0.8
                    
                    # 验证维度
                    valid_dimensions = {
                        'basic_info': ProfileDimension.BASIC_INFO.value,
                        'interests': ProfileDimension.INTERESTS.value,
                        'skills': ProfileDimension.SKILLS.value,
                        'learning_style': ProfileDimension.LEARNING_STYLE.value,
                        'knowledge_level': ProfileDimension.KNOWLEDGE_LEVEL.value,
                        'goals': ProfileDimension.GOALS.value,
                        'personality': ProfileDimension.PERSONALITY.value,
                        'preferences': ProfileDimension.PREFERENCES.value
                    }
                    
                    dimension_value = valid_dimensions.get(dimension, ProfileDimension.PREFERENCES.value)
                    
                    triple = {
                        'subject': subject,
                        'predicate': predicate,
                        'object': obj,
                        'dimension': dimension_value,
                        'confidence': confidence,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'llm_based'
                    }
                    triples.append(triple)
                    
            except Exception as e:
                self.logger.warning(f"解析三元组失败: {line}, 错误: {e}")
                continue
        
        return triples
    
    def _extract_rule_based_triples(self, text: str) -> List[Dict[str, Any]]:
        """基于规则的三元组抽取"""
        triples = []
        
        for rule in self.config['extraction_rules']:
            matches = re.findall(rule.pattern, text)
            for match in matches:
                triple = {
                    'subject': rule.subject,
                    'predicate': rule.predicate,
                    'object': rule.object_template.format(match=match),
                    'dimension': rule.dimension.value,
                    'confidence': rule.confidence * self.dimension_weights.get(rule.dimension, 1.0),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'rule_based'
                }
                triples.append(triple)
        
        return triples
    
    def _extract_pattern_triples(self, text: str) -> List[Dict[str, Any]]:
        """基于模式的三元组抽取"""
        triples = []
        
        # 简单模式匹配
        patterns = [
            (r"我认为(.+?)(?:很|非常)(.+?)(?:，|。|$)", "用户", "认为", "{0}很{1}"),
            (r"我觉得(.+?)(?:，|。|$)", "用户", "觉得", "{0}"),
            (r"我需要(.+?)(?:，|。|$)", "用户", "需要", "{0}"),
            (r"我不喜欢(.+?)(?:，|。|$)", "用户", "不喜欢", "{0}"),
            (r"我爱(.+?)(?:，|。|$)", "用户", "喜欢", "{0}"),
            (r"我爱吃(.+?)(?:，|。|$)", "用户", "喜欢", "{0}"),
            (r"我还喜欢(.+?)(?:，|。|$)", "用户", "喜欢", "{0}"),
            (r"我讨厌(.+?)(?:，|。|$)", "用户", "不喜欢", "{0}"),
            (r"我习惯(.+?)(?:，|。|$)", "用户", "习惯", "{0}"),
            (r"我经常(.+?)(?:，|。|$)", "用户", "经常", "{0}")
        ]
        
        for pattern, subject, predicate, obj_template in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    obj = obj_template.format(*match)
                else:
                    obj = obj_template.format(match)
                
                triple = {
                    'subject': subject,
                    'predicate': predicate,
                    'object': obj,
                    'dimension': self._identify_triple_dimension({'predicate': predicate}),
                    'confidence': 0.7,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'pattern_based'
                }
                triples.append(triple)
        
        return triples
    
    def _identify_triple_dimension(self, triple: Dict[str, Any]) -> str:
        """识别三元组维度"""
        predicate = triple.get('predicate', '').lower()
        
        if predicate in ['姓名', '年龄', '职业']:
            return ProfileDimension.BASIC_INFO.value
        elif predicate in ['喜欢', '爱好', '感兴趣', '爱']:
            return ProfileDimension.INTERESTS.value
        elif predicate in ['擅长', '会', '技能']:
            return ProfileDimension.SKILLS.value
        elif predicate in ['学习习惯', '理解方式', '习惯']:
            return ProfileDimension.LEARNING_STYLE.value
        elif predicate in ['熟悉领域', '不懂领域']:
            return ProfileDimension.KNOWLEDGE_LEVEL.value
        elif predicate in ['目标', '希望']:
            return ProfileDimension.GOALS.value
        elif predicate in ['性格']:
            return ProfileDimension.PERSONALITY.value
        elif predicate in ['经常', '需要']:
            return ProfileDimension.PREFERENCES.value
        else:
            return ProfileDimension.PREFERENCES.value
    
    def _analyze_emotion(self, text: str) -> Dict[str, Any]:
        """分析情感"""
        emotion_scores = {}
        
        for emotion_type, words in self.config['emotion_lexicon'].items():
            score = sum(1 for word in words if word in text)
            emotion_scores[emotion_type] = score
        
        # 确定主要情感
        if not any(emotion_scores.values()):
            primary_emotion = EmotionType.NEUTRAL
            confidence = 0.5
        else:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            total_score = sum(emotion_scores.values())
            confidence = emotion_scores[primary_emotion] / total_score if total_score > 0 else 0.5
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': confidence,
            'emotion_scores': emotion_scores,
            'emotional_indicators': [word for word in self.config['emotion_lexicon'][primary_emotion] if word in text]
        }
    
    def _identify_learning_patterns(self, state: AgentState) -> List[Dict[str, Any]]:
        """识别学习模式"""
        text = state.user_query.lower()
        patterns = []
        
        for pattern_type, words in self.config['learning_patterns'].items():
            score = sum(1 for word in words if word in text)
            if score > 0:
                patterns.append({
                    'pattern': pattern_type,
                    'score': score,
                    'confidence': min(score / len(words), 1.0),
                    'indicators': [word for word in words if word in text]
                })
        
        # 按得分排序
        patterns.sort(key=lambda x: x['score'], reverse=True)
        return patterns[:3]  # 返回前3个模式
    
    async def _update_user_profile(self, user_id: str, triples: List[Dict[str, Any]], 
                                 emotion_analysis: Dict[str, Any], 
                                 learning_patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """更新用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'triples': [],
                'emotions': [],
                'learning_patterns': [],
                'insights': []
            }
        
        profile = self.user_profiles[user_id]
        
        # 更新三元组
        for triple in triples:
            # 添加时间戳
            triple['added_at'] = datetime.now().isoformat()
            profile['triples'].append(triple)
            
            # 更新图谱存储
            self._add_triple_to_graph(user_id, triple)
        
        # 更新情感历史
        emotion_analysis['timestamp'] = datetime.now().isoformat()
        profile['emotions'].append(emotion_analysis)
        
        # 更新学习模式
        for pattern in learning_patterns:
            pattern['timestamp'] = datetime.now().isoformat()
            profile['learning_patterns'].append(pattern)
        
        profile['updated_at'] = datetime.now()
        
        # 保存到MongoDB服务（包含本地文件备份）
        if MONGODB_AVAILABLE:
            try:
                await self._save_to_mongodb(user_id, profile)
                self.logger.info(f"用户画像已保存到MongoDB和本地文件: {user_id}")
            except Exception as e:
                self.logger.warning(f"保存到MongoDB失败: {e}")
        else:
            # 如果MongoDB不可用，直接保存到本地文件
            try:
                await self._save_to_local_file(user_id, profile)
                self.logger.info(f"用户画像已保存到本地文件: {user_id}")
            except Exception as e:
                self.logger.warning(f"保存到本地文件失败: {e}")
        
        return {
            'added_triples': len(triples),
            'total_triples': len(profile['triples']),
            'emotion_updates': 1,
            'pattern_updates': len(learning_patterns)
        }
    
    def _add_triple_to_graph(self, user_id: str, triple: Dict[str, Any]):
        """添加三元组到图谱"""
        key = f"{user_id}:{triple['subject']}:{triple['predicate']}"
        self.triples_store[key].append(triple)
        
        # 更新实体集合
        self.entity_set.add(triple['subject'])
        self.entity_set.add(triple['object'])
        
        # 更新关系
        self.entity_relations[triple['subject']].append({
            'predicate': triple['predicate'],
            'object': triple['object'],
            'confidence': triple['confidence']
        })
    
    async def _build_user_context(self, user_id: str, state: AgentState) -> Dict[str, Any]:
        """构建用户上下文"""
        if user_id not in self.user_profiles:
            return {}
        
        profile = self.user_profiles[user_id]
        
        # 分析最近的交互
        recent_triples = [t for t in profile['triples'] if self._is_recent(t.get('added_at', ''))]
        recent_emotions = profile['emotions'][-5:] if profile['emotions'] else []
        recent_patterns = profile['learning_patterns'][-3:] if profile['learning_patterns'] else []
        
        # 构建上下文
        context = {
            'user_id': user_id,
            'profile_summary': {
                'total_interactions': len(profile['triples']),
                'primary_interests': self._extract_primary_interests(profile['triples']),
                'dominant_emotion': self._get_dominant_emotion(recent_emotions),
                'preferred_learning_style': self._get_preferred_learning_style(recent_patterns),
                'knowledge_areas': self._extract_knowledge_areas(profile['triples'])
            },
            'recent_activity': {
                'new_triples': len(recent_triples),
                'emotion_trend': self._analyze_emotion_trend(recent_emotions),
                'learning_pattern_changes': self._analyze_pattern_changes(recent_patterns)
            },
            'personalization_hints': self._generate_personalization_hints(profile)
        }
        
        return context
    
    def _is_recent(self, timestamp_str: str, hours: int = 24) -> bool:
        """检查是否为最近的时间"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return (datetime.now() - timestamp) <= timedelta(hours=hours)
        except:
            return False
    
    def _extract_primary_interests(self, triples: List[Dict[str, Any]]) -> List[str]:
        """提取主要兴趣"""
        interest_triples = [t for t in triples if t.get('dimension') == ProfileDimension.INTERESTS.value]
        interests = [t['object'] for t in interest_triples]
        return list(Counter(interests).most_common(5))
    
    def _get_dominant_emotion(self, emotions: List[Dict[str, Any]]) -> str:
        """获取主导情感"""
        if not emotions:
            return EmotionType.NEUTRAL
        
        emotion_counts = Counter(e['primary_emotion'] for e in emotions)
        return emotion_counts.most_common(1)[0][0] if emotion_counts else EmotionType.NEUTRAL
    
    def _get_preferred_learning_style(self, patterns: List[Dict[str, Any]]) -> str:
        """获取偏好学习风格"""
        if not patterns:
            return LearningPattern.READING
        
        pattern_scores = defaultdict(float)
        for pattern_group in patterns:
            for pattern in pattern_group if isinstance(pattern_group, list) else [pattern_group]:
                if isinstance(pattern, dict) and 'pattern' in pattern:
                    pattern_scores[pattern['pattern']] += pattern.get('score', 0)
        
        return max(pattern_scores, key=pattern_scores.get) if pattern_scores else LearningPattern.READING
    
    def _extract_knowledge_areas(self, triples: List[Dict[str, Any]]) -> List[str]:
        """提取知识领域"""
        knowledge_triples = [t for t in triples if t.get('dimension') == ProfileDimension.KNOWLEDGE_LEVEL.value]
        areas = [t['object'] for t in knowledge_triples]
        return list(set(areas))
    
    def _analyze_emotion_trend(self, emotions: List[Dict[str, Any]]) -> str:
        """分析情感趋势"""
        if len(emotions) < 2:
            return "stable"
        
        positive_emotions = [EmotionType.POSITIVE, EmotionType.EXCITED, EmotionType.CURIOUS, EmotionType.SATISFIED]
        
        recent_positive = sum(1 for e in emotions[-3:] if e['primary_emotion'] in positive_emotions)
        earlier_positive = sum(1 for e in emotions[-6:-3] if e['primary_emotion'] in positive_emotions)
        
        if recent_positive > earlier_positive:
            return "improving"
        elif recent_positive < earlier_positive:
            return "declining"
        else:
            return "stable"
    
    def _analyze_pattern_changes(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析模式变化"""
        if not patterns:
            return {"status": "no_data"}
        
        # 简化分析：查看最新模式是否与之前不同
        if len(patterns) >= 2:
            latest = patterns[-1] if isinstance(patterns[-1], dict) else patterns[-1][0] if patterns[-1] else {}
            previous = patterns[-2] if isinstance(patterns[-2], dict) else patterns[-2][0] if patterns[-2] else {}
            
            if latest.get('pattern') != previous.get('pattern'):
                return {"status": "changing", "from": previous.get('pattern'), "to": latest.get('pattern')}
        
        return {"status": "stable"}
    
    def _generate_personalization_hints(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """生成个性化提示"""
        hints = {}
        
        # 基于学习模式的提示
        recent_patterns = profile['learning_patterns'][-3:] if profile['learning_patterns'] else []
        if recent_patterns:
            dominant_pattern = max(recent_patterns, key=lambda x: x.get('score', 0) if isinstance(x, dict) else 0)
            if isinstance(dominant_pattern, dict):
                pattern_type = dominant_pattern.get('pattern')
                if pattern_type in self.config['personalization_strategies']['learning_style_adaptation']:
                    hints['learning_style'] = self.config['personalization_strategies']['learning_style_adaptation'][pattern_type]
        
        # 基于情感的提示
        recent_emotions = profile['emotions'][-3:] if profile['emotions'] else []
        if recent_emotions:
            dominant_emotion = self._get_dominant_emotion(recent_emotions)
            if dominant_emotion == EmotionType.CONFUSED:
                hints['approach'] = "provide_more_examples"
            elif dominant_emotion == EmotionType.CURIOUS:
                hints['approach'] = "encourage_exploration"
            elif dominant_emotion == EmotionType.ANXIOUS:
                hints['approach'] = "provide_reassurance"
        
        return hints
    
    def _analyze_user_profile(self, user_id: str) -> Dict[str, Any]:
        """分析用户画像"""
        if user_id not in self.user_profiles:
            return {}
        
        profile = self.user_profiles[user_id]
        
        # 基础统计
        basic_stats = {
            'total_triples': len(profile['triples']),
            'total_emotions': len(profile['emotions']),
            'total_patterns': len(profile['learning_patterns']),
            'profile_age_days': (datetime.now() - profile['created_at']).days,
            'last_update': profile['updated_at'].isoformat()
        }
        
        # 学习画像分析
        learning_profile = self._analyze_learning_profile(profile)
        
        # 性格画像分析
        personality_profile = self._analyze_personality_profile(profile)
        
        # 兴趣分析
        interests_analysis = self._analyze_interests(profile)
        
        # 生成洞察
        insights = self._generate_insights(profile, learning_profile, personality_profile)
        
        return {
            'basic_statistics': basic_stats,
            'learning_profile': learning_profile.__dict__ if learning_profile else {},
            'personality_profile': personality_profile.__dict__ if personality_profile else {},
            'interests_analysis': interests_analysis,
            'insights': [insight.__dict__ for insight in insights],
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_learning_profile(self, profile: Dict[str, Any]) -> Optional[LearningProfile]:
        """分析学习画像"""
        triples = profile['triples']
        learning_triples = [t for t in triples if t.get('dimension') == ProfileDimension.LEARNING_STYLE.value]
        knowledge_triples = [t for t in triples if t.get('dimension') == ProfileDimension.KNOWLEDGE_LEVEL.value]
        skill_triples = [t for t in triples if t.get('dimension') == ProfileDimension.SKILLS.value]
        
        if not any([learning_triples, knowledge_triples, skill_triples]):
            return None
        
        # 确定学习风格
        learning_style = self._determine_learning_style(learning_triples)
        
        # 确定知识水平
        knowledge_level = self._determine_knowledge_level(knowledge_triples)
        
        # 识别优势和劣势
        strengths = self._identify_strengths(skill_triples, knowledge_triples)
        weaknesses = self._identify_weaknesses(knowledge_triples)
        
        # 分析学习偏好
        preferences = self._analyze_learning_preferences(learning_triples, knowledge_triples)
        
        return LearningProfile(
            learning_style=learning_style,
            knowledge_level=knowledge_level,
            strengths=strengths,
            weaknesses=weaknesses,
            preferences=preferences
        )
    
    def _analyze_personality_profile(self, profile: Dict[str, Any]) -> Optional[PersonalityProfile]:
        """分析性格画像"""
        personality_triples = [t for t in profile['triples'] if t.get('dimension') == ProfileDimension.PERSONALITY.value]
        
        if not personality_triples:
            return None
        
        traits = self._extract_personality_traits(personality_triples)
        communication_style = self._infer_communication_style(profile)
        motivation_factors = self._extract_motivation_factors(profile)
        stress_indicators = self._identify_stress_indicators(profile)
        
        return PersonalityProfile(
            traits=traits,
            communication_style=communication_style,
            motivation_factors=motivation_factors,
            stress_indicators=stress_indicators
        )
    
    def _analyze_interests(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析兴趣"""
        interest_triples = [t for t in profile['triples'] if t.get('dimension') == ProfileDimension.INTERESTS.value]
        
        # 提取兴趣类别
        interests = [t['object'] for t in interest_triples]
        interest_counts = Counter(interests)
        
        # 分类兴趣
        categories = self._categorize_interests(interests)
        
        return {
            'top_interests': interest_counts.most_common(5),
            'interest_categories': categories,
            'total_interests': len(set(interests)),
            'interest_diversity_score': len(categories) / max(len(interests), 1)
        }
    
    def _generate_insights(self, profile: Dict[str, Any], learning_profile: Optional[LearningProfile], 
                          personality_profile: Optional[PersonalityProfile]) -> List[ProfileInsight]:
        """生成画像洞察"""
        insights = []
        
        # 学习相关洞察
        if learning_profile:
            insights.append(ProfileInsight(
                insight_type="learning_style",
                description=f"用户偏向{learning_profile.learning_style}学习方式",
                confidence=0.8,
                evidence=[f"学习风格: {learning_profile.learning_style}"],
                recommendations=[f"建议使用{learning_profile.learning_style}相关的教学方法"],
                created_at=datetime.now()
            ))
        
        # 情感相关洞察
        recent_emotions = profile['emotions'][-5:] if profile['emotions'] else []
        if recent_emotions:
            dominant_emotion = self._get_dominant_emotion(recent_emotions)
            insights.append(ProfileInsight(
                insight_type="emotional_state",
                description=f"用户当前主要情感状态为{dominant_emotion}",
                confidence=0.7,
                evidence=[f"最近情感: {dominant_emotion}"],
                recommendations=self._get_emotion_based_recommendations(dominant_emotion),
                created_at=datetime.now()
            ))
        
        return insights
    
    # 辅助方法
    def _determine_learning_style(self, learning_triples: List[Dict]) -> str:
        """确定学习风格"""
        if not learning_triples:
            return "未知"
        
        # 简单基于最常见的模式
        styles = [t['object'] for t in learning_triples]
        style_counts = Counter(styles)
        return style_counts.most_common(1)[0][0] if style_counts else "未知"
    
    def _determine_knowledge_level(self, knowledge_triples: List[Dict]) -> str:
        """确定知识水平"""
        if not knowledge_triples:
            return "未知"
        
        # 基于熟悉和不熟悉的比例
        familiar = sum(1 for t in knowledge_triples if "熟悉" in t.get('predicate', ''))
        unfamiliar = sum(1 for t in knowledge_triples if "不懂" in t.get('predicate', ''))
        
        if familiar > unfamiliar * 2:
            return "高级"
        elif familiar > unfamiliar:
            return "中级"
        else:
            return "初级"
    
    def _identify_strengths(self, skill_triples: List[Dict], knowledge_triples: List[Dict]) -> List[str]:
        """识别优势"""
        strengths = []
        
        # 从技能中提取
        skills = [t['object'] for t in skill_triples if "擅长" in t.get('predicate', '')]
        strengths.extend(skills[:3])
        
        # 从知识中提取
        knowledge = [t['object'] for t in knowledge_triples if "熟悉" in t.get('predicate', '')]
        strengths.extend(knowledge[:2])
        
        return list(set(strengths))[:5]
    
    def _identify_weaknesses(self, knowledge_triples: List[Dict]) -> List[str]:
        """识别劣势"""
        weaknesses = [t['object'] for t in knowledge_triples if "不懂" in t.get('predicate', '')]
        return weaknesses[:3]
    
    def _analyze_learning_preferences(self, learning_triples: List[Dict], knowledge_triples: List[Dict]) -> Dict[str, Any]:
        """分析学习偏好"""
        preferences = {}
        
        # 基于学习三元组分析偏好
        if learning_triples:
            methods = [t['object'] for t in learning_triples]
            preferences['preferred_methods'] = list(set(methods))
        
        # 基于知识掌握情况推断难度偏好
        familiar_count = sum(1 for t in knowledge_triples if "熟悉" in t.get('predicate', ''))
        if familiar_count > 3:
            preferences['difficulty_preference'] = "challenging"
        elif familiar_count > 1:
            preferences['difficulty_preference'] = "moderate"
        else:
            preferences['difficulty_preference'] = "basic"
        
        return preferences
    
    def _extract_personality_traits(self, personality_triples: List[Dict]) -> List[str]:
        """提取性格特征"""
        traits = [t['object'] for t in personality_triples]
        return list(set(traits))
    
    def _infer_communication_style(self, profile: Dict[str, Any]) -> str:
        """推断沟通风格"""
        # 基于情感和表达方式推断
        emotions = profile.get('emotions', [])
        if emotions:
            recent_emotions = emotions[-3:]
            positive_count = sum(1 for e in recent_emotions if e.get('primary_emotion') in [EmotionType.POSITIVE, EmotionType.EXCITED])
            if positive_count >= 2:
                return "积极主动"
            elif any(e.get('primary_emotion') == EmotionType.CURIOUS for e in recent_emotions):
                return "好奇探索"
            else:
                return "谨慎保守"
        return "中性"
    
    def _extract_motivation_factors(self, profile: Dict[str, Any]) -> List[str]:
        """提取动机因素"""
        goal_triples = [t for t in profile['triples'] if t.get('dimension') == ProfileDimension.GOALS.value]
        factors = [t['object'] for t in goal_triples]
        return list(set(factors))[:3]
    
    def _identify_stress_indicators(self, profile: Dict[str, Any]) -> List[str]:
        """识别压力指标"""
        indicators = []
        emotions = profile.get('emotions', [])
        
        # 检查负面情感频率
        recent_emotions = emotions[-5:] if emotions else []
        negative_emotions = [EmotionType.ANXIOUS, EmotionType.CONFUSED, EmotionType.NEGATIVE]
        negative_count = sum(1 for e in recent_emotions if e.get('primary_emotion') in negative_emotions)
        
        if negative_count >= 3:
            indicators.append("高频负面情感")
        if any(e.get('primary_emotion') == EmotionType.CONFUSED for e in recent_emotions):
            indicators.append("理解困难")
        
        return indicators
    
    def _categorize_interests(self, interests: List[str]) -> Dict[str, List[str]]:
        """分类兴趣"""
        categories = {
            "学术类": [],
            "艺术类": [],
            "体育类": [],
            "技术类": [],
            "其他": []
        }
        
        # 简单分类逻辑
        for interest in interests:
            if any(keyword in interest for keyword in ["学习", "研究", "数学", "科学", "历史"]):
                categories["学术类"].append(interest)
            elif any(keyword in interest for keyword in ["音乐", "绘画", "设计", "艺术"]):
                categories["艺术类"].append(interest)
            elif any(keyword in interest for keyword in ["运动", "健身", "球", "游泳"]):
                categories["体育类"].append(interest)
            elif any(keyword in interest for keyword in ["编程", "技术", "电脑", "软件"]):
                categories["技术类"].append(interest)
            else:
                categories["其他"].append(interest)
        
        # 移除空分类
        return {k: v for k, v in categories.items() if v}
    
    def _get_emotion_based_recommendations(self, emotion: str) -> List[str]:
        """基于情感的建议"""
        recommendations_map = {
            EmotionType.CONFUSED: ["提供更多示例", "简化解释", "分步骤说明"],
            EmotionType.CURIOUS: ["鼓励深入探索", "提供相关资源", "引导发现"],
            EmotionType.ANXIOUS: ["提供支持和鼓励", "降低学习难度", "增加正面反馈"],
            EmotionType.EXCITED: ["保持学习热情", "提供挑战性内容", "扩展学习范围"],
            EmotionType.SATISFIED: ["巩固已学内容", "适度增加难度", "总结学习成果"]
        }
        return recommendations_map.get(emotion, ["继续保持良好的学习状态"])
    
    async def _save_to_local_file(self, user_id: str, profile: Dict[str, Any]):
        """保存用户画像到本地文件系统"""
        try:
            # 使用相对路径，从项目根目录开始
            # 获取当前文件所在目录的上级目录（项目根目录）
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # src/agents -> src -> project_root
            
            # 创建数据目录
            data_dir = project_root / "data" / "user_profiles"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建要保存的数据
            profile_data = {
                'user_id': user_id,
                'triples': profile.get('triples', []),
                'emotions': profile.get('emotions', []),
                'learning_patterns': profile.get('learning_patterns', []),
                'insights': profile.get('insights', []),
                'created_at': profile.get('created_at').isoformat() if profile.get('created_at') else None,
                'updated_at': profile.get('updated_at').isoformat() if profile.get('updated_at') else None,
                'profile_completeness': self._calculate_profile_completeness(profile),
                'export_time': datetime.now().isoformat()
            }
            
            # 保存到JSON文件
            filename = f"user_profile_{user_id}.json"
            file_path = data_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"用户画像已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存用户画像到本地文件失败: {e}")
            raise
    
    async def _save_to_mongodb(self, user_id: str, profile: Dict[str, Any]):
        """保存用户画像到MongoDB和本地文件"""
        if not MONGODB_AVAILABLE:
            return
        
        try:
            # 确保MongoDB服务已初始化
            if not hasattr(mongodb_service, 'initialized') or not mongodb_service.initialized:
                await mongodb_service.initialize()
            
            # 构建要保存的数据
            profile_data = {
                'user_id': user_id,
                'triples': profile.get('triples', []),
                'emotions': profile.get('emotions', []),
                'learning_patterns': profile.get('learning_patterns', []),
                'insights': profile.get('insights', []),
                'created_at': profile.get('created_at'),
                'updated_at': profile.get('updated_at'),
                'profile_completeness': self._calculate_profile_completeness(profile)
            }
            
            # 使用MongoDB服务的本地文件备份功能
            await mongodb_service.save_user_profile_to_file(user_id, profile_data)
            
        except Exception as e:
            self.logger.error(f"保存用户画像到MongoDB失败: {e}")
            raise
    
    def _calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """计算用户画像完整度"""
        total_score = 0
        max_score = 0
        
        # 三元组完整度
        triples = profile.get('triples', [])
        total_score += min(len(triples), 10)  # 最多10分
        max_score += 10
        
        # 情感记录完整度
        emotions = profile.get('emotions', [])
        total_score += min(len(emotions), 5)  # 最多5分
        max_score += 5
        
        # 学习模式完整度
        patterns = profile.get('learning_patterns', [])
        total_score += min(len(patterns), 5)  # 最多5分
        max_score += 5
        
        return total_score / max_score if max_score > 0 else 0.0

# 全局配置函数
def get_user_profile_config():
    """获取用户画像配置"""
    agent = UserProfileAgent()
    return agent.config
