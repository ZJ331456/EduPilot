#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理器 - 负责会话记忆的管理
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from src.infrastructure.utils import AgentState


class SessionManager:
    """会话管理器
    
    职责：
    1. 构建对话历史
    2. 提取执行信息
    3. 汇总知识检索信息
    4. 生成会话摘要
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def build_session_data(self, user_id: str, state: AgentState, memory_analysis: Any) -> Dict[str, Any]:
        """构建会话数据
        
        Args:
            user_id: 用户ID
            state: 当前状态
            memory_analysis: 记忆分析结果
            
        Returns:
            完整的会话数据
        """
        return {
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
            
            # 元数据
            'metadata': {
                'conversation_complete': state.metadata.get('conversation_complete', False),
                'waiting_for_user': state.metadata.get('waiting_for_user', False),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _build_dialogue_history(self, state: AgentState) -> List[Dict[str, Any]]:
        """构建完整的对话历史
        
        🔧 修复：正确构建对话历史，确保问题和回答正确对应
        """
        dialogue_history = []
        
        if hasattr(state, 'dialogue_history') and state.dialogue_history:
            # 如果state已有完整的dialogue_history，直接使用
            dialogue_history = state.dialogue_history
        else:
            # 🔧 从苏格拉底问答构建对话历史
            questions = state.socratic_questions or []
            responses = state.user_responses or []
            
            for i in range(max(len(questions), len(responses))):
                turn = {
                    'round': i + 1,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 🔧 处理问题（可能是字典或字符串）
                if i < len(questions):
                    question_data = questions[i]
                    if isinstance(question_data, dict):
                        turn['question'] = question_data
                    else:
                        # 如果是字符串，包装成字典
                        turn['question'] = {
                            'question': question_data,
                            'type': 'unknown'
                        }
                
                # 🔧 处理用户回答
                if i < len(responses):
                    turn['response'] = responses[i]
                    turn['response_timestamp'] = datetime.now().isoformat()
                
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
            'top_results': results[:3] if results else [],
            'knowledge_snippets': [r.get('content', '')[:200] for r in results[:3]]
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

