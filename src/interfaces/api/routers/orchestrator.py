#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator API路由
对应 core.agents.orchestrator 模块

⚠️ 重要说明：
这是底层 Agent 的直接调用入口，主要用于：
1. 开发调试
2. 单元测试
3. 性能分析
4. 独立功能验证

生产环境建议使用 /api/agent/v1/workflow/ 接口。
"""

import time
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import (
    PlanningRequest,
    PlanningResponse,
    ActionItemModel,
)
from ..dependencies import (
    get_planner,
    handle_agent_error,
    log_request,
    log_response,
)
from src.core.agents import OrchestratorAgent, AgentState
from src.infrastructure.utils import QueryType


logger = logging.getLogger("EduPilotAPI.Orchestrator")
router = APIRouter()


@router.post(
    "/plan",
    response_model=PlanningResponse,
    summary="学习规划",
    description="根据查询和检索结果制定学习计划",
)
async def create_plan(
    request: PlanningRequest,
    orchestrator: OrchestratorAgent = Depends(get_planner),
):
    """
    编排器接口
    
    功能：
    1. 分析查询和知识内容
    2. 制定学习计划
    3. 分解行动步骤
    4. 确定执行优先级
    """
    start_time = time.time()
    
    try:
        log_request("orchestrator/plan", {"query": request.query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=request.session_id or "default",
            user_query=request.query,
            query_type=QueryType[request.query_type.upper()] if request.query_type else QueryType.OPEN_ENDED,
            retrieved_knowledge=request.retrieved_knowledge or {},
        )
        
        # 设置元数据
        state.metadata["user_id"] = "anonymous"
        if request.user_context:
            state.metadata.update(request.user_context)
        
        # 执行规划
        result_state = await orchestrator.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "规划失败",
            )
        
        # 提取规划结果
        plan_data = result_state.learning_plan or {}
        plan_type = plan_data.get("type", "unknown")
        
        # 构建行动项列表
        action_items = []
        for action_data in plan_data.get("action_items", []):
            action_items.append(ActionItemModel(
                action_type=action_data.get("action_type", ""),
                description=action_data.get("description", ""),
                priority=action_data.get("priority", 1),
                parameters=action_data.get("parameters", {}),
                expected_outcome=action_data.get("expected_outcome", ""),
            ))
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("orchestrator/plan", True, duration_ms)
        
        return PlanningResponse(
            success=True,
            message="规划成功",
            data=plan_data,
            plan_type=plan_type,
            action_items=action_items,
            estimated_steps=len(action_items),
            reasoning=plan_data.get("reasoning", ""),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("orchestrator/plan", False, duration_ms)
        raise handle_agent_error("Orchestrator", e)

