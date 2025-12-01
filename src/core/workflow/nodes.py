#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph 节点定义
将现有 Agent 重构为 LangGraph 节点
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .state import LearningWorkflowState, state_to_agent_state, update_state_from_agent_state
from src.core.agents import (
    QueryAnalyzerAgent, KnowledgeManagerAgent, MemoryManagerAgent,
    SocraticGuideAgent, OrchestratorAgent
)
from src.core.agents.draft_writer import DraftWriterAgent
from src.core.agents.reviewer import ReviewerAgent
from src.core.agents.curriculum_designer import CurriculumDesignerAgent
from src.core.agents.quiz_master import QuizMasterAgent
from src.core.agents.tool_specialist import ToolSpecialistAgent
from src.infrastructure.utils.enums import QueryType, ConversationStage, UnderstandingLevel


class LearningWorkflowNodes:
    """学习工作流节点集合
    
    优化后的架构：
    - 主流程节点：query_analyzer, planner, executor, conclusion, error_handler
    - 工具 agents：knowledge_manager, socratic_guide, memory_manager（通过 executor 调用）
    """
    
    def __init__(self, feature_flags: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.feature_flags = {
            "enable_memory_manager": True,
            "enable_knowledge_manager": True,
            "enable_socratic_guide": True,
        }
        if feature_flags:
            self.feature_flags.update(feature_flags)
        
        # 初始化所有智能体
        self.agents = {
            # 主流程 agents
            "query_analyzer": QueryAnalyzerAgent(enable_llm=False),  # 临时禁用 LLM 避免超时
            "planner": OrchestratorAgent(),
            "draft_writer": DraftWriterAgent(),
            "reviewer": ReviewerAgent(),
            "curriculum_designer": CurriculumDesignerAgent(),
            "quiz_master": QuizMasterAgent(),
            "tool_specialist": ToolSpecialistAgent(),
            "knowledge_manager": KnowledgeManagerAgent(),
            "memory_manager": MemoryManagerAgent(),
            "socratic_guide": SocraticGuideAgent(),
        }
        
        # 将工具 agents 注册到 Executor，受特征开关控制
        # enabled_tools = {
        #     name: agent
        #     for name, agent in {
        #         "knowledge_manager": self.agents["knowledge_manager"],
        #         "socratic_guide": self.agents["socratic_guide"],
        #         "memory_manager": self.agents["memory_manager"],
        #     }.items()
        #     if self.feature_flags.get(f"enable_{name}", True)
        # }
        # self.agents["executor"].register_tool_agents(enabled_tools)
        
        self.logger.info(f"Learning workflow nodes initialized with feature flags: {self.feature_flags}")
    
    def set_feature_flags(self, feature_flags: Dict[str, Any]):
        """更新节点级 feature flag（用于消融实验和快速对比）"""
        self.feature_flags.update(feature_flags or {})
        # 同步到执行器和工具协调器
        # if "executor" in self.agents:
        #     self.agents["executor"].update_feature_flags(self.feature_flags)
        
        # 重新注册工具 agent，确保禁用项被剔除
        # enabled_tools = {
        #     name: agent
        #     for name, agent in {
        #         "knowledge_manager": self.agents.get("knowledge_manager"),
        #         "socratic_guide": self.agents.get("socratic_guide"),
        #         "memory_manager": self.agents.get("memory_manager"),
        #     }.items()
        #     if agent and self.feature_flags.get(f"enable_{name}", True)
        # }
        # self.agents["executor"].register_tool_agents(enabled_tools)
        self.logger.info(f"Feature flags applied to workflow nodes: {self.feature_flags}")
    
    async def query_analyzer_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """查询分析节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] QueryAnalyzer: 分析用户查询")
            
            # 转换为 AgentState
            agent_state = state_to_agent_state(state)
            
            # 执行查询分析
            agent = self.agents["query_analyzer"]
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            # 更新状态
            state = update_state_from_agent_state(state, agent_state)
            
            # 设置下一步
            state["next_step"] = "planner"
            
            # 添加消息
            if agent_state.interpretation:
                state["messages"].append({
                    "role": "system",
                    "content": f"查询分析完成: {agent_state.interpretation.get('intent', '未知意图')}"
                })
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["query_analyzer_ms"] = duration_ms
            return state
            
        except Exception as e:
            self.logger.error(f"Query analyzer node failed: {e}")
            state["error_info"] = {
                "type": "query_analyzer_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            state["next_step"] = "error_handler"
            return state
    
    async def planner_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """规划节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] Planner: 制定执行计划")
            
            agent_state = state_to_agent_state(state)
            
            # 1. 检查是否需要调用特定策略 Agent
            intent = ""
            if agent_state.interpretation:
                intent = agent_state.interpretation.get("intent", "")
            
            parallel_actions = []
            if "structure_learning" in intent:
                parallel_actions.append("curriculum_designer")
            if "calculate" in intent or "current_news" in intent:
                # 暂时 executor 也能处理 tool，但 ideally 应该分发
                pass
            
            # 2. 执行常规规划
            agent = self.agents["planner"]
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            # 更新状态
            state = update_state_from_agent_state(state, agent_state)
            
            # 设置下一步：根据 Planner 决定的 next_workers 路由
            # Planner 已经将 "executor" 拆解为具体的 workers (e.g., knowledge_manager, tool_specialist)
            plan = agent_state.plan or {}
            next_workers = plan.get("next_workers", [])
            
            if next_workers:
                # 如果有多个 worker，这里简单地取第一个，或者返回列表供 Graph 扇出
                # 假设 LearningWorkflowState 支持 next_step 为 list
                state["next_step"] = next_workers if len(next_workers) > 1 else next_workers[0]
            else:
                # 默认去 draft_writer
                state["next_step"] = "draft_writer"
            
            # 添加消息
            if agent_state.plan:
                state["messages"].append({
                    "role": "system",
                    "content": f"执行计划制定完成: {agent_state.plan.get('plan_type', '未知计划')}. 下一步: {state['next_step']}"
                })
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["planner_ms"] = duration_ms
            return state
            
        except Exception as e:
            self.logger.error(f"Planner node failed: {e}")
            state["error_info"] = {
                "type": "planner_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            state["next_step"] = "error_handler"
            return state

    async def curriculum_designer_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """课程设计节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] CurriculumDesigner: 生成课程结构")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["curriculum_designer"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            state = update_state_from_agent_state(state, agent_state)
            
            # 课程设计完成后，通常继续执行后续流程（如生成介绍内容）
            state["next_step"] = "draft_writer"
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["curriculum_designer_ms"] = duration_ms
            return state
        except Exception as e:
            self.logger.error(f"CurriculumDesigner node failed: {e}")
            state["next_step"] = "draft_writer" # 失败降级
            return state

    async def quiz_master_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """出题节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] QuizMaster: 生成测试题")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["quiz_master"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            state = update_state_from_agent_state(state, agent_state)
            
            # 出题完成后进入结论
            state["next_step"] = "conclusion"
            
            # 将题目添加到 tool_outputs (如果 DraftWriter 没有处理的话，这里确保加上)
            if "quiz_data" in state["tool_outputs"]:
                # 可以在这里做一些额外的格式化
                pass
                
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["quiz_master_ms"] = duration_ms
            return state
        except Exception as e:
            self.logger.error(f"QuizMaster node failed: {e}")
            state["next_step"] = "conclusion" # 失败降级
            return state

    async def tool_specialist_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """工具专家节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] ToolSpecialist: 执行工具调用")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["tool_specialist"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
                
            state = update_state_from_agent_state(state, agent_state)
            state["next_step"] = "draft_writer"
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["tool_specialist_ms"] = duration_ms
            return state
        except Exception as e:
            self.logger.error(f"ToolSpecialist node failed: {e}")
            state["next_step"] = "draft_writer"
            return state

    async def draft_writer_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """初稿生成节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] DraftWriter: 生成/修改草稿")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["draft_writer"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            state = update_state_from_agent_state(state, agent_state)
            state["next_step"] = "reviewer"
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["draft_writer_ms"] = duration_ms
            return state
            
        except Exception as e:
            self.logger.error(f"DraftWriter node failed: {e}")
            state["error_info"] = {"type": "draft_writer_error", "message": str(e)}
            state["next_step"] = "error_handler"
            return state

    async def reviewer_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """审核节点"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] Reviewer: 审核草稿")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["reviewer"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            state = update_state_from_agent_state(state, agent_state)
            
            # 根据审核结果决定下一步
            if state["is_satisfactory"]:
                # 审核通过，进入结论
                state["next_step"] = "conclusion"
                # 将草稿作为最终响应
                final_response = state["draft_content"]
                state.setdefault("execution_result", {})["final_response"] = final_response
                
                # 添加最终响应到消息历史
                state["messages"].append({
                    "role": "assistant",
                    "content": final_response
                })
            else:
                # 审核不通过，回退到 DraftWriter
                state["next_step"] = "draft_writer"
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["reviewer_ms"] = duration_ms
            return state
            
        except Exception as e:
            self.logger.error(f"Reviewer node failed: {e}")
            state["error_info"] = {"type": "reviewer_error", "message": str(e)}
            state["next_step"] = "error_handler"
            return state
    
    async def knowledge_manager_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """知识检索节点 (Worker Node)"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] KnowledgeManager: 执行知识检索")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["knowledge_manager"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            state = update_state_from_agent_state(state, agent_state)
            
            # Tools 运行完通常汇聚到 DraftWriter
            state["next_step"] = "draft_writer"
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["knowledge_manager_ms"] = duration_ms
            return state
        except Exception as e:
            self.logger.error(f"KnowledgeManager node failed: {e}")
            state["error_info"] = {"type": "knowledge_manager_error", "message": str(e)}
            state["next_step"] = "draft_writer" # 失败降级，继续生成
            return state

    async def socratic_guide_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """苏格拉底引导节点 (Worker Node)"""
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] SocraticGuide: 生成引导性问题")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["socratic_guide"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
            
            state = update_state_from_agent_state(state, agent_state)
            state["next_step"] = "draft_writer"
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["socratic_guide_ms"] = duration_ms
            return state
        except Exception as e:
            self.logger.error(f"SocraticGuide node failed: {e}")
            state["next_step"] = "draft_writer"
            return state

    async def memory_manager_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """记忆管理节点 (Worker Node - Usually Read/Write)"""
        # 注意：MemoryManager 在新架构中可能主要用于 DraftWriter 之前读取画像
        # 或者在 Conclusion 之前保存记忆。这里假设是通用调用。
        try:
            node_started_at = datetime.now()
            self.logger.info("[Node] MemoryManager: 处理记忆")
            
            agent_state = state_to_agent_state(state)
            agent = self.agents["memory_manager"]
            
            if agent.can_execute(agent_state):
                agent_state = await agent.run(agent_state)
                
            state = update_state_from_agent_state(state, agent_state)
            # 默认去 draft_writer，如果是 write 操作可能会不一样，但通常图结构控制流向
            state["next_step"] = "draft_writer" 
            
            duration_ms = (datetime.now() - node_started_at).total_seconds() * 1000
            state.setdefault("performance_data", {})["memory_manager_ms"] = duration_ms
            return state
        except Exception as e:
            self.logger.error(f"MemoryManager node failed: {e}")
            state["next_step"] = "draft_writer"
            return state
    
    async def conclusion_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """结论节点"""
        try:
            self.logger.info("[Node] Conclusion: 生成对话结论")
            
            # 检查是否跳过正式结论（简单查询）
            if state.get("skip_formal_conclusion", False):
                self.logger.info("[Node] Conclusion: 简单查询，跳过正式结论")
                state["workflow_complete"] = True
                state["waiting_for_user"] = False
                state["next_step"] = None
                return state
            
            # 构建结论消息
            conclusion_parts = []
            
            # 检查理解水平
            # 修复：直接使用 UnderstandingLevel 类
            try:
                # 尝试将字符串转换为枚举
                current_level_val = state.get("understanding_level", "no_understanding")
                if isinstance(current_level_val, str):
                    # 处理可能的前缀或不匹配情况
                    current_level_val = current_level_val.lower()
                    
                # 简单逻辑：如果有良好的理解
                if current_level_val in ["good_understanding", "deep_understanding"]:
                     conclusion_parts.append("很好！通过我们的对话，您已经对这个概念有了很好的理解。")
                else:
                     conclusion_parts.append("我们的对话时间已经到了。让我们总结一下讨论的要点。")
            except Exception as e:
                self.logger.warning(f"Error checking understanding level: {e}")
                conclusion_parts.append("让我们总结一下讨论的要点。")
            
            # 添加学习总结
            if state.get("learning_feedback"):
                summary = state["learning_feedback"].get("summary", "")
                if summary:
                    conclusion_parts.append(f"\n📚 学习总结：\n{summary}")
            
            # 添加建议
            if state.get("learning_feedback") and state["learning_feedback"].get("recommendations"):
                recommendations = state["learning_feedback"]["recommendations"]
                if recommendations:
                    conclusion_parts.append(f"\n💡 进一步学习建议：")
                    for rec in recommendations[:3]:  # 最多3个建议
                        conclusion_parts.append(f"• {rec}")
            
            conclusion_text = "\n".join(conclusion_parts)
            
            # 添加结论消息 (如果前面没有生成过类似的)
            if conclusion_text:
                state["messages"].append({
                    "role": "assistant",
                    "content": conclusion_text
                })
            
            # 设置完成状态
            state["workflow_complete"] = True
            state["waiting_for_user"] = False
            state["next_step"] = None
            
            return state
            
        except Exception as e:
            self.logger.error(f"Conclusion node failed: {e}")
            state["error_info"] = {
                "type": "conclusion_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            state["next_step"] = "error_handler"
            return state
    
    async def error_handler_node(self, state: LearningWorkflowState) -> LearningWorkflowState:
        """错误处理节点"""
        try:
            self.logger.info("[Node] ErrorHandler: 处理错误")
            
            error_info = state.get("error_info")
            if error_info:
                error_message = error_info.get("message", "未知错误")
            else:
                error_message = "未知错误"
            
            # 添加错误消息
            state["messages"].append({
                "role": "assistant",
                "content": f"抱歉，处理过程中出现了问题：{error_message}。让我们重新开始吧。"
            })
            
            # 设置完成状态
            state["workflow_complete"] = True
            state["waiting_for_user"] = False
            state["next_step"] = None
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error handler node failed: {e}")
            # 最后的错误处理
            state["messages"].append({
                "role": "assistant",
                "content": "系统出现严重错误，请重新开始对话。"
            })
            state["workflow_complete"] = True
            state["waiting_for_user"] = False
            state["next_step"] = None
            return state
    
