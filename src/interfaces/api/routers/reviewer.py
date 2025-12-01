#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer API路由
对应 core.agents.reviewer 模块

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
    get_reviewer,
    handle_agent_error,
    log_request,
    log_response,
    validate_query,
)
from src.core.agents import ReviewerAgent, AgentState


logger = logging.getLogger("EduPilotAPI.Reviewer")
router = APIRouter()


@router.post(
    "/review",
    summary="审核内容质量",
    description="审核内容草稿，确保准确性、教学性和结构清晰",
)
async def review_content(
    query: str,
    draft_content: str,
    session_id: str = None,
    reviewer: ReviewerAgent = Depends(get_reviewer),
):
    """
    内容审核接口
    
    功能：
    1. 检查幻觉、语气、难度匹配度
    2. 决定是否重写
    3. 给出修改意见
    """
    start_time = time.time()
    
    try:
        query = validate_query(query)
        log_request("reviewer/review", {"query": query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=session_id or "default",
            user_query=query,
            draft_content=draft_content,
        )
        
        # 执行审核
        result_state = await reviewer.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "内容审核失败",
            )
        
        # 提取审核结果
        is_satisfactory = result_state.is_satisfactory or False
        critique = result_state.critique or ""
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("reviewer/review", True, duration_ms)
        
        return {
            "success": True,
            "message": "内容审核完成",
            "data": {
                "is_satisfactory": is_satisfactory,
                "critique": critique,
                "revision_count": result_state.revision_count or 0,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("reviewer/review", False, duration_ms)
        raise handle_agent_error("Reviewer", e)

