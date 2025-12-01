#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
苏格拉底引导API路由
对应 core.agents.socratic_guide 模块

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
    SocraticGuideRequest,
    SocraticGuideResponse,
)
from ..dependencies import (
    get_socratic_guide,
    handle_agent_error,
    log_request,
    log_response,
)
from src.core.agents import SocraticGuideAgent, AgentState


logger = logging.getLogger("EduPilotAPI.SocraticGuide")
router = APIRouter()


@router.post(
    "/guide",
    response_model=SocraticGuideResponse,
    summary="苏格拉底引导",
    description="提供苏格拉底式引导问题，帮助学生思考",
)
async def get_socratic_guidance(
    request: SocraticGuideRequest,
    guide: SocraticGuideAgent = Depends(get_socratic_guide),
):
    """
    苏格拉底引导接口
    
    功能：
    1. 生成引导性问题
    2. 评估理解水平
    3. 提供思考线索
    4. 激发深度思考
    """
    start_time = time.time()
    
    try:
        log_request("socratic-guide/guide", {"query": request.user_query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=request.session_id or "default",
            user_query=request.user_query,
            user_response=request.user_response or "",
            retrieved_knowledge=request.knowledge_context or {},
        )
        
        # 设置元数据
        state.metadata["user_id"] = "anonymous"
        if request.guidance_level:
            state.metadata["guidance_level"] = request.guidance_level
        
        # 执行引导
        result_state = await guide.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "引导生成失败",
            )
        
        # 提取引导结果
        guidance_text = result_state.final_response or ""
        socratic_result = result_state.socratic_guidance or {}
        question_type = socratic_result.get("question_type", "clarifying")
        understanding_level = socratic_result.get("understanding_level", "unknown")
        next_steps = socratic_result.get("next_steps", [])
        metadata = socratic_result.get("metadata", {})
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("socratic-guide/guide", True, duration_ms)
        
        return SocraticGuideResponse(
            success=True,
            message="引导生成成功",
            guidance_text=guidance_text,
            question_type=question_type,
            understanding_level=understanding_level,
            next_steps=next_steps,
            metadata=metadata,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("socratic-guide/guide", False, duration_ms)
        raise handle_agent_error("SocraticGuide", e)

