#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正的LangGraph工作流实现
调用agents目录下的智能体，实现完整的学习交互流程
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List, Literal, Annotated
from datetime import datetime
from dataclasses import dataclass, field
from operator import add

try:
    from langgraph.graph import StateGraph, END, START
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import ToolNode
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_core.tools import BaseTool, tool
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LangGraph导入失败: {e}")
    LANGGRAPH_AVAILABLE = False

from utils import AgentState, QueryType, ConversationStage, UnderstandingLevel
from agents.query_interpreter_integrated import QueryInterpreterAgent
from agents.decision_agent import DecisionAgent
from agents.knowledge_retriever import KnowledgeRetrieverAgent
from agents.user_profile_integrated import UserProfileAgent
from agents.socratic_guide import SocraticGuideAgent
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.learner import LearnerAgent


@dataclass
class LangGraphWorkflowState:
    """LangGraph工作流状态"""
    
    # 消息历史（LangGraph标准）
    messages: Annotated[List[BaseMessage], add] = field(default_factory=list)
    
    # 会话信息
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    
    # 查询信息
    user_query: str = ""
    query_type: Optional[QueryType] = None
    query_interpretation: Dict[str, Any] = field(default_factory=dict)
    
    # 决策信息
    retrieval_decision: Dict[str, Any] = field(default_factory=dict)
    teaching_strategy: str = "adaptive"
    
    # 知识信息
    retrieved_knowledge: Dict[str, Any] = field(default_factory=dict)
    knowledge_sources: List[str] = field(default_factory=list)
    
    # 用户信息
    user_profile: Dict[str, Any] = field(default_factory=dict)
    understanding_level: UnderstandingLevel = UnderstandingLevel.NO_UNDERSTANDING
    
    # 对话状态
    conversation_stage: ConversationStage = ConversationStage.INITIAL_QUERY
    conversation_round: int = 1
    max_rounds: int = 10
    
    # 苏格拉底式对话
    socratic_questions: List[str] = field(default_factory=list)
    user_responses: List[str] = field(default_factory=list)
    current_socratic_question: Optional[str] = None
    
    # 执行结果
    plan: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    learning_feedback: Dict[str, Any] = field(default_factory=dict)
    
    # 系统状态
    error_info: Optional[Dict[str, Any]] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentNodeWrapper:
    """智能体节点包装器 - 将现有智能体包装为LangGraph节点"""
    
    def __init__(self, agent, node_name: str):
        self.agent = agent
        self.node_name = node_name
        self.logger = logging.getLogger(f"AgentNode.{node_name}")
    
    async def invoke(self, state: LangGraphWorkflowState) -> LangGraphWorkflowState:
        """调用智能体并更新状态"""
        try:
            self.logger.info(f"执行节点: {self.node_name}")
            start_time = datetime.now()
            
            # 将LangGraph状态转换为AgentState
            agent_state = self._convert_to_agent_state(state)
            
            # 检查智能体是否可以执行
            if not self.agent.can_execute(agent_state):
                self.logger.warning(f"智能体 {self.node_name} 无法执行，跳过")
                return state
            
            # 执行智能体
            updated_agent_state = await self.agent.execute(agent_state)
            
            # 将AgentState转换回LangGraph状态
            updated_state = self._convert_from_agent_state(state, updated_agent_state)
            
            # 记录性能指标
            execution_time = (datetime.now() - start_time).total_seconds()
            updated_state.performance_metrics[f"{self.node_name}_execution_time"] = execution_time
            
            self.logger.info(f"节点 {self.node_name} 执行完成，耗时: {execution_time:.2f}秒")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"节点 {self.node_name} 执行失败: {e}")
            # 设置错误信息，但不中断工作流
            state.error_info = {
                "node": self.node_name, 
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            return state
    
    def _convert_to_agent_state(self, state: LangGraphWorkflowState) -> AgentState:
        """将LangGraph状态转换为AgentState"""
        # 创建AgentState实例，不传递retrieval_decision参数
        agent_state = AgentState(
            session_id=state.session_id,
            user_query=state.user_query,
            user_context=state.user_profile,
            conversation_stage=state.conversation_stage,
            conversation_round=state.conversation_round,
            max_conversation_rounds=state.max_rounds,
            understanding_level=state.understanding_level,
            query_type=state.query_type,
            interpretation=state.query_interpretation,
            retrieved_knowledge=state.retrieved_knowledge,
            knowledge_sources=state.knowledge_sources,
            socratic_questions=state.socratic_questions,
            user_responses=state.user_responses,
            plan=state.plan,
            execution_result=state.execution_result,
            learning_feedback=state.learning_feedback,
            metadata=state.metadata
        )
        
        # 将retrieval_decision存储在metadata中，因为AgentState没有这个字段
        if state.retrieval_decision:
            agent_state.metadata["retrieval_decision"] = state.retrieval_decision
        
        return agent_state
    
    def _convert_from_agent_state(self, original_state: LangGraphWorkflowState, agent_state: AgentState) -> LangGraphWorkflowState:
        """将AgentState转换回LangGraph状态"""
        # 更新状态
        original_state.query_type = agent_state.query_type
        original_state.query_interpretation = agent_state.interpretation or {}
        original_state.retrieved_knowledge = agent_state.retrieved_knowledge or {}
        original_state.knowledge_sources = agent_state.knowledge_sources or []
        original_state.user_profile.update(agent_state.user_context or {})
        original_state.understanding_level = agent_state.understanding_level
        original_state.conversation_stage = agent_state.conversation_stage
        original_state.conversation_round = agent_state.conversation_round
        original_state.socratic_questions = agent_state.socratic_questions or []
        original_state.user_responses = agent_state.user_responses or []
        original_state.plan = agent_state.plan or {}
        original_state.execution_result = agent_state.execution_result or {}
        original_state.learning_feedback = agent_state.learning_feedback or {}
        original_state.metadata.update(agent_state.metadata or {})
        
        # 从metadata中恢复retrieval_decision
        if "retrieval_decision" in agent_state.metadata:
            original_state.retrieval_decision = agent_state.metadata["retrieval_decision"]
        
        # 更新错误信息
        if agent_state.has_error():
            original_state.error_info = {"agent_errors": agent_state.get_errors()}
        
        return original_state


class LangGraphWorkflowRouter:
    """LangGraph工作流路由器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def route_after_decision(self, state: LangGraphWorkflowState) -> str:
        """决策后的路由"""
        decision = state.retrieval_decision
        
        if decision.get("need_retrieval", False):
            return "knowledge_retrieval"
        else:
            return "planning"
    
    def route_after_knowledge_retrieval(self, state: LangGraphWorkflowState) -> str:
        """知识检索后的路由"""
        return "planning"
    
    def route_after_planning(self, state: LangGraphWorkflowState) -> str:
        """规划后的路由"""
        return "execution"
    
    def route_after_execution(self, state: LangGraphWorkflowState) -> str:
        """执行后的路由"""
        # 根据查询类型决定是否需要苏格拉底式引导
        if state.query_type == QueryType.DIRECT_ANSWER:
            return "learning_analysis"
        else:
            return "socratic_guidance"
    
    def route_after_socratic_guidance(self, state: LangGraphWorkflowState) -> str:
        """苏格拉底引导后的路由"""
        # 检查是否应该继续对话
        if self._should_continue_conversation(state):
            return "learning_analysis"
        else:
            return "learning_analysis"
    
    def route_after_learning_analysis(self, state: LangGraphWorkflowState) -> str:
        """学习分析后的路由"""
        return END
    
    def _should_continue_conversation(self, state: LangGraphWorkflowState) -> bool:
        """判断是否应该继续对话"""
        # 检查对话轮次
        if state.conversation_round >= state.max_rounds:
            return False
        
        # 检查理解水平
        if state.understanding_level.level_value >= 4:  # GOOD_UNDERSTANDING或更高
            return False
        
        # 检查苏格拉底问题数量
        if len(state.socratic_questions) >= 5:
            return False
        
        # 即使有错误也允许继续对话，但会记录错误
        # 这样可以提供更好的用户体验和错误恢复
        
        return True


class LangGraphEduWorkflow:
    """真正的LangGraph教育智能体工作流"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化智能体
        self._initialize_agents()
        
        # 初始化路由器
        self.router = LangGraphWorkflowRouter()
        
        # 构建工作流图
        self.graph = self._build_workflow_graph()
        
        # 性能统计
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "error_count": 0,
            "average_execution_time": 0.0
        }
    
    def _initialize_agents(self):
        """初始化所有智能体"""
        try:
            # 创建智能体实例
            self.query_interpreter = QueryInterpreterAgent()
            self.decision_agent = DecisionAgent()
            self.knowledge_retriever = KnowledgeRetrieverAgent()
            self.user_profile = UserProfileAgent()
            self.socratic_guide = SocraticGuideAgent(enable_enhanced_mode=True)
            self.planner = PlannerAgent()
            self.executor = ExecutorAgent()
            self.learner = LearnerAgent(enable_enhanced_mode=True)
            
            # 创建节点包装器
            self.nodes = {
                "query_interpreter": AgentNodeWrapper(self.query_interpreter, "query_interpreter"),
                "decision_agent": AgentNodeWrapper(self.decision_agent, "decision_agent"),
                "user_profile": AgentNodeWrapper(self.user_profile, "user_profile"),
                "knowledge_retrieval": AgentNodeWrapper(self.knowledge_retriever, "knowledge_retrieval"),
                "planning": AgentNodeWrapper(self.planner, "planning"),
                "execution": AgentNodeWrapper(self.executor, "execution"),
                "socratic_guidance": AgentNodeWrapper(self.socratic_guide, "socratic_guidance"),
                "learning_analysis": AgentNodeWrapper(self.learner, "learning_analysis")
            }
            
            self.logger.info("所有智能体初始化成功")
            
        except Exception as e:
            self.logger.error(f"智能体初始化失败: {e}")
            raise
    
    def _build_workflow_graph(self):
        """构建LangGraph工作流图"""
        if not LANGGRAPH_AVAILABLE:
            return self._build_fallback_workflow()
        
        # 创建状态图
        workflow = StateGraph(LangGraphWorkflowState)
        
        # 添加节点
        for node_name, node_wrapper in self.nodes.items():
            workflow.add_node(node_name, node_wrapper.invoke)
        
        # 设置入口点
        workflow.set_entry_point("query_interpreter")
        
        # 添加边和条件路由
        workflow.add_edge("query_interpreter", "decision_agent")
        workflow.add_edge("decision_agent", "user_profile")
        
        # 决策后的条件路由
        workflow.add_conditional_edges(
            "user_profile",
            self.router.route_after_decision,
            {
                "knowledge_retrieval": "knowledge_retrieval",
                "planning": "planning"
            }
        )
        
        # 知识检索后的路由
        workflow.add_edge("knowledge_retrieval", "planning")
        
        # 规划后的路由
        workflow.add_edge("planning", "execution")
        
        # 执行后的条件路由
        workflow.add_conditional_edges(
            "execution",
            self.router.route_after_execution,
            {
                "socratic_guidance": "socratic_guidance",
                "learning_analysis": "learning_analysis"
            }
        )
        
        # 苏格拉底引导后的路由
        workflow.add_edge("socratic_guidance", "learning_analysis")
        
        # 学习分析后结束
        workflow.add_edge("learning_analysis", END)
        
        # 编译图
        return workflow.compile()
    
    def _build_fallback_workflow(self):
        """构建回退工作流（当LangGraph不可用时）"""
        class FallbackWorkflow:
            def __init__(self, nodes, router):
                self.nodes = nodes
                self.router = router
                self.logger = logging.getLogger("FallbackWorkflow")
            
            async def ainvoke(self, state: LangGraphWorkflowState, config: Optional[Dict] = None):
                """执行回退工作流"""
                try:
                    # 按顺序执行节点
                    state = await self.nodes["query_interpreter"].invoke(state)
                    if state.error_info:
                        return state
                    
                    state = await self.nodes["decision_agent"].invoke(state)
                    if state.error_info:
                        return state
                    
                    state = await self.nodes["user_profile"].invoke(state)
                    if state.error_info:
                        return state
                    
                    # 根据决策结果选择路径
                    route = self.router.route_after_decision(state)
                    if route == "knowledge_retrieval":
                        state = await self.nodes["knowledge_retrieval"].invoke(state)
                        if state.error_info:
                            return state
                    
                    state = await self.nodes["planning"].invoke(state)
                    if state.error_info:
                        return state
                    
                    state = await self.nodes["execution"].invoke(state)
                    if state.error_info:
                        return state
                    
                    # 根据查询类型决定是否需要苏格拉底引导
                    route = self.router.route_after_execution(state)
                    if route == "socratic_guidance":
                        state = await self.nodes["socratic_guidance"].invoke(state)
                        if state.error_info:
                            return state
                    
                    state = await self.nodes["learning_analysis"].invoke(state)
                    
                    return state
                    
                except Exception as e:
                    self.logger.error(f"回退工作流执行失败: {e}")
                    state.error_info = {"workflow": "fallback", "error": str(e)}
                    return state
        
        return FallbackWorkflow(self.nodes, self.router)
    
    async def execute(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        start_time = datetime.now()
        
        try:
            # 更新统计
            self.stats["total_executions"] += 1
            
            # 创建初始状态
            initial_state = LangGraphWorkflowState(
                session_id=session_id or str(uuid.uuid4()),
                user_id=user_id,
                user_query=user_query,
                user_profile=user_context or {},
                messages=[HumanMessage(content=user_query)] if LANGGRAPH_AVAILABLE else []
            )
            
            self.logger.info(f"开始执行LangGraph工作流，会话ID: {initial_state.session_id}")
            
            # 执行工作流
            final_state = await self.graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": initial_state.session_id}}
            )
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计
            self.stats["successful_executions"] += 1
            self._update_average_execution_time(execution_time)
            
            self.logger.info(f"LangGraph工作流执行完成，耗时: {execution_time:.2f}秒")
            
            return self._format_response(final_state, execution_time)
            
        except Exception as e:
            # 更新错误统计
            self.stats["error_count"] += 1
            
            self.logger.error(f"LangGraph工作流执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_info": {"workflow": "execution", "error": str(e)},
                "session_id": session_id,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "conversation_stage": "error",
                "understanding_level": "no_understanding",
                "conversation_round": 0
            }
    
    def _update_average_execution_time(self, execution_time: float):
        """更新平均执行时间"""
        current_avg = self.stats["average_execution_time"]
        total = self.stats["total_executions"]
        
        new_avg = (current_avg * (total - 1) + execution_time) / total
        self.stats["average_execution_time"] = new_avg
    
    def _format_response(self, state, execution_time: float) -> Dict[str, Any]:
        """格式化响应"""
        # 处理LangGraph可能返回字典的情况
        if isinstance(state, dict):
            # 如果state是字典，直接使用字典的值
            response = {
                "success": not bool(state.get("error_info")),
                "session_id": state.get("session_id", "unknown"),
                "user_id": state.get("user_id"),
                "execution_time": execution_time,
                "conversation_stage": state.get("conversation_stage", "error"),
                "understanding_level": state.get("understanding_level", "no_understanding"),
                "conversation_round": state.get("conversation_round", 0),
                "query_type": state.get("query_type")
            }
            
            # 添加其他字段
            if state.get("execution_result"):
                response["execution_result"] = state["execution_result"]
            if state.get("learning_feedback"):
                response["learning_feedback"] = state["learning_feedback"]
            if state.get("socratic_questions"):
                response["socratic_questions"] = state["socratic_questions"]
                response["current_socratic_question"] = state.get("current_socratic_question")
            if state.get("user_profile"):
                response["user_profile"] = state["user_profile"]
            if state.get("knowledge_sources"):
                response["knowledge_sources"] = state["knowledge_sources"]
            if state.get("performance_metrics"):
                response["performance_metrics"] = state["performance_metrics"]
            if state.get("error_info"):
                response["error_info"] = state["error_info"]
            
            return response
        
        # 处理LangGraphWorkflowState对象的情况
        response = {
            "success": not bool(state.error_info),
            "session_id": state.session_id,
            "user_id": state.user_id,
            "execution_time": execution_time,
            "conversation_stage": state.conversation_stage.value,
            "understanding_level": state.understanding_level.value,
            "conversation_round": state.conversation_round,
            "query_type": state.query_type.value if state.query_type else None
        }
        
        # 添加消息历史
        if LANGGRAPH_AVAILABLE:
            response["messages"] = [
                {
                    "type": msg.__class__.__name__,
                    "content": msg.content
                }
                for msg in state.messages
            ]
        
        # 添加执行结果
        if state.execution_result:
            response["execution_result"] = state.execution_result
        
        # 添加学习反馈
        if state.learning_feedback:
            response["learning_feedback"] = state.learning_feedback
        
        # 添加苏格拉底问题
        if state.socratic_questions:
            response["socratic_questions"] = state.socratic_questions
            response["current_socratic_question"] = state.current_socratic_question
        
        # 添加用户画像
        if state.user_profile:
            response["user_profile"] = state.user_profile
        
        # 添加知识来源
        if state.knowledge_sources:
            response["knowledge_sources"] = state.knowledge_sources
        
        # 添加性能指标
        response["performance_metrics"] = state.performance_metrics
        
        # 添加错误信息（如果有）
        if state.error_info:
            response["error_info"] = state.error_info
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        if stats["total_executions"] > 0:
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
        else:
            stats["success_rate"] = 0.0
        
        return stats


# 工厂函数
def create_langgraph_workflow(config: Optional[Dict[str, Any]] = None) -> LangGraphEduWorkflow:
    """创建LangGraph工作流"""
    return LangGraphEduWorkflow(config)