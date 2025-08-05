#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
苏格拉底引导者智能体
使用LLM生成苏格拉底式问题，引导用户批判性思考和理解知识
"""

import logging
from typing import Dict, Any, List, Optional
from utils import BaseAgent, AgentState, QueryType, ConversationStage, UnderstandingLevel
from prompts import get_prompt, PromptType, SocraticPrompts
from utils.llm import Message, MessageRole

class SocraticGuideAgent(BaseAgent):
    """苏格拉底引导代理（整合版）
    
    通过生成引导性问题来帮助用户深入思考和理解问题。
    支持基础和增强两种模式：
    - 基础模式：使用LLM生成高质量的苏格拉底式问题
    - 增强模式：包含逻辑连贯性、澄清、探索和批判性思维的高级功能
    """
    
    def __init__(self, llm_client=None, config: Dict[str, Any] = None, enable_enhanced_mode: bool = False):
        super().__init__(
            name="SocraticGuide",
            description="生成苏格拉底式问题，引导用户批判性思考"
        )
        self.llm_client = llm_client
        self.config = config or {}
        
        # 基础配置
        self.question_history = []  # 问题历史
        self.max_questions = self.config.get('max_questions', 5)  # 最大问题数量
        self.question_depth = self.config.get('question_depth', 'medium')
        
        # 增强模式配置
        self.enable_enhanced_mode = enable_enhanced_mode or self.config.get('enable_enhanced_mode', False)
        self.coherence_strategies = self.config.get('coherence_strategies', [
            'sequential', 'spiral', 'branching', 'comparative'
        ])
        self.question_types = self.config.get('question_types', [
            'clarification', 'assumption', 'evidence', 'perspective', 
            'implication', 'meta', 'synthesis', 'application'
        ])
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        # 放宽条件：允许在各种情况下执行苏格拉底式引导
        if len(state.socratic_questions) >= self.max_questions:
            self.logger.debug(f"Max questions reached: {len(state.socratic_questions)}")
            return False
        
        # 基本条件：有用户查询即可
        if not state.user_query.strip():
            self.logger.debug("No user query available")
            return False
        
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行苏格拉底式引导"""
        try:
            # 根据对话阶段确定引导策略
            if state.conversation_stage == ConversationStage.SOCRATIC_QUESTIONING:
                return await self._execute_socratic_questioning(state)
            elif state.conversation_stage == ConversationStage.UNDERSTANDING_CHECK:
                return await self._execute_understanding_check(state)
            elif state.conversation_stage == ConversationStage.DEEPER_EXPLORATION:
                return await self._execute_deeper_exploration(state)
            else:
                # 默认执行基础引导
                if self.enable_enhanced_mode:
                    return self._execute_enhanced_guidance(state)
                else:
                    return self._execute_basic_guidance(state)
                
        except Exception as e:
            self.logger.error(f"Socratic guidance failed: {e}")
            state.set_error(
                "socratic_guidance_error",
                f"Failed to generate socratic guidance: {str(e)}"
            )
            return state
    
    async def _execute_socratic_questioning(self, state: AgentState) -> AgentState:
        """执行苏格拉底式提问"""
        try:
            # 分析用户上一次回答（如果有）
            if state.user_response:
                understanding_analysis = self._analyze_user_response_for_understanding(state)
                state.conversation_context["last_understanding_analysis"] = understanding_analysis
            
            # 确定问题类型
            question_type = self._determine_question_type(state)
            
            # 生成苏格拉底式问题
            question_result = await self._generate_intelligent_question(state, question_type)
            
            if question_result and question_result.get("question"):
                state.socratic_question = question_result["question"]
                state.socratic_questions.append(question_result["question"])
                
                # 更新对话上下文
                state.conversation_context["last_question_type"] = question_type
                state.conversation_context["question_purpose"] = question_result.get("purpose", "")
                
                self.logger.info(f"Generated {question_type} question: {state.socratic_question[:50]}...")
            else:
                # 生成默认问题
                state.socratic_question = self._generate_fallback_question(state)
                state.socratic_questions.append(state.socratic_question)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Socratic questioning failed: {e}")
            state.set_error("socratic_questioning_error", str(e))
            return state
    
    async def _execute_understanding_check(self, state: AgentState) -> AgentState:
        """执行理解检查"""
        try:
            # 分析用户理解程度
            understanding_analysis = self._analyze_user_response_for_understanding(state)
            
            # 基于理解程度生成相应问题
            if understanding_analysis["understanding_level"] >= 0.7:
                # 理解良好，生成深入探索问题
                question_type = "implication"
                state.advance_conversation_stage(ConversationStage.DEEPER_EXPLORATION)
            elif understanding_analysis["understanding_level"] >= 0.4:
                # 理解一般，生成澄清问题
                question_type = "clarification"
            else:
                # 理解不足，生成引导问题
                question_type = "evidence"
            
            question_result = await self._generate_intelligent_question(state, question_type)
            
            if question_result and question_result.get("question"):
                state.socratic_question = question_result["question"]
                state.socratic_questions.append(question_result["question"])
            
            return state
            
        except Exception as e:
            self.logger.error(f"Understanding check failed: {e}")
            state.set_error("understanding_check_error", str(e))
            return state
    
    async def _execute_deeper_exploration(self, state: AgentState) -> AgentState:
        """执行深入探索"""
        try:
            # 生成深层次思考问题
            question_types = ["perspective", "implication", "assumption", "meta"]
            question_type = question_types[len(state.socratic_questions) % len(question_types)]
            
            question_result = await self._generate_intelligent_question(state, question_type)
            
            if question_result and question_result.get("question"):
                state.socratic_question = question_result["question"]
                state.socratic_questions.append(question_result["question"])
            
            return state
            
        except Exception as e:
            self.logger.error(f"Deeper exploration failed: {e}")
            state.set_error("deeper_exploration_error", str(e))
            return state
    
    async def _generate_intelligent_question(self, state: AgentState, question_type: str) -> Optional[Dict[str, Any]]:
        """生成智能化的苏格拉底式问题"""
        try:
            from utils.llm import get_llm_manager
            
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                return None
            
            # 构建问题生成上下文
            context = {
                "concept": state.current_focus or self._extract_main_concept(state),
                "understanding_level": state.understanding_level.value,
                "question_type": question_type,
                "learning_objective": state.learning_objectives[0] if state.learning_objectives else "深入理解概念"
            }
            
            # 添加用户画像上下文（如果有）
            user_profile_context = state.metadata.get("user_profile_context", {})
            if user_profile_context:
                context["user_profile"] = {
                    "summary": user_profile_context.get("user_summary", ""),
                    "entities": user_profile_context.get("user_entities", []),
                    "interests": self._extract_user_interests(user_profile_context)
                }
            
            # 获取问题生成提示
            prompt = get_prompt(PromptType.QUESTION_GENERATION, context)
            
            # 添加类型特定的指导
            type_guidance = SocraticPrompts.get_question_type_prompt(question_type)
            
            messages = [
                Message(role=MessageRole.SYSTEM, content=type_guidance),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                return self._parse_question_response(response.content, question_type)
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Intelligent question generation failed: {e}")
            return None
    
    def _determine_question_type(self, state: AgentState) -> str:
        """确定问题类型"""
        # 基于对话轮次和理解水平确定问题类型
        round_count = state.conversation_round
        understanding = state.understanding_level
        
        if round_count <= 1:
            return "clarification"
        elif understanding == UnderstandingLevel.NO_UNDERSTANDING:
            return "evidence"
        elif understanding == UnderstandingLevel.SURFACE_UNDERSTANDING:
            return "clarification"
        elif understanding == UnderstandingLevel.BASIC_UNDERSTANDING:
            return "assumption"
        elif understanding == UnderstandingLevel.GOOD_UNDERSTANDING:
            return "perspective"
        else:
            return "implication"
    
    def _analyze_user_response_for_understanding(self, state: AgentState) -> Dict[str, Any]:
        """分析用户回答的理解程度"""
        if not state.user_response:
            return {"understanding_level": 0.0, "confidence": 0.0}
        
        response = state.user_response.strip()
        
        # 简单的理解程度分析
        understanding_indicators = {
            "high": ["理解", "明白", "清楚", "知道原理", "可以解释", "举例来说"],
            "medium": ["知道", "听说过", "大概", "基本", "应该是"],
            "low": ["不太清楚", "不明白", "困惑", "不知道", "?", "？"]
        }
        
        high_count = sum(1 for word in understanding_indicators["high"] if word in response)
        medium_count = sum(1 for word in understanding_indicators["medium"] if word in response)
        low_count = sum(1 for word in understanding_indicators["low"] if word in response)
        
        # 计算理解水平
        if high_count > 0:
            understanding_level = 0.8 + (high_count * 0.05)
        elif medium_count > 0:
            understanding_level = 0.5 + (medium_count * 0.1)
        elif low_count > 0:
            understanding_level = 0.2 - (low_count * 0.1)
        else:
            # 基于回答长度判断
            understanding_level = min(len(response) / 100, 0.6)
        
        understanding_level = max(0.0, min(1.0, understanding_level))
        
        return {
            "understanding_level": understanding_level,
            "confidence": 0.7,
            "indicators": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }
    
    def _extract_main_concept(self, state: AgentState) -> str:
        """提取主要概念"""
        if state.current_focus:
            return state.current_focus
        elif state.key_concepts_covered:
            return state.key_concepts_covered[0]
        elif state.retrieved_knowledge and state.retrieved_knowledge.get("target_concepts"):
            return state.retrieved_knowledge["target_concepts"][0]
        else:
            # 从查询中提取
            query_words = state.user_query.split()
            # 简单提取：返回最长的词
            return max(query_words, key=len) if query_words else "概念"
    
    def _generate_fallback_question(self, state: AgentState) -> str:
        """生成备用问题 - 针对各种学习领域"""
        query = state.user_query.lower()
        round_count = len(state.socratic_questions)
        
        # 评价判断类问题（好人/坏人、对错、优劣等）
        if any(word in query for word in ["好人", "坏人", "对", "错", "好", "坏", "优", "劣", "应该", "值得"]):
            return self._generate_evaluative_question(state.user_query, round_count)
        
        # 概念解释类问题（什么是、定义、概念等）
        elif any(word in query for word in ["什么是", "介绍", "定义", "概念", "含义", "意思"]):
            return self._generate_conceptual_question(state.user_query, round_count)
        
        # 原因解释类问题（为什么、怎么、如何）
        elif any(word in query for word in ["为什么", "怎么", "如何", "原因", "怎样"]):
            return self._generate_causal_question(state.user_query, round_count)
        
        # 比较类问题（区别、不同、相同）
        elif any(word in query for word in ["区别", "不同", "相同", "比较", "差别", "异同"]):
            return self._generate_comparative_question(state.user_query, round_count)
        
        # 应用类问题（用途、作用、功能）
        elif any(word in query for word in ["用途", "作用", "功能", "应用", "用处", "意义"]):
            return self._generate_application_question(state.user_query, round_count)
        
        # 科学技术类问题
        elif any(word in query for word in ["原理", "机制", "工作", "运行", "实验", "技术", "科学"]):
            return self._generate_scientific_question(state.user_query, round_count)
        
        # 历史文化类问题
        elif any(word in query for word in ["历史", "古代", "朝代", "文化", "传统", "背景"]):
            return self._generate_historical_question(state.user_query, round_count)
        
        # 数学逻辑类问题
        elif any(word in query for word in ["证明", "推导", "计算", "公式", "定理", "解题"]):
            return self._generate_mathematical_question(state.user_query, round_count)
        
        # 默认通用引导
        else:
            return self._generate_general_question(state.user_query, round_count)
    
    def _parse_question_response(self, response_content: str, question_type: str) -> Dict[str, Any]:
        """解析LLM生成的问题响应"""
        try:
            import json
            # 尝试解析JSON格式
            if "{" in response_content and "}" in response_content:
                json_str = response_content[response_content.find("{"):response_content.rfind("}")+1]
                result = json.loads(json_str)
                return result
        except:
            pass
        
        # 如果不是JSON格式，尝试提取问题
        lines = response_content.strip().split('\n')
        question = None
        
        for line in lines:
            line = line.strip()
            if line.endswith('?') or line.endswith('？'):
                question = line
                break
            elif '问题:' in line or '问题：' in line:
                question = line.split(':', 1)[-1].split('：', 1)[-1].strip()
                break
        
        if not question:
            question = response_content.strip()
        
        return {
            "question": question,
            "type": question_type,
            "purpose": f"引导学生通过{question_type}问题深入思考"
        }

    def _execute_basic_guidance(self, state: AgentState) -> AgentState:
        """执行基础苏格拉底引导"""
        # 1. 分析当前状态，确定引导策略
        guidance_strategy = self._determine_guidance_strategy(state)
        
        # 2. 生成苏格拉底式问题
        socratic_question = self._generate_socratic_question(state, guidance_strategy)
        
        if socratic_question:
            # 3. 更新状态
            state.socratic_questions.append(socratic_question)
            state.current_socratic_question = socratic_question
            
            # 4. 记录问题历史
            self.question_history.append({
                "question": socratic_question,
                "strategy": guidance_strategy,
                "context": state.user_query,
                "timestamp": state.timestamp
            })
            
            self.logger.info(f"Generated socratic question with strategy: {guidance_strategy['type']}")
        else:
            self.logger.warning("Failed to generate socratic question")
            state.set_error(
                "socratic_generation_error",
                "Failed to generate socratic question"
            )
        
        return state
    
    def _execute_enhanced_guidance(self, state: AgentState) -> AgentState:
        """执行增强苏格拉底引导"""
        # 1. 分析学习状态
        learning_state = self._analyze_learning_state(state)
        
        # 2. 确定问题策略
        question_strategy = self._determine_question_strategy(state, learning_state)
        
        # 3. 生成连贯的问题序列
        questions_result = self._generate_coherent_questions(state, learning_state, question_strategy)
        
        if questions_result and questions_result.get('questions'):
            # 4. 更新状态
            for question in questions_result['questions']:
                state.socratic_questions.append(question)
            
            state.current_socratic_question = questions_result['questions'][-1]
            
            # 5. 记录问题历史
            for question in questions_result['questions']:
                self.question_history.append({
                    "question": question,
                    "strategy": question_strategy,
                    "context": state.user_query,
                    "timestamp": state.timestamp,
                    "learning_state": learning_state
                })
            
            # 保持历史记录在合理范围内
            if len(self.question_history) > self.max_questions * 2:
                self.question_history = self.question_history[-self.max_questions:]
            
            self.logger.info(f"Generated {len(questions_result['questions'])} enhanced socratic questions")
        else:
            self.logger.warning("Failed to generate enhanced socratic questions")
            state.set_error(
                "enhanced_socratic_generation_error",
                "Failed to generate enhanced socratic questions"
            )
        
        return state
    
    def _determine_guidance_strategy(self, state: AgentState) -> Dict[str, Any]:
        """确定引导策略"""
        strategy = {
            "type": "exploration",
            "focus": "understanding",
            "depth": "basic"
        }
        
        # 根据查询类型调整策略
        if state.query_type == QueryType.CONCEPT_EXPLANATION:
            if not state.user_responses:
                # 首次问题：探索基础理解
                strategy.update({
                    "type": "foundation",
                    "focus": "prior_knowledge",
                    "depth": "basic"
                })
            elif len(state.user_responses) == 1:
                # 第二个问题：深入概念
                strategy.update({
                    "type": "exploration",
                    "focus": "concept_depth",
                    "depth": "intermediate"
                })
            else:
                # 后续问题：应用和批判性思考
                strategy.update({
                    "type": "application",
                    "focus": "critical_thinking",
                    "depth": "advanced"
                })
        
        elif state.query_type == QueryType.LEARNING_GUIDANCE:
            strategy.update({
                "type": "guidance",
                "focus": "learning_path",
                "depth": "adaptive"
            })
        
        # 根据检索到的知识调整策略
        if state.retrieved_knowledge:
            knowledge_complexity = self._assess_knowledge_complexity(state.retrieved_knowledge)
            if knowledge_complexity > 0.7:
                strategy["depth"] = "advanced"
            elif knowledge_complexity < 0.3:
                strategy["depth"] = "basic"
        
        return strategy
    
    def _generate_socratic_question(self, state: AgentState, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成苏格拉底式问题"""
        try:
            from utils.llm import get_llm_manager
            
            # 优先使用百炼大模型
            llm_manager = get_llm_manager()
            qwen_client = llm_manager.get_client("qwen")
            
            if not qwen_client:
                self.logger.warning("Qwen client not available, falling back to Ollama")
                ollama_client = llm_manager.get_client("ollama")
                if not ollama_client:
                    self.logger.error("No LLM client available")
                    return None
                client = ollama_client
            else:
                client = qwen_client
            
            # 构建提示词
            prompt = self._build_socratic_prompt(state, strategy)
            
            # 生成问题
            messages = [
                Message(role=MessageRole.SYSTEM, content=self._get_system_prompt()),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                question_data = self._parse_question_response(response.content, strategy)
                return question_data
            else:
                self.logger.error(f"LLM response failed: {response.error}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to generate socratic question: {e}")
            return None
    
    def _build_socratic_prompt(self, state: AgentState, strategy: Dict[str, Any]) -> str:
        """构建苏格拉底式问题生成提示词"""
        prompt_parts = []
        
        # 基础信息
        prompt_parts.append(f"用户查询: {state.user_query}")
        
        # 查询解释
        if state.interpretation:
            prompt_parts.append(f"查询意图: {state.interpretation.get('intent', '未知')}")
            if "keywords" in state.interpretation:
                prompt_parts.append(f"关键词: {', '.join(state.interpretation['keywords'])}")
        
        # 检索到的知识
        if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
            knowledge_summary = self._summarize_knowledge(state.retrieved_knowledge["results"])
            prompt_parts.append(f"相关知识: {knowledge_summary}")
        
        # 之前的问答历史
        if state.socratic_questions and state.user_responses:
            prompt_parts.append("\n之前的对话:")
            for i, (q, r) in enumerate(zip(state.socratic_questions, state.user_responses)):
                prompt_parts.append(f"问题{i+1}: {q.get('question', '')}")
                prompt_parts.append(f"回答{i+1}: {r}")
        
        # 策略指导
        strategy_guidance = self._get_strategy_guidance(strategy)
        prompt_parts.append(f"\n引导策略: {strategy_guidance}")
        
        # 生成要求
        prompt_parts.append("\n请生成一个苏格拉底式问题，要求:")
        prompt_parts.append("1. 问题应该引导用户思考，而不是直接给出答案")
        prompt_parts.append("2. 问题应该基于已有知识，帮助用户深入理解")
        prompt_parts.append("3. 问题应该适合当前的学习阶段和理解水平")
        prompt_parts.append("4. 问题应该鼓励批判性思考和自主探索")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return get_prompt(PromptType.SOCRATIC_SYSTEM)
    
    def _get_strategy_guidance(self, strategy: Dict[str, Any]) -> str:
        """获取策略指导文本"""
        strategy_map = {
            "foundation": "探索学习者的基础知识和先验理解",
            "exploration": "引导深入探索概念的内涵和外延",
            "application": "促进知识的应用和迁移",
            "guidance": "提供学习路径和方法指导"
        }
        
        focus_map = {
            "prior_knowledge": "关注已有知识基础",
            "concept_depth": "深入理解概念本质",
            "critical_thinking": "培养批判性思维",
            "learning_path": "优化学习路径"
        }
        
        depth_map = {
            "basic": "基础水平",
            "intermediate": "中等水平",
            "advanced": "高级水平",
            "adaptive": "自适应水平"
        }
        
        return f"{strategy_map.get(strategy['type'], strategy['type'])}, {focus_map.get(strategy['focus'], strategy['focus'])}, {depth_map.get(strategy['depth'], strategy['depth'])}"
    
    def _summarize_knowledge(self, knowledge_results: List[Dict[str, Any]]) -> str:
        """总结检索到的知识"""
        if not knowledge_results:
            return "无相关知识"
        
        # 取前3个最相关的结果
        top_results = sorted(
            knowledge_results,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )[:3]
        
        summaries = []
        for result in top_results:
            content = result.get("content", "")
            # 截取前100个字符作为摘要
            summary = content[:100] + "..." if len(content) > 100 else content
            summaries.append(summary)
        
        return " | ".join(summaries)
    
    def _assess_knowledge_complexity(self, knowledge: Dict[str, Any]) -> float:
        """评估知识复杂度"""
        try:
            results = knowledge.get("results", [])
            if not results:
                return 0.5
            
            # 简单的复杂度评估
            total_length = sum(len(r.get("content", "")) for r in results)
            avg_length = total_length / len(results)
            
            # 基于内容长度和结果数量评估复杂度
            complexity = min((avg_length / 500) + (len(results) / 10), 1.0)
            return complexity
            
        except Exception:
            return 0.5
    
    def _parse_question_response(self, response_content: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """解析问题响应"""
        try:
            import json
            
            # 尝试解析JSON响应
            if response_content.strip().startswith("{"):
                question_data = json.loads(response_content)
            else:
                # 如果不是JSON格式，创建基本结构
                question_data = {
                    "question": response_content.strip(),
                    "purpose": "引导思考",
                    "expected_thinking": "深入理解概念",
                    "follow_up_hints": []
                }
            
            # 添加策略信息
            question_data["strategy"] = strategy
            question_data["question_id"] = len(self.question_history) + 1
            
            return question_data
            
        except json.JSONDecodeError:
            # JSON解析失败，返回基本结构
            return {
                "question": response_content.strip(),
                "purpose": "引导思考",
                "expected_thinking": "深入理解概念",
                "follow_up_hints": [],
                "strategy": strategy,
                "question_id": len(self.question_history) + 1
            }
        except Exception as e:
            self.logger.error(f"Failed to parse question response: {e}")
            return {
                "question": "请分享你对这个问题的理解？",
                "purpose": "引导思考",
                "expected_thinking": "基础理解",
                "follow_up_hints": [],
                "strategy": strategy,
                "question_id": len(self.question_history) + 1
            }
    
    def process_user_response(self, state: AgentState, user_response: str) -> AgentState:
        """处理用户响应"""
        try:
            # 记录用户响应
            state.user_responses.append(user_response)
            
            # 分析响应质量
            response_analysis = self._analyze_user_response(user_response, state)
            
            # 更新学习状态
            if hasattr(state, 'learning_progress'):
                state.learning_progress.append(response_analysis)
            
            self.logger.info(f"Processed user response: {len(user_response)} characters")
            
        except Exception as e:
            self.logger.error(f"Failed to process user response: {e}")
            
        return state
    
    def _analyze_user_response(self, response: str, state: AgentState) -> Dict[str, Any]:
        """分析用户响应质量"""
        analysis = {
            "response_length": len(response),
            "engagement_level": self._assess_engagement(response),
            "understanding_indicators": self._identify_understanding_indicators(response),
            "timestamp": state.timestamp
        }
        
        return analysis
    
    def _assess_engagement(self, response: str) -> float:
        """评估用户参与度"""
        if len(response) < 10:
            return 0.2
        elif len(response) < 50:
            return 0.5
        elif len(response) < 150:
            return 0.8
        else:
            return 1.0
    
    def _identify_understanding_indicators(self, response: str) -> List[str]:
        """识别理解指标"""
        indicators = []
        
        # 简单的关键词检测
        if any(word in response.lower() for word in ['因为', '所以', '但是', '然而']):
            indicators.append('logical_reasoning')
        
        if any(word in response.lower() for word in ['例如', '比如', '举例']):
            indicators.append('concrete_examples')
        
        if any(word in response.lower() for word in ['我认为', '我觉得', '我的看法']):
            indicators.append('personal_reflection')
        
        return indicators
    
    # ==================== 增强苏格拉底引导方法 ====================
    
    def _analyze_learning_state(self, state: AgentState) -> Dict[str, Any]:
        """分析学习状态"""
        learning_state = {
            "user_understanding_level": 0.5,
            "knowledge_complexity": 0.5,
            "engagement_history": [],
            "learning_style_indicators": [],
            "current_focus_area": "general",
            "confusion_indicators": [],
            "progress_indicators": []
        }
        
        # 分析用户理解水平
        if state.user_responses:
            understanding_scores = []
            for response in state.user_responses:
                score = self._assess_understanding_level(response)
                understanding_scores.append(score)
            
            if understanding_scores:
                learning_state["user_understanding_level"] = sum(understanding_scores) / len(understanding_scores)
        
        # 分析知识复杂度
        if state.retrieved_knowledge:
            learning_state["knowledge_complexity"] = self._assess_knowledge_complexity(state.retrieved_knowledge)
        
        # 分析参与历史
        if state.user_responses:
            for response in state.user_responses:
                engagement = self._assess_engagement(response)
                learning_state["engagement_history"].append(engagement)
        
        # 识别学习风格
        learning_state["learning_style_indicators"] = self._identify_learning_style(state)
        
        # 识别当前焦点领域
        learning_state["current_focus_area"] = self._identify_focus_area(state)
        
        return learning_state
    
    def _assess_understanding_level(self, response: str) -> float:
        """评估理解水平"""
        score = 0.3  # 基础分数
        
        # 基于响应长度
        if len(response) > 50:
            score += 0.2
        
        # 基于逻辑连接词
        logical_words = ['因为', '所以', '但是', '然而', '因此', '由于']
        if any(word in response for word in logical_words):
            score += 0.2
        
        # 基于具体例子
        example_words = ['例如', '比如', '举例', '比方说']
        if any(word in response for word in example_words):
            score += 0.2
        
        # 基于反思性语言
        reflection_words = ['我认为', '我觉得', '我的理解', '我的看法']
        if any(word in response for word in reflection_words):
            score += 0.1
        
        return min(score, 1.0)
    
    def _identify_learning_style(self, state: AgentState) -> List[str]:
        """识别学习风格"""
        style_indicators = []
        
        if state.user_responses:
            combined_responses = ' '.join(state.user_responses)
            
            # 视觉学习者指标
            visual_words = ['看', '图', '图表', '示意图', '可视化']
            if any(word in combined_responses for word in visual_words):
                style_indicators.append('visual')
            
            # 实践学习者指标
            practical_words = ['实际', '例子', '应用', '实践', '操作']
            if any(word in combined_responses for word in practical_words):
                style_indicators.append('practical')
            
            # 理论学习者指标
            theoretical_words = ['原理', '理论', '概念', '定义', '本质']
            if any(word in combined_responses for word in theoretical_words):
                style_indicators.append('theoretical')
        
        return style_indicators
    
    def _identify_focus_area(self, state: AgentState) -> str:
        """识别当前焦点领域"""
        if state.query_type:
            query_type = str(state.query_type).lower()
            if 'explanation' in query_type:
                return 'conceptual_understanding'
            elif 'example' in query_type:
                return 'practical_application'
            elif 'comparison' in query_type:
                return 'analytical_thinking'
        
        return 'general_inquiry'
    
    def _determine_question_strategy(self, state: AgentState, learning_state: Dict[str, Any]) -> Dict[str, Any]:
        """确定问题策略"""
        strategy = {
            "strategy": "adaptive",
            "coherence_strategy": "sequential",
            "primary_question_types": [],
            "difficulty_level": "medium",
            "focus_areas": []
        }
        
        # 基于理解水平确定难度
        understanding_level = learning_state.get("user_understanding_level", 0.5)
        if understanding_level < 0.4:
            strategy["difficulty_level"] = "basic"
            strategy["coherence_strategy"] = "sequential"
        elif understanding_level > 0.7:
            strategy["difficulty_level"] = "advanced"
            strategy["coherence_strategy"] = "spiral"
        else:
            strategy["difficulty_level"] = "medium"
            strategy["coherence_strategy"] = "branching"
        
        # 基于学习风格确定问题类型
        style_indicators = learning_state.get("learning_style_indicators", [])
        if 'practical' in style_indicators:
            strategy["primary_question_types"].extend(['application', 'example'])
        if 'theoretical' in style_indicators:
            strategy["primary_question_types"].extend(['clarification', 'assumption'])
        if 'visual' in style_indicators:
            strategy["primary_question_types"].extend(['perspective', 'comparison'])
        
        # 默认问题类型
        if not strategy["primary_question_types"]:
            strategy["primary_question_types"] = ['clarification', 'evidence']
        
        # 确定焦点领域
        focus_area = learning_state.get("current_focus_area", "general")
        strategy["focus_areas"].append(focus_area)
        
        return strategy
    
    def _generate_coherent_questions(self, state: AgentState, learning_state: Dict[str, Any], 
                                   question_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """生成连贯的问题序列"""
        coherence_strategy = question_strategy.get("coherence_strategy", "sequential")
        
        if coherence_strategy == "sequential":
            return self._generate_sequential_questions(state, learning_state, question_strategy)
        elif coherence_strategy == "spiral":
            return self._generate_spiral_questions(state, learning_state, question_strategy)
        elif coherence_strategy == "branching":
            return self._generate_branching_questions(state, learning_state, question_strategy)
        elif coherence_strategy == "comparative":
            return self._generate_comparative_questions(state, learning_state, question_strategy)
        else:
            return self._generate_sequential_questions(state, learning_state, question_strategy)
    
    def _generate_sequential_questions(self, state: AgentState, learning_state: Dict[str, Any], 
                                     question_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """生成顺序问题"""
        questions = []
        question_types = []
        
        # 基础理解问题
        if not state.socratic_questions:
            question = self._create_clarification_question(state, learning_state)
            questions.append(question)
            question_types.append('clarification')
        
        # 深入探索问题
        if len(state.socratic_questions) >= 1:
            question = self._create_evidence_question(state, learning_state)
            questions.append(question)
            question_types.append('evidence')
        
        # 应用问题
        if len(state.socratic_questions) >= 2:
            question = self._create_application_question(state, learning_state)
            questions.append(question)
            question_types.append('application')
        
        return {
            "questions": questions,
            "question_types": question_types,
            "coherence_strategy": "sequential",
            "quality_score": 0.8
        }
    
    def _generate_spiral_questions(self, state: AgentState, learning_state: Dict[str, Any], 
                                 question_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """生成螺旋式问题"""
        questions = []
        question_types = []
        
        # 螺旋式逐步深入
        depth_level = len(state.socratic_questions)
        
        if depth_level == 0:
            question = self._create_perspective_question(state, learning_state)
            questions.append(question)
            question_types.append('perspective')
        elif depth_level == 1:
            question = self._create_assumption_question(state, learning_state)
            questions.append(question)
            question_types.append('assumption')
        else:
            question = self._create_synthesis_question(state, learning_state)
            questions.append(question)
            question_types.append('synthesis')
        
        return {
            "questions": questions,
            "question_types": question_types,
            "coherence_strategy": "spiral",
            "quality_score": 0.85
        }
    
    def _generate_branching_questions(self, state: AgentState, learning_state: Dict[str, Any], 
                                    question_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """生成分支问题"""
        questions = []
        question_types = []
        
        # 基于用户响应生成分支问题
        if state.user_responses:
            last_response = state.user_responses[-1]
            
            # 分析响应内容决定分支方向
            if self._contains_uncertainty(last_response):
                question = self._create_clarification_question(state, learning_state)
                question_types.append('clarification')
            elif self._contains_examples(last_response):
                question = self._create_implication_question(state, learning_state)
                question_types.append('implication')
            else:
                question = self._create_meta_question(state, learning_state)
                question_types.append('meta')
            
            questions.append(question)
        else:
            # 默认起始问题
            question = self._create_clarification_question(state, learning_state)
            questions.append(question)
            question_types.append('clarification')
        
        return {
            "questions": questions,
            "question_types": question_types,
            "coherence_strategy": "branching",
            "quality_score": 0.75
        }
    
    def _generate_comparative_questions(self, state: AgentState, learning_state: Dict[str, Any], 
                                      question_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """生成比较式问题"""
        questions = []
        question_types = []
        
        # 生成比较和对比问题
        question = self._create_comparative_question(state, learning_state)
        questions.append(question)
        question_types.append('comparison')
        
        return {
            "questions": questions,
            "question_types": question_types,
            "coherence_strategy": "comparative",
            "quality_score": 0.8
        }
    
    # 问题创建方法
    def _create_clarification_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建澄清问题"""
        templates = [
            "你能更具体地解释一下你对{}的理解吗？",
            "当你提到{}时，你具体指的是什么？",
            "你是如何理解{}这个概念的？"
        ]
        
        # 提取关键概念
        key_concept = self._extract_key_concept(state)
        template = templates[len(state.socratic_questions) % len(templates)]
        
        return template.format(key_concept)
    
    def _create_evidence_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建证据问题"""
        templates = [
            "你有什么证据支持这个观点？",
            "你能举个例子来说明这一点吗？",
            "什么让你相信这是正确的？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_application_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建应用问题"""
        templates = [
            "这个概念在实际生活中如何应用？",
            "你能想到这个原理的其他应用场景吗？",
            "如果要向朋友解释这个概念，你会怎么说？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_perspective_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建视角问题"""
        templates = [
            "从不同的角度来看，这个问题还有什么其他的理解方式？",
            "如果站在相反的立场，你会如何看待这个问题？",
            "其他人可能会如何理解这个概念？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_assumption_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建假设问题"""
        templates = [
            "你的这个观点基于什么假设？",
            "如果这个假设不成立，会发生什么？",
            "你认为这些假设都是合理的吗？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_synthesis_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建综合问题"""
        templates = [
            "综合我们讨论的内容，你现在对这个问题有什么新的理解？",
            "你能将这些不同的观点整合成一个完整的理解吗？",
            "基于我们的对话，你会如何总结这个概念的核心要点？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_implication_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建含义问题"""
        templates = [
            "这意味着什么？",
            "这会带来什么后果？",
            "这对我们的理解有什么影响？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_meta_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建元认知问题"""
        templates = [
            "你是如何得出这个结论的？",
            "你的思考过程是什么？",
            "你觉得自己的理解还有哪些不足？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    def _create_comparative_question(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """创建比较问题"""
        templates = [
            "这与你之前了解的概念有什么相似和不同之处？",
            "你能比较一下这两种观点的优缺点吗？",
            "这个方法与其他方法相比有什么特点？"
        ]
        
        template = templates[len(state.socratic_questions) % len(templates)]
        return template
    
    # 辅助方法
    def _extract_key_concept(self, state: AgentState) -> str:
        """提取关键概念"""
        if state.interpretation and 'keywords' in state.interpretation:
            keywords = state.interpretation['keywords']
            if keywords:
                return keywords[0]
        
        # 从用户查询中提取
        query_words = state.user_query.split()
        if len(query_words) > 2:
            return query_words[1]  # 简单启发式
        
        return "这个概念"
    
    def _contains_uncertainty(self, response: str) -> bool:
        """检查响应是否包含不确定性"""
        uncertainty_indicators = ['不确定', '可能', '也许', '大概', '不太清楚']
        return any(indicator in response for indicator in uncertainty_indicators)
    
    def _contains_examples(self, response: str) -> bool:
        """检查响应是否包含例子"""
        example_indicators = ['例如', '比如', '举例', '比方说']
        return any(indicator in response for indicator in example_indicators)
    
    def _analyze_user_response_detailed(self, response: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """详细分析用户响应（增强模式）"""
        analysis = {
            "response": response,
            "question_id": question.get("question_id", 0),
            "length": len(response),
            "quality": "medium",
            "insights": [],
            "suggestions": []
        }
        
        # 简单的响应质量评估
        if len(response) < 10:
            analysis["quality"] = "low"
            analysis["suggestions"].append("可以更详细地表达你的想法")
        elif len(response) > 100:
            analysis["quality"] = "high"
            analysis["insights"].append("回答详细，显示了深入思考")
        
        # 检查是否包含关键思考元素
        thinking_indicators = ["因为", "所以", "但是", "如果", "为什么", "怎么", "认为", "觉得"]
        found_indicators = [ind for ind in thinking_indicators if ind in response]
        
        if found_indicators:
            analysis["insights"].append(f"包含思考指示词: {', '.join(found_indicators)}")
        
        return analysis
    
    def should_continue_questioning(self, state: AgentState) -> bool:
        """判断是否应该继续提问"""
        # 检查问题数量限制
        if len(state.socratic_questions) >= self.max_questions:
            return False
        
        # 检查用户响应质量
        if hasattr(state, 'response_analyses') and state.response_analyses:
            recent_quality = state.response_analyses[-1].get("quality", "medium")
            if recent_quality == "high" and len(state.socratic_questions) >= 3:
                return False
        
        return True
    
    def get_question_summary(self, state: AgentState) -> Dict[str, Any]:
        """获取问题总结"""
        return {
            "total_questions": len(state.socratic_questions),
            "total_responses": len(state.user_responses),
            "question_history": self.question_history[-5:],  # 最近5个问题
            "engagement_level": self._calculate_engagement_level(state)
        }
    
    def _calculate_engagement_level(self, state: AgentState) -> str:
        """计算参与度水平"""
        if not state.user_responses:
            return "low"
        
        avg_response_length = sum(len(r) for r in state.user_responses) / len(state.user_responses)
        
        if avg_response_length > 80:
            return "high"
        elif avg_response_length > 30:
            return "medium"
        else:
            return "low"
    
    # 针对不同学习领域的专门问题生成方法
    def _generate_evaluative_question(self, query: str, round_count: int) -> str:
        """生成评价判断类问题"""
        questions = [
            "在做出这种评价之前，你认为我们应该用什么标准来判断？",
            "这个评价涉及到哪些方面的考虑？我们可以从哪些角度来分析？",
            "不同的人可能会有不同的评价标准，你觉得为什么会这样？",
            "如果站在不同的立场或时代背景下，这个评价会有变化吗？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_conceptual_question(self, query: str, round_count: int) -> str:
        """生成概念解释类问题"""
        concept = self._extract_main_concept_from_query(query)
        questions = [
            f"在我们深入了解{concept}之前，你已经对它有什么了解或印象？",
            f"你认为{concept}最核心的特征是什么？",
            f"你能想到{concept}和其他相关概念的联系吗？",
            f"如果要向完全不了解的人解释{concept}，你会用什么样的例子？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_causal_question(self, query: str, round_count: int) -> str:
        """生成原因解释类问题"""
        questions = [
            "你觉得这个现象或问题的根本原因可能是什么？",
            "这个过程涉及哪些关键的步骤或因素？",
            "如果我们改变其中的某个条件，会产生什么不同的结果？",
            "你能从不同的层面（比如直接原因和深层原因）来分析吗？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_comparative_question(self, query: str, round_count: int) -> str:
        """生成比较类问题"""
        questions = [
            "在比较这些内容时，你认为最重要的比较维度是什么？",
            "它们之间的相似点主要体现在哪些方面？",
            "它们的差异主要源于什么根本性的不同？",
            "这些差异对实际应用或理解有什么重要意义？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_application_question(self, query: str, round_count: int) -> str:
        """生成应用类问题"""
        questions = [
            "你能想到这个概念在日常生活中的具体应用场景吗？",
            "这个应用为什么重要？它解决了什么问题？",
            "如果没有这个应用，会产生什么影响或问题？",
            "你能预想到它在未来可能有哪些新的应用方向吗？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_scientific_question(self, query: str, round_count: int) -> str:
        """生成科学技术类问题"""
        questions = [
            "这个科学原理背后的基本机制是什么？你能简单描述一下吗？",
            "我们如何通过实验或观察来验证这个原理？",
            "这个技术的关键创新点在哪里？它突破了什么限制？",
            "这个科学发现对我们理解世界有什么重要意义？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_historical_question(self, query: str, round_count: int) -> str:
        """生成历史文化类问题"""
        questions = [
            "这个历史事件或人物处在什么样的时代背景下？",
            "当时的社会环境对这个事件有什么影响？",
            "这个事件对后来的历史发展产生了什么影响？",
            "如果我们站在当时人的角度，会如何看待这个问题？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_mathematical_question(self, query: str, round_count: int) -> str:
        """生成数学逻辑类问题"""
        questions = [
            "这个数学概念的核心思想是什么？它要解决什么问题？",
            "你能用自己的话解释这个推理过程的逻辑吗？",
            "这个公式或定理在什么条件下适用？有什么限制？",
            "你能想到这个数学工具在实际问题中的应用吗？"
        ]
        return questions[round_count % len(questions)]
    
    def _generate_general_question(self, query: str, round_count: int) -> str:
        """生成通用引导问题"""
        questions = [
            "这是一个很好的问题。在深入思考之前，你觉得这个问题的核心是什么？",
            "你提出这个问题是基于什么想法或困惑？",
            "让我们换个角度思考，这个问题可能涉及哪些不同的层面？",
            "你认为要完整回答这个问题，我们需要考虑哪些关键因素？"
        ]
        return questions[round_count % len(questions)]
    
    def _extract_main_concept_from_query(self, query: str) -> str:
        """从查询中提取主要概念"""
        # 移除常见的疑问词
        stop_words = {"什么是", "介绍", "定义", "概念", "含义", "意思", "的", "了", "吗", "呢", "?", "？"}
        words = query.split()
        
        # 过滤掉停用词，找到最长的实质性词汇
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        if meaningful_words:
            return max(meaningful_words, key=len)
        else:
            return "这个概念"
    
    def _extract_user_interests(self, user_profile_context: Dict[str, Any]) -> List[str]:
        """从用户画像上下文中提取用户兴趣"""
        interests = []
        
        try:
            # 从用户关系中提取兴趣相关信息
            user_relations = user_profile_context.get("user_relations", [])
            
            for relation in user_relations:
                predicate = relation.get("predicate", "").lower()
                obj = relation.get("object", "")
                
                # 识别兴趣相关的关系
                if any(keyword in predicate for keyword in ["喜欢", "兴趣", "爱好", "热爱", "擅长"]):
                    if obj and obj not in interests:
                        interests.append(obj)
                
                # 识别职业和专业背景
                if any(keyword in predicate for keyword in ["职业", "工作", "专业", "学习", "研究"]):
                    if obj and obj not in interests:
                        interests.append(obj)
            
            return interests[:5]  # 最多返回5个兴趣
            
        except Exception as e:
            self.logger.warning(f"Failed to extract user interests: {e}")
            return []