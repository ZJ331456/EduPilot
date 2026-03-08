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
from .state import (
    LearningWorkflowState,
    create_initial_state,
    sync_compat_fields,
)

# v3 兼容别名（state.py v4 已移除双状态转换）
def state_to_agent_state(state):
    """v3 兼容别名，v4 中不再需要转换，直接返回 state"""
    return state

def update_state_from_agent_state(state, agent_state):
    """v3 兼容别名，v4 中 agent_state 即为 state"""
    return state if agent_state is state else {**state, **agent_state}

# LearningWorkflowRouter 兼容别名
class LearningWorkflowRouter:
    """v3 兼容别名，v4 中路由函数已改为纯函数"""
    pass


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
