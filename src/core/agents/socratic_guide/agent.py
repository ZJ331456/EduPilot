#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
苏格拉底引导者智能体（MARS优化版）
参考MARS的Teacher-Critic架构，实现高质量的苏格拉底式问题生成
"""

import json
import logging
import re
import time
from typing import Dict, Any, List, Optional

from src.infrastructure.utils import BaseAgent, AgentState, QueryType, ConversationStage, UnderstandingLevel
from src.infrastructure.llm import Message, MessageRole, get_llm_manager
from .prompts import get_prompt, PromptType, SocraticPrompts
from .validation_prompts import build_question_validation_prompt, build_question_validation_system_prompt


class SocraticGuideAgent(BaseAgent):
    """苏格拉底引导代理（MARS优化版）
    
    核心特性：
    MARS链接：https://github.com/exoskeletonzj/MARS
    1. 质量验证机制：借鉴MARS的Critic，确保问题符合苏格拉底风格
    2. 个性化分析：基于用户理解水平和学习状态调整问题
    3. 8种问题类型：全方位培养批判性思维
    4. 自动重试机制：质量不达标自动重新生成
    """
    
    # ==================== 公共接口方法 ====================
    @staticmethod
    def get_understanding_assessment_prompt() -> str:
        """获取理解评估系统提示（公共接口）"""
        return get_prompt(PromptType.UNDERSTANDING_ASSESSMENT_SYSTEM)
    
    @staticmethod
    def get_prompt_by_type(prompt_type: str) -> str:
        """根据类型获取提示词（公共接口）"""
        try:
            pt = PromptType[prompt_type.upper()]
            return get_prompt(pt)
        except (KeyError, AttributeError):
            return ""
    
    def __init__(self, llm_client=None, config: Dict[str, Any] = None):
        super().__init__(
            name="SocraticGuide",
            description="生成苏格拉底式问题，引导用户批判性思考"
        )
        self.llm_client = llm_client
        self.config = config or {}
        
        # 核心配置
        self.question_history = []  # 问题历史
        self.max_questions = self.config.get('max_questions', 5)
        self.max_retries = self.config.get('max_retries', 2)  # 🔧 新增：质量验证重试次数
        self.enable_quality_check = self.config.get('enable_quality_check', True)  # 🔧 新增：是否启用质量检查
        
        # 问题类型配置
        self.question_types = [
            'clarification',   # 澄清
            'assumption',      # 假设
            'evidence',        # 证据
            'perspective',     # 视角
            'implication',     # 含义
            'meta',           # 元认知
            'synthesis',      # 综合
            'application'     # 应用
        ]
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        if len(state.socratic_questions) >= self.max_questions:
            self.logger.debug(f"Max questions reached: {len(state.socratic_questions)}")
            return False
        
        # 🔧 修复：检查是否处于苏格拉底对话模式
        # 如果有苏格拉底问题历史，说明正在进行苏格拉底对话
        if state.socratic_questions:
            self.logger.debug("处于苏格拉底对话模式，可以继续引导")
            return True
        
        # 如果没有苏格拉底问题历史，检查是否有用户查询
        if not state.user_query.strip():
            self.logger.debug("No user query available")
            return False
        
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行苏格拉底式引导（简化版主入口）
        
        🔧 优化点：
        1. 移除复杂的模式判断
        2. 统一的问题生成流程
        3. 集成质量验证机制
        """
        try:
            # 检查缓存
            cache_key = f"socratic_{hash(state.user_query)}_{len(state.socratic_questions)}"
            if state.is_cache_valid(cache_key):
                cached_question = state.get_cached(cache_key)
                if cached_question:
                    self.logger.info("Using cached socratic question")
                    state.socratic_question = cached_question
                    state.socratic_questions.append(cached_question)
                    return state
            
            # 🔧 统一的问题生成流程（参考MARS的简洁设计）
            question_data = await self._generate_socratic_question_with_validation(state)
            
            # 🔧 修复：处理没有生成问题的情况（用户表示重复等）
            if question_data is None:
                self.logger.info("没有生成新问题，可能是用户表示重复或达到最大轮次")
                # 设置一个特殊的状态表示停止提问
                state.socratic_question = ""
                state.socratic_guidance = {
                    "guidance_text": "感谢您的回答，我们已经通过对话深入探讨了这个话题。",
                    "question_type": "conclusion",
                    "understanding_level": state.understanding_level.value if hasattr(state.understanding_level, 'value') else "unknown",
                    "purpose": "结束引导",
                    "next_steps": [],
                    "metadata": {
                        "generated_at": time.time(),
                        "question_index": len(state.socratic_questions),
                        "reason": "user_indicated_repetition"
                    }
                }
                return state
            
            if question_data and question_data.get("question"):
                state.socratic_question = question_data["question"]
                state.socratic_questions.append(question_data)
                
                # 🔧 添加调试日志
                self.logger.info(f"📝 添加苏格拉底问题到列表: 当前总数={len(state.socratic_questions)}")
                
                # 🔧 修复：设置 socratic_guidance 字段供API使用
                state.socratic_guidance = {
                    "guidance_text": question_data["question"],
                    "question_type": question_data.get("type", "clarifying"),
                    "understanding_level": state.understanding_level.value if hasattr(state.understanding_level, 'value') else "unknown",
                    "purpose": question_data.get("purpose", "引导思考"),
                    "next_steps": question_data.get("next_steps", []),
                    "metadata": {
                        "generated_at": time.time(),
                        "question_index": len(state.socratic_questions),
                        "validation_score": question_data.get("validation_score", 1.0)
                    }
                }
                
                # 更新对话上下文
                state.conversation_context["last_question_type"] = question_data.get("type", "unknown")
                state.conversation_context["question_purpose"] = question_data.get("purpose", "")
                
                # 缓存问题
                state.set_cache(cache_key, question_data["question"], ttl=180)
                
                self.logger.info(f"✅ Generated validated question: {question_data['question'][:50]}...")
            else:
                # 降级：生成备用问题
                fallback_question = self._generate_fallback_question(state)
                state.socratic_question = fallback_question
                state.socratic_questions.append({"question": fallback_question, "type": "fallback"})
                
                self.logger.warning("⚠️ Using fallback question")
            
            return state
                
        except Exception as e:
            self.logger.error(f"Socratic guidance failed: {e}")
            state.set_error(
                "socratic_guidance_error",
                f"Failed to generate socratic guidance: {str(e)}"
            )
            return state
    
    async def _generate_socratic_question_with_validation(self, state: AgentState) -> Optional[Dict[str, Any]]:
        """生成并验证苏格拉底式问题（核心方法）
        
        🔧 借鉴MARS的Teacher-Critic循环：
        1. 生成问题
        2. 质量验证
        3. 不合格则重试
        
        Returns:
            问题数据字典，包含question, type, purpose等
        """
        retry_count = 0
        
        while retry_count <= self.max_retries:
            # 🔧 Step 1: 分析用户理解状态
            learning_state = self._analyze_learning_state(state)
            
            # 🔧 Step 2: 确定问题类型
            question_type = self._determine_question_type(state, learning_state)
            
            # 🔧 修复：如果问题类型为None，说明用户表示重复，停止提问
            if question_type is None:
                self.logger.info("用户表示问题重复，停止生成新问题")
                return None
            
            # 🔧 Step 3: 生成问题
            question_data = await self._generate_question(state, question_type, learning_state)
            
            if not question_data:
                retry_count += 1
                continue
            
            # 🔧 修复：检查问题是否与之前的问题重复
            if self._is_question_duplicate(question_data.get("question", ""), state):
                self.logger.warning(f"检测到重复问题，重新生成: {question_data.get('question', '')[:50]}...")
                retry_count += 1
                continue
            
            # 🔧 Step 4: 质量验证（参考MARS的Critic）
            if self.enable_quality_check:
                validation_result = await self._validate_question_quality(
                    question_data, state, question_type
                )
                
                if validation_result["is_valid"]:
                    self.logger.info(f"✅ Question validated (score: {validation_result.get('score', 'N/A')})")
                    return question_data
                else:
                    self.logger.warning(
                        f"⚠️ Question validation failed (attempt {retry_count + 1}/{self.max_retries + 1}): "
                        f"{validation_result.get('reason', 'Unknown')}"
                    )
                    # 🔧 优化：记录失败原因，用于后续改进
                    if not hasattr(state, 'validation_failures'):
                        state.validation_failures = []
                    state.validation_failures.append({
                        "question": question_data.get("question"),
                        "reason": validation_result.get("reason"),
                        "attempt": retry_count + 1
                    })
                    retry_count += 1
            else:
                # 跳过质量检查，直接返回
                return question_data
        
        # 重试失败，返回None
        self.logger.error(f"❌ Failed to generate valid question after {self.max_retries + 1} attempts")
        return None
    
    async def _generate_question(
        self, 
        state: AgentState, 
        question_type: str, 
        learning_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """生成问题（使用LLM）
        
        Args:
            state: 当前状态
            question_type: 问题类型
            learning_state: 学习状态分析
            
        Returns:
            问题数据字典
        """
        try:
            # 获取LLM客户端
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                self.logger.error("No LLM client available")
                return None
            
            # 构建问题生成上下文
            context = self._build_question_context(state, question_type, learning_state)
            
            # 获取问题生成提示
            prompt = get_prompt(PromptType.QUESTION_GENERATION, context)
            
            # 添加类型特定的指导
            type_guidance = SocraticPrompts.get_question_type_prompt(question_type)
            
            # 🔧 构建消息（参考MARS的提示结构 + Few-shot示例）
            messages = [
                Message(role=MessageRole.SYSTEM, content=type_guidance),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            # 🔧 关键优化：添加Few-shot示例（提高生成质量）
            few_shot_examples = self._get_few_shot_examples(question_type)
            if few_shot_examples:
                # 在user prompt后添加示例
                messages.append(Message(
                    role=MessageRole.ASSISTANT, 
                    content=few_shot_examples["good_example"]
                ))
                messages.append(Message(
                    role=MessageRole.USER, 
                    content=f"很好！现在请为以下情况生成一个类似风格的{question_type}类问题：\n{prompt}"
                ))
            
            # 调用LLM（降低temperature提高稳定性）
            response = client.chat_completion(messages, temperature=0.7)
            
            if response.success:
                return self._parse_question_response(response.content, question_type)
            else:
                self.logger.error(f"LLM response failed: {response.error}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to generate question: {e}")
            return None
    
    async def _validate_question_quality(
        self, 
        question_data: Dict[str, Any], 
        state: AgentState,
        question_type: str
    ) -> Dict[str, Any]:
        """验证问题质量（借鉴MARS的Critic机制）
        
        🔧 质量标准（参考MARS的system_prompt_critic）：
        1. 是否符合苏格拉底式提问风格
        2. 是否引导而非直接告知
        3. 是否基于当前理解水平
        4. 是否促进批判性思维
        
        Args:
            question_data: 问题数据
            state: 当前状态
            question_type: 问题类型
            
        Returns:
            验证结果: {is_valid: bool, score: float, reason: str, suggestions: List[str]}
        """
        try:
            question = question_data.get("question", "")
            
            # 🔧 快速质量检查（基于规则）
            quick_check = self._quick_quality_check(question, state)
            if not quick_check["is_valid"]:
                return quick_check
            
            # 🔧 深度质量检查（使用LLM，参考MARS的Critic）
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                # LLM不可用，使用快速检查结果
                return quick_check
            
            # 🔧 构建验证提示（完全参考MARS的Critic设计）
            understanding_level = state.understanding_level.value if state.understanding_level else 'unknown'
            validation_prompt = build_question_validation_prompt(
                question, state.user_query, question_type, understanding_level
            )
            system_prompt = build_question_validation_system_prompt()
            
            messages = [
                Message(role=MessageRole.SYSTEM, content=system_prompt),
                Message(role=MessageRole.USER, content=validation_prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                return self._parse_validation_response(response.content)
            else:
                # LLM调用失败，使用快速检查结果
                return quick_check
                
        except Exception as e:
            self.logger.warning(f"Question validation failed: {e}, using quick check")
            return self._quick_quality_check(question_data.get("question", ""), state)
    
    def _quick_quality_check(self, question: str, state: AgentState) -> Dict[str, Any]:
        """快速质量检查（基于MARS的核心原则）
        
        Returns:
            {is_valid: bool, score: float, reason: str}
        """
        issues = []
        score = 1.0
        
        # 🔧 核心检查1: 问题是否为空或过短
        if not question or len(question) < 5:
            return {
                "is_valid": False,
                "score": 0.0,
                "reason": "问题为空或过短",
                "suggestions": []
            }
        
        # 🔧 核心检查2: 是否包含问号（基本格式）
        if not question.endswith('?') and not question.endswith('？'):
            issues.append("缺少问号")
            score -= 0.1  # 降低权重，不是关键问题
        
        # 🔧 核心检查3: 是否使用了"直接要求"的表达（MARS关键原则）
        direct_request_patterns = [
            '请解释', '请说明', '请列举', '请描述', '请分析', '请总结',
            '解释一下', '说明一下', '列举一下', '描述一下', '分析一下',
            '你能解释', '你能说明', '你能列举', '你能描述', '你能告诉',
            '告诉我', '给我', '为我'
        ]
        
        has_direct_request = any(pattern in question for pattern in direct_request_patterns)
        if has_direct_request:
            return {
                "is_valid": False,
                "score": 0.2,
                "reason": "问题使用了直接要求的表达（如'请解释'、'请说明'），不符合引导式提问原则",
                "suggestions": ["尝试使用'让我们想想'、'如果...会怎样'等引导性表达"]
            }
        
        # 🔧 核心检查4: 是否直接给出答案
        answer_keywords = ['答案是', '正确答案', '应该是', '就是', '等于', '可以这样理解']
        if any(keyword in question for keyword in answer_keywords):
            return {
                "is_valid": False,
                "score": 0.1,
                "reason": "问题中包含了答案或解释，不符合只提问不回答的原则",
                "suggestions": []
            }
        
        # 🔧 检查5: 是否过于笼统（降低权重）
        generic_questions = ['你明白了吗', '懂了吗', '还有问题吗', '清楚了吗']
        if any(generic in question for generic in generic_questions):
            issues.append("问题过于笼统")
            score -= 0.2
        
        # 🔧 检查6: 问题长度（更宽松）
        if len(question) > 200:
            issues.append("问题过长，建议精简")
            score -= 0.1
        
        # 🔧 降低通过阈值：只要没有严重问题就通过
        is_valid = score >= 0.5
        
        return {
            "is_valid": is_valid,
            "score": max(0.0, score),
            "reason": "; ".join(issues) if issues else "通过快速检查",
            "suggestions": []
        }
    
    def _parse_validation_response(self, response_content: str) -> Dict[str, Any]:
        """解析验证响应（完全参考MARS的Critic响应格式）
        
        MARS Expected format:
        [True]
        
        OR
        
        [False]
        [suggestion: <reason>]
        """
        try:
            # 检查是否包含[True]或[False]
            if "[True]" in response_content or "[true]" in response_content.lower():
                return {
                    "is_valid": True,
                    "score": 0.9,  # 通过验证给予高分
                    "reason": "通过苏格拉底式验证",
                    "suggestions": []
                }
            else:
                # 🔧 MARS格式：使用[suggestion:]而不是[reason:]
                suggestion_match = re.search(r'\[suggestion:\s*(.+?)\]', response_content, re.IGNORECASE | re.DOTALL)
                if suggestion_match:
                    suggestion = suggestion_match.group(1).strip()
                else:
                    # 兼容处理：尝试提取整个响应中的建议
                    suggestion = response_content.replace("[False]", "").replace("[false]", "").strip()
                    if not suggestion:
                        suggestion = "未通过苏格拉底式验证"
                
                return {
                    "is_valid": False,
                    "score": 0.3,
                    "reason": suggestion,
                    "suggestions": [suggestion]  # 保持向后兼容
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to parse validation response: {e}")
            return {
                "is_valid": False,
                "score": 0.5,
                "reason": "响应解析失败",
                "suggestions": []
            }
    
    def _get_few_shot_examples(self, question_type: str) -> Optional[Dict[str, str]]:
        """获取Few-shot示例（关键优化：通过示例引导LLM生成更好的问题）
        
        Args:
            question_type: 问题类型
            
        Returns:
            包含good_example的字典
        """
        examples = {
            "clarification": {
                "good_example": "当我们谈到大化改新时，你心中浮现的第一个画面是什么？这个改革对你来说意味着什么？"
            },
            "assumption": {
                "good_example": "在思考大化改新的时候，我们是否默认了改革一定是好的？如果不做这个假设，会有什么不同的理解？"
            },
            "evidence": {
                "good_example": "让我们想想，历史上有哪些具体的事件或现象能够体现大化改新的影响？"
            },
            "perspective": {
                "good_example": "如果站在当时日本贵族的角度，他们会如何看待这场改革？和平民的视角可能有什么不同？"
            },
            "implication": {
                "good_example": "假如大化改新没有发生，你觉得日本的历史发展可能会走向何方？"
            },
            "meta": {
                "good_example": "在思考大化改新这个问题的过程中，是什么让你开始改变最初的想法？"
            },
            "synthesis": {
                "good_example": "大化改新和我们之前讨论的其他改革，它们之间有什么共同的规律吗？"
            },
            "application": {
                "good_example": "大化改新中的哪些经验，在今天的社会变革中可能仍然有借鉴意义？"
            }
        }
        
        return examples.get(question_type)
    
    def _analyze_learning_state(self, state: AgentState) -> Dict[str, Any]:
        """分析学习状态（保留EduPilot的个性化优势）
        
        Returns:
            学习状态分析结果
        """
        learning_state = {
            "understanding_level": 0.5,
            "engagement_level": 0.5,
            "confusion_indicators": [],
            "learning_style": "general"
        }
        
        # 分析用户理解水平
        if state.user_responses:
            understanding_scores = []
            for response in state.user_responses[-3:]:  # 最近3次回答
                score = self._assess_understanding_level(response)
                understanding_scores.append(score)
            
            if understanding_scores:
                learning_state["understanding_level"] = sum(understanding_scores) / len(understanding_scores)
        
        # 分析参与度
        if state.user_responses:
            recent_response = state.user_responses[-1]
            learning_state["engagement_level"] = self._assess_engagement(recent_response)
        
        # 识别困惑指标
        if state.user_response:
            confusion_words = ['不理解', '不明白', '困惑', '不清楚', '疑问']
            for word in confusion_words:
                if word in state.user_response:
                    learning_state["confusion_indicators"].append(word)
        
        return learning_state
    
    def _is_question_duplicate(self, new_question: str, state: AgentState) -> bool:
        """检查问题是否与之前的问题重复
        
        Args:
            new_question: 新生成的问题
            state: 当前状态
            
        Returns:
            True if duplicate, False otherwise
        """
        if not new_question or not state.socratic_questions:
            return False
        
        # 获取之前的问题文本
        previous_questions = []
        for q in state.socratic_questions:
            if isinstance(q, dict):
                question_text = q.get("question", "")
            else:
                question_text = str(q)
            if question_text:
                previous_questions.append(question_text)
        
        # 检查是否与之前的问题相似
        for prev_q in previous_questions:
            # 简单的相似度检查：如果新问题包含之前问题的核心词汇
            similarity_score = self._calculate_question_similarity(new_question, prev_q)
            if similarity_score > 0.8:  # 相似度阈值
                self.logger.debug(f"问题相似度过高: {similarity_score:.2f}")
                return True
        
        return False
    
    def _calculate_question_similarity(self, q1: str, q2: str) -> float:
        """计算两个问题的相似度
        
        Args:
            q1, q2: 两个问题文本
            
        Returns:
            相似度分数 (0-1)
        """
        if not q1 or not q2:
            return 0.0
        
        # 提取关键词
        def extract_keywords(text):
            # 移除标点符号和常见停用词
            import re
            text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', ' ', text)
            words = text.split()
            stop_words = {'什么', '怎么', '如何', '为什么', '哪些', '请', '解释', '说明', '介绍', '一下', '详细'}
            return [w for w in words if w not in stop_words and len(w) > 1]
        
        keywords1 = set(extract_keywords(q1))
        keywords2 = set(extract_keywords(q2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    def _determine_question_type(self, state: AgentState, learning_state: Dict[str, Any]) -> str:
        """确定问题类型
        
        基于对话轮次和理解水平智能选择问题类型，避免重复
        """
        round_count = len(state.socratic_questions)
        understanding_level = learning_state.get("understanding_level", 0.5)
        
        # 🔧 修复：检查用户是否表达了困惑或重复感
        if state.user_response:
            confusion_indicators = ['上面问过', '重复', '不是问过', '刚才问过', '一样的问题']
            if any(indicator in state.user_response for indicator in confusion_indicators):
                self.logger.warning("用户表示问题重复，停止提问")
                return None  # 返回None表示停止提问
        
        # 🔧 修复：获取已使用的问题类型，避免重复
        used_types = []
        for q in state.socratic_questions:
            if isinstance(q, dict) and 'type' in q:
                used_types.append(q['type'])
            elif isinstance(q, str):
                # 尝试从问题文本推断类型
                if '最核心' in q or '特征' in q:
                    used_types.append('clarification')
                elif '例子' in q or '解释' in q:
                    used_types.append('evidence')
                else:
                    used_types.append('clarification')
        
        # 第一轮：澄清基础理解
        if round_count == 0:
            return "clarification"
        
        # 🔧 修复：根据理解水平和已使用类型选择新问题类型
        if understanding_level < 0.4:
            available_types = ["evidence", "clarification"]
        elif understanding_level < 0.7:
            available_types = ["assumption", "perspective", "evidence", "clarification"]
        else:
            available_types = ["implication", "meta", "synthesis", "application", "assumption", "perspective"]
        
        # 过滤掉已使用的类型
        remaining_types = [t for t in available_types if t not in used_types]
        
        # 如果所有类型都用过了，选择最合适的
        if not remaining_types:
            if understanding_level < 0.4:
                return "evidence"  # 低理解水平优先证据类问题
            elif understanding_level < 0.7:
                return "assumption"  # 中等理解水平使用假设类问题
            else:
                return "implication"  # 高理解水平使用含义类问题
        
        # 从剩余类型中选择
        return remaining_types[0]
    
    def _build_question_context(
        self, 
        state: AgentState, 
        question_type: str, 
        learning_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建问题生成上下文"""
        # 🔧 修复：优先使用对话历史中的原始查询，而不是当前用户响应
        original_query = state.user_query
        
        # 如果处于苏格拉底对话模式，尝试从对话历史中获取原始查询
        if state.socratic_questions and state.dialogue_history:
            # 从对话历史中找到最初的查询
            for dialogue in state.dialogue_history:
                if dialogue.get("query") and not dialogue.get("response"):
                    original_query = dialogue["query"]
                    break
        
        return {
            "concept": state.current_focus or self._extract_main_concept(state),
            "understanding_level": state.understanding_level.value if state.understanding_level else "unknown",
            "question_type": question_type,
            "learning_objective": state.learning_objectives[0] if state.learning_objectives else "深入理解概念",
            "user_query": original_query,  # 🔧 使用原始查询而不是当前响应
            "previous_questions": self._format_previous_questions(state),
            "user_latest_response": state.user_responses[-1] if state.user_responses else "",
            "dialogue_context": self._format_dialogue_context(state)  # 🔧 添加对话上下文
        }
    
    def _format_previous_questions(self, state: AgentState) -> str:
        """格式化之前的问题历史"""
        if not state.socratic_questions:
            return "无"
        
        recent_questions = state.socratic_questions[-2:]  # 最近2个问题
        formatted = []
        for i, q in enumerate(recent_questions, 1):
            question_text = q.get("question", q) if isinstance(q, dict) else q
            formatted.append(f"{i}. {question_text}")
        
        return "\n".join(formatted)
    
    def _format_dialogue_context(self, state: AgentState) -> str:
        """🔧 新增：格式化对话上下文，帮助理解当前对话状态"""
        if not state.dialogue_history:
            return "无对话历史"
        
        context_parts = []
        
        # 添加原始查询
        for dialogue in state.dialogue_history:
            if dialogue.get("query") and not dialogue.get("response"):
                context_parts.append(f"原始问题: {dialogue['query']}")
                break
        
        # 添加最近的问答对
        recent_dialogues = state.dialogue_history[-2:]  # 最近2轮对话
        for dialogue in recent_dialogues:
            if dialogue.get("query") and dialogue.get("response"):
                context_parts.append(f"问题: {dialogue['query']}")
                context_parts.append(f"回答: {dialogue['response']}")
        
        return "\n".join(context_parts) if context_parts else "无对话历史"
    
    def _extract_main_concept(self, state: AgentState) -> str:
        """提取主要概念"""
        if state.current_focus:
            return state.current_focus
        
        concept = self._extract_concept_from_query(state.user_query)
        if concept and concept != "概念":
            return concept
        
        if state.key_concepts_covered:
            return state.key_concepts_covered[0]
        
        query_words = state.user_query.split()
        return max(query_words, key=len) if query_words else "这个问题"
    
    def _extract_concept_from_query(self, query: str) -> str:
        """从查询中智能提取概念"""
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', query)
        
        stop_words = {
            '什么', '怎么', '如何', '为什么', '哪些', '请', '解释', '说明', 
            '介绍', '是什么', '有什么', '可以', '能够', '一下', '详细'
        }
        
        meaningful_words = [w for w in chinese_words if w not in stop_words]
        
        if meaningful_words:
            return max(meaningful_words, key=len)
        
        return "概念"
    
    def _parse_question_response(self, response_content: str, question_type: str) -> Dict[str, Any]:
        """解析LLM生成的问题响应"""
        try:
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

    def _assess_understanding_level(self, response: str) -> float:
        """评估理解水平"""
        score = 0.3
        
        if len(response) > 50:
            score += 0.2
        
        logical_words = ['因为', '所以', '但是', '然而', '因此', '由于']
        if any(word in response for word in logical_words):
            score += 0.2
        
        example_words = ['例如', '比如', '举例', '比方说']
        if any(word in response for word in example_words):
            score += 0.2
        
        reflection_words = ['我认为', '我觉得', '我的理解', '我的看法']
        if any(word in response for word in reflection_words):
            score += 0.1
        
        return min(score, 1.0)
    
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
    
    def _generate_fallback_question(self, state: AgentState) -> str:
        """生成备用问题（当LLM不可用或验证失败时）
        
        针对不同学习领域的专门问题
        """
        # 🔧 修复：检查用户最近的回应，如果是"我不知道"等表达，使用更具体的引导
        if state.user_responses:
            latest_response = state.user_responses[-1].lower()
            if any(phrase in latest_response for phrase in ["我不知道", "不明白", "不清楚", "不懂", "不会"]):
                # 用户表达了困惑，提供更具体的引导
                concept = self._extract_main_concept(state)
                questions = [
                    f"让我们从最基本的地方开始，{concept}这个词让你想到了什么？",
                    f"如果让你用一句话描述{concept}，你会怎么说？",
                    f"在你看来，{concept}最重要的特点是什么？",
                    f"你能想到{concept}的一个具体例子吗？"
                ]
                round_count = len(state.socratic_questions)
                return questions[round_count % len(questions)]
        
        query = state.user_query.lower()
        round_count = len(state.socratic_questions)
        
        # 评价判断类
        if any(word in query for word in ["好人", "坏人", "对", "错", "好", "坏"]):
            questions = [
                "在做出这种评价之前，你认为我们应该用什么标准来判断？",
                "这个评价涉及到哪些方面的考虑？",
                "不同的人可能会有不同的评价标准，你觉得为什么会这样？"
            ]
            return questions[round_count % len(questions)]
        
        # 概念解释类
        elif any(word in query for word in ["什么是", "介绍", "定义", "概念"]):
            concept = self._extract_main_concept(state)
            questions = [
                f"在我们深入了解{concept}之前，你已经对它有什么了解或印象？",
                f"你认为{concept}最核心的特征是什么？",
                f"如果要向完全不了解的人解释{concept}，你会用什么样的例子？"
            ]
            return questions[round_count % len(questions)]
        
        # 原因解释类
        elif any(word in query for word in ["为什么", "怎么", "如何", "原因"]):
            questions = [
                "你觉得这个现象或问题的根本原因可能是什么？",
                "这个过程涉及哪些关键的步骤或因素？",
                "如果我们改变其中的某个条件，会产生什么不同的结果？"
            ]
            return questions[round_count % len(questions)]
        
        # 默认通用引导
        else:
            questions = [
                "这是一个很好的问题。你觉得这个问题的核心是什么？",
                "让我们换个角度思考，这个问题可能涉及哪些不同的层面？",
                "你认为要完整回答这个问题，我们需要考虑哪些关键因素？"
            ]
            return questions[round_count % len(questions)]
    
    def process_user_response(self, state: AgentState, user_response: str) -> AgentState:
        """处理用户响应"""
        try:
            state.user_responses.append(user_response)
            
            response_analysis = self._analyze_user_response(user_response, state)
            
            if hasattr(state, 'learning_progress'):
                state.learning_progress.append(response_analysis)
            
            self.logger.info(f"Processed user response: {len(user_response)} characters")
            
        except Exception as e:
            self.logger.error(f"Failed to process user response: {e}")
            
        return state
    
    def _analyze_user_response(self, response: str, state: AgentState) -> Dict[str, Any]:
        """分析用户响应质量"""
        return {
            "response_length": len(response),
            "engagement_level": self._assess_engagement(response),
            "understanding_indicators": self._identify_understanding_indicators(response),
            "timestamp": state.timestamp
        }
    
    def _identify_understanding_indicators(self, response: str) -> List[str]:
        """识别理解指标"""
        indicators = []
        
        if any(word in response.lower() for word in ['因为', '所以', '但是', '然而']):
            indicators.append('logical_reasoning')
        
        if any(word in response.lower() for word in ['例如', '比如', '举例']):
            indicators.append('concrete_examples')
        
        if any(word in response.lower() for word in ['我认为', '我觉得', '我的看法']):
            indicators.append('personal_reflection')
        
        return indicators
    
    def should_continue_questioning(self, state: AgentState) -> bool:
        """判断是否应该继续提问"""
        if len(state.socratic_questions) >= self.max_questions:
            return False
        
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
            "question_history": self.question_history[-5:],
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
    