#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator Agent (原 Planner)
负责分析用户意图，动态调度下游 Agent (KnowledgeManager, ToolSpecialist, CurriculumDesigner 等)
"""

import logging
from typing import Dict, Any, List, Optional

from src.infrastructure.utils import BaseAgent, AgentState, QueryType, PlanType

class OrchestratorAgent(BaseAgent):
    """Orchestrator Agent (原 Planner)
    
    核心职责：
    1. 接收 QueryAnalyzer 的分析结果。
    2. 分析当前上下文和资源需求。
    3. 生成调度指令 (next_workers)，决定下一步激活哪些 Worker Agent。
    """
    
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            description="任务编排与动态调度"
        )
        # 保留历史记录以便调试
        self.plan_history = []
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行编排逻辑"""
        try:
            # 1. 分析当前状态和上下文
            analysis = self._analyze_situation(state)
            
            # 2. 确定计划类型 (保留作为元数据，辅助决策)
            plan_type = self._determine_plan_type(state, analysis)
            
            # 3. 核心：确定需要调用的 Worker Agents
            next_workers = self._determine_next_workers(state, plan_type, analysis)
            
            # 4. 生成 Plan 对象（核心是 next_workers，用于 LangGraph 路由）
            plan = {
                "type": plan_type,
                "next_workers": next_workers,
                "reasoning": f"Based on intent '{state.interpretation.get('intent', 'unknown')}' and analysis.",
                "analysis": analysis,
                "timestamp": state.timestamp
            }
            
            # 5. 更新状态
            state.plan = plan
            state.plan_type = plan_type
            
            # 记录历史
            self.plan_history.append(plan)
            
            self.logger.info(f"Orchestrator decision: {plan_type} -> Next Workers: {next_workers}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}", exc_info=True)
            state.set_error("orchestration_error", str(e))
            # 出错时的兜底策略：尝试直接去 DraftWriter
            state.plan = {"next_workers": ["draft_writer"], "error": str(e)}
            return state

    def _determine_next_workers(self, state: AgentState, plan_type: PlanType, analysis: Dict[str, Any]) -> List[str]:
        """决定下一步激活哪些 Agent"""
        next_workers = []
        intent = state.interpretation.get("intent", "") if state.interpretation else ""
        query = state.user_query.lower()
        
        # 1. 优先检查明确的意图
        
        # 课程设计：用户想要系统学习
        if "structure_learning" in intent or plan_type == PlanType.CONCEPT_BUILDING:
            if "curriculum_designer" not in next_workers:
                next_workers.append("curriculum_designer")
        
        # 工具调用：计算、搜索、实时信息
        if "calculate" in intent or "current_news" in intent or "search" in intent:
             if "tool_specialist" not in next_workers:
                next_workers.append("tool_specialist")
        
        # 简单的关键词匹配作为补充
        if any(k in query for k in ["计算", "算一下", "天气", "新闻", "搜索"]):
             if "tool_specialist" not in next_workers:
                next_workers.append("tool_specialist")

        # 2. 知识检索判断 (默认大多数情况都需要，除非是纯闲聊)
        # 如果已经有足够的知识（比如多轮对话中），可能不需要
        if self._need_knowledge_retrieval(state, analysis):
            if "knowledge_manager" not in next_workers:
                next_workers.append("knowledge_manager")
        
        # 3. 苏格拉底引导
        # 通常在 DraftWriter 之后由 Reviewer 决定是否进入 Quiz/Conclusion，
        # 但如果是 GUIDED_LEARNING 模式，可以在 DraftWriter 之前准备好引导策略
        if self._need_socratic_guidance(state, plan_type, analysis):
             if "socratic_guide" not in next_workers:
                next_workers.append("socratic_guide")
                
        # 4. 记忆管理 (读取用户画像)
        # 几乎总是需要，为了个性化
        if "memory_manager" not in next_workers:
            next_workers.append("memory_manager")

        # 5. 如果没有任何工具被选中，直接去 DraftWriter
        if not next_workers:
            self.logger.info("No specific tools needed, proceeding to DraftWriter.")
            next_workers.append("draft_writer")
            
        return next_workers

    def _analyze_situation(self, state: AgentState) -> Dict[str, Any]:
        """分析当前情况 (简化版)"""
        return {
            "query_complexity": self._assess_query_complexity(state.user_query),
            "knowledge_availability": self._assess_knowledge_availability(state),
            "user_engagement": self._assess_user_engagement(state),
        }

    def _assess_query_complexity(self, query: str) -> float:
        """评估查询复杂度"""
        if not query: return 0.0
        indicators = ["为什么", "怎么", "比较", "分析", "原理"]
        score = 0.1
        if len(query) > 20: score += 0.3
        if any(i in query for i in indicators): score += 0.4
        return min(1.0, score)

    def _assess_knowledge_availability(self, state: AgentState) -> float:
        """评估知识可用性"""
        if not state.retrieved_knowledge: return 0.0
        results = state.retrieved_knowledge.get("results", [])
        return 1.0 if results else 0.0

    def _assess_user_engagement(self, state: AgentState) -> float:
        """评估用户参与度"""
        if not state.user_responses: return 0.5
        return 0.8 # 假定有回应就是高参与

    def _determine_plan_type(self, state: AgentState, analysis: Dict[str, Any]) -> PlanType:
        """确定计划类型"""
        # 优先使用 QueryAnalyzer 的结果
        if state.query_type:
            # 映射 QueryType 到 PlanType
            if state.query_type == QueryType.DIRECT_ANSWER:
                return PlanType.DIRECT_ANSWER
            elif state.query_type == QueryType.CONCEPT_EXPLANATION:
                return PlanType.CONCEPT_BUILDING
            elif state.query_type == QueryType.SOCRATIC_DIALOGUE:
                return PlanType.SOCRATIC_DIALOGUE
        
        # 兜底逻辑
        if analysis["query_complexity"] > 0.6:
            return PlanType.GUIDED_LEARNING
        return PlanType.DIRECT_ANSWER

    def _need_knowledge_retrieval(self, state: AgentState, analysis: Dict[str, Any]) -> bool:
        """判断是否需要知识检索"""
        # 1. 优先检查 QueryAnalyzer 的决策
        if hasattr(state, 'retrieval_decision') and state.retrieval_decision:
            if state.retrieval_decision.get('need_retrieval', False):
                return True
        
        # 2. 如果已经有检索结果，跳过
        if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
            return False
            
        # 3. 简单类型不需要
        if state.query_type in ["smalltalk", "greeting"]:
            return False
            
        return True

    def _need_socratic_guidance(self, state: AgentState, plan_type: PlanType, analysis: Dict[str, Any]) -> bool:
        """判断是否需要苏格拉底引导"""
        # 1. 正在进行中
        if state.socratic_questions:
            return True
            
        # 2. 特定计划类型
        if plan_type in [PlanType.GUIDED_LEARNING, PlanType.SOCRATIC_DIALOGUE]:
            return True
            
        # 3. 复杂度高
        if analysis["query_complexity"] > 0.7:
            return True
            
        return False
