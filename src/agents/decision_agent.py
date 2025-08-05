#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策代理智能体
根据用户查询判断是否需要知识检索，并优化查询拆分策略
实现二级索引的完美匹配：一级是知识库标题/核心概念；二级是相关概念的阐述
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from utils import BaseAgent, AgentState, QueryType
from utils.llm import get_llm_manager, Message, MessageRole

class DecisionAgent(BaseAgent):
    """决策代理智能体
    
    负责：
    1. 判断是否需要进行知识检索
    2. 优化查询拆分，提高检索效果
    3. 实现一级索引的完美匹配策略
    4. 为二级检索提供精准的查询条件
    """
    
    def __init__(self):
        super().__init__(
            name="DecisionAgent",
            description="决策是否进行知识检索并优化查询拆分策略"
        )
        
        # 导入配置管理器
        from config import get_agent_config
        
        decision_config = get_agent_config('decision_agent')
        
        # 不需要知识检索的查询类型
        self.no_retrieval_patterns = decision_config.get('no_retrieval_patterns', [
            r"你好|您好|hello|hi",
            r"谢谢|感谢|thank",
            r"再见|拜拜|goodbye|bye",
            r"今天天气|现在几点|当前时间",
            r"计算|算一下|\d+[+\-*/]\d+",
            r"翻译.*成|translate.*to"
        ])
        
        # 需要知识检索的强指示词
        self.strong_retrieval_indicators = decision_config.get('strong_retrieval_indicators', [
            r"什么是|介绍一下|解释|说明|定义",
            r".*的概念|.*的含义|.*的定义|.*的特点",
            r".*的历史|.*的发展|.*的起源",
            r".*的作用|.*的功能|.*的意义",
            r".*的分类|.*的类型|.*的种类",
            r".*的原理|.*的机制|.*的过程"
        ])
        
        # 核心概念提取模式
        self.concept_patterns = [
            r"(\w+)是什么",
            r"什么是(\w+)",
            r"介绍一下(\w+)",
            r"(\w+)的概念",
            r"(\w+)的定义",
            r"(\w+)的含义",
            r"解释(\w+)",
            r"说明(\w+)"
        ]
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行
        
        决策代理应该在查询解释之后、知识检索之前执行
        """
        return (
            bool(state.user_query.strip()) and
            not hasattr(state, 'retrieval_decision')  # 放宽条件：不强制要求interpretation
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行决策分析
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 1. 判断是否需要知识检索
            retrieval_decision = self._decide_knowledge_retrieval(state)
            
            # 2. 如果需要检索，进行查询优化
            if retrieval_decision['need_retrieval']:
                query_optimization = self._optimize_query_for_retrieval(state)
                retrieval_decision.update(query_optimization)
            
            # 3. 更新状态
            state.retrieval_decision = retrieval_decision
            
            self.logger.info(
                f"Decision made - Need retrieval: {retrieval_decision['need_retrieval']}, "
                f"Confidence: {retrieval_decision['confidence']:.2f}"
            )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Decision analysis failed: {e}")
            state.set_error(
                "decision_analysis_error",
                f"Failed to analyze retrieval decision: {str(e)}"
            )
            return state
    
    def _decide_knowledge_retrieval(self, state: AgentState) -> Dict[str, Any]:
        """判断是否需要进行知识检索
        
        Args:
            state: 当前状态
            
        Returns:
            决策结果字典
        """
        query = state.user_query.lower().strip()
        
        # 1. 检查明确不需要检索的模式
        for pattern in self.no_retrieval_patterns:
            if re.search(pattern, query):
                return {
                    'need_retrieval': False,
                    'reason': 'matched_no_retrieval_pattern',
                    'matched_pattern': pattern,
                    'confidence': 0.9
                }
        
        # 2. 检查强烈需要检索的指示词
        strong_indicators = 0
        matched_indicators = []
        
        for pattern in self.strong_retrieval_indicators:
            if re.search(pattern, query):
                strong_indicators += 1
                matched_indicators.append(pattern)
        
        # 3. 基于查询类型判断
        query_type_score = self._get_query_type_retrieval_score(state.query_type)
        
        # 4. 基于查询长度和复杂度判断
        complexity_score = self._assess_query_complexity(query)
        
        # 5. 综合决策
        total_score = (
            strong_indicators * 0.4 +  # 强指示词权重
            query_type_score * 0.3 +   # 查询类型权重
            complexity_score * 0.3     # 复杂度权重
        )
        
        need_retrieval = total_score > 0.5
        confidence = min(total_score, 1.0)
        
        return {
            'need_retrieval': need_retrieval,
            'confidence': confidence,
            'strong_indicators': strong_indicators,
            'matched_indicators': matched_indicators,
            'query_type_score': query_type_score,
            'complexity_score': complexity_score,
            'total_score': total_score,
            'reason': 'comprehensive_analysis'
        }
    
    def _get_query_type_retrieval_score(self, query_type: QueryType) -> float:
        """根据查询类型获取检索需求分数
        
        Args:
            query_type: 查询类型
            
        Returns:
            检索需求分数 (0.0-1.0)
        """
        type_scores = {
            QueryType.KNOWLEDGE_RETRIEVAL: 1.0,
            QueryType.CONCEPT_EXPLANATION: 0.9,
            QueryType.LEARNING_GUIDANCE: 0.8,
            QueryType.SOCRATIC_DIALOGUE: 0.7,
            QueryType.DIRECT_ANSWER: 0.6
        }
        
        return type_scores.get(query_type, 0.5)
    
    def _assess_query_complexity(self, query: str) -> float:
        """评估查询复杂度
        
        Args:
            query: 用户查询
            
        Returns:
            复杂度分数 (0.0-1.0)
        """
        # 基于查询长度
        length_score = min(len(query) / 50, 1.0)
        
        # 基于专业词汇数量
        professional_terms = 0
        for word in query.split():
            if len(word) > 3 and any(char in word for char in '学理论概念原理机制'):
                professional_terms += 1
        
        term_score = min(professional_terms / 3, 1.0)
        
        # 基于问句复杂度
        question_complexity = 0
        complex_patterns = [r"为什么.*而不是", r".*和.*的区别", r".*的优缺点", r".*的影响因素"]
        for pattern in complex_patterns:
            if re.search(pattern, query):
                question_complexity += 0.3
        
        return (length_score * 0.3 + term_score * 0.4 + min(question_complexity, 1.0) * 0.3)
    
    def _optimize_query_for_retrieval(self, state: AgentState) -> Dict[str, Any]:
        """优化查询以提高检索效果
        
        实现二级索引策略：
        1. 提取核心概念作为一级索引
        2. 生成相关查询词作为二级索引
        3. 构建多层次查询策略
        
        Args:
            state: 当前状态
            
        Returns:
            查询优化结果
        """
        query = state.user_query
        
        # 1. 提取核心概念（一级索引）
        core_concepts = self._extract_core_concepts(query)
        
        # 2. 生成相关查询词（二级索引）
        related_queries = self._generate_related_queries(query, core_concepts)
        
        # 3. 构建查询策略
        query_strategy = self._build_query_strategy(core_concepts, related_queries)
        
        # 4. 生成优化后的查询列表
        optimized_queries = self._generate_optimized_queries(query, query_strategy)
        
        return {
            'core_concepts': core_concepts,
            'related_queries': related_queries,
            'query_strategy': query_strategy,
            'optimized_queries': optimized_queries,
            'original_query': query
        }
    
    def _extract_core_concepts(self, query: str) -> List[str]:
        """提取核心概念
        
        Args:
            query: 用户查询
            
        Returns:
            核心概念列表
        """
        concepts = []
        
        # 使用正则表达式提取概念
        for pattern in self.concept_patterns:
            matches = re.findall(pattern, query)
            concepts.extend(matches)
        
        # 移除重复和过短的概念
        concepts = list(set([c for c in concepts if len(c) > 1]))
        
        # 如果没有提取到概念，尝试从查询中提取名词
        if not concepts:
            concepts = self._extract_nouns_from_query(query)
        
        return concepts[:3]  # 最多返回3个核心概念
    
    def _extract_nouns_from_query(self, query: str) -> List[str]:
        """从查询中提取可能的名词概念
        
        Args:
            query: 用户查询
            
        Returns:
            名词列表
        """
        # 简单的名词提取策略
        words = query.split()
        nouns = []
        
        # 过滤掉常见的非名词词汇
        stop_words = {'什么', '是', '的', '了', '在', '有', '和', '与', '或', '但', '而', '因为', '所以'}
        
        for word in words:
            # 移除标点符号
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 1 and clean_word not in stop_words:
                nouns.append(clean_word)
        
        return nouns[:3]
    
    def _generate_related_queries(self, original_query: str, core_concepts: List[str]) -> List[str]:
        """生成相关查询词
        
        Args:
            original_query: 原始查询
            core_concepts: 核心概念列表
            
        Returns:
            相关查询词列表
        """
        related_queries = []
        
        for concept in core_concepts:
            # 为每个核心概念生成相关查询
            concept_queries = [
                f"{concept}的定义",
                f"{concept}的概念",
                f"{concept}是什么",
                f"{concept}的特点",
                f"{concept}的作用",
                f"{concept}的原理"
            ]
            related_queries.extend(concept_queries)
        
        # 去重并限制数量
        return list(set(related_queries))[:10]
    
    def _build_query_strategy(self, core_concepts: List[str], related_queries: List[str]) -> Dict[str, Any]:
        """构建查询策略
        
        Args:
            core_concepts: 核心概念列表
            related_queries: 相关查询列表
            
        Returns:
            查询策略字典
        """
        return {
            'primary_strategy': 'concept_matching',  # 主要策略：概念匹配
            'secondary_strategy': 'semantic_expansion',  # 次要策略：语义扩展
            'fallback_strategy': 'keyword_search',  # 备用策略：关键词搜索
            'priority_order': [
                'exact_concept_match',  # 精确概念匹配
                'partial_concept_match',  # 部分概念匹配
                'related_concept_match',  # 相关概念匹配
                'keyword_match'  # 关键词匹配
            ],
            'concept_weights': {concept: 1.0 - i * 0.1 for i, concept in enumerate(core_concepts)}
        }
    
    def _generate_optimized_queries(self, original_query: str, query_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成优化后的查询列表
        
        Args:
            original_query: 原始查询
            query_strategy: 查询策略
            
        Returns:
            优化查询列表
        """
        optimized_queries = []
        
        # 1. 原始查询（最高优先级）
        optimized_queries.append({
            'query': original_query,
            'type': 'original',
            'priority': 1.0,
            'strategy': 'exact_match'
        })
        
        # 2. 核心概念查询
        for concept, weight in query_strategy.get('concept_weights', {}).items():
            optimized_queries.append({
                'query': concept,
                'type': 'core_concept',
                'priority': weight * 0.9,
                'strategy': 'concept_match'
            })
        
        # 3. 组合概念查询
        concepts = list(query_strategy.get('concept_weights', {}).keys())
        if len(concepts) > 1:
            for i in range(len(concepts)):
                for j in range(i + 1, len(concepts)):
                    combined_query = f"{concepts[i]} {concepts[j]}"
                    optimized_queries.append({
                        'query': combined_query,
                        'type': 'combined_concept',
                        'priority': 0.7,
                        'strategy': 'multi_concept_match'
                    })
        
        # 按优先级排序
        optimized_queries.sort(key=lambda x: x['priority'], reverse=True)
        
        return optimized_queries[:5]  # 最多返回5个优化查询
    
    def get_retrieval_recommendation(self, state: AgentState) -> Dict[str, Any]:
        """获取检索建议
        
        Args:
            state: 当前状态
            
        Returns:
            检索建议字典
        """
        if not hasattr(state, 'retrieval_decision'):
            return {'error': 'No retrieval decision available'}
        
        decision = state.retrieval_decision
        
        if not decision['need_retrieval']:
            return {
                'recommendation': 'skip_retrieval',
                'reason': decision.get('reason', 'Not needed'),
                'confidence': decision['confidence']
            }
        
        return {
            'recommendation': 'proceed_with_retrieval',
            'optimized_queries': decision.get('optimized_queries', []),
            'query_strategy': decision.get('query_strategy', {}),
            'confidence': decision['confidence']
        }