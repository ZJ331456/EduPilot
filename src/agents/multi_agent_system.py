#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多智能体系统
协调所有智能体的工作流程
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid
from utils import BaseAgent, AgentState, AgentRegistry, ConversationStage, UnderstandingLevel
from prompts import get_prompt, PromptType
from agents.query_interpreter_integrated import QueryInterpreterAgent
from agents.decision_agent import DecisionAgent
from agents.knowledge_retriever import KnowledgeRetrieverAgent
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.socratic_guide import SocraticGuideAgent
from agents.learner import LearnerAgent
from agents.user_profile_integrated import UserProfileAgent
from utils.enums import QueryType

class MultiAgentSystem:
    """多智能体系统
    
    协调所有智能体的工作流程，实现完整的学习交互循环
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化智能体注册表
        self.registry = AgentRegistry()
        
        # 初始化所有智能体
        self._initialize_agents()
        
        # 工作流程配置
        self.workflow_config = {
            "max_iterations": self.config.get("max_iterations", 5),
            "timeout_seconds": self.config.get("timeout_seconds", 300),
            "enable_learning": self.config.get("enable_learning", True),
            "enable_socratic": self.config.get("enable_socratic", True),
            "auto_continue": self.config.get("auto_continue", False)
        }
        
        # 系统状态
        self.active_sessions = {}
        self.system_stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "average_session_duration": 0.0,
            "total_queries_processed": 0
        }
        
        # 工作流程定义
        self.workflow_steps = [
            ("query_interpreter", self._execute_query_interpretation),
            ("decision_agent", self._execute_decision_analysis),
            ("user_profile", self._execute_user_profile_analysis),
            ("knowledge_retriever", self._execute_knowledge_retrieval),
            ("socratic_guide", self._execute_socratic_guidance),
            ("planner", self._execute_planning),
            ("executor", self._execute_execution),
            ("learner", self._execute_learning)
        ]
    
    def _initialize_agents(self):
        """初始化所有智能体"""
        try:
            # 创建智能体实例
            agents = {
                "QueryInterpreterAgent": QueryInterpreterAgent(),
                "DecisionAgent": DecisionAgent(),
                "KnowledgeRetrieverAgent": KnowledgeRetrieverAgent(),
                "UserProfileAgent": UserProfileAgent(),
                "SocraticGuideAgent": SocraticGuideAgent(enable_enhanced_mode=True),
                "PlannerAgent": PlannerAgent(),
                "ExecutorAgent": ExecutorAgent(),
                "LearnerAgent": LearnerAgent(enable_enhanced_mode=True)
            }
            
            # 注册所有智能体
            for name, agent in agents.items():
                self.registry.register(agent)
            
            # 设置智能体字典以便在对话流程中使用
            self.agents = {
                "query_interpreter": agents["QueryInterpreterAgent"],
                "decision_agent": agents["DecisionAgent"],
                "knowledge_retriever": agents["KnowledgeRetrieverAgent"],
                "user_profile": agents["UserProfileAgent"],
                "socratic_guide": agents["SocraticGuideAgent"],
                "planner": agents["PlannerAgent"],
                "executor": agents["ExecutorAgent"],
                "learner": agents["LearnerAgent"]
            }
            
            # 设置智能体属性以便外部访问
            self.learner = agents["LearnerAgent"]
            self.socratic_guide = agents["SocraticGuideAgent"]
            self.planner = agents["PlannerAgent"]
            self.decision_agent = agents["DecisionAgent"]
            self.executor = agents["ExecutorAgent"]
            self.query_interpreter = agents["QueryInterpreterAgent"]
            self.knowledge_retriever = agents["KnowledgeRetrieverAgent"]
            self.user_profile = agents["UserProfileAgent"]
            
            self.logger.info(f"Initialized {len(agents)} agents successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def process_query(self, user_query: str, session_id: Optional[str] = None, 
                          user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户查询
        
        Args:
            user_query: 用户查询
            session_id: 会话ID（可选）
            user_context: 用户上下文（可选）
            
        Returns:
            处理结果
        """
        try:
            # 检查是否是新话题
            is_new_topic = self._detect_new_topic(user_query, session_id)
            
            # 如果是新话题，重置会话状态
            if is_new_topic and session_id in self.active_sessions:
                self.logger.info(f"检测到新话题，重置会话 {session_id}")
                del self.active_sessions[session_id]
                session_id = None
            
            # 创建或获取会话
            if not session_id:
                session_id = str(uuid.uuid4())
                self.logger.info(f"创建新会话: {session_id}")
            
            # 初始化或获取状态
            if session_id not in self.active_sessions:
                state = AgentState(
                    session_id=session_id,
                    user_query=user_query,
                    user_context=user_context or {},
                    conversation_stage=ConversationStage.INITIAL_QUERY,
                    conversation_round=1,
                    max_conversation_rounds=10
                )
                self.active_sessions[session_id] = {
                    "state": state,
                    "start_time": datetime.now(),
                    "current_step": "initial_query"
                }
            else:
                state = self.active_sessions[session_id]["state"]
                state.user_query = user_query
                state.user_context.update(user_context or {})
                # 如果是新话题，重置对话阶段
                if is_new_topic:
                    state.conversation_stage = ConversationStage.INITIAL_QUERY
                    state.conversation_round = 1
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行对话工作流程
            result = await self._execute_conversation_workflow(state)
            
            # 更新会话信息
            self.active_sessions[session_id]["current_step"] = state.conversation_stage.value
            
            # 更新统计信息
            self._update_system_stats(session_id, start_time, result.get("success", False))
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理查询失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _execute_conversation_workflow(self, state: AgentState) -> Dict[str, Any]:
        """执行对话式工作流程，支持多轮交互"""
        try:
            # 根据对话阶段执行不同的流程
            if state.conversation_stage == ConversationStage.INITIAL_QUERY:
                return await self._handle_initial_query(state)
            elif state.conversation_stage == ConversationStage.UNDERSTANDING_CHECK:
                return await self._handle_understanding_check(state)
            elif state.conversation_stage == ConversationStage.SOCRATIC_QUESTIONING:
                return await self._handle_socratic_questioning(state)
            elif state.conversation_stage == ConversationStage.COMPREHENSION_VALIDATION:
                return await self._handle_comprehension_validation(state)
            else:
                # 默认处理
                return await self._execute_workflow(state)
                
        except Exception as e:
            self.logger.error(f"Conversation workflow failed: {e}")
            return {
                "success": False,
                "response": "对话处理过程中出现错误",
                "conversation_complete": True,
                "waiting_for_user": False,
                "error": str(e)
            }
    
    async def _handle_initial_query(self, state: AgentState) -> Dict[str, Any]:
        """处理初始查询"""
        # 1. 解释查询
        state = await self._run_agent_async(self.agents["query_interpreter"], state)
        if state.has_error():
            return self._create_error_response(state)
        
        # 2. 决策分析
        state = await self._run_agent_async(self.agents["decision_agent"], state)
        if state.has_error():
            return self._create_error_response(state)
        
        # 3. 用户画像分析
        state = await self._run_agent_async(self.agents["user_profile"], state)
        if state.has_error():
            self.logger.warning(f"User profile analysis failed: {state.get_errors()}")
            # 用户画像分析失败不应该阻止整个流程
        
        # 4. 知识检索（如果需要）
        if hasattr(state, 'retrieval_decision') and state.retrieval_decision.get('need_retrieval', False):
            state = await self._run_agent_async(self.agents["knowledge_retriever"], state)
            if state.has_error():
                return self._create_error_response(state)
        
        # 5. 规划
        state = await self._run_agent_async(self.agents["planner"], state)
        if state.has_error():
            return self._create_error_response(state)
        
        # 6. 执行初始回答
        state = await self._run_agent_async(self.agents["executor"], state)
        if state.has_error():
            return self._create_error_response(state)
        
        # 7. 生成苏格拉底式问题（仅对非直接回答类型）
        if state.query_type != QueryType.DIRECT_ANSWER:
            state.advance_conversation_stage(ConversationStage.SOCRATIC_QUESTIONING)
            state = await self._run_agent_async(self.agents["socratic_guide"], state)
            
            if state.has_error():
                return self._create_error_response(state)
        else:
            # 对于直接回答类型，直接结束对话
            state.advance_conversation_stage(ConversationStage.CONCLUSION)
        
        # 构建响应
        response_parts = []
        
        # 添加初始回答
        if state.execution_result and state.execution_result.get("final_response"):
            response_parts.append(state.execution_result["final_response"])
        
        # 添加苏格拉底式问题（仅对非直接回答类型）
        if state.query_type != QueryType.DIRECT_ANSWER and state.socratic_question:
            response_parts.append(f"\n💭 {state.socratic_question}")
        
        # 构建返回结果
        result = {
            "success": True,
            "session_id": state.session_id,
            "response": "\n\n".join(response_parts),
            "conversation_complete": state.query_type == QueryType.DIRECT_ANSWER,  # 直接回答类型直接结束
            "waiting_for_user": state.query_type != QueryType.DIRECT_ANSWER,  # 直接回答类型不等待用户回应
            "conversation_stage": state.conversation_stage.value,
            "understanding_level": state.understanding_level.value,
            "round": state.conversation_round
        }
        
        # 添加苏格拉底式问题字段（如果存在）
        if state.query_type != QueryType.DIRECT_ANSWER and state.socratic_question:
            result["socratic_question"] = state.socratic_question
        
        return result
    
    async def _handle_understanding_check(self, state: AgentState) -> Dict[str, Any]:
        """处理理解检查阶段"""
        # 评估用户理解
        understanding_result = await self._assess_user_understanding(state)
        
        if understanding_result["is_understood"]:
            # 理解正确，进入验证阶段
            state.advance_conversation_stage(ConversationStage.COMPREHENSION_VALIDATION)
            state.update_understanding_level(understanding_result["understanding_level"])
        else:
            # 理解不够，继续苏格拉底式引导
            state.advance_conversation_stage(ConversationStage.SOCRATIC_QUESTIONING)
        
        return await self._handle_socratic_questioning(state)
    
    async def _handle_socratic_questioning(self, state: AgentState) -> Dict[str, Any]:
        """处理苏格拉底式提问阶段"""
        # 如果有用户回应，先评估理解水平
        if state.user_response:
            understanding_result = await self._assess_user_understanding(state)
            state.update_understanding_level(understanding_result["understanding_level"])
            
            # 记录评估信息
            state.conversation_context["last_understanding_assessment"] = understanding_result
        
        # 检查是否应该继续提问
        if not state.should_continue_socratic_questioning():
            return await self._conclude_conversation(state)
        
        # 生成下一个苏格拉底式问题
        state = await self._run_agent_async(self.agents["socratic_guide"], state)
        
        if state.has_error():
            return self._create_error_response(state)
        
        return {
            "success": True,
            "session_id": state.session_id,
            "response": state.socratic_question,
            "socratic_question": state.socratic_question,
            "conversation_complete": False,
            "waiting_for_user": True,
            "conversation_stage": state.conversation_stage.value,
            "understanding_level": state.understanding_level.value,
            "round": state.conversation_round
        }
    
    async def _handle_comprehension_validation(self, state: AgentState) -> Dict[str, Any]:
        """处理理解验证阶段"""
        # 最终验证理解
        understanding_result = await self._assess_user_understanding(state, final_check=True)
        
        if understanding_result["is_mastered"]:
            # 完全理解，结束对话
            return await self._conclude_conversation(state, success=True)
        elif understanding_result["is_understood"]:
            # 基本理解，可以结束或继续深入
            if state.conversation_round >= state.max_conversation_rounds - 2:
                return await self._conclude_conversation(state, success=True)
            else:
                # 继续深入探索
                state.advance_conversation_stage(ConversationStage.DEEPER_EXPLORATION)
                return await self._handle_socratic_questioning(state)
        else:
            # 理解不够，回到苏格拉底式提问
            state.advance_conversation_stage(ConversationStage.SOCRATIC_QUESTIONING)
            return await self._handle_socratic_questioning(state)
    
    async def _conclude_conversation(self, state: AgentState, success: bool = True) -> Dict[str, Any]:
        """结束对话"""
        state.advance_conversation_stage(ConversationStage.CONCLUSION)
        
        # 生成学习分析
        state = await self._run_agent_async(self.agents["learner"], state)
        
        # 构建结束响应
        conclusion_parts = []
        
        if success:
            conclusion_parts.append("很好！通过我们的对话，您已经对这个概念有了很好的理解。")
        else:
            conclusion_parts.append("我们的对话时间已经到了。让我们总结一下讨论的要点。")
        
        # 添加学习总结
        if state.learning_feedback:
            summary = state.learning_feedback.get("summary", "")
            if summary:
                conclusion_parts.append(f"\n📚 学习总结：\n{summary}")
        
        # 添加建议
        if state.learning_feedback and state.learning_feedback.get("recommendations"):
            recommendations = state.learning_feedback["recommendations"]
            if recommendations:
                conclusion_parts.append(f"\n💡 进一步学习建议：")
                for rec in recommendations[:3]:  # 最多3个建议
                    conclusion_parts.append(f"• {rec}")
        
        return {
            "success": success,
            "session_id": state.session_id,
            "response": "\n".join(conclusion_parts),
            "conversation_complete": True,
            "waiting_for_user": False,
            "conversation_stage": state.conversation_stage.value,
            "understanding_level": state.understanding_level.value,
            "total_rounds": state.conversation_round,
            "conversation_summary": state.get_conversation_summary()
        }
    
    async def _assess_user_understanding(self, state: AgentState, final_check: bool = False) -> Dict[str, Any]:
        """评估用户理解程度"""
        try:
            from utils.llm import get_llm_manager, Message, MessageRole
            
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                self.logger.warning("No LLM client available, using simple assessment")
                return self._simple_understanding_assessment(state)
            
            # 构建详细的评估提示
            topic = state.current_focus or state.user_query
            user_response = state.user_response
            
            # 获取对话历史用于上下文
            dialogue_context = ""
            if state.dialogue_history:
                recent_dialogue = state.dialogue_history[-3:]  # 最近3轮对话
                dialogue_context = "\n".join([
                    f"问题: {turn.get('question', '')}\n回答: {turn.get('response', '')}"
                    for turn in recent_dialogue
                ])
            
            system_prompt = get_prompt(PromptType.UNDERSTANDING_ASSESSMENT_SYSTEM)

            user_prompt = f"""请评估以下学生回答的理解水平：

话题：{topic}

最新回答：{user_response}

对话历史（用于上下文）：
{dialogue_context}

请仔细分析并给出评估结果。"""

            messages = [
                Message(role=MessageRole.SYSTEM, content=system_prompt),
                Message(role=MessageRole.USER, content=user_prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                # 解析LLM的评估结果
                return self._parse_llm_understanding_result(response.content, final_check)
            else:
                self.logger.warning(f"LLM assessment failed: {response.error}")
                return self._simple_understanding_assessment(state)
                
        except Exception as e:
            self.logger.warning(f"Understanding assessment failed: {e}")
            return self._simple_understanding_assessment(state)
    
    def _simple_understanding_assessment(self, state: AgentState) -> Dict[str, Any]:
        """简单的理解评估（fallback方法）"""
        response = state.user_response.strip()
        self.logger.info(f"评估用户回答: '{response}'")
        
        # 困惑或拒绝的表达
        confusion_indicators = ["什么意思", "不懂", "不明白", "困惑", "不理解", "?", "？", "啥", "什么"]
        if any(indicator in response for indicator in confusion_indicators):
            self.logger.info(f"检测到困惑表达，评估为NO_UNDERSTANDING")
            return {
                "understanding_level": UnderstandingLevel.NO_UNDERSTANDING,
                "is_understood": False,
                "is_mastered": False,
                "confidence": 0.9
            }
        
        # 基于回答长度和内容质量评估
        response_length = len(response)
        self.logger.info(f"回答长度: {response_length}")
        
        if response_length < 5:
            understanding_level = UnderstandingLevel.NO_UNDERSTANDING
            is_understood = False
            self.logger.info(f"回答太短，评估为NO_UNDERSTANDING")
        elif response_length < 15:
            understanding_level = UnderstandingLevel.SURFACE_UNDERSTANDING
            is_understood = False
            self.logger.info(f"回答较短，评估为SURFACE_UNDERSTANDING")
        else:
            # 检查是否有实质性内容
            substantive_indicators = [
                "因为", "所以", "认为", "觉得", "应该", "可能", "比如", "例如", 
                "历史", "政治", "军事", "品格", "道德", "标准", "角度", "立场",
                "贡献", "功绩", "评价", "判断"  # 添加更多相关词汇
            ]
            
            found_indicators = [indicator for indicator in substantive_indicators if indicator in response]
            self.logger.info(f"找到的实质性指标: {found_indicators}")
            
            if found_indicators:
                understanding_level = UnderstandingLevel.BASIC_UNDERSTANDING
                is_understood = True
                self.logger.info(f"检测到实质性内容，评估为BASIC_UNDERSTANDING")
            else:
                understanding_level = UnderstandingLevel.SURFACE_UNDERSTANDING

                is_understood = False
                self.logger.info(f"未检测到实质性内容，评估为SURFACE_UNDERSTANDING")
        
        result = {
            "understanding_level": understanding_level,
            "is_understood": is_understood,
            "is_mastered": understanding_level in [UnderstandingLevel.DEEP_UNDERSTANDING, UnderstandingLevel.MASTERY],
            "confidence": 0.7
        }
        
        self.logger.info(f"最终评估结果: {result}")
        return result
    
    def _parse_llm_understanding_result(self, llm_response: str, final_check: bool) -> Dict[str, Any]:
        """解析LLM的理解评估结果（新版本）"""
        try:
            import json
            
            self.logger.info(f"LLM评估原始响应: {llm_response}")
            
            # 尝试解析JSON格式的响应
            if "{" in llm_response and "}" in llm_response:
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                json_str = llm_response[json_start:json_end]
                
                try:
                    result = json.loads(json_str)
                    
                    # 获取理解水平
                    understanding_level_str = result.get("understanding_level", "basic_understanding")
                    
                    # 映射理解水平
                    level_mapping = {
                        "no_understanding": UnderstandingLevel.NO_UNDERSTANDING,
                        "surface_understanding": UnderstandingLevel.SURFACE_UNDERSTANDING,
                        "basic_understanding": UnderstandingLevel.BASIC_UNDERSTANDING,
                        "good_understanding": UnderstandingLevel.GOOD_UNDERSTANDING,
                        "deep_understanding": UnderstandingLevel.DEEP_UNDERSTANDING,
                        "mastery": UnderstandingLevel.MASTERY
                    }
                    
                    understanding_level = level_mapping.get(understanding_level_str, UnderstandingLevel.BASIC_UNDERSTANDING)
                    confidence = result.get("confidence", 0.7)
                    
                    # 判断是否理解
                    is_understood = understanding_level.level_value >= UnderstandingLevel.BASIC_UNDERSTANDING.level_value
                    is_mastered = understanding_level in [UnderstandingLevel.DEEP_UNDERSTANDING, UnderstandingLevel.MASTERY]
                    
                    assessment_result = {
                        "understanding_level": understanding_level,
                        "is_understood": is_understood,
                        "is_mastered": is_mastered,
                        "confidence": confidence,
                        "analysis": result.get("analysis", ""),
                        "evidence": result.get("evidence", []),
                        "suggestions": result.get("suggestions", [])
                    }
                    
                    self.logger.info(f"LLM评估结果: 理解水平={understanding_level.value}, 已理解={is_understood}, 置信度={confidence}")
                    return assessment_result
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON解析失败: {e}")
            
            # 如果JSON解析失败，尝试从文本中提取信息
            return self._extract_understanding_from_text(llm_response)
            
        except Exception as e:
            self.logger.warning(f"LLM评估结果解析失败: {e}")
            # 回退到简单评估
            return self._simple_understanding_assessment_fallback(llm_response)
    
    def _extract_understanding_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取理解水平（当JSON解析失败时使用）"""
        text_lower = text.lower()
        
        # 查找理解水平关键词
        level_keywords = {
            "mastery": ["精通", "掌握", "融会贯通", "创新"],
            "deep_understanding": ["深度理解", "深入", "多角度", "全面"],
            "good_understanding": ["良好理解", "很好", "不错", "清楚", "明确"],
            "basic_understanding": ["基础理解", "基本", "初步", "简单"],
            "surface_understanding": ["表面理解", "肤浅", "浅显"],
            "no_understanding": ["不理解", "困惑", "不懂", "混乱"]
        }
        
        # 按优先级检查（从高到低）
        for level, keywords in level_keywords.items():
            if any(keyword in text for keyword in keywords):
                understanding_level = getattr(UnderstandingLevel, level.upper())
                is_understood = understanding_level.level_value >= UnderstandingLevel.BASIC_UNDERSTANDING.level_value
                
                return {
                    "understanding_level": understanding_level,
                    "is_understood": is_understood,
                    "is_mastered": understanding_level in [UnderstandingLevel.DEEP_UNDERSTANDING, UnderstandingLevel.MASTERY],
                    "confidence": 0.6,
                    "analysis": f"从文本中提取的评估: {text[:200]}...",
                    "evidence": [],
                    "suggestions": []
                }
        
        # 默认返回基础理解
        return {
            "understanding_level": UnderstandingLevel.BASIC_UNDERSTANDING,
            "is_understood": True,
            "is_mastered": False,
            "confidence": 0.5,
            "analysis": "无法从文本中明确判断理解水平",
            "evidence": [],
            "suggestions": []
        }
    
    def _simple_understanding_assessment_fallback(self, text: str) -> Dict[str, Any]:
        """简化的评估方法（最后的fallback）"""
        text_length = len(text.strip())
        
        if text_length < 10:
            understanding_level = UnderstandingLevel.NO_UNDERSTANDING
        elif text_length < 30:
            understanding_level = UnderstandingLevel.SURFACE_UNDERSTANDING
        else:
            understanding_level = UnderstandingLevel.BASIC_UNDERSTANDING
        
        return {
            "understanding_level": understanding_level,
            "is_understood": understanding_level.level_value >= UnderstandingLevel.BASIC_UNDERSTANDING.level_value,
            "is_mastered": False,
            "confidence": 0.4,
            "analysis": f"基于文本长度的简单评估: {text_length}字符",
            "evidence": [],
            "suggestions": []
        }
    
    def _parse_understanding_result(self, llm_response: str, final_check: bool) -> Dict[str, Any]:
        """解析LLM的理解评估结果"""
        try:
            import json
            # 尝试解析JSON格式的响应
            if "{" in llm_response and "}" in llm_response:
                json_str = llm_response[llm_response.find("{"):llm_response.rfind("}")+1]
                result = json.loads(json_str)
                
                understanding_level_str = result.get("understanding_level", "basic_understanding")
                
                # 映射理解水平
                level_mapping = {
                    "完全理解": UnderstandingLevel.DEEP_UNDERSTANDING,
                    "基本理解": UnderstandingLevel.BASIC_UNDERSTANDING,
                    "部分理解": UnderstandingLevel.SURFACE_UNDERSTANDING,
                    "理解不足": UnderstandingLevel.NO_UNDERSTANDING,
                    "mastery": UnderstandingLevel.MASTERY,
                    "deep_understanding": UnderstandingLevel.DEEP_UNDERSTANDING,
                    "good_understanding": UnderstandingLevel.GOOD_UNDERSTANDING,
                    "basic_understanding": UnderstandingLevel.BASIC_UNDERSTANDING,
                    "surface_understanding": UnderstandingLevel.SURFACE_UNDERSTANDING,
                    "no_understanding": UnderstandingLevel.NO_UNDERSTANDING
                }
                
                understanding_level = level_mapping.get(understanding_level_str, UnderstandingLevel.BASIC_UNDERSTANDING)
                
                return {
                    "understanding_level": understanding_level,
                    "is_understood": result.get("is_ready_to_proceed", False) or understanding_level.level_value >= UnderstandingLevel.BASIC_UNDERSTANDING.level_value,
                    "is_mastered": understanding_level in [UnderstandingLevel.DEEP_UNDERSTANDING, UnderstandingLevel.MASTERY],
                    "confidence": result.get("confidence", 0.7)
                }
        except Exception as e:
            self.logger.debug(f"Failed to parse understanding result: {e}")
        
        # 回退到简单评估
        return self._simple_understanding_assessment(state)
    
    def _create_error_response(self, state: AgentState) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "success": False,
            "session_id": state.session_id,
            "response": "抱歉，处理过程中出现了问题。让我们重新开始吧。",
            "conversation_complete": True,
            "waiting_for_user": False,
            "error": state.get_errors()
        }

    async def _execute_workflow(self, state: AgentState) -> Dict[str, Any]:
        """执行完整的工作流程"""
        workflow_result = {
            "success": False,
            "session_id": state.session_id,
            "steps_completed": [],
            "final_response": "",
            "execution_summary": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 执行每个工作流程步骤
            for step_name, step_function in self.workflow_steps:
                try:
                    self.logger.info(f"Executing step: {step_name} for session {state.session_id}")
                    
                    # 更新当前步骤
                    if state.session_id in self.active_sessions:
                        self.active_sessions[state.session_id]["current_step"] = step_name
                    
                    # 执行步骤
                    state = await step_function(state)
                    
                    # 记录完成的步骤
                    workflow_result["steps_completed"].append(step_name)
                    
                    # 检查是否有错误
                    if state.has_error():
                        self.logger.warning(f"Step {step_name} completed with errors: {state.get_errors()}")
                        # 继续执行，不中断工作流程
                    
                    # 特殊处理：如果是苏格拉底引导步骤，可能需要等待用户响应
                    if step_name == "socratic_guide" and self._should_wait_for_user_response(state):
                        # 在实际应用中，这里可能需要暂停工作流程等待用户输入
                        # 目前我们继续执行
                        pass
                    
                except Exception as e:
                    self.logger.error(f"Step {step_name} failed: {e}")
                    state.set_error(f"{step_name}_error", str(e))
                    # 继续执行下一步
            
            # 检查是否有苏格拉底问题需要用户响应
            if self._should_wait_for_user_response(state):
                # 获取最新的苏格拉底问题
                latest_question = state.socratic_questions[-1] if state.socratic_questions else None
                
                workflow_result["socratic_question"] = latest_question
                workflow_result["waiting_for_response"] = True
                workflow_result["final_response"] = "正在进行苏格拉底式引导，请回答上述问题。"
                workflow_result["success"] = True  # 苏格拉底模式下的暂停也算成功
                
                # 获取问题总结
                socratic_agent = self.registry.get("SocraticGuide")
                if socratic_agent and hasattr(socratic_agent, 'get_question_summary'):
                    workflow_result["question_summary"] = socratic_agent.get_question_summary(state)
            else:
                # 提取最终结果
                if state.execution_result:
                    workflow_result["final_response"] = state.execution_result.get("final_response", "")
                    workflow_result["execution_summary"] = state.execution_result.get("execution_summary", {})
                
                # 检查整体成功状态
                workflow_result["success"] = (
                    len(workflow_result["steps_completed"]) >= 4 and  # 至少完成4个关键步骤
                    bool(workflow_result["final_response"])  # 有最终响应
                )
            
            # 添加状态信息
            workflow_result["state_summary"] = self._create_state_summary(state)
            
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            workflow_result["error"] = str(e)
            return workflow_result
    
    async def _execute_query_interpretation(self, state: AgentState) -> AgentState:
        """执行查询解释步骤"""
        agent = self.registry.get("QueryInterpreter")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_knowledge_retrieval(self, state: AgentState) -> AgentState:
        """执行知识检索步骤"""
        agent = self.registry.get("KnowledgeRetriever")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_decision_analysis(self, state: AgentState) -> AgentState:
        """执行决策分析步骤"""
        agent = self.registry.get("DecisionAgent")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_user_profile_analysis(self, state: AgentState) -> AgentState:
        """执行用户画像分析步骤"""
        agent = self.registry.get("UserProfileAgent")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_socratic_guidance(self, state: AgentState) -> AgentState:
        """执行苏格拉底引导步骤（已集成增强功能）"""
        if not self.workflow_config["enable_socratic"]:
            return state
        
        agent = self.registry.get("SocraticGuide")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_planning(self, state: AgentState) -> AgentState:
        """执行规划步骤"""
        agent = self.registry.get("Planner")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_execution(self, state: AgentState) -> AgentState:
        """执行执行步骤"""
        agent = self.registry.get("Executor")
        if agent and agent.can_execute(state):
            return await self._run_agent_async(agent, state)
        return state
    
    async def _execute_learning(self, state: AgentState) -> AgentState:
        """执行学习步骤（已集成增强功能）"""
        if not self.workflow_config["enable_learning"]:
            return state
        
        agent = self.registry.get("Learner")
        if agent and agent.can_execute(state):
            state = await self._run_agent_async(agent, state)
            self.logger.info("Learning analysis completed with enhanced features")
        
        return state
    
    async def _run_agent_async(self, agent: BaseAgent, state: AgentState) -> AgentState:
        """异步运行智能体"""
        try:
            # 直接调用异步的run方法
            return await agent.run(state)
        except Exception as e:
            self.logger.error(f"Agent {agent.name} execution failed: {e}")
            state.set_error(f"{agent.name}_execution_error", str(e))
            return state
    
    def _should_wait_for_user_response(self, state: AgentState) -> bool:
        """判断是否应该等待用户响应"""
        return (
            state.socratic_questions and
            len(state.socratic_questions) > len(state.user_responses or [])
        )
    
    def _create_state_summary(self, state: AgentState) -> Dict[str, Any]:
        """创建状态摘要"""
        summary = {
            "session_id": state.session_id,
            "query_interpreted": bool(state.interpretation),
            "knowledge_retrieved": bool(state.retrieved_knowledge),
            "socratic_questions_count": len(state.socratic_questions or []),
            "user_responses_count": len(state.user_responses or []),
            "plan_created": bool(state.plan),
            "execution_completed": bool(state.execution_result),
            "learning_feedback_generated": bool(state.learning_feedback),
            "errors_count": len(state.get_errors()),
            "has_errors": state.has_error()
        }
        
        # 添加用户画像数据
        try:
            user_profile_agent = self.registry.get("UserProfileAgent")
            if user_profile_agent:
                # 获取用户ID
                user_id = state.metadata.get('user_id', 'default_user')
                # 构建用户上下文（需要使用 await，但这里是同步方法，所以先检查是否有缓存的数据）
                if hasattr(user_profile_agent, 'user_profiles') and user_id in user_profile_agent.user_profiles:
                    profile = user_profile_agent.user_profiles[user_id]
                    summary["user_profile_data"] = {
                        "entity_count": len(profile.get('triples', [])),
                        "relationship_count": len([t for t in profile.get('triples', []) if 'predicate' in t]),
                        "user_summary": {
                            "total_interactions": len(profile.get('triples', [])),
                            "primary_interests": [t['object'] for t in profile.get('triples', []) if t.get('dimension') == 'interests'][:3],
                            "knowledge_areas": list(set([t['object'] for t in profile.get('triples', []) if t.get('dimension') == 'knowledge_level']))[:5]
                        }
                    }
        except Exception as e:
            self.logger.warning(f"Failed to get user profile data: {e}")
        
        return summary
    
    def _update_system_stats(self, session_id: str, start_time: datetime, success: bool):
        """更新系统统计信息"""
        try:
            duration = (datetime.now() - start_time).total_seconds()
            
            self.system_stats["total_sessions"] += 1
            self.system_stats["total_queries_processed"] += 1
            
            if success:
                self.system_stats["successful_sessions"] += 1
            
            # 更新平均会话时长
            total_sessions = self.system_stats["total_sessions"]
            current_avg = self.system_stats["average_session_duration"]
            self.system_stats["average_session_duration"] = (
                (current_avg * (total_sessions - 1) + duration) / total_sessions
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to update system stats: {e}")
    
    def add_user_response(self, session_id: str, response: str) -> Dict[str, Any]:
        """添加用户响应
        
        Args:
            session_id: 会话ID
            response: 用户响应
            
        Returns:
            处理结果
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "error": "Session not found or expired"
                }
            
            session_info = self.active_sessions[session_id]
            state = session_info["state"]
            
            # 添加用户响应
            if not state.user_responses:
                state.user_responses = []
            state.user_responses.append(response)
            
            # 如果启用了自动继续，可以继续执行工作流程
            if self.workflow_config["auto_continue"]:
                # 这里可以实现继续执行逻辑
                pass
            
            return {
                "success": True,
                "message": "User response added successfully",
                "responses_count": len(state.user_responses)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to add user response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态信息
        """
        if session_id not in self.active_sessions:
            return {
                "exists": False,
                "message": "Session not found"
            }
        
        session_info = self.active_sessions[session_id]
        state = session_info["state"]
        
        return {
            "exists": True,
            "session_id": session_id,
            "start_time": session_info["start_time"].isoformat(),
            "current_step": session_info.get("current_step", "unknown"),
            "state_summary": self._create_state_summary(state),
            "waiting_for_response": self._should_wait_for_user_response(state),
            "latest_question": state.socratic_questions[-1] if state.socratic_questions else None
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = dict(self.system_stats)
        stats["active_sessions_count"] = len(self.active_sessions)
        stats["registered_agents_count"] = len(self.registry.list_agents())
        stats["success_rate"] = (
            self.system_stats["successful_sessions"] / max(self.system_stats["total_sessions"], 1)
        )
        
        # 添加智能体统计信息
        agent_stats = {}
        for name, agent in self.registry.get_all_agents().items():
            if hasattr(agent, 'get_statistics'):
                try:
                    agent_stats[name] = agent.get_statistics()
                except Exception as e:
                    self.logger.warning(f"Failed to get stats for agent {name}: {e}")
                    agent_stats[name] = {"error": str(e)}
        
        stats["agent_statistics"] = agent_stats
        
        return stats
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流程配置"""
        return dict(self.workflow_config)
    
    def update_workflow_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流程配置
        
        Args:
            config_updates: 配置更新
            
        Returns:
            更新结果
        """
        try:
            # 验证配置键
            valid_keys = set(self.workflow_config.keys())
            invalid_keys = set(config_updates.keys()) - valid_keys
            
            if invalid_keys:
                return {
                    "success": False,
                    "error": f"Invalid configuration keys: {invalid_keys}"
                }
            
            # 更新配置
            self.workflow_config.update(config_updates)
            
            return {
                "success": True,
                "message": "Workflow configuration updated successfully",
                "updated_config": dict(self.workflow_config)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """清理过期会话
        
        Args:
            max_age_hours: 最大会话年龄（小时）
        """
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_info in list(self.active_sessions.items()):
                session_age = current_time - session_info["start_time"]
                if session_age.total_seconds() > max_age_hours * 3600:
                    expired_sessions.append(session_id)
            
            # 删除过期会话
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            if expired_sessions:
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            self.logger.warning(f"Failed to cleanup expired sessions: {e}")
    
    def shutdown(self):
        """关闭多智能体系统"""
        try:
            # 清理所有活动会话
            self.active_sessions.clear()
            
            # 清理智能体注册表
            self.registry.clear()
            
            self.logger.info("Multi-agent system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
    
    # 用户画像管理方法
    
    def get_user_profile(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取用户画像信息"""
        try:
            if hasattr(self, 'user_profile') and self.user_profile:
                return self.user_profile.get_user_profile(session_id)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get user profile: {e}")
            return {}
    
    def export_user_profile(self, export_path: str, format_type: str = 'rdf-json') -> bool:
        """导出用户画像知识图谱"""
        try:
            if hasattr(self, 'user_profile') and self.user_profile:
                return self.user_profile.export_user_profile(export_path, format_type)
            return False
        except Exception as e:
            self.logger.error(f"Failed to export user profile: {e}")
            return False
    
    def clear_user_profile(self) -> bool:
        """清空用户画像知识图谱"""
        try:
            if hasattr(self, 'user_profile') and self.user_profile:
                return self.user_profile.clear_user_profile()
            return False
        except Exception as e:
            self.logger.error(f"Failed to clear user profile: {e}")
            return False
    
    def get_user_profile_statistics(self) -> Dict[str, Any]:
        """获取用户画像统计信息"""
        try:
            if hasattr(self, 'user_profile') and self.user_profile:
                return self.user_profile.get_statistics()
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get user profile statistics: {e}")
            return {}
    
    def _detect_new_topic(self, user_query: str, session_id: Optional[str] = None) -> bool:
        """检测是否是新话题
        
        Args:
            user_query: 用户查询
            session_id: 会话ID
            
        Returns:
            是否是新话题
        """
        # 如果没有会话，肯定是新话题
        if not session_id or session_id not in self.active_sessions:
            return True
        
        # 获取当前会话状态
        state = self.active_sessions[session_id]["state"]
        
        # 检测新话题的关键词
        new_topic_indicators = [
            # 身份询问
            "你是什么", "你叫什么", "你是谁", "你的名字", "你是什么模型", "你是什么AI", "基座模型",
            # 功能询问
            "你能做什么", "你有什么功能", "你会什么", "你的能力",
            # 问候和开始
            "你好", "您好", "hi", "hello", "开始", "重新开始",
            # 明确的话题切换
            "换个话题", "说点别的", "我们聊点别的", "换个问题",
            # 系统相关
            "系统", "设置", "配置", "帮助", "说明",
            # 技术相关（容易引起话题切换）
            "机器学习", "人工智能", "深度学习", "神经网络", "算法", "编程", "代码"
        ]
        
        # 检查是否包含新话题指示词
        query_lower = user_query.lower()
        for indicator in new_topic_indicators:
            if indicator in query_lower:
                self.logger.info(f"检测到新话题指示词: {indicator}")
                return True
        
        # 检查对话轮次，如果超过3轮，可能是新话题
        if state.conversation_round > 3:
            # 分析查询与当前话题的相关性
            current_topic = self._extract_current_topic(state)
            if current_topic and not self._is_related_to_topic(user_query, current_topic):
                self.logger.info(f"检测到话题切换，当前话题: {current_topic}")
                return True
        
        return False
    
    def _extract_current_topic(self, state: AgentState) -> Optional[str]:
        """提取当前话题
        
        Args:
            state: 代理状态
            
        Returns:
            当前话题
        """
        # 从用户查询中提取关键词作为话题
        if state.user_query:
            # 简单的关键词提取
            keywords = self._extract_keywords(state.user_query)
            if keywords:
                return " ".join(keywords[:3])  # 取前3个关键词
        return None
    
    def _is_related_to_topic(self, user_query: str, current_topic: str) -> bool:
        """检查查询是否与当前话题相关
        
        Args:
            user_query: 用户查询
            current_topic: 当前话题
            
        Returns:
            是否相关
        """
        # 简单的相关性检查
        query_keywords = set(self._extract_keywords(user_query))
        topic_keywords = set(self._extract_keywords(current_topic))
        
        # 如果有共同关键词，认为是相关的
        common_keywords = query_keywords & topic_keywords
        return len(common_keywords) > 0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（可以后续改进为更复杂的NLP方法）
        import re
        
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词
        stopwords = {'的', '了', '是', '在', '有', '和', '与', '或', '但', '可以', '能够', '什么', '怎么', '为什么', '如何'}
        keywords = [word for word in words if word not in stopwords and len(word) > 1]
        
        return keywords[:5]  # 返回前5个关键词


# 全局多智能体系统实例
_global_multi_agent_system = None

def get_multi_agent_system(config: Optional[Dict[str, Any]] = None) -> MultiAgentSystem:
    """获取全局多智能体系统实例"""
    global _global_multi_agent_system
    
    if _global_multi_agent_system is None:
        _global_multi_agent_system = MultiAgentSystem(config)
    
    return _global_multi_agent_system

def initialize_multi_agent_system(config: Optional[Dict[str, Any]] = None) -> MultiAgentSystem:
    """初始化多智能体系统"""
    global _global_multi_agent_system
    _global_multi_agent_system = MultiAgentSystem(config)
    return _global_multi_agent_system