#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询解释与分类智能体（整合版）
集成查询意图分析、类型判断和普通问答/苏格拉底式提问分类功能
使用大模型进行智能判断，基于最新的对话系统研究优化
"""
import re
import logging
import json
from typing import Dict, Any, List, Optional
from utils import BaseAgent, AgentState, QueryType
from utils.llm import get_llm_manager, Message, MessageRole
from prompts import get_prompt, PromptType

class QueryInterpreterAgent(BaseAgent):
    """查询解释与分类智能体（整合版）
    
    功能：
    1. 使用大模型分析用户查询意图和类型
    2. 智能分类为普通问答或苏格拉底式提问模式
    3. 提取关键词和上下文信息
    4. 基于上下文感知的意图识别
    """
    
    def __init__(self):
        super().__init__("QueryInterpreter", "查询解释与分类：意图分析和模式判断")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_manager = get_llm_manager()
        
        # 意图分类模式（基于BERT-Intent和DialoGPT研究）
        self.intent_patterns = {
            'identity_inquiry': {
                'patterns': [
                    r'你是什么.*模型', r'你是什么.*ai', r'你是什么.*系统',
                    r'你是谁', r'你的名字', r'基座模型', r'底层模型',
                    r'你基于.*模型', r'你使用.*模型'
                ],
                'confidence': 0.95,
                'query_type': QueryType.DIRECT_ANSWER,
                'socratic_probability': 0.05
            },
            'capability_inquiry': {
                'patterns': [
                    r'你能做什么', r'你有什么功能', r'你会什么',
                    r'你的能力', r'你能帮什么', r'你可以.*吗',
                    r'你会不会.*', r'你能.*吗'
                ],
                'confidence': 0.9,
                'query_type': QueryType.DIRECT_ANSWER,
                'socratic_probability': 0.1
            },
            'greeting': {
                'patterns': [
                    r'^你好$', r'^您好$', r'^hi$', r'^hello$',
                    r'^嗨$', r'^早上好$', r'^下午好$', r'^晚上好$',
                    r'^good morning$', r'^good afternoon$', r'^good evening$'
                ],
                'confidence': 0.95,
                'query_type': QueryType.DIRECT_ANSWER,
                'socratic_probability': 0.05
            },
            'system_help': {
                'patterns': [
                    r'系统', r'设置', r'配置', r'帮助', r'说明',
                    r'使用方法', r'怎么用', r'如何使用'
                ],
                'confidence': 0.85,
                'query_type': QueryType.DIRECT_ANSWER,
                'socratic_probability': 0.15
            },
            'topic_switch': {
                'patterns': [
                    r'换个话题', r'说点别的', r'我们聊点别的',
                    r'换个问题', r'不谈这个了', r'换个方向'
                ],
                'confidence': 0.9,
                'query_type': QueryType.DIRECT_ANSWER,
                'socratic_probability': 0.1
            },
            'knowledge_retrieval': {
                'patterns': [
                    r'什么是.*', r'如何.*', r'怎么.*', r'为什么.*',
                    r'.*是什么', r'.*的定义', r'.*的概念',
                    r'请介绍.*', r'请解释.*', r'请说明.*'
                ],
                'confidence': 0.8,
                'query_type': QueryType.KNOWLEDGE_RETRIEVAL,
                'socratic_probability': 0.3
            },
            'concept_explanation': {
                'patterns': [
                    r'深入.*', r'详细.*', r'全面.*', r'系统.*',
                    r'深入理解.*', r'深度分析.*', r'全面解释.*'
                ],
                'confidence': 0.85,
                'query_type': QueryType.CONCEPT_EXPLANATION,
                'socratic_probability': 0.4
            },
            'learning_guidance': {
                'patterns': [
                    r'学习.*', r'如何学习.*', r'学习方法.*',
                    r'学习建议.*', r'学习路径.*', r'学习计划.*'
                ],
                'confidence': 0.8,
                'query_type': QueryType.LEARNING_GUIDANCE,
                'socratic_probability': 0.5
            },
            'socratic_dialogue': {
                'patterns': [
                    r'思考.*', r'反思.*', r'探讨.*', r'讨论.*',
                    r'你认为.*', r'你觉得.*', r'你怎么看.*',
                    r'为什么.*重要', r'.*的意义', r'.*的价值'
                ],
                'confidence': 0.9,
                'query_type': QueryType.SOCRATIC_DIALOGUE,
                'socratic_probability': 0.8
            }
        }
        
        # 上下文关键词（用于相关性判断）
        self.context_keywords = {
            'technical': ['算法', '编程', '代码', '机器学习', '人工智能', '深度学习', '神经网络'],
            'academic': ['研究', '论文', '学术', '理论', '方法', '分析'],
            'practical': ['应用', '实践', '项目', '工具', '技术', '实现'],
            'philosophical': ['思考', '哲学', '意义', '价值', '本质', '原理']
        }
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return bool(state.user_query and state.user_query.strip())
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行查询解释与分类"""
        try:
            self.logger.info("执行查询解释与分类...")
            
            # 预处理查询
            processed_query = self._preprocess_query(state.user_query)
            
            # 使用大模型进行智能分析
            analysis_result = await self._analyze_with_llm(processed_query, state)
            
            # 如果LLM分析失败，使用增强的规则分析
            if not analysis_result:
                analysis_result = self._enhanced_rule_analysis(processed_query, state)
            
            # 更新状态
            state.query_type = analysis_result['query_type']
            state.interpretation = {
                'query_type': analysis_result['query_type'].value,
                'keywords': analysis_result['keywords'],
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence'],
                'mode_classification': analysis_result['mode_classification'],
                'processed_query': processed_query,
                'llm_analysis': analysis_result['llm_analysis'],
                'context_analysis': analysis_result.get('context_analysis', {})
            }
            state.metadata.update({
                'processed_query': processed_query,
                'keywords': analysis_result['keywords'],
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence'],
                'mode_classification': analysis_result['mode_classification'],
                'query_analysis': {
                    'type': analysis_result['query_type'].value,
                    'keywords': analysis_result['keywords'],
                    'intent': analysis_result['intent'],
                    'confidence': analysis_result['confidence'],
                    'llm_reasoning': analysis_result['llm_analysis']['reasoning'],
                    'context_relevance': analysis_result.get('context_analysis', {}).get('relevance', 0.0)
                }
            })
            
            state.status = "completed"
            self.logger.info(f"查询分析完成: {analysis_result['mode_classification']['recommended_mode']} 模式")
            
        except Exception as e:
            self.logger.error(f"查询解释失败: {e}")
            # 使用备用方法
            fallback_result = self._fallback_analysis(state.user_query)
            state.query_type = fallback_result['query_type']
            state.interpretation = fallback_result
            state.status = "completed"
            
        return state
    
    async def _analyze_with_llm(self, query: str, state: AgentState) -> Dict[str, Any]:
        """使用大模型进行智能分析"""
        
        # 使用统一的prompt
        system_prompt = get_prompt(PromptType.QUERY_INTERPRETATION)
        
        # 构建上下文信息
        context_info = self._build_context_info(state)
        
        user_prompt = f"""请分析以下查询：

查询内容：{query}
用户上下文：{context_info}
对话历史：{self._get_conversation_history(state)}

请提供详细的分析结果。"""

        try:
            # 调用大模型
            response = await self.llm_manager.async_generate_response(
                user_input=user_prompt,
                system_prompt=system_prompt
            )
            
            # 解析响应
            llm_response = response.strip()
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                raise ValueError("无法解析LLM响应中的JSON")
            
            # 直接使用LLM返回的意图，如果已经是标准标识符
            intent = analysis_data.get('intent', '')
            if intent in ['identity_inquiry', 'capability_inquiry', 'greeting', 'system_help', 
                         'topic_switch', 'knowledge_retrieval', 'concept_explanation', 
                         'learning_guidance', 'socratic_dialogue']:
                # LLM已经返回了标准标识符
                pass
            else:
                # 需要映射到标准化标识符
                intent = self._map_intent_to_standard(intent)
            
            # 基于意图修正查询类型
            query_type = self._convert_query_type_with_intent(
                analysis_data.get('query_type', ''), 
                intent
            )
            
            # 添加上下文分析
            context_analysis = self._analyze_context(query, state)
            
            return {
                'query_type': query_type,
                'keywords': analysis_data.get('keywords', []),
                'intent': intent,
                'confidence': float(analysis_data.get('confidence', 0.8)),
                'mode_classification': analysis_data.get('mode_classification', {}),
                'llm_analysis': {
                    'raw_response': llm_response,
                    'reasoning': analysis_data.get('reasoning', ''),
                    'confidence': float(analysis_data.get('confidence', 0.8))
                },
                'context_analysis': context_analysis
            }
            
        except Exception as e:
            self.logger.warning(f"LLM分析失败，使用增强规则分析: {e}")
            return None
    
    def _enhanced_rule_analysis(self, query: str, state: AgentState) -> Dict[str, Any]:
        """增强的规则分析方法（基于模式匹配和上下文分析）"""
        
        # 1. 模式匹配
        intent_result = self._pattern_matching(query)
        
        # 2. 上下文分析
        context_analysis = self._analyze_context(query, state)
        
        # 3. 关键词提取
        keywords = self._extract_keywords(query)
        
        # 4. 置信度调整
        confidence = self._adjust_confidence(intent_result['confidence'], context_analysis)
        
        # 5. 苏格拉底概率调整
        socratic_prob = self._adjust_socratic_probability(
            intent_result['socratic_probability'], 
            context_analysis, 
            keywords
        )
        
        return {
            'query_type': intent_result['query_type'],
            'keywords': keywords,
            'intent': intent_result['intent'],
            'confidence': confidence,
            'mode_classification': {
                'recommended_mode': 'socratic' if socratic_prob > 0.5 else 'normal',
                'socratic_probability': socratic_prob,
                'normal_probability': 1 - socratic_prob,
                'confidence': confidence,
                'reasoning': intent_result['reasoning']
            },
            'llm_analysis': {
                'raw_response': '使用增强规则分析',
                'reasoning': intent_result['reasoning'],
                'confidence': confidence
            },
            'context_analysis': context_analysis
        }
    
    def _pattern_matching(self, query: str) -> Dict[str, Any]:
        """基于正则表达式的模式匹配"""
        query_lower = query.lower()
        
        for intent_name, intent_config in self.intent_patterns.items():
            for pattern in intent_config['patterns']:
                if re.search(pattern, query_lower):
                    return {
                        'intent': intent_name,
                        'query_type': intent_config['query_type'],
                        'confidence': intent_config['confidence'],
                        'socratic_probability': intent_config['socratic_probability'],
                        'reasoning': f'匹配到{intent_name}模式'
                    }
        
        # 默认分类
        return {
            'intent': 'general_inquiry',
            'query_type': QueryType.KNOWLEDGE_RETRIEVAL,
            'confidence': 0.7,
            'socratic_probability': 0.3,
            'reasoning': '未匹配到特定模式，默认为一般查询'
        }
    
    def _analyze_context(self, query: str, state: AgentState) -> Dict[str, Any]:
        """分析查询与上下文的相关性"""
        context_relevance = 0.0
        context_type = 'none'
        
        # 分析查询中的关键词类型
        query_keywords = set(self._extract_keywords(query))
        
        # 改进的上下文关键词匹配
        context_matches = {}
        
        for context_type_name, keywords in self.context_keywords.items():
            # 计算匹配度
            common_keywords = query_keywords & set(keywords)
            if common_keywords:
                # 使用更精确的匹配算法
                match_score = len(common_keywords) / max(len(query_keywords), 1)
                context_matches[context_type_name] = match_score
        
        # 选择最佳匹配
        if context_matches:
            best_context = max(context_matches.items(), key=lambda x: x[1])
            context_type = best_context[0]
            context_relevance = best_context[1]
        
        # 特殊处理：哲学思考类查询
        philosophical_keywords = ['思考', '反思', '探讨', '讨论', '认为', '觉得', '意义', '价值', '本质', '原理']
        if any(keyword in query for keyword in philosophical_keywords):
            context_type = 'philosophical'
            context_relevance = max(context_relevance, 0.8)
        
        return {
            'relevance': context_relevance,
            'type': context_type,
            'keywords': list(query_keywords),
            'matches': context_matches
        }
    
    def _adjust_confidence(self, base_confidence: float, context_analysis: Dict[str, Any]) -> float:
        """根据上下文调整置信度"""
        # 如果上下文相关性高，提高置信度
        if context_analysis['relevance'] > 0.5:
            return min(base_confidence + 0.1, 1.0)
        return base_confidence
    
    def _adjust_socratic_probability(self, base_prob: float, context_analysis: Dict[str, Any], keywords: List[str]) -> float:
        """根据上下文和关键词调整苏格拉底概率"""
        adjusted_prob = base_prob
        
        # 根据上下文类型调整
        if context_analysis['type'] == 'philosophical':
            adjusted_prob += 0.2
        elif context_analysis['type'] == 'academic':
            adjusted_prob += 0.1
        
        # 根据关键词调整
        socratic_keywords = ['为什么', '如何', '思考', '理解', '意义', '价值']
        if any(keyword in keywords for keyword in socratic_keywords):
            adjusted_prob += 0.15
        
        return min(adjusted_prob, 1.0)
    
    def _build_context_info(self, state: AgentState) -> str:
        """构建上下文信息"""
        context_parts = []
        
        if state.user_context:
            context_parts.append(f"用户信息: {state.user_context}")
        
        if hasattr(state, 'conversation_round') and state.conversation_round:
            context_parts.append(f"对话轮次: {state.conversation_round}")
        
        if hasattr(state, 'conversation_stage') and state.conversation_stage:
            context_parts.append(f"对话阶段: {state.conversation_stage.value}")
        
        return " | ".join(context_parts) if context_parts else "无"
    
    def _get_conversation_history(self, state: AgentState) -> str:
        """获取对话历史（简化版）"""
        # 这里可以扩展为获取完整的对话历史
        return f"当前查询: {state.user_query}"
    
    def _convert_query_type(self, type_str: str) -> QueryType:
        """转换查询类型字符串为枚举"""
        # 先尝试直接匹配（包括小写）
        direct_mapping = {
            'DIRECT_ANSWER': QueryType.DIRECT_ANSWER,
            'KNOWLEDGE_RETRIEVAL': QueryType.KNOWLEDGE_RETRIEVAL,
            'CONCEPT_EXPLANATION': QueryType.CONCEPT_EXPLANATION,
            'LEARNING_GUIDANCE': QueryType.LEARNING_GUIDANCE,
            'SOCRATIC_DIALOGUE': QueryType.SOCRATIC_DIALOGUE,
            # 小写版本
            'direct_answer': QueryType.DIRECT_ANSWER,
            'knowledge_retrieval': QueryType.KNOWLEDGE_RETRIEVAL,
            'concept_explanation': QueryType.CONCEPT_EXPLANATION,
            'learning_guidance': QueryType.LEARNING_GUIDANCE,
            'socratic_dialogue': QueryType.SOCRATIC_DIALOGUE,
            # 特殊映射
            'greeting': QueryType.DIRECT_ANSWER,
            'identity_inquiry': QueryType.DIRECT_ANSWER,
            'capability_inquiry': QueryType.DIRECT_ANSWER,
            'system_help': QueryType.DIRECT_ANSWER,
            'topic_switch': QueryType.DIRECT_ANSWER
        }
        
        # 先尝试直接匹配
        if type_str in direct_mapping:
            return direct_mapping[type_str]
        
        # 再尝试大写匹配
        return direct_mapping.get(type_str.upper(), QueryType.KNOWLEDGE_RETRIEVAL)
    
    def _map_intent_to_standard(self, llm_intent: str) -> str:
        """将LLM返回的自然语言意图映射到标准化标识符"""
        llm_intent_lower = llm_intent.lower()
        
        # 身份询问映射 - 更精确的匹配
        identity_keywords = ['模型', 'ai', '系统', '基座', '底层', '基于', '使用', '询问', '了解']
        if any(keyword in llm_intent_lower for keyword in identity_keywords):
            # 进一步检查是否包含身份相关词汇
            if any(word in llm_intent_lower for word in ['你是什么', '你是谁', '你的', '身份']):
                return 'identity_inquiry'
        
        # 功能询问映射
        capability_keywords = ['功能', '能力', '可以', '能够', '会', '帮', '做什么', '写代码', '协助']
        if any(keyword in llm_intent_lower for keyword in capability_keywords):
            return 'capability_inquiry'
        
        # 问候映射
        greeting_keywords = ['问候', '打招呼', '你好', '早上好', '下午好', '晚上好', 'hi', 'hello']
        if any(keyword in llm_intent_lower for keyword in greeting_keywords):
            return 'greeting'
        
        # 系统帮助映射
        system_keywords = ['系统', '使用', '帮助', '说明', '配置', '设置']
        if any(keyword in llm_intent_lower for keyword in system_keywords):
            return 'system_help'
        
        # 话题切换映射
        topic_switch_keywords = ['话题', '换个', '说点别的', '不谈这个']
        if any(keyword in llm_intent_lower for keyword in topic_switch_keywords):
            return 'topic_switch'
        
        # 苏格拉底对话映射 - 优先检查
        socratic_keywords = ['思考', '反思', '探讨', '讨论', '认为', '觉得', '意义', '价值', '为什么', '哲学', '本质', '原理']
        if any(keyword in llm_intent_lower for keyword in socratic_keywords):
            return 'socratic_dialogue'
        
        # 学习指导映射 - 更精确的匹配
        learning_keywords = ['学习', '建议', '计划', '路径', '方法', '指导', '制定', '如何学习', '学习建议']
        if any(keyword in llm_intent_lower for keyword in learning_keywords):
            # 进一步检查是否包含学习相关词汇
            if any(word in llm_intent_lower for word in ['学习', '建议', '计划', '方法', '指导']):
                return 'learning_guidance'
        
        # 概念解释映射
        concept_keywords = ['深入', '详细', '全面', '分析', '解释', '理解', '原理', '概念']
        if any(keyword in llm_intent_lower for keyword in concept_keywords):
            return 'concept_explanation'
        
        # 知识检索映射
        knowledge_keywords = ['定义', '概念', '信息', '了解', '学习', '编程', '什么是', '如何', '获取', '检索']
        if any(keyword in llm_intent_lower for keyword in knowledge_keywords):
            return 'knowledge_retrieval'
        
        # 默认返回
        return 'general_inquiry'
    
    def _convert_query_type_with_intent(self, llm_query_type: str, intent: str) -> QueryType:
        """基于意图修正查询类型"""
        
        # 意图到查询类型的映射
        intent_to_type = {
            'identity_inquiry': QueryType.DIRECT_ANSWER,
            'capability_inquiry': QueryType.DIRECT_ANSWER,
            'greeting': QueryType.DIRECT_ANSWER,
            'system_help': QueryType.DIRECT_ANSWER,
            'topic_switch': QueryType.DIRECT_ANSWER,
            'learning_guidance': QueryType.LEARNING_GUIDANCE,
            'socratic_dialogue': QueryType.SOCRATIC_DIALOGUE,
            'concept_explanation': QueryType.CONCEPT_EXPLANATION,
            'knowledge_retrieval': QueryType.KNOWLEDGE_RETRIEVAL
        }
        
        # 如果意图明确，优先使用意图映射的类型
        if intent in intent_to_type:
            return intent_to_type[intent]
        
        # 否则使用LLM返回的类型
        return self._convert_query_type(llm_query_type)
    
    def _fallback_analysis(self, query: str) -> Dict[str, Any]:
        """备用分析方法（基于规则）"""
        # 使用增强的规则分析作为备用
        return self._enhanced_rule_analysis(query, AgentState(
            session_id="fallback",
            user_query=query,
            conversation_stage=None,
            conversation_round=1
        ))
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询文本"""
        processed = query.strip()
        # 保留中文标点，移除其他特殊字符
        processed = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】]', '', processed)
        return processed
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词（增强版）"""
        # 移除标点符号
        clean_query = re.sub(r'[^\w\s\u4e00-\u9fff]', '', query)
        
        # 分词
        words = clean_query.split()
        
        # 扩展的停用词列表
        stopwords = {
            '的', '了', '是', '在', '有', '和', '与', '或', '但', '可以', '能够',
            '什么', '怎么', '为什么', '如何', '这个', '那个', '这些', '那些',
            '一个', '一些', '很多', '非常', '特别', '比较', '更加', '最',
            '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们'
        }
        
        keywords = [word for word in words if word not in stopwords and len(word) > 1]
        
        # 按长度排序，优先返回较长的关键词
        keywords.sort(key=len, reverse=True)
        
        return keywords[:5]
