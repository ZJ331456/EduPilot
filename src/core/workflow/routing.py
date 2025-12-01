#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph 路由逻辑
定义条件分支和路由决策
"""

import logging
from typing import Dict, Any, List, Optional

from .state import LearningWorkflowState
from src.infrastructure.utils.enums import QueryType, ConversationStage, UnderstandingLevel


class LearningWorkflowRouter:
    """学习工作流路由器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def route_after_query_analysis(self, state: LearningWorkflowState) -> str:
        """查询分析后的路由决策
        
        优化后：直接进入 planner，由 planner 决定是否需要调用 knowledge_manager
        """
        try:
            # 检查是否有错误
            if state.get("error_info"):
                return "error_handler"
            
            # 直接进入规划阶段 - planner 会根据 retrieval_decision 决定是否调用 knowledge_manager
            return "planner"
            
        except Exception as e:
            self.logger.error(f"Routing after query analysis failed: {e}")
            return "error_handler"
    
    def route_after_planning(self, state: LearningWorkflowState) -> str:
        """规划后的路由决策
        
        优化后：根据 Planner 的输出决定下一步（工具或 DraftWriter）
        """
        try:
            # 检查是否有错误
            if state.get("error_info"):
                return "error_handler"
            
            # 检查是否有显式的 next_step 指示
            next_step = state.get("next_step")
            if next_step and isinstance(next_step, str) and next_step not in ["planner", "error_handler"]:
                return next_step
            elif next_step and isinstance(next_step, list):
                 # 简单取第一个，或者根据优先级
                 return next_step[0]
            
            # 默认去 draft_writer
            return "draft_writer"
            
        except Exception as e:
            self.logger.error(f"Routing after planning failed: {e}")
            return "error_handler"

    def route_after_tool_execution(self, state: LearningWorkflowState) -> str:
        """工具执行后的路由决策 (KnowledgeManager, ToolSpecialist, etc.)"""
        try:
             # 工具执行完通常去 DraftWriter 汇总
             return "draft_writer"
        except Exception as e:
            self.logger.error(f"Routing after tool execution failed: {e}")
            return "error_handler"

    def route_after_reviewer(self, state: LearningWorkflowState) -> str:
        """审核后的路由决策"""
        # 如果审核通过
        if state.get("is_satisfactory", False):
            # 检查是否需要生成测试题 (基于 intent 或其他标志)
            # 这里简单逻辑：如果有教学内容，尝试生成题目
            if state.get("draft_content"):
                 return "quiz_master"
            return "conclusion"
        # 否则回退到 draft_writer
        return "draft_writer"
        
    def route_after_quiz_master(self, state: LearningWorkflowState) -> str:
        """QuizMaster 后的路由"""
        return "conclusion"

    def route_after_curriculum_designer(self, state: LearningWorkflowState) -> str:
        """CurriculumDesigner 后的路由"""
        return "draft_writer"

    def route_after_tool_specialist(self, state: LearningWorkflowState) -> str:
        """ToolSpecialist 后的路由"""
        return "draft_writer"
    
    def route_error_handler(self, state: LearningWorkflowState) -> str:
        """错误处理路由"""
        return "error_handler"
    
    def route_conclusion(self, state: LearningWorkflowState) -> str:
        """结论路由"""
        return "conclusion"
    
    def route_wait_for_user(self, state: LearningWorkflowState) -> str:
        """等待用户输入路由"""
        return "wait_for_user"


# 路由函数（LangGraph 需要的函数形式）
def route_after_query_analysis(state: LearningWorkflowState) -> str:
    """查询分析后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_query_analysis(state)


def route_after_planning(state: LearningWorkflowState) -> str:
    """规划后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_planning(state)


def route_after_tool_execution(state: LearningWorkflowState) -> str:
    """工具执行后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_tool_execution(state)


def route_after_reviewer(state: LearningWorkflowState) -> str:
    """审核后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_reviewer(state)

def route_after_quiz_master(state: LearningWorkflowState) -> str:
    """QuizMaster 后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_quiz_master(state)

def route_after_curriculum_designer(state: LearningWorkflowState) -> str:
    """CurriculumDesigner 后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_curriculum_designer(state)

def route_after_tool_specialist(state: LearningWorkflowState) -> str:
    """ToolSpecialist 后的路由"""
    router = LearningWorkflowRouter()
    return router.route_after_tool_specialist(state)

def route_error_handler(state: LearningWorkflowState) -> str:
    """错误处理路由"""
    router = LearningWorkflowRouter()
    return router.route_error_handler(state)


def route_conclusion(state: LearningWorkflowState) -> str:
    """结论路由"""
    router = LearningWorkflowRouter()
    return router.route_conclusion(state)


def route_wait_for_user(state: LearningWorkflowState) -> str:
    """等待用户输入路由"""
    router = LearningWorkflowRouter()
    return router.route_wait_for_user(state)
