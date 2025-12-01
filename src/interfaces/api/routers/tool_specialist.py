#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ToolSpecialist API路由
对应 core.agents.tool_specialist 模块

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

from ..dependencies import (
    get_tool_specialist,
    handle_agent_error,
    log_request,
    log_response,
    validate_query,
)
from src.core.agents import ToolSpecialistAgent, AgentState


logger = logging.getLogger("EduPilotAPI.ToolSpecialist")
router = APIRouter()


@router.post(
    "/execute",
    summary="执行工具调用",
    description="执行数学计算、网络搜索等工具调用",
)
async def execute_tool(
    query: str,
    tool_type: str = None,
    session_id: str = None,
    specialist: ToolSpecialistAgent = Depends(get_tool_specialist),
):
    """
    工具执行接口
    
    功能：
    1. 处理计算、实时信息获取等任务
    2. 支持 Web Search 和 Code Interpreter
    """
    start_time = time.time()
    
    try:
        query = validate_query(query)
        log_request("tool-specialist/execute", {
            "query": query[:100],
            "tool_type": tool_type,
        })
        
        # 创建智能体状态
        state = AgentState(
            session_id=session_id or "default",
            user_query=query,
        )
        
        # 设置工具类型（使用 metadata 字段）
        if tool_type:
            state.metadata["tool_type"] = tool_type
        
        # 执行工具调用
        result_state = await specialist.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "工具执行失败",
            )
        
        # 提取工具输出
        tool_outputs = result_state.tool_outputs or {}
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("tool-specialist/execute", True, duration_ms)
        
        return {
            "success": True,
            "message": "工具执行成功",
            "data": {
                "tool_outputs": tool_outputs,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("tool-specialist/execute", False, duration_ms)
        raise handle_agent_error("ToolSpecialist", e)

