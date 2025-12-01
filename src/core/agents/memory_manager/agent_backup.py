#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理器智能体 (MemoryManagerAgent)
整合了用户画像和学习分析功能，统一管理短期和长期记忆

设计理念:
1. 短期记忆: 当前会话的学习分析和交互质量评估
2. 长期记忆: 用户画像的持久化存储和累积更新
3. 元认知: 学习模式识别和知识缺口分析

架构原则:
- 单一职责: 专注于记忆管理
- 开闭原则: 易于扩展新的分析维度
- 依赖倒置: 依赖抽象的存储接口
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict, field

from src.infrastructure.utils import BaseAgent, AgentState
from src.infrastructure.utils import (
    ProfileDimension, EmotionType, LearningPattern
)

from .storage import LocalStorageManager, StorageConfig


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


@dataclass
class UserProfileUpdate:
    """用户画像更新"""
    triples: List[Dict[str, Any]] = field(default_factory=list)  # 新增三元组
    emotions: Dict[str, Any] = field(default_factory=dict)  # 情感分析
    learning_patterns: List[Dict[str, Any]] = field(default_factory=list)  # 学习模式
    insights: List[Dict[str, Any]] = field(default_factory=list)  # 画像洞察


@dataclass
class MemoryAnalysis:
    """统一的记忆分析结果"""
    interaction: InteractionAnalysis  # 交互分析
    profile_update: UserProfileUpdate  # 画像更新
    learning_feedback: Dict[str, Any]  # 学习反馈
    knowledge_gaps: List[Dict[str, Any]]  # 知识缺口


class MemoryManagerAgent(BaseAgent):
    """记忆管理器智能体
    
    核心功能:
    1. 短期记忆管理:
       - 分析当前会话的交互质量
       - 提取学习洞察
       - 生成即时反馈
    
    2. 长期记忆管理:
       - 提取并更新用户画像
       - 维护用户三元组知识图谱
       - 情感历史追踪
    
    3. 元认知分析:
       - 识别学习模式和偏好
       - 发现知识缺口
       - 推荐个性化学习路径
    """
    
    def __init__(self, storage_config: Optional[StorageConfig] = None):
        super().__init__(
            name="MemoryManager",
            description="统一的记忆管理器：管理短期交互记忆和长期用户画像"
        )
        
        # 初始化存储管理器
        self.storage = LocalStorageManager(storage_config)
        
        # 内存缓存（用于快速访问）
        self.user_profiles_cache = {}  # 用户画像缓存
        self.triples_store = defaultdict(list)  # 三元组存储
        self.entity_set = set()  # 实体集合
        
        # 配置参数
        self.config = self._init_config()
        self.dimension_weights = {dim: 1.0 for dim in ProfileDimension}
        
        self.logger.info("记忆管理器初始化完成")
    
    def _init_config(self) -> Dict[str, Any]:
        """初始化配置"""
        return {
            'dimensions': self._init_dimensions(),
            'emotion_lexicon': self._init_emotion_lexicon(),
            'learning_patterns': self._init_learning_patterns(),
            'extraction_rules': self._init_extraction_rules(),
        }
    
    def _init_dimensions(self) -> Dict[ProfileDimension, Dict[str, Any]]:
        """初始化维度配置"""
        return {
            ProfileDimension.BASIC_INFO: {
                "name": "基本信息",
                "weight": 1.0,
                "keywords": ["我叫", "我是", "年龄", "职业"]
            },
            ProfileDimension.INTERESTS: {
                "name": "兴趣爱好",
                "weight": 1.2,
                "keywords": ["喜欢", "爱好", "感兴趣", "爱"]
            },
            ProfileDimension.LEARNING_STYLE: {
                "name": "学习风格",
                "weight": 1.5,
                "keywords": ["学习", "理解", "习惯"]
            },
            ProfileDimension.KNOWLEDGE_LEVEL: {
                "name": "知识水平",
                "weight": 1.3,
                "keywords": ["知道", "了解", "不懂", "熟悉"]
            },
            ProfileDimension.SKILLS: {
                "name": "技能能力",
                "weight": 1.2,
                "keywords": ["会", "擅长", "技能"]
            },
            ProfileDimension.GOALS: {
                "name": "目标动机",
                "weight": 1.4,
                "keywords": ["想要", "希望", "目标"]
            },
        }
    
    def _init_emotion_lexicon(self) -> Dict[str, List[str]]:
        """🔧 增强的情感词典"""
        return {
            EmotionType.POSITIVE: [
                # 基础积极词汇
                "喜欢", "开心", "满意", "兴奋", "好奇", "积极", "棒", "好", "很好", "不错",
                # 学习相关积极
                "有趣", "明白", "理解", "学会", "懂了", "清楚", "掌握", "知道了",
                # 情感强化
                "非常喜欢", "很开心", "太棒了", "很兴奋", "真好", "太好了",
                # 积极态度
                "想学", "希望", "期待", "愿意", "乐意", "感谢", "赞同"
            ],
            EmotionType.NEGATIVE: [
                # 基础消极词汇
                "讨厌", "困惑", "担心", "焦虑", "沮丧", "消极", "差", "不好",
                # 学习困难
                "太难", "复杂", "不会", "记不住", "忘了", "烦", "麻烦",
                # 情感强化
                "很讨厌", "非常困惑", "很担心", "太难了", "真难", "好难",
                # 消极态度
                "不想", "拒绝", "无聊", "厌烦", "失望", "沮丧", "压力大"
            ],
            EmotionType.CURIOUS: [
                # 基础好奇词汇
                "好奇", "疑问", "探索", "想了解", "感兴趣", "为什么",
                # 求知欲望
                "想知道", "想学", "如何", "怎样", "怎么", "什么", "哪个",
                # 探索性表达
                "请教", "指导", "帮忙", "告诉我", "能否", "可以吗",
                # 学习兴趣
                "研究", "深入", "详细", "具体", "更多", "进一步"
            ],
            EmotionType.CONFUSED: [
                # 基础困惑词汇
                "困惑", "迷茫", "不解", "不清楚", "不懂", "不明白",
                # 理解困难
                "看不懂", "听不懂", "搞不清", "分不清", "理不清",
                # 疑惑表达
                "奇怪", "为什么", "怎么回事", "什么意思", "是什么",
                # 认知模糊
                "模糊", "混乱", "乱", "晕", "蒙", "不确定"
            ],
            EmotionType.NEUTRAL: [
                # 中性认知词汇
                "觉得", "认为", "知道", "了解", "学习", "思考",
                # 陈述性词汇
                "是", "有", "存在", "包括", "属于", "关于",
                # 客观表达
                "事实", "情况", "现象", "问题", "方面", "内容"
            ]
        }
    
    def _init_learning_patterns(self) -> Dict[str, List[str]]:
        """🔧 增强的学习模式词汇"""
        return {
            LearningPattern.VISUAL: [
                # 视觉学习词汇
                "图表", "图片", "视频", "可视化", "看", "观察", "展示", "演示",
                "画图", "图解", "示意图", "流程图", "图像", "颜色", "形状",
                "直观", "清晰", "明确", "视觉", "看起来", "显示"
            ],
            LearningPattern.AUDITORY: [
                # 听觉学习词汇
                "听", "说", "讨论", "音频", "对话", "交流", "沟通", "讲解",
                "讲述", "复述", "朗读", "背诵", "听讲", "声音", "语音",
                "口头", "听起来", "声音", "解释", "说明"
            ],
            LearningPattern.KINESTHETIC: [
                # 动觉学习词汇
                "动手", "实践", "操作", "体验", "互动", "练习", "做", "尝试",
                "实验", "实际", "亲自", "操作", "触摸", "感受", "体会",
                "实战", "练习", "模拟", "演练", "实操"
            ],
            LearningPattern.READING: [
                # 阅读学习词汇
                "阅读", "文字", "文档", "书籍", "资料", "文本", "读", "文章",
                "笔记", "记录", "写", "文献", "材料", "内容", "信息",
                "详细", "仔细", "研读", "学习资料"
            ],
        }
    
    def _init_extraction_rules(self) -> List[Dict[str, Any]]:
        """初始化抽取规则 - 增强版"""
        return [
            # 基本信息
            {
                "pattern": r"我叫(.+?)(?:，|。|$)",
                "subject": "用户",
                "predicate": "姓名",
                "dimension": ProfileDimension.BASIC_INFO,
                "confidence": 0.9
            },
            # 兴趣爱好
            {
                "pattern": r"我喜欢(.+?)(?:，|。|$)",
                "subject": "用户",
                "predicate": "喜欢",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.85
            },
            {
                "pattern": r"我对(.+?)(?:感兴趣|很感兴趣|有兴趣)",
                "subject": "用户",
                "predicate": "感兴趣",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.85
            },
            # 技能和擅长领域
            {
                "pattern": r"我擅长(.+?)(?:，|。|$)",
                "subject": "用户",
                "predicate": "擅长",
                "dimension": ProfileDimension.SKILLS,
                "confidence": 0.8
            },
            # 学习目标
            {
                "pattern": r"我想要(.+?)(?:，|。|$)",
                "subject": "用户",
                "predicate": "目标",
                "dimension": ProfileDimension.GOALS,
                "confidence": 0.8
            },
            {
                "pattern": r"我想(?:学习|了解|知道)(.+?)(?:，|。|？|$)",
                "subject": "用户",
                "predicate": "学习目标",
                "dimension": ProfileDimension.GOALS,
                "confidence": 0.75
            },
            # 🔧 新增：从查询中推断兴趣（更宽松的规则）
            {
                "pattern": r"(?:什么是|介绍|解释)(.+?)(?:？|$)",
                "subject": "用户",
                "predicate": "学习兴趣",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.6
            },
            {
                "pattern": r"(.+?)(?:的历史|的文化|的特点|的意义)",
                "subject": "用户",
                "predicate": "关注领域",
                "dimension": ProfileDimension.INTERESTS,
                "confidence": 0.65
            },
            {
                "pattern": r"如何(?:学习|理解|掌握)(.+?)(?:？|$)",
                "subject": "用户",
                "predicate": "学习需求",
                "dimension": ProfileDimension.GOALS,
                "confidence": 0.7
            },
        ]
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行记忆管理
        
        工作流程:
        1. 短期记忆: 分析当前交互
        2. 长期记忆: 提取并更新用户画像
        3. 元认知: 生成学习反馈和识别知识缺口
        """
        try:
            self.logger.info("开始执行记忆管理...")
            
            # 获取用户ID
            user_id = self._get_user_id(state)
            
            # ===== 1. 短期记忆: 交互分析 =====
            interaction_analysis = self._analyze_interaction(state)
            
            # ===== 2. 长期记忆: 用户画像更新 =====
            profile_update = await self._update_user_profile(user_id, state)
            
            # ===== 3. 元认知: 学习反馈和知识缺口 =====
            learning_feedback = self._generate_learning_feedback(
                state, interaction_analysis, profile_update
            )
            knowledge_gaps = self._identify_knowledge_gaps(
                state, interaction_analysis
            )
            
            # ===== 4. 构建统一的记忆分析结果 =====
            memory_analysis = MemoryAnalysis(
                interaction=interaction_analysis,
                profile_update=profile_update,
                learning_feedback=learning_feedback,
                knowledge_gaps=knowledge_gaps
            )
            
            # ===== 5. 保存到存储 =====
            await self._persist_memory(user_id, state, memory_analysis)
            
            # ===== 6. 更新状态 =====
            state.metadata.update({
                'memory_analysis': {
                    'interaction': asdict(interaction_analysis),
                    'profile_update': asdict(profile_update),
                    'learning_feedback': learning_feedback,
                    'knowledge_gaps': knowledge_gaps
                }
            })
            
            state.status = "completed"
            self.logger.info(
                f"记忆管理完成 - 质量分数: {interaction_analysis.quality_score:.2f}, "
                f"新增三元组: {len(profile_update.triples)}"
            )
            
        except Exception as e:
            self.logger.error(f"记忆管理失败: {e}", exc_info=True)
            state.status = "failed"
            state.error = str(e)
        
        return state
    
    def _get_user_id(self, state: AgentState) -> str:
        """获取用户ID"""
        user_id = state.metadata.get('user_id')
        if not user_id and state.user_context:
            user_id = state.user_context.get('user_id')
        return user_id or 'anonymous'
    
    # ==================== 短期记忆: 交互分析 ====================
    
    def _analyze_interaction(self, state: AgentState) -> InteractionAnalysis:
        """分析当前交互质量
        
        评估维度:
        1. 用户参与度
        2. 知识覆盖度
        3. 响应效果
        4. 学习价值
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
        areas_for_improvement = []
        if engagement_level < 0.5:
            areas_for_improvement.append("提高用户参与度")
        if knowledge_coverage < 0.6:
            areas_for_improvement.append("增强知识覆盖度")
        if response_effectiveness < 0.7:
            areas_for_improvement.append("优化响应效果")
        if learning_value < 0.5:
            areas_for_improvement.append("增加学习价值")
        
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
    
    # ==================== 长期记忆: 用户画像更新 ====================
    
    async def _update_user_profile(self, user_id: str, state: AgentState) -> UserProfileUpdate:
        """更新用户画像
        
        步骤:
        1. 提取用户信息三元组
        2. 进行情感分析
        3. 识别学习模式
        4. 生成画像洞察
        """
        # 1. 提取三元组
        triples = self._extract_user_triples(state.user_query)
        
        # 2. 情感分析
        emotion_analysis = self._analyze_emotion(state.user_query)
        
        # 3. 学习模式识别
        learning_patterns = self._identify_learning_patterns(state)
        
        # 4. 生成洞察
        insights = self._generate_profile_insights(triples, emotion_analysis, learning_patterns)
        
        # 5. 更新内存缓存
        if user_id not in self.user_profiles_cache:
            self.user_profiles_cache[user_id] = {
                'created_at': datetime.now().isoformat(),
                'triples': [],
                'emotions': [],
                'learning_patterns': [],
                'insights': []
            }
        
        profile = self.user_profiles_cache[user_id]
        profile['triples'].extend(triples)
        profile['emotions'].append(emotion_analysis)
        profile['learning_patterns'].extend(learning_patterns)
        profile['insights'].extend(insights)
        profile['updated_at'] = datetime.now().isoformat()
        
        # 6. 更新图谱存储
        for triple in triples:
            self._add_triple_to_graph(user_id, triple)
        
        return UserProfileUpdate(
            triples=triples,
            emotions=emotion_analysis,
            learning_patterns=learning_patterns,
            insights=insights
        )
    
    def _extract_user_triples(self, text: str) -> List[Dict[str, Any]]:
        """🔧 增强的用户信息三元组提取"""
        triples = []
        
        # 1. 基于规则的提取（保持现有逻辑）
        rule_based_triples = self._extract_triples_by_rules(text)
        triples.extend(rule_based_triples)
        
        # 2. 🔧 新增：基于语义的三元组推断
        semantic_triples = self._extract_semantic_triples(text)
        triples.extend(semantic_triples)
        
        # 3. 🔧 新增：基于上下文的关系推断
        contextual_triples = self._extract_contextual_triples(text)
        triples.extend(contextual_triples)
        
        # 4. 🔧 新增：概念关系三元组
        concept_triples = self._extract_concept_relations(text)
        triples.extend(concept_triples)
        
        # 5. 去重和合并相似三元组
        unique_triples = self._deduplicate_triples(triples)
        
        return unique_triples
    
    def _extract_triples_by_rules(self, text: str) -> List[Dict[str, Any]]:
        """基于规则的三元组提取（原有逻辑）"""
        triples = []
        
        for rule in self.config['extraction_rules']:
            matches = re.findall(rule['pattern'], text)
            for match in matches:
                triple = {
                    'subject': rule['subject'],
                    'predicate': rule['predicate'],
                    'object': match,
                    'dimension': rule['dimension'].value,
                    'confidence': rule['confidence'],
                    'timestamp': datetime.now().isoformat(),
                    'source': 'rule_based'
                }
                triples.append(triple)
        
        return triples
    
    def _extract_semantic_triples(self, text: str) -> List[Dict[str, Any]]:
        """基于语义的三元组提取"""
        triples = []
        
        # 学科领域识别
        academic_domains = self._identify_academic_domains(text)
        for domain in academic_domains:
            triples.append({
                "subject": "用户",
                "predicate": "关注学科",
                "object": domain,
                "dimension": ProfileDimension.INTERESTS.value,
                "confidence": 0.7,
                "source": "semantic_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        # 学习动机识别
        learning_motivations = self._identify_learning_motivations(text)
        for motivation in learning_motivations:
            triples.append({
                "subject": "用户",
                "predicate": "学习动机",
                "object": motivation,
                "dimension": ProfileDimension.GOALS.value,
                "confidence": 0.6,
                "source": "semantic_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        return triples
    
    def _extract_contextual_triples(self, text: str) -> List[Dict[str, Any]]:
        """基于上下文的关系推断"""
        triples = []
        
        # 困难度感知
        difficulty_level = self._assess_perceived_difficulty(text)
        if difficulty_level:
            triples.append({
                "subject": "用户",
                "predicate": "感知难度",
                "object": difficulty_level,
                "dimension": ProfileDimension.PREFERENCES.value,
                "confidence": 0.65,
                "source": "contextual_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        # 学习深度偏好
        depth_preference = self._assess_learning_depth_preference(text)
        if depth_preference:
            triples.append({
                "subject": "用户",
                "predicate": "学习深度偏好",
                "object": depth_preference,
                "dimension": ProfileDimension.PREFERENCES.value,
                "confidence": 0.6,
                "source": "contextual_inference",
                "timestamp": datetime.now().isoformat()
            })
        
        return triples
    
    def _extract_concept_relations(self, text: str) -> List[Dict[str, Any]]:
        """提取概念间的关系"""
        triples = []
        
        # 比较关系
        comparison_patterns = [
            r"(.+?)和(.+?)(?:有什么区别|的区别)",
            r"(.+?)与(.+?)(?:的关系|的联系)"
        ]
        
        for pattern in comparison_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                concept_a = match.group(1).strip()
                concept_b = match.group(2).strip()
                if concept_a and concept_b:
                    triples.append({
                        "subject": concept_a,
                        "predicate": "比较关系",
                        "object": concept_b,
                        "dimension": ProfileDimension.INTERESTS.value,
                        "confidence": 0.8,
                        "source": "concept_relation_extraction",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return triples
    
    def _identify_academic_domains(self, text: str) -> List[str]:
        """识别学术领域"""
        domain_keywords = {
            "历史": ["历史", "古代", "朝代", "文化", "传统", "史记", "遗事"],
            "文学": ["文学", "诗歌", "小说", "散文", "作家", "作品"],
            "科学": ["科学", "实验", "理论", "研究", "技术"],
            "艺术": ["艺术", "绘画", "音乐", "美术", "设计"],
            "哲学": ["哲学", "思想", "理论", "观点", "思考"]
        }
        
        identified_domains = []
        text_lower = text.lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_domains.append(domain)
        
        return identified_domains
    
    def _identify_learning_motivations(self, text: str) -> List[str]:
        """识别学习动机"""
        motivation_patterns = {
            "好奇心驱动": ["好奇", "想知道", "有趣", "探索"],
            "实用目的": ["有用", "实用", "应用", "工作"],
            "学术兴趣": ["深入", "研究", "学术", "理论"],
            "个人成长": ["提升", "成长", "发展", "进步"]
        }
        
        identified_motivations = []
        text_lower = text.lower()
        
        for motivation, patterns in motivation_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                identified_motivations.append(motivation)
        
        return identified_motivations
    
    def _assess_perceived_difficulty(self, text: str) -> Optional[str]:
        """评估感知难度"""
        difficulty_indicators = {
            "简单": ["简单", "容易", "基础", "入门"],
            "中等": ["一般", "普通", "适中"],
            "困难": ["难", "复杂", "困惑", "不懂"]
        }
        
        text_lower = text.lower()
        for level, indicators in difficulty_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return level
        
        return None
    
    def _assess_learning_depth_preference(self, text: str) -> Optional[str]:
        """评估学习深度偏好"""
        if any(word in text for word in ["详细", "深入", "全面", "系统"]):
            return "深度学习"
        elif any(word in text for word in ["简单", "概括", "大概", "简介"]):
            return "概括了解"
        
        return None
    
    def _deduplicate_triples(self, triples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和合并相似三元组"""
        unique_triples = {}
        
        for triple in triples:
            # 创建唯一键
            key = f"{triple['subject']}_{triple['predicate']}_{triple['object']}"
            
            if key in unique_triples:
                # 如果已存在，保留置信度更高的
                if triple['confidence'] > unique_triples[key]['confidence']:
                    unique_triples[key] = triple
            else:
                unique_triples[key] = triple
        
        return list(unique_triples.values())
    
    def _analyze_emotion(self, text: str) -> Dict[str, Any]:
        """🔧 增强的情感分析算法"""
        emotion_scores = {}
        text_lower = text.lower()
        
        # 1. 基础词典匹配（增强权重）
        for emotion_type, words in self.config['emotion_lexicon'].items():
            score = 0
            for word in words:
                if word in text_lower:
                    # 根据词汇重要性给予不同权重
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
        
        # 5. 确定主要情感（改进算法）
        if not any(emotion_scores.values()):
            # 默认推断：如果是问句，倾向于好奇；如果很短，倾向于中性
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
            # 应用强度修正
            confidence = min(0.95, base_confidence * intensity_modifier)
        
        # 6. 情感历史趋势（简单实现）
        emotion_trend = self._get_emotion_trend(primary_emotion)
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': confidence,
            'emotion_scores': emotion_scores,
            'context_factors': context_emotions,
            'intensity_modifier': intensity_modifier,
            'emotion_trend': emotion_trend,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_emotion_word_weight(self, word: str, emotion_type: str) -> float:
        """获取情感词汇权重"""
        # 高权重词汇（强情感表达）
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
        
        # 学习相关的上下文
        if any(phrase in text for phrase in ['学习', '了解', '掌握']):
            context_emotions[EmotionType.CURIOUS] = 0.3
        
        # 困难相关的上下文
        if any(phrase in text for phrase in ['太难', '复杂', '不会']):
            context_emotions[EmotionType.CONFUSED] = 0.5
        
        # 积极学习态度
        if any(phrase in text for phrase in ['想学', '希望', '期待']):
            context_emotions[EmotionType.POSITIVE] = 0.4
        
        # 请求帮助的情感
        if any(phrase in text for phrase in ['帮忙', '请教', '指导']):
            context_emotions[EmotionType.CURIOUS] = 0.2
            
        return context_emotions
    
    def _analyze_question_emotions(self, text: str) -> Dict[str, float]:
        """分析问句类型对应的情感"""
        question_emotions = {}
        
        # 探索性问题 -> 好奇
        if any(q in text for q in ['什么是', '为什么', '如何', '怎样']):
            question_emotions[EmotionType.CURIOUS] = 0.6
        
        # 确认性问题 -> 轻微困惑
        if any(q in text for q in ['是吗', '对吗', '真的吗']):
            question_emotions[EmotionType.CONFUSED] = 0.3
        
        # 求助性问题 -> 积极求知
        if any(q in text for q in ['能否', '可以', '请问']):
            question_emotions[EmotionType.POSITIVE] = 0.2
            question_emotions[EmotionType.CURIOUS] = 0.4
            
        return question_emotions
    
    def _analyze_emotion_intensity(self, text: str) -> float:
        """分析情感强度修正因子"""
        base_intensity = 1.0
        
        # 强化词汇
        intensifiers = ['非常', '很', '特别', '极其', '超级', '太', '真的']
        for intensifier in intensifiers:
            if intensifier in text:
                base_intensity += 0.2
        
        # 重复词汇或标点
        if '!!' in text or '？？' in text:
            base_intensity += 0.3
        
        # 长度影响（短文本情感可能不明显）
        if len(text) < 5:
            base_intensity *= 0.8
        elif len(text) > 50:
            base_intensity *= 1.1
            
        return min(1.5, base_intensity)
    
    def _get_emotion_trend(self, current_emotion: str) -> str:
        """获取情感趋势（简单实现）"""
        # 这里可以根据历史情感数据分析趋势
        # 暂时返回稳定状态
        return "stable"
    
    def _identify_learning_patterns(self, state: AgentState) -> List[Dict[str, Any]]:
        """🔧 增强的学习模式识别"""
        text = state.user_query.lower()
        patterns = []
        
        # 1. 基础词汇匹配（增强权重计算）
        for pattern_type, words in self.config['learning_patterns'].items():
            matches = []
            total_score = 0
            
            for word in words:
                if word in text:
                    # 根据词汇重要性调整权重
                    weight = self._get_learning_pattern_weight(word, pattern_type)
                    total_score += weight
                    matches.append(word)
            
            if total_score > 0:
                # 计算置信度
                max_possible_score = len(words) * 2.0  # 假设所有词都是高权重
                confidence = min(total_score / max_possible_score, 1.0)
                
                patterns.append({
                    'pattern': pattern_type,
                    'score': total_score,
                    'confidence': confidence,
                    'indicators': matches,
                    'timestamp': datetime.now().isoformat()
                })
        
        # 2. 上下文学习模式推理
        context_patterns = self._infer_learning_patterns_from_context(state)
        patterns.extend(context_patterns)
        
        # 3. 查询类型学习模式推理
        query_patterns = self._infer_learning_patterns_from_query_type(text)
        patterns.extend(query_patterns)
        
        # 4. 历史行为学习模式（如果有历史数据）
        history_patterns = self._infer_learning_patterns_from_history(state)
        patterns.extend(history_patterns)
        
        # 按置信度排序，合并重复模式
        merged_patterns = self._merge_learning_patterns(patterns)
        
        return sorted(merged_patterns, key=lambda x: x['confidence'], reverse=True)
    
    def _get_learning_pattern_weight(self, word: str, pattern_type: str) -> float:
        """获取学习模式词汇权重"""
        # 高权重词汇（强指示词）
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
    
    def _infer_learning_patterns_from_context(self, state: AgentState) -> List[Dict[str, Any]]:
        """从上下文推理学习模式"""
        patterns = []
        
        # 检查是否有知识检索结果
        if hasattr(state, 'retrieved_knowledge') and state.retrieved_knowledge:
            # 如果有大量文本内容，推断为阅读偏好
            total_text_length = sum(len(str(item)) for item in state.retrieved_knowledge)
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
    
    def _infer_learning_patterns_from_query_type(self, text: str) -> List[Dict[str, Any]]:
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
    
    def _infer_learning_patterns_from_history(self, state: AgentState) -> List[Dict[str, Any]]:
        """从历史行为推理学习模式（待实现）"""
        # TODO: 根据用户历史交互记录推断学习偏好
        return []
    
    def _merge_learning_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并重复的学习模式"""
        merged = {}
        
        for pattern in patterns:
            pattern_type = pattern['pattern']
            if pattern_type in merged:
                # 合并分数和置信度
                merged[pattern_type]['score'] += pattern['score']
                merged[pattern_type]['confidence'] = max(
                    merged[pattern_type]['confidence'], 
                    pattern['confidence']
                )
                merged[pattern_type]['indicators'].extend(pattern['indicators'])
            else:
                merged[pattern_type] = pattern.copy()
                if 'indicators' not in merged[pattern_type]:
                    merged[pattern_type]['indicators'] = []
        
        return list(merged.values())
    
    def _generate_profile_insights(self, triples: List[Dict], 
                                   emotion: Dict, patterns: List[Dict]) -> List[Dict[str, Any]]:
        """生成画像洞察"""
        insights = []
        
        # 基于三元组数量的洞察
        if len(triples) > 0:
            insights.append({
                'type': 'information_richness',
                'description': f'用户在本次交互中提供了{len(triples)}条新信息',
                'confidence': 0.9,
                'timestamp': datetime.now().isoformat()
            })
        
        # 基于情感的洞察
        if emotion['confidence'] > 0.7:
            insights.append({
                'type': 'emotional_state',
                'description': f'用户当前情感状态: {emotion["primary_emotion"]}',
                'confidence': emotion['confidence'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 基于学习模式的洞察
        if patterns:
            dominant_pattern = patterns[0]
            insights.append({
                'type': 'learning_preference',
                'description': f'用户偏好{dominant_pattern["pattern"]}学习方式',
                'confidence': dominant_pattern['confidence'],
                'timestamp': datetime.now().isoformat()
            })
        
        return insights
    
    def _add_triple_to_graph(self, user_id: str, triple: Dict[str, Any]):
        """添加三元组到图谱"""
        key = f"{user_id}:{triple['subject']}:{triple['predicate']}"
        self.triples_store[key].append(triple)
        
        # 更新实体集合
        self.entity_set.add(triple['subject'])
        self.entity_set.add(triple['object'])
    
    # ==================== 元认知: 学习反馈和知识缺口 ====================
    
    def _generate_learning_feedback(self, state: AgentState, 
                                    interaction: InteractionAnalysis,
                                    profile_update: UserProfileUpdate) -> Dict[str, Any]:
        """生成学习反馈"""
        feedback = {
            'overall_score': interaction.quality_score,
            'strengths': [],
            'areas_for_improvement': interaction.areas_for_improvement,
            'recommendations': [],
            'personalized_insights': {}
        }
        
        # 分析优势
        if interaction.engagement_level > 0.7:
            feedback['strengths'].append('高度参与')
        if interaction.learning_value > 0.7:
            feedback['strengths'].append('学习价值显著')
        
        # 生成建议
        if interaction.quality_score < 0.6:
            feedback['recommendations'].append('建议增加互动深度')
        if len(profile_update.triples) < 2:
            feedback['recommendations'].append('可以分享更多个人信息以获得个性化建议')
        
        # 个性化洞察
        if profile_update.learning_patterns:
            dominant_pattern = profile_update.learning_patterns[0]
            feedback['personalized_insights']['learning_style'] = dominant_pattern['pattern']
        
        if profile_update.emotions['primary_emotion'] == EmotionType.CONFUSED:
            feedback['recommendations'].append('建议提供更多示例和解释')
        
        return feedback
    
    def _identify_knowledge_gaps(self, state: AgentState, 
                                 analysis: InteractionAnalysis) -> List[Dict[str, Any]]:
        """识别知识缺口"""
        gaps = []
        
        # 基于参与度识别缺口
        if analysis.engagement_level < 0.4:
            gaps.append({
                'type': 'engagement_gap',
                'description': '用户参与度不足',
                'severity': 'high',
                'suggestions': ['简化问题', '提供更多引导', '增加互动元素'],
                'priority': 0.9
            })
        
        # 基于知识覆盖度识别缺口
        if analysis.knowledge_coverage < 0.5:
            gaps.append({
                'type': 'knowledge_gap',
                'description': '知识库内容不足',
                'severity': 'medium',
                'suggestions': ['扩展知识库', '改进检索算法'],
                'priority': 0.7
            })
        
        # 基于响应效果识别缺口
        if analysis.response_effectiveness < 0.5:
            gaps.append({
                'type': 'effectiveness_gap',
                'description': '响应效果有待提升',
                'severity': 'medium',
                'suggestions': ['优化响应策略', '增加个性化'],
                'priority': 0.6
            })
        
        # 按优先级排序
        gaps.sort(key=lambda x: x['priority'], reverse=True)
        
        return gaps
    
    # ==================== 持久化操作 ====================
    
    async def _persist_memory(self, user_id: str, state: AgentState, 
                             memory_analysis: MemoryAnalysis):
        """持久化记忆数据"""
        try:
            # 1. 保存用户画像
            if user_id in self.user_profiles_cache:
                profile_data = self.user_profiles_cache[user_id]
                self.storage.save_user_profile(user_id, profile_data)
            
            # 2. 🔧 增强：保存完整的会话记忆（包含对话历史、知识检索、执行计划等）
            session_data = {
                'user_id': user_id,
                'session_id': state.session_id,
                'query': state.user_query,
                
                # 对话历史
                'dialogue_history': self._build_dialogue_history(state),
                
                # 查询分析结果
                'query_analysis': {
                    'query_type': state.query_type.value if state.query_type else None,
                    'interpretation': state.interpretation,
                    'keywords': state.interpretation.get('keywords', []) if state.interpretation else [],
                    'concepts': state.interpretation.get('concepts', []) if state.interpretation else []
                },
                
                # 知识检索详情
                'knowledge_retrieval': self._build_knowledge_retrieval_summary(state),
                
                # 苏格拉底问答
                'socratic_dialogue': {
                    'questions': state.socratic_questions or [],
                    'user_responses': state.user_responses or [],
                    'current_question': state.socratic_question,
                    'total_rounds': len(state.socratic_questions or [])
                },
                
                # 理解水平追踪
                'understanding_tracking': {
                    'current_level': state.understanding_level.value if state.understanding_level else 'no_understanding',
                    'conversation_stage': state.conversation_stage.value if state.conversation_stage else 'initial_query',
                    'conversation_round': state.conversation_round,
                    'understanding_progression': state.metadata.get('understanding_progression', [])
                },
                
                # 执行计划和结果
                'execution_details': {
                    'plan': state.plan,
                    'execution_result': state.execution_result,
                    'actions_taken': self._extract_actions_taken(state)
                },
                
                # 交互分析
                'interaction_analysis': asdict(memory_analysis.interaction),
                
                # 画像更新
                'profile_update': asdict(memory_analysis.profile_update),
                
                # 元数据
                'metadata': {
                    'conversation_complete': state.metadata.get('conversation_complete', False),
                    'waiting_for_user': state.metadata.get('waiting_for_user', False),
                    'timestamp': datetime.now().isoformat()
                }
            }
            self.storage.save_session_memory(state.session_id, session_data)
            
            # 3. 🔧 增强：保存详细的学习记录（包含知识点、掌握度、学习路径等）
            learning_data = {
                # 基础反馈
                'learning_feedback': memory_analysis.learning_feedback,
                'knowledge_gaps': memory_analysis.knowledge_gaps,
                'quality_score': memory_analysis.interaction.quality_score,
                
                # 🔧 新增：学习内容详情
                'learning_content': {
                    'topic': state.current_focus or state.user_query,
                    'concepts_learned': self._extract_learned_concepts(state),
                    'knowledge_points': self._extract_knowledge_points(state),
                    'depth_level': state.understanding_level.value if state.understanding_level else 'no_understanding'
                },
                
                # 🔧 新增：知识掌握度
                'knowledge_mastery': {
                    'mastered_concepts': self._identify_mastered_concepts(state),
                    'partially_understood': self._identify_partial_concepts(state),
                    'needs_review': self._identify_review_needed_concepts(state),
                    'understanding_score': self._calculate_understanding_score(state)
                },
                
                # 🔧 新增：学习进度
                'learning_progress': {
                    'session_id': state.session_id,
                    'total_interactions': state.conversation_round,
                    'questions_asked': len(state.socratic_questions or []),
                    'responses_given': len(state.user_responses or []),
                    'knowledge_sources_used': len(state.retrieved_knowledge.get('results', [])) if state.retrieved_knowledge else 0,
                    'engagement_metrics': {
                        'engagement_level': memory_analysis.interaction.engagement_level,
                        'learning_value': memory_analysis.interaction.learning_value,
                        'knowledge_coverage': memory_analysis.interaction.knowledge_coverage
                    }
                },
                
                # 🔧 新增：学习路径
                'learning_path': {
                    'entry_point': state.user_query,
                    'exploration_sequence': self._build_exploration_sequence(state),
                    'key_milestones': self._identify_learning_milestones(state),
                    'related_topics': self._extract_related_topics(state)
                },
                
                # 🔧 新增：概念理解深度分析
                'conceptual_understanding': {
                    'core_concepts': self._extract_core_concepts(state),
                    'concept_relationships': self._analyze_concept_relationships(state),
                    'misconceptions_addressed': self._identify_misconceptions(state),
                    'insights_gained': memory_analysis.profile_update.insights
                },
                
                # 时间戳
                'timestamp': datetime.now().isoformat()
            }
            self.storage.save_learning_record(user_id, learning_data)
            
            self.logger.info(f"记忆数据已持久化: {user_id}")
            
        except Exception as e:
            self.logger.error(f"持久化记忆数据失败: {e}")
    
    # ==================== 辅助方法：数据提取和分析 ====================
    
    def _build_dialogue_history(self, state: AgentState) -> List[Dict[str, Any]]:
        """构建完整的对话历史"""
        dialogue_history = []
        
        # 从state的dialogue_history获取
        if hasattr(state, 'dialogue_history') and state.dialogue_history:
            dialogue_history = state.dialogue_history
        else:
            # 如果没有现成的，从苏格拉底问答构建
            questions = state.socratic_questions or []
            responses = state.user_responses or []
            
            for i in range(max(len(questions), len(responses))):
                turn = {
                    'round': i + 1,
                    'timestamp': datetime.now().isoformat()
                }
                
                if i < len(questions):
                    turn['question'] = questions[i]
                if i < len(responses):
                    turn['response'] = responses[i]
                
                dialogue_history.append(turn)
        
        return dialogue_history
    
    def _build_knowledge_retrieval_summary(self, state: AgentState) -> Dict[str, Any]:
        """构建知识检索摘要"""
        if not state.retrieved_knowledge:
            return {
                'retrieved': False,
                'sources': [],
                'total_results': 0,
                'avg_relevance': 0.0
            }
        
        results = state.retrieved_knowledge.get('results', [])
        successful_sources = state.retrieved_knowledge.get('successful_sources', [])
        
        relevance_scores = [r.get('relevance_score', 0) for r in results if 'relevance_score' in r]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        return {
            'retrieved': True,
            'sources': successful_sources,
            'total_results': len(results),
            'avg_relevance': avg_relevance,
            'top_results': results[:3] if results else [],  # 前3个最相关的结果
            'knowledge_snippets': [r.get('content', '')[:200] for r in results[:3]]  # 摘要
        }
    
    def _extract_actions_taken(self, state: AgentState) -> List[Dict[str, Any]]:
        """提取执行的行动"""
        actions = []
        
        if state.plan:
            plan_actions = state.plan.get('actions', [])
            for action in plan_actions:
                actions.append({
                    'action_type': action.get('action_type', 'unknown'),
                    'description': action.get('description', ''),
                    'status': 'completed' if state.execution_result else 'planned'
                })
        
        return actions
    
    def _extract_learned_concepts(self, state: AgentState) -> List[str]:
        """提取学到的概念"""
        concepts = []
        
        # 从查询解释中提取
        if state.interpretation and 'concepts' in state.interpretation:
            concepts.extend(state.interpretation['concepts'])
        
        # 从知识检索结果中提取
        if state.retrieved_knowledge:
            results = state.retrieved_knowledge.get('results', [])
            for result in results:
                if 'concepts' in result:
                    concepts.extend(result['concepts'])
        
        # 去重并返回
        return list(set(concepts))
    
    def _extract_knowledge_points(self, state: AgentState) -> List[Dict[str, Any]]:
        """提取知识点"""
        knowledge_points = []
        
        # 从检索结果提取知识点
        if state.retrieved_knowledge:
            results = state.retrieved_knowledge.get('results', [])
            for idx, result in enumerate(results[:5], 1):  # 最多5个
                knowledge_points.append({
                    'point_id': f"kp_{idx}",
                    'title': result.get('title', f'知识点{idx}'),
                    'content_summary': result.get('content', '')[:150],
                    'source': result.get('source', 'unknown'),
                    'relevance': result.get('relevance_score', 0.0)
                })
        
        return knowledge_points
    
    def _identify_mastered_concepts(self, state: AgentState) -> List[str]:
        """识别已掌握的概念"""
        mastered = []
        
        # 如果理解水平较高，认为核心概念已掌握
        if state.understanding_level and state.understanding_level.level_value >= 4:  # GOOD_UNDERSTANDING及以上
            mastered = self._extract_learned_concepts(state)
        
        return mastered
    
    def _identify_partial_concepts(self, state: AgentState) -> List[str]:
        """识别部分理解的概念"""
        partial = []
        
        # 中等理解水平的概念
        if state.understanding_level and 2 <= state.understanding_level.level_value < 4:
            partial = self._extract_learned_concepts(state)
        
        return partial
    
    def _identify_review_needed_concepts(self, state: AgentState) -> List[str]:
        """识别需要复习的概念"""
        review_needed = []
        
        # 理解水平较低的概念需要复习
        if state.understanding_level and state.understanding_level.level_value < 2:
            review_needed = self._extract_learned_concepts(state)
        
        return review_needed
    
    def _calculate_understanding_score(self, state: AgentState) -> float:
        """计算理解分数"""
        if not state.understanding_level:
            return 0.0
        
        # 基于理解水平计算分数（0-1）
        level_scores = {
            0: 0.0,   # NO_UNDERSTANDING
            1: 0.2,   # SURFACE_UNDERSTANDING
            2: 0.4,   # BASIC_UNDERSTANDING
            3: 0.6,   # GOOD_UNDERSTANDING
            4: 0.8,   # DEEP_UNDERSTANDING
            5: 1.0    # MASTERY
        }
        
        base_score = level_scores.get(state.understanding_level.level_value, 0.0)
        
        # 根据对话轮次调整
        if state.conversation_round > 1:
            engagement_bonus = min(0.1, state.conversation_round * 0.02)
            base_score = min(1.0, base_score + engagement_bonus)
        
        return round(base_score, 2)
    
    def _build_exploration_sequence(self, state: AgentState) -> List[Dict[str, Any]]:
        """构建探索序列"""
        sequence = []
        
        # 添加初始查询
        sequence.append({
            'step': 1,
            'type': 'initial_query',
            'content': state.user_query,
            'timestamp': state.metadata.get('created_at', datetime.now().isoformat())
        })
        
        # 添加苏格拉底问答序列
        questions = state.socratic_questions or []
        responses = state.user_responses or []
        
        for i, (q, r) in enumerate(zip(questions, responses), 2):
            sequence.append({
                'step': i,
                'type': 'socratic_interaction',
                'question': q,
                'response': r,
                'timestamp': datetime.now().isoformat()
            })
        
        return sequence
    
    def _identify_learning_milestones(self, state: AgentState) -> List[Dict[str, Any]]:
        """识别学习里程碑"""
        milestones = []
        
        # 里程碑1：成功检索到知识
        if state.retrieved_knowledge and state.retrieved_knowledge.get('results'):
            milestones.append({
                'milestone': 'knowledge_retrieved',
                'description': f"成功检索到{len(state.retrieved_knowledge['results'])}条相关知识",
                'timestamp': datetime.now().isoformat()
            })
        
        # 里程碑2：达到基础理解
        if state.understanding_level and state.understanding_level.level_value >= 2:
            milestones.append({
                'milestone': 'basic_understanding_achieved',
                'description': f"达到{state.understanding_level.value}水平",
                'timestamp': datetime.now().isoformat()
            })
        
        # 里程碑3：完成多轮对话
        if state.conversation_round >= 3:
            milestones.append({
                'milestone': 'deep_exploration',
                'description': f"完成{state.conversation_round}轮深度探讨",
                'timestamp': datetime.now().isoformat()
            })
        
        return milestones
    
    def _extract_related_topics(self, state: AgentState) -> List[str]:
        """提取相关话题"""
        related_topics = []
        
        # 从检索结果中提取相关话题
        if state.retrieved_knowledge:
            results = state.retrieved_knowledge.get('results', [])
            for result in results:
                if 'related_topics' in result:
                    related_topics.extend(result['related_topics'])
                # 从标题和内容推断相关话题
                elif 'title' in result:
                    related_topics.append(result['title'])
        
        # 去重
        return list(set(related_topics))[:10]  # 最多10个
    
    def _extract_core_concepts(self, state: AgentState) -> List[str]:
        """提取核心概念"""
        core_concepts = []
        
        # 从查询中提取
        if state.interpretation and 'concepts' in state.interpretation:
            core_concepts.extend(state.interpretation['concepts'][:3])  # 最核心的3个
        
        # 从当前焦点提取
        if state.current_focus:
            core_concepts.append(state.current_focus)
        
        return list(set(core_concepts))
    
    def _analyze_concept_relationships(self, state: AgentState) -> List[Dict[str, Any]]:
        """分析概念关系"""
        relationships = []
        
        concepts = self._extract_core_concepts(state)
        
        # 简单的关系推断（基于检索结果）
        if len(concepts) >= 2 and state.retrieved_knowledge:
            results = state.retrieved_knowledge.get('results', [])
            for result in results[:3]:
                content = result.get('content', '')
                # 检查哪些概念在同一文档中出现
                concepts_in_doc = [c for c in concepts if c in content]
                if len(concepts_in_doc) >= 2:
                    relationships.append({
                        'concepts': concepts_in_doc,
                        'relationship_type': 'co-occurrence',
                        'source': result.get('source', 'unknown')
                    })
        
        return relationships
    
    def _identify_misconceptions(self, state: AgentState) -> List[Dict[str, Any]]:
        """识别已解决的误解"""
        misconceptions = []
        
        # 从用户回答中识别可能的误解
        responses = state.user_responses or []
        
        # 困惑表达可能暗示误解
        confusion_keywords = ['不是', '不对', '搞错', '误解', '混淆', '以为']
        
        for idx, response in enumerate(responses):
            for keyword in confusion_keywords:
                if keyword in response:
                    misconceptions.append({
                        'round': idx + 1,
                        'potential_misconception': response[:100],
                        'addressed': True if idx < len(state.socratic_questions) else False
                    })
                    break
        
        return misconceptions
    
    # ==================== 公共接口 ====================
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像
        
        优先从缓存读取，缓存未命中则从存储加载
        """
        # 先检查缓存
        if user_id in self.user_profiles_cache:
            return self.user_profiles_cache[user_id]
        
        # 从存储加载
        profile = self.storage.load_user_profile(user_id)
        if profile:
            self.user_profiles_cache[user_id] = profile
        
        return profile
    
    def get_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户的会话历史"""
        return self.storage.load_user_session_history(user_id, limit)
    
    def get_learning_records(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户的学习记录
        
        Args:
            user_id: 用户ID
            limit: 返回的最大记录数
            offset: 跳过的记录数（用于分页）
            
        Returns:
            学习记录列表
        """
        # 获取所有记录
        all_records = self.storage.load_learning_records(user_id, limit + offset)
        
        # 应用分页
        return all_records[offset:offset + limit]
    
    def get_user_triples(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """🔧 获取用户的知识三元组
        
        Args:
            user_id: 用户ID
            
        Returns:
            三元组列表，如果用户不存在返回None
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
        
        return profile.get('triples', [])
    
    def get_user_emotions(self, user_id: str) -> Optional[Dict[str, Any]]:
        """🔧 获取用户的情感分析数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            情感分析数据，如果用户不存在返回None
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
        
        emotions_list = profile.get('emotions', [])
        
        # 返回最新的情感数据和历史趋势
        if not emotions_list:
            return {
                'current': None,
                'history': [],
                'trend': 'unknown'
            }
        
        # 获取最新情感
        latest_emotion = emotions_list[-1] if emotions_list else None
        
        # 分析情感趋势
        trend = self._analyze_emotion_trend_from_history(emotions_list)
        
        return {
            'current': latest_emotion,
            'history': emotions_list[-10:],  # 最近10条
            'trend': trend,
            'statistics': self._calculate_emotion_statistics(emotions_list)
        }
    
    def get_learning_patterns(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """🔧 获取用户的学习模式
        
        Args:
            user_id: 用户ID
            
        Returns:
            学习模式列表，如果用户不存在返回None
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
        
        patterns = profile.get('learning_patterns', [])
        
        # 按置信度排序
        sorted_patterns = sorted(
            patterns,
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )
        
        return sorted_patterns
    
    def _analyze_emotion_trend_from_history(self, emotions_list: List[Dict[str, Any]]) -> str:
        """从历史情感数据分析趋势"""
        if len(emotions_list) < 2:
            return 'stable'
        
        # 获取最近5条情感数据
        recent_emotions = emotions_list[-5:]
        emotion_values = {
            'positive': 1.0,
            'curious': 0.5,
            'neutral': 0.0,
            'confused': -0.5,
            'negative': -1.0
        }
        
        # 计算情感值变化
        values = []
        for emotion in recent_emotions:
            emotion_type = emotion.get('primary_emotion', 'neutral')
            value = emotion_values.get(emotion_type, 0.0)
            values.append(value)
        
        # 简单的趋势判断
        if len(values) < 2:
            return 'stable'
        
        avg_change = (values[-1] - values[0]) / len(values)
        
        if avg_change > 0.2:
            return 'improving'
        elif avg_change < -0.2:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_emotion_statistics(self, emotions_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算情感统计数据"""
        if not emotions_list:
            return {
                'total_count': 0,
                'distribution': {},
                'average_confidence': 0.0
            }
        
        # 统计情感分布
        distribution = {}
        total_confidence = 0.0
        
        for emotion in emotions_list:
            emotion_type = emotion.get('primary_emotion', 'neutral')
            confidence = emotion.get('confidence', 0.0)
            
            distribution[emotion_type] = distribution.get(emotion_type, 0) + 1
            total_confidence += confidence
        
        return {
            'total_count': len(emotions_list),
            'distribution': distribution,
            'average_confidence': total_confidence / len(emotions_list) if emotions_list else 0.0
        }
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        storage_stats = self.storage.get_storage_statistics()
        
        return {
            'cache_size': len(self.user_profiles_cache),
            'entity_count': len(self.entity_set),
            'triples_count': sum(len(v) for v in self.triples_store.values()),
            'storage_stats': storage_stats
        }

