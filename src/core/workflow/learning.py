#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 LangGraph 的学习工作流引擎
重构原有 LearningWorkflow 为 LangGraph 实现
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END

from .state import (
    LearningWorkflowState, create_initial_state, state_to_agent_state, update_state_from_agent_state
)
from .nodes import LearningWorkflowNodes
from .routing import (
    route_after_query_analysis, route_after_planning,
    route_error_handler, route_conclusion, route_wait_for_user,
    route_after_reviewer, route_after_quiz_master
)
from src.infrastructure.utils.enums import QueryType, ConversationStage, UnderstandingLevel


class LangGraphLearningWorkflow:
    """基于 LangGraph 的学习工作流
    
    使用 LangGraph 框架重构原有的学习工作流，提供更好的可视化、调试和扩展性。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化节点
        self.feature_flags = {
            "enable_memory_manager": True,
            "enable_knowledge_manager": True,
            "enable_socratic_guide": True,
        }
        if "feature_flags" in self.config:
            self.feature_flags.update(self.config.get("feature_flags") or {})
        self.nodes = LearningWorkflowNodes(self.feature_flags)
        
        # 工作流程配置
        self.workflow_config = {
            "max_iterations": self.config.get("max_iterations", 5),
            "timeout_seconds": self.config.get("timeout_seconds", 300),
            "enable_learning": self.config.get("enable_learning", True),
            "enable_socratic": self.config.get("enable_socratic", True),
            "auto_continue": self.config.get("auto_continue", False),
            "feature_flags": self.feature_flags,
        }
        
        # 系统状态
        self.active_sessions = {}
        self.system_stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "average_session_duration": 0.0,
            "total_queries_processed": 0
        }
        
        # 构建 LangGraph 图
        self.graph = self._build_graph()
        
        self.logger.info("LangGraph learning workflow initialized")

    def _merge_workflow_config(self, runtime_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """合并默认配置和请求级配置，便于实验时快速切换"""
        merged = dict(self.workflow_config)
        if runtime_config:
            for key, value in runtime_config.items():
                merged[key] = value
        return merged
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 状态图"""
        try:
            # 创建状态图
            workflow = StateGraph(LearningWorkflowState)
            
            # 添加节点 - 优化后的架构：移除 Executor，工具节点独立
            # 工具类 agents (knowledge_manager, socratic_guide, memory_manager) 现在作为独立节点
            workflow.add_node("query_analyzer", self.nodes.query_analyzer_node)
            workflow.add_node("planner", self.nodes.planner_node)
            # workflow.add_node("executor", self.nodes.executor_node) # Removed
            workflow.add_node("draft_writer", self.nodes.draft_writer_node)
            workflow.add_node("reviewer", self.nodes.reviewer_node)
            workflow.add_node("curriculum_designer", self.nodes.curriculum_designer_node)
            workflow.add_node("quiz_master", self.nodes.quiz_master_node)
            workflow.add_node("tool_specialist", self.nodes.tool_specialist_node)
            workflow.add_node("knowledge_manager", self.nodes.knowledge_manager_node)
            workflow.add_node("socratic_guide", self.nodes.socratic_guide_node)
            workflow.add_node("memory_manager", self.nodes.memory_manager_node)
            workflow.add_node("evidence_validator", self.nodes.evidence_validator_node)
            workflow.add_node("conclusion", self.nodes.conclusion_node)
            workflow.add_node("error_handler", self.nodes.error_handler_node)
            
            # 添加条件边（路由） - 优化后的简化架构
            # query_analyzer → planner → [Tools] → draft_writer → reviewer → [conclusion/loop]
            workflow.add_conditional_edges(
                "query_analyzer",
                route_after_query_analysis,
                {
                    "planner": "planner",
                    "error_handler": "error_handler"
                }
            )
            
            # Planner Fan-out to Tools or DraftWriter
            workflow.add_conditional_edges(
                "planner",
                route_after_planning,
                {
                    "knowledge_manager": "knowledge_manager",
                    "tool_specialist": "tool_specialist",
                    "curriculum_designer": "curriculum_designer",
                    "socratic_guide": "socratic_guide",
                    "memory_manager": "memory_manager",
                    "draft_writer": "draft_writer",
                    "error_handler": "error_handler"
                }
            )
            
            # Tools -> EvidenceValidator -> DraftWriter (Fan-in)
            workflow.add_edge("knowledge_manager", "evidence_validator")
            workflow.add_edge("tool_specialist", "evidence_validator")
            workflow.add_edge("curriculum_designer", "draft_writer")
            workflow.add_edge("socratic_guide", "draft_writer")
            workflow.add_edge("memory_manager", "draft_writer")
            workflow.add_edge("evidence_validator", "draft_writer")
            
            # CurriculumDesigner -> DraftWriter (Already handled by add_edge above, but keeping routing conditional if needed)
            # workflow.add_conditional_edges(
            #     "curriculum_designer",
            #     route_after_curriculum_designer,
            #     {
            #         "draft_writer": "draft_writer"
            #     }
            # )
            
            # DraftWriter -> Reviewer
            workflow.add_edge("draft_writer", "reviewer")
            
            # Reviewer -> (QuizMaster | DraftWriter | Conclusion)
            workflow.add_conditional_edges(
                "reviewer",
                route_after_reviewer,
                {
                    "conclusion": "conclusion", # Fallback or simple pass
                    "quiz_master": "quiz_master", # Success path with quiz
                    "draft_writer": "draft_writer" # Reject path
                }
            )
            
            # QuizMaster -> Conclusion
            workflow.add_conditional_edges(
                "quiz_master",
                route_after_quiz_master,
                {
                    "conclusion": "conclusion"
                }
            )
            
            # 错误处理和结论节点直接结束
            workflow.add_edge("error_handler", END)
            workflow.add_edge("conclusion", END)
            # wait_for_user 也是结束点，等待外部再次触发
            # workflow.add_edge("wait_for_user", END)
            
            # 设置入口点
            workflow.set_entry_point("query_analyzer")
            
            # 编译图
            graph = workflow.compile()
            
            self.logger.info("LangGraph workflow compiled successfully")
            return graph
            
        except Exception as e:
            self.logger.error(f"Failed to build LangGraph workflow: {e}")
            raise
    
    async def process_query(self, user_query: str, session_id: Optional[str] = None, 
                          user_context: Optional[Dict[str, Any]] = None,
                          workflow_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户查询
        
        Args:
            user_query: 用户查询
            session_id: 会话ID（可选）
            user_context: 用户上下文（可选）
            
        Returns:
            处理结果
        """
        try:
            # 合并配置并应用特征开关
            effective_config = self._merge_workflow_config(workflow_config)
            runtime_feature_flags = effective_config.get("feature_flags", {})
            if runtime_feature_flags:
                self.feature_flags.update(runtime_feature_flags)
                self.nodes.set_feature_flags(self.feature_flags)
            
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
            
            # 创建初始状态
            initial_state = create_initial_state(
                user_query=user_query,
                session_id=session_id,
                user_context=user_context
            )
            initial_state["feature_flags"] = dict(self.feature_flags)
            initial_state["experiment_tags"] = effective_config.get("experiment_tags", [])
            initial_state["metadata"] = {
                **initial_state.get("metadata", {}),
                "experiment_config": {
                    "feature_flags": self.feature_flags,
                    "workflow_config": effective_config
                }
            }
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行 LangGraph 工作流（增加超时保护）
            timeout_seconds = effective_config.get("timeout_seconds", self.workflow_config.get("timeout_seconds", 300))
            result = await asyncio.wait_for(
                self._execute_graph_workflow(initial_state),
                timeout=timeout_seconds
            )
            
            # 更新会话信息
            self.active_sessions[session_id] = {
                "state": result.get("final_state", initial_state),
                "start_time": start_time,
                "current_step": result.get("current_step", "unknown")
            }
            
            # 更新统计信息
            self._update_system_stats(session_id, start_time, result.get("success", False))
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"工作流执行超时（>{effective_config.get('timeout_seconds', self.workflow_config.get('timeout_seconds', 300))}s）")
            return {
                "success": False,
                "error": "工作流超时，请缩短输入或稍后重试",
                "session_id": session_id
            }
        except Exception as e:
            self.logger.error(f"处理查询失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def continue_session(self, session_id: str, user_id: str, 
                             user_response: str) -> Dict[str, Any]:
        """继续现有会话（用于多轮对话）
        
        🔧 修复：从持久化存储加载历史状态
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_response: 用户的响应内容
            
        Returns:
            处理结果
        """
        try:
            # 🔧 修复：先尝试从内存获取，如果不存在则从持久化存储加载
            current_state = None
            
            if session_id in self.active_sessions:
                # 从内存获取
                session_info = self.active_sessions[session_id]
                current_state = session_info["state"]
                self.logger.info(f"从内存加载会话: {session_id}")
            else:
                # 🔧 从持久化存储加载
                current_state = await self._load_session_from_storage(session_id, user_id)
                
                if current_state:
                    self.logger.info(f"从存储加载会话: {session_id}")
                    # 恢复到 active_sessions
                    self.active_sessions[session_id] = {
                        "state": current_state,
                        "start_time": datetime.now(),
                        "current_step": "continue_session"
                    }
                else:
                    self.logger.warning(f"会话不存在于内存和存储中，创建新会话: {session_id}")
                    # 如果会话真的不存在，将用户响应作为新查询处理
                    return await self.process_query(
                        user_query=user_response,
                        session_id=session_id,
                        user_context={"user_id": user_id}
                    )
            
            # 获取会话信息
            session_info = self.active_sessions[session_id]
            
            # 🔧 修复：保持苏格拉底问题历史，不要重置
            # 将用户响应添加到用户响应历史中
            if "user_responses" not in current_state:
                current_state["user_responses"] = []
            current_state["user_responses"].append(user_response)
            
            # 🔧 修复：更新dialogue_history，将用户回答添加到最后一轮对话中
            if "dialogue_history" not in current_state:
                current_state["dialogue_history"] = []
            
            # 获取当前对话轮次
            current_round = len(current_state["dialogue_history"])
            
            if current_round > 0:
                # 更新最后一轮对话，添加用户回答
                last_dialogue = current_state["dialogue_history"][-1]
                if "response" not in last_dialogue:
                    last_dialogue["response"] = user_response
                    last_dialogue["response_timestamp"] = datetime.now().isoformat()
                    self.logger.info(f"已将用户回答添加到对话历史第{current_round}轮")
            
            # 更新用户响应
            current_state["user_response"] = user_response
            # 🔧 修复：不要将用户响应覆盖user_query，保持原始查询
            # current_state["user_query"] = user_response  # 注释掉这行，保持原始查询
            
            # 增加对话轮次
            current_state["conversation_round"] += 1
            
            # 更新用户上下文
            if "user_id" not in current_state["user_context"]:
                current_state["user_context"]["user_id"] = user_id

            # 确保特征开关在续写中保持一致
            current_state.setdefault("feature_flags", self.feature_flags)
            self.nodes.set_feature_flags(current_state.get("feature_flags", {}))
            
            # 记录开始时间
            start_time = datetime.now()
            
            self.logger.info(f"继续会话 {session_id}, 轮次: {current_state['conversation_round']}, 已提问次数: {len(current_state.get('socratic_questions', []))}")
            
            # 根据当前状态决定下一步
            # 注意：用户响应后，从头开始执行完整工作流
            # 这样可以重新分析用户的理解程度并制定新计划
            # 优化方向：未来可以考虑直接从 planner 开始以提高效率
            timeout_seconds = self.workflow_config.get("timeout_seconds", 300)
            result = await asyncio.wait_for(
                self._execute_graph_workflow(current_state),
                timeout=timeout_seconds
            )
            
            # 更新会话信息
            session_info["current_step"] = result.get("current_step", "unknown")
            session_info["last_activity"] = datetime.now()
            session_info["state"] = result.get("final_state", current_state)
            
            # 更新统计信息
            self._update_system_stats(session_id, start_time, result.get("success", False))
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"继续会话超时（>{self.workflow_config.get('timeout_seconds', 300)}s）")
            return {
                "success": False,
                "error": "会话处理超时，请稍后重试",
                "session_id": session_id
            }
        except Exception as e:
            self.logger.error(f"继续会话失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _execute_graph_workflow(self, initial_state: LearningWorkflowState, 
                                    start_node: Optional[str] = None) -> Dict[str, Any]:
        """执行 LangGraph 工作流"""
        try:
            # 执行图
            if start_node:
                # 从指定节点开始执行
                result = await self.graph.ainvoke(initial_state, config={"start_node": start_node})
            else:
                # 从入口点开始执行
                result = await self.graph.ainvoke(initial_state)
            
            # 构建响应
            response_parts = []
            final_response = ""
            socratic_question = None
            
            # 从消息历史中提取响应
            messages = result.get("messages", [])
            conclusion_message = None
            
            for message in messages:
                if message.get("role") == "assistant":
                    content = message.get("content", "")
                    if content.startswith("💭"):
                        socratic_question = content
                    elif "我们的对话时间已经到了" in content or "很好！通过我们的对话" in content:
                        # 这是 conclusion 消息，单独保存
                        conclusion_message = content
                    else:
                        response_parts.append(content)
            
            # 构建最终响应
            if response_parts:
                # 只取最后一条实际响应，避免重复
                final_response = response_parts[-1]
                
                # 如果有 conclusion，作为补充添加
                if conclusion_message and result.get("workflow_complete", False):
                    final_response = f"{final_response}\n\n{conclusion_message}"
            elif conclusion_message:
                final_response = conclusion_message
            
            # 判断是否完成
            workflow_complete = result.get("workflow_complete", False)
            waiting_for_user = result.get("waiting_for_user", False)
            performance = result.get("performance_data", {})

            # 将性能数据合并到各阶段结果，便于前端展示与实验记录
            analysis_result = result.get("interpretation", {}) or {}
            if performance.get("query_analyzer_ms") is not None:
                analysis_result["duration_ms"] = performance.get("query_analyzer_ms", 0)
            
            plan_result = result.get("plan", {}) or {}
            if performance.get("orchestrator_ms") is not None:
                plan_result["duration_ms"] = performance.get("orchestrator_ms", 0)
            elif performance.get("planner_ms") is not None: # 兼容旧key
                plan_result["duration_ms"] = performance.get("planner_ms", 0)
            
            execution_summary = result.get("execution_result", {}) or {}
            # 收集所有执行相关 Agent 的耗时作为总耗时参考
            exec_time = 0
            for agent_key in ["draft_writer_ms", "reviewer_ms", "tool_specialist_ms", "curriculum_designer_ms", "quiz_master_ms", "knowledge_manager_ms", "socratic_guide_ms"]:
                exec_time += performance.get(agent_key, 0)
            execution_summary["duration_ms"] = exec_time
            
            # Merge tool outputs and curriculum plan into execution summary for frontend accessibility
            if result.get("tool_outputs"):
                execution_summary["tool_outputs"] = result.get("tool_outputs")
            if result.get("curriculum_plan"):
                execution_summary["curriculum_plan"] = result.get("curriculum_plan")
            if result.get("draft_content"):
                execution_summary["draft_content"] = result.get("draft_content")
            if result.get("critique"):
                execution_summary["critique"] = result.get("critique")
            
            # 构建返回结果
            return {
                "success": True,
                "session_id": result.get("session_id"),
                "response": final_response,
                "conversation_complete": workflow_complete and not waiting_for_user,
                "waiting_for_user": waiting_for_user,
                "conversation_stage": result.get("conversation_stage"),
                "understanding_level": result.get("understanding_level"),
                "round": result.get("conversation_round", 0),
                "socratic_question": socratic_question,
                "final_state": result,
                "current_step": result.get("next_step", "unknown"),
                # 🔧 修复：添加苏格拉底问题相关字段
                "socratic_questions": result.get("socratic_questions", []),
                "socratic_guidance": result.get("socratic_guidance", {}),
                "messages": result.get("messages", []),
                # 添加API需要的字段
                "analysis": analysis_result,
                "plan": plan_result,
                "execution_summary": execution_summary,
                "next_suggestions": self._generate_next_suggestions(result),
                "performance_data": performance,
            }
            
        except Exception as e:
            self.logger.error(f"Graph workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": initial_state.get("session_id"),
                "response": "工作流执行过程中出现错误",
                "conversation_complete": True,
                "waiting_for_user": False
            }
    
    def _generate_next_suggestions(self, state: LearningWorkflowState) -> List[str]:
        """生成下一步学习建议"""
        suggestions = []
        
        # 根据查询类型生成建议
        query_type = state.get("query_type")
        if query_type == QueryType.CONCEPT_EXPLANATION.value:
            suggestions = [
                "你可以询问相关的应用示例",
                "你可以请求更深入的解释",
                "你可以询问相关的其他概念",
            ]
        elif query_type == QueryType.DIRECT_ANSWER.value:
            suggestions = [
                "你可以要求解释背后的原理",
                "你可以询问相关的例子",
                "你可以提出进一步的问题",
            ]
        elif query_type == QueryType.COMPARISON_ANALYSIS.value:
            suggestions = [
                "你可以深入比较具体方面",
                "你可以询问背景和原因",
                "你可以了解发展演变过程",
            ]
        else:
            suggestions = [
                "你可以继续深入探讨",
                "你可以换个角度提问",
                "你可以请求更多示例",
            ]
        
        return suggestions
    
    def _detect_new_topic(self, user_query: str, session_id: Optional[str] = None) -> bool:
        """检测是否是新话题"""
        # 如果没有会话，肯定是新话题
        if not session_id or session_id not in self.active_sessions:
            return True
        
        # 获取当前会话状态
        current_state = self.active_sessions[session_id]["state"]
        
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
        conversation_round = current_state.get("conversation_round", 0)
        if conversation_round > 3:
            # 分析查询与当前话题的相关性
            current_topic = self._extract_current_topic(current_state)
            if current_topic and not self._is_related_to_topic(user_query, current_topic):
                self.logger.info(f"检测到话题切换，当前话题: {current_topic}")
                return True
        
        return False
    
    def _extract_current_topic(self, state: LearningWorkflowState) -> Optional[str]:
        """提取当前话题"""
        # 从用户查询中提取关键词作为话题
        user_query = state.get("user_query", "")
        if user_query:
            # 简单的关键词提取
            keywords = self._extract_keywords(user_query)
            if keywords:
                return " ".join(keywords[:3])  # 取前3个关键词
        return None
    
    def _is_related_to_topic(self, user_query: str, current_topic: str) -> bool:
        """检查查询是否与当前话题相关"""
        # 简单的相关性检查
        query_keywords = set(self._extract_keywords(user_query))
        topic_keywords = set(self._extract_keywords(current_topic))
        
        # 如果有共同关键词，认为是相关的
        common_keywords = query_keywords & topic_keywords
        return len(common_keywords) > 0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
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
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
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
            "waiting_for_response": state.get("waiting_for_user", False),
            "conversation_round": state.get("conversation_round", 0),
            "understanding_level": state.get("understanding_level", "no_understanding"),
            "latest_question": state.get("socratic_question", "")
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = dict(self.system_stats)
        stats["active_sessions_count"] = len(self.active_sessions)
        stats["success_rate"] = (
            self.system_stats["successful_sessions"] / max(self.system_stats["total_sessions"], 1)
        )
        
        return stats
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流程配置"""
        return dict(self.workflow_config)
    
    def update_workflow_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流程配置"""
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
        """清理过期会话"""
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
        """关闭学习工作流并释放资源"""
        try:
            # 清理所有活动会话
            self.active_sessions.clear()
            
            self.logger.info("LangGraph learning workflow shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
    
    def get_graph_visualization(self) -> str:
        """获取图的可视化表示"""
        try:
            # 返回图的Mermaid表示 - 优化后的简化架构
            return """
graph TD
    A[query_analyzer] -->|分析意图| B[planner]
    B -->|制定计划| C[executor]
    C -->|执行计划| D{是否等待用户?}
    D -->|是| E[END - 等待用户输入]
    D -->|否| F[conclusion]
    F --> G[END]
    
    A -.错误.-> H[error_handler]
    B -.错误.-> H
    C -.错误.-> H
    H --> G
    
    style C fill:#e1f5ff
    note1[executor 内部调用顺序:]
    note2[1. before_response: knowledge_manager, memory_manager]
    note3[2. 执行 actions]
    note4[3. 生成响应]
    note5[4. after_response: socratic_guide, memory_manager]
"""
        except Exception as e:
            self.logger.error(f"Failed to generate graph visualization: {e}")
            return "Graph visualization not available"
    
    async def _load_session_from_storage(self, session_id: str, user_id: str) -> Optional[LearningWorkflowState]:
        """从持久化存储加载会话状态
        
        🔧 新增：支持从存储恢复会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            Optional[LearningWorkflowState]: 会话状态，不存在返回None
        """
        try:
            # 使用 memory_manager 的存储管理器
            from src.core.agents.memory_manager import MemoryManagerAgent
            from src.core.agents.memory_manager.storage import StorageConfig
            
            # 创建存储管理器
            storage_config = StorageConfig.create_default()
            storage = MemoryManagerAgent(storage_config).storage
            
            # 加载会话数据
            session_data = storage.load_session_memory(session_id)
            
            if not session_data:
                return None
            
            # 重构为 LearningWorkflowState
            state = create_initial_state(
                user_query=session_data.get("query", ""),
                session_id=session_id,
                user_context={"user_id": user_id}
            )
            
            # 恢复关键字段
            if "query_analysis" in session_data:
                state["interpretation"] = session_data["query_analysis"].get("interpretation", {})
                state["query_type"] = session_data["query_analysis"].get("query_type", "")
                state["keywords"] = session_data["query_analysis"].get("keywords", [])
            
            if "socratic_dialogue" in session_data:
                socratic = session_data["socratic_dialogue"]
                state["socratic_questions"] = socratic.get("questions", [])
                state["socratic_question"] = socratic.get("current_question", "")
                state["user_responses"] = socratic.get("user_responses", [])
            
            if "understanding_tracking" in session_data:
                tracking = session_data["understanding_tracking"]
                state["understanding_level"] = tracking.get("current_level", "no_understanding")
                state["conversation_stage"] = tracking.get("conversation_stage", "initial_query")
                state["conversation_round"] = tracking.get("conversation_round", 0)
            
            if "dialogue_history" in session_data:
                state["dialogue_history"] = session_data["dialogue_history"]
            
            if "execution_details" in session_data:
                state["plan"] = session_data["execution_details"].get("plan", {})
                state["execution_result"] = session_data["execution_details"].get("execution_result")
            
            if "knowledge_retrieval" in session_data:
                state["knowledge_sources"] = session_data["knowledge_retrieval"].get("sources", [])
            
            self.logger.info(
                f"成功从存储恢复会话 {session_id}: "
                f"轮次={state['conversation_round']}, "
                f"苏格拉底问题数={len(state.get('socratic_questions', []))}, "
                f"对话历史={len(state.get('dialogue_history', []))}"
            )
            
            return state
            
        except Exception as e:
            self.logger.error(f"从存储加载会话失败: {session_id}, 错误: {e}", exc_info=True)
            return None


# 全局学习工作流实例
_global_langgraph_workflow: Optional[LangGraphLearningWorkflow] = None


def get_langgraph_learning_workflow(config: Optional[Dict[str, Any]] = None) -> LangGraphLearningWorkflow:
    """获取全局 LangGraph 学习工作流实例"""
    global _global_langgraph_workflow

    if _global_langgraph_workflow is None:
        _global_langgraph_workflow = LangGraphLearningWorkflow(config)

    return _global_langgraph_workflow


def initialize_langgraph_learning_workflow(config: Optional[Dict[str, Any]] = None) -> LangGraphLearningWorkflow:
    """初始化全局 LangGraph 学习工作流实例"""
    global _global_langgraph_workflow
    _global_langgraph_workflow = LangGraphLearningWorkflow(config)
    return _global_langgraph_workflow
