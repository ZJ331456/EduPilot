#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心工作流模块

提供学习工作流实例化的统一入口。
直接使用 LangGraph 实现。
"""

from typing import Any, Dict

# 直接导入工作流组件
from .learning import (
    LangGraphLearningWorkflow,
    get_langgraph_learning_workflow,
    initialize_langgraph_learning_workflow
)
from .nodes import LearningWorkflowNodes
from .routing import LearningWorkflowRouter
from .state import (
    LearningWorkflowState,
    create_initial_state,
    state_to_agent_state,
    update_state_from_agent_state
)


def get_workflow_info() -> Dict[str, Any]:
    """获取工作流信息"""
    return {
        "implementation": "langgraph",
        "framework": "LangGraph",
        "description": "基于 LangGraph 框架的学习工作流",
        "features": [
            "图结构工作流",
            "可视化调试",
            "条件分支路由",
            "状态管理",
            "错误处理"
        ]
    }


__all__ = [
    # 主要工作流类
    "LangGraphLearningWorkflow",
    
    # 工作流管理函数
    "get_langgraph_learning_workflow",
    "initialize_langgraph_learning_workflow",
    "get_workflow_info",
    
    # LangGraph 组件
    "LearningWorkflowNodes",
    "LearningWorkflowRouter",
    "LearningWorkflowState",
    
    # 状态管理函数
    "create_initial_state",
    "state_to_agent_state",
    "update_state_from_agent_state",
]
