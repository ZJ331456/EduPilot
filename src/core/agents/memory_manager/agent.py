#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理器智能体 (MemoryManagerAgent) - 重构版 v3.1

设计理念：
1. 短期记忆：当前会话的学习分析和交互质量评估
2. 长期记忆：用户画像的持久化存储和累积更新
3. 元认知：学习模式识别和知识缺口分析

架构优化：
- 模块化设计：职责清晰分离
- 单一职责：每个模块只负责一个核心功能
- 易于扩展：新增分析器只需添加新模块
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from src.infrastructure.utils import BaseAgent, AgentState

# 导入模块化组件
from .analyzers import (
    InteractionAnalyzer,
    EmotionAnalyzer,
    LearningPatternDetector,
    KnowledgeGapDetector
)
from .extractors import (
    TripleExtractor,
    ProfileInsightGenerator
)
from .managers import (
    ProfileManager,
    SessionManager
)
from .storage import LocalStorageManager, StorageConfig


@dataclass
class UserProfileUpdate:
    """用户画像更新"""
    triples: List[Dict[str, Any]] = field(default_factory=list)
    emotions: Dict[str, Any] = field(default_factory=dict)
    learning_patterns: List[Dict[str, Any]] = field(default_factory=list)
    insights: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MemoryAnalysis:
    """统一的记忆分析结果"""
    interaction: Any  # InteractionAnalysis
    profile_update: UserProfileUpdate
    learning_feedback: Dict[str, Any]
    knowledge_gaps: List[Dict[str, Any]]


class MemoryManagerAgent(BaseAgent):
    """记忆管理器智能体 - 重构版
    
    核心功能：
    1. 短期记忆管理：分析当前会话的交互质量
    2. 长期记忆管理：提取并更新用户画像
    3. 元认知分析：识别学习模式和知识缺口
    
    优化点：
    - 从1780行优化到约300行
    - 模块化设计，职责清晰
    - 易于测试和维护
    """
    
    def __init__(self, storage_config: Optional[StorageConfig] = None):
        super().__init__(
            name="MemoryManager",
            description="统一的记忆管理器：管理短期交互记忆和长期用户画像"
        )
        
        # 初始化组件
        self.interaction_analyzer = InteractionAnalyzer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.pattern_detector = LearningPatternDetector()
        self.gap_detector = KnowledgeGapDetector()
        # 临时禁用 LLM 提取以加快速度
        self.triple_extractor = TripleExtractor(use_llm=False)
        self.insight_generator = ProfileInsightGenerator()
        self.profile_manager = ProfileManager()
        self.session_manager = SessionManager()
        self.storage = LocalStorageManager(storage_config)
        
        self.logger.info("记忆管理器初始化完成（重构版 v3.1）")
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行记忆管理
        
        工作流程：
        1. 短期记忆：分析当前交互
        2. 长期记忆：提取并更新用户画像
        3. 元认知：生成学习反馈和识别知识缺口
        4. 持久化：保存所有数据
        """
        try:
            self.logger.info("开始执行记忆管理（重构版）...")
            
            # 获取用户ID
            user_id = self._get_user_id(state)
            
            # === 1. 短期记忆：交互分析 ===
            interaction_analysis = self.interaction_analyzer.analyze(state)
            self.logger.debug(f"交互质量分数: {interaction_analysis.quality_score:.2f}")
            
            # === 2. 长期记忆：用户画像更新 ===
            profile_update = await self._update_user_profile(user_id, state)
            self.logger.debug(f"新增三元组: {len(profile_update.triples)}")
            
            # === 3. 元认知：学习反馈和知识缺口 ===
            learning_feedback = self._generate_learning_feedback(
                state, interaction_analysis, profile_update
            )
            knowledge_gaps = self.gap_detector.detect(state, interaction_analysis)
            
            # === 4. 构建统一的记忆分析结果 ===
            memory_analysis = MemoryAnalysis(
                interaction=interaction_analysis,
                profile_update=profile_update,
                learning_feedback=learning_feedback,
                knowledge_gaps=knowledge_gaps
            )
            
            # === 5. 持久化 ===
            await self._persist_memory(user_id, state, memory_analysis)
            
            # === 6. 更新状态 ===
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
                f"✅ 记忆管理完成 - 质量分数: {interaction_analysis.quality_score:.2f}, "
                f"新增三元组: {len(profile_update.triples)}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ 记忆管理失败: {e}", exc_info=True)
            state.status = "failed"
            state.error = str(e)
        
        return state
    
    def _get_user_id(self, state: AgentState) -> str:
        """获取用户ID"""
        user_id = state.metadata.get('user_id')
        if not user_id and state.user_context:
            user_id = state.user_context.get('user_id')
        return user_id or 'anonymous'
    
    async def _update_user_profile(self, user_id: str, state: AgentState) -> UserProfileUpdate:
        """更新用户画像
        
        步骤：
        1. 提取用户信息三元组
        2. 进行情感分析
        3. 识别学习模式
        4. 生成画像洞察
        5. 更新画像管理器
        """
        # 1. 提取三元组
        triples = self.triple_extractor.extract(state.user_query)
        
        # 2. 情感分析
        profile = self.profile_manager.get_profile(user_id)
        emotion_history = profile.get('emotions', []) if profile else None
        emotion_analysis = self.emotion_analyzer.analyze(state.user_query, emotion_history)
        
        # 3. 学习模式识别
        learning_patterns = self.pattern_detector.detect(state)
        
        # 4. 生成洞察
        insights = self.insight_generator.generate(triples, emotion_analysis, learning_patterns)
        
        # 5. 更新画像管理器
        self.profile_manager.update_profile(
            user_id, triples, emotion_analysis, learning_patterns, insights
        )
        
        return UserProfileUpdate(
            triples=triples,
            emotions=emotion_analysis,
            learning_patterns=learning_patterns,
            insights=insights
        )
    
    def _generate_learning_feedback(
        self, 
        state: AgentState, 
        interaction: Any,
        profile_update: UserProfileUpdate
    ) -> Dict[str, Any]:
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
            feedback['personalized_insights']['learning_style'] = dominant_pattern.get('pattern', 'unknown')
        
        if profile_update.emotions.get('primary_emotion') == 'confused':
            feedback['recommendations'].append('建议提供更多示例和解释')
        
        return feedback
    
    async def _persist_memory(self, user_id: str, state: AgentState, memory_analysis: MemoryAnalysis):
        """持久化记忆数据"""
        try:
            # 1. 保存用户画像
            profile = self.profile_manager.get_profile(user_id)
            if profile:
                self.storage.save_user_profile(user_id, profile)
            
            # 2. 保存会话记忆
            session_data = self.session_manager.build_session_data(user_id, state, memory_analysis)
            # 添加交互和画像分析结果
            session_data['interaction_analysis'] = asdict(memory_analysis.interaction)
            session_data['profile_update'] = asdict(memory_analysis.profile_update)
            self.storage.save_session_memory(state.session_id, session_data)
            
            # 3. 保存学习记录（详细版）
            learning_data = self._build_learning_record(user_id, state, memory_analysis)
            self.storage.save_learning_record(user_id, learning_data)
            
            self.logger.debug(f"记忆数据已持久化: {user_id}")
            
        except Exception as e:
            self.logger.error(f"持久化记忆数据失败: {e}")
    
    def _build_learning_record(
        self, 
        user_id: str, 
        state: AgentState, 
        memory_analysis: MemoryAnalysis
    ) -> Dict[str, Any]:
        """构建学习记录"""
        return {
            # 基础反馈
            'learning_feedback': memory_analysis.learning_feedback,
            'knowledge_gaps': memory_analysis.knowledge_gaps,
            'quality_score': memory_analysis.interaction.quality_score,
            
            # 学习内容详情
            'learning_content': {
                'topic': state.current_focus or state.user_query,
                'concepts_learned': self._extract_concepts(state),
                'depth_level': state.understanding_level.value if state.understanding_level else 'no_understanding'
            },
            
            # 知识掌握度
            'knowledge_mastery': {
                'understanding_score': self._calculate_understanding_score(state)
            },
            
            # 学习进度
            'learning_progress': {
                'session_id': state.session_id,
                'total_interactions': state.conversation_round,
                'questions_asked': len(state.socratic_questions or []),
                'responses_given': len(state.user_responses or []),
                'engagement_metrics': {
                    'engagement_level': memory_analysis.interaction.engagement_level,
                    'learning_value': memory_analysis.interaction.learning_value,
                    'knowledge_coverage': memory_analysis.interaction.knowledge_coverage
                }
            },
            
            # 时间戳
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_concepts(self, state: AgentState) -> List[str]:
        """提取学到的概念"""
        concepts = []
        if state.interpretation and 'concepts' in state.interpretation:
            concepts.extend(state.interpretation['concepts'])
        return list(set(concepts))
    
    def _calculate_understanding_score(self, state: AgentState) -> float:
        """计算理解分数"""
        if not state.understanding_level:
            return 0.0
        
        level_scores = {0: 0.0, 1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}
        base_score = level_scores.get(state.understanding_level.level_value, 0.0)
        
        if state.conversation_round > 1:
            engagement_bonus = min(0.1, state.conversation_round * 0.02)
            base_score = min(1.0, base_score + engagement_bonus)
        
        return round(base_score, 2)
    
    # ========== 公共接口 ==========
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            profile = self.storage.load_user_profile(user_id)
            if profile:
                # 加载到缓存
                self.profile_manager.profiles_cache[user_id] = profile
        return profile
    
    def get_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户的会话历史"""
        return self.storage.load_user_session_history(user_id, limit)
    
    def get_learning_records(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户的学习记录"""
        all_records = self.storage.load_learning_records(user_id, limit + offset)
        return all_records[offset:offset + limit]
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        profile_stats = self.profile_manager.get_statistics()
        storage_stats = self.storage.get_storage_statistics()
        
        return {
            'profile_stats': profile_stats,
            'storage_stats': storage_stats
        }
    
    def get_user_triples(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的知识三元组"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return []
            
            # 尝试两种字段名（兼容性）
            triples = profile.get('triples', profile.get('knowledge_triples', []))
            result = triples if isinstance(triples, list) else []
            self.logger.info(f"Agent - get_user_triples: profile keys={list(profile.keys())}, triples count={len(result)}")
            return result
        except Exception as e:
            self.logger.error(f"获取用户三元组失败: {e}")
            return []
    
    def get_user_emotions(self, user_id: str) -> Dict[str, Any]:
        """获取用户的情感状态"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                self.logger.info(f"Agent - get_user_emotions: No profile for user {user_id}")
                return None
            
            self.logger.info(f"Agent - get_user_emotions: profile keys={list(profile.keys())}")
            
            # 从 emotions 列表中获取最新的情感数据
            emotions_list = profile.get('emotions', [])
            if not emotions_list:
                self.logger.debug(f"get_user_emotions: No emotions data")
                return None
            
            # 构建前端期望的格式
            latest_emotion = emotions_list[-1] if emotions_list else {}
            
            # 统计情感分布
            emotion_counts = {}
            for emotion in emotions_list:
                primary = emotion.get('primary_emotion', 'neutral')
                emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
            
            # 判断趋势
            trend = "stable"
            if len(emotions_list) >= 2:
                # 简单的趋势判断逻辑
                recent_emotions = [e.get('primary_emotion') for e in emotions_list[-3:]]
                positive_emotions = ['positive', 'curious', 'confident']
                if all(e in positive_emotions for e in recent_emotions):
                    trend = "improving"
            
            return {
                "current": {
                    "primary_emotion": latest_emotion.get('primary_emotion', 'neutral'),
                    "confidence": latest_emotion.get('confidence', 0.0)
                },
                "trend": trend,
                "statistics": {
                    "distribution": emotion_counts,
                    "total_count": len(emotions_list)
                }
            }
        except Exception as e:
            self.logger.error(f"获取用户情感状态失败: {e}")
            return None
    
    def get_learning_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的学习模式"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return []
            
            self.logger.info(f"Agent - get_learning_patterns: profile keys={list(profile.keys())}")
            
            # 从 profile 中提取学习模式
            patterns_data = profile.get('learning_patterns', [])
            
            # 确保返回正确的格式
            formatted_patterns = []
            for pattern in patterns_data:
                if isinstance(pattern, dict):
                    formatted_patterns.append({
                        "pattern": pattern.get('pattern', 'unknown'),
                        "confidence": pattern.get('confidence', 0.0),
                        "indicators": pattern.get('indicators', [])
                    })
            
            return formatted_patterns
        except Exception as e:
            self.logger.error(f"获取用户学习模式失败: {e}")
            return []
    
    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户画像"""
        try:
            # 获取现有画像
            profile = self.get_user_profile(user_id)
            if not profile:
                profile = {
                    'user_id': user_id,
                    'knowledge_triples': [],
                    'emotional_state': {},
                    'learning_patterns': {},
                    'total_interactions': 0,
                }
            
            # 更新数据
            if 'knowledge_triples' in update_data:
                profile['knowledge_triples'].extend(update_data['knowledge_triples'])
            
            if 'emotional_state' in update_data:
                profile['emotional_state'].update(update_data['emotional_state'])
            
            if 'learning_patterns' in update_data:
                profile['learning_patterns'].update(update_data['learning_patterns'])
            
            # 保存更新后的画像
            self.storage.save_user_profile(user_id, profile)
            
            return {
                'success': True,
                'message': '用户画像更新成功',
                'profile': profile
            }
        except Exception as e:
            self.logger.error(f"更新用户画像失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话记忆"""
        try:
            return self.storage.load_session_memory(session_id)
        except Exception as e:
            self.logger.error(f"获取会话记忆失败: {e}")
            return None