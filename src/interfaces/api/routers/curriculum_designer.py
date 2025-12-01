#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CurriculumDesigner API路由
对应 core.agents.curriculum_designer 模块

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
    get_curriculum_designer,
    handle_agent_error,
    log_request,
    log_response,
    validate_query,
)
from src.core.agents import CurriculumDesignerAgent, AgentState


logger = logging.getLogger("EduPilotAPI.CurriculumDesigner")
router = APIRouter()


@router.post(
    "/design",
    summary="设计课程结构",
    description="生成系统化的学习路径（思维导图结构）",
)
async def design_curriculum(
    query: str,
    retrieved_knowledge: Dict[str, Any] = None,
    session_id: str = None,
    designer: CurriculumDesignerAgent = Depends(get_curriculum_designer),
):
    """
    课程设计接口
    
    功能：
    1. 生成知识树结构
    2. 输出 JSON 格式的 MindMap 数据
    3. 设计系统化学习路径
    """
    start_time = time.time()
    
    try:
        query = validate_query(query)
        log_request("curriculum-designer/design", {"query": query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=session_id or "default",
            user_query=query,
            retrieved_knowledge=retrieved_knowledge or {},
        )
        
        # 执行设计
        result_state = await designer.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "课程设计失败",
            )
        
        # 提取课程计划
        curriculum_plan = result_state.curriculum_plan or {}
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("curriculum-designer/design", True, duration_ms)
        
        return {
            "success": True,
            "message": "课程设计成功",
            "data": {
                "curriculum_plan": curriculum_plan,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("curriculum-designer/design", False, duration_ms)
        raise handle_agent_error("CurriculumDesigner", e)

