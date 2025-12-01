#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuizMaster API路由
对应 core.agents.quiz_master 模块

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
    get_quiz_master,
    handle_agent_error,
    log_request,
    log_response,
    validate_query,
)
from src.core.agents import QuizMasterAgent, AgentState


logger = logging.getLogger("EduPilotAPI.QuizMaster")
router = APIRouter()


@router.post(
    "/generate",
    summary="生成测试题",
    description="根据讲解内容生成测试题，评估用户掌握度",
)
async def generate_quiz(
    query: str,
    draft_content: str,
    session_id: str = None,
    quiz_master: QuizMasterAgent = Depends(get_quiz_master),
):
    """
    测试题生成接口
    
    功能：
    1. 根据讲解内容生成单选题
    2. 评估用户回答（如果是交互式测评）
    """
    start_time = time.time()
    
    try:
        query = validate_query(query)
        log_request("quiz-master/generate", {"query": query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=session_id or "default",
            user_query=query,
            draft_content=draft_content,
            is_satisfactory=True,  # 只有审核通过的内容才出题
        )
        
        # 执行出题
        result_state = await quiz_master.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "测试题生成失败",
            )
        
        # 提取测试题
        quiz_data = result_state.quiz_data or {}
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("quiz-master/generate", True, duration_ms)
        
        return {
            "success": True,
            "message": "测试题生成成功",
            "data": {
                "quiz_data": quiz_data,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("quiz-master/generate", False, duration_ms)
        raise handle_agent_error("QuizMaster", e)

