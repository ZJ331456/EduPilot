#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraftWriter API路由
对应 core.agents.draft_writer 模块

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
    get_draft_writer,
    handle_agent_error,
    log_request,
    log_response,
    validate_query,
)
from src.core.agents import DraftWriterAgent, AgentState


logger = logging.getLogger("EduPilotAPI.DraftWriter")
router = APIRouter()


@router.post(
    "/write",
    summary="生成内容草稿",
    description="根据规划和工具执行结果生成内容草稿",
)
async def write_draft(
    query: str,
    plan: Dict[str, Any] = None,
    retrieved_knowledge: Dict[str, Any] = None,
    session_id: str = None,
    writer: DraftWriterAgent = Depends(get_draft_writer),
):
    """
    内容撰写接口
    
    功能：
    1. 整合 RAG 检索结果
    2. 整合工具输出
    3. 生成初稿内容
    """
    start_time = time.time()
    
    try:
        query = validate_query(query)
        log_request("draft-writer/write", {"query": query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=session_id or "default",
            user_query=query,
            retrieved_knowledge=retrieved_knowledge or {},
        )
        
        # 设置规划信息
        if plan:
            state.learning_plan = plan
        
        # 执行撰写
        result_state = await writer.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "内容撰写失败",
            )
        
        # 提取草稿内容
        draft_content = result_state.draft_content or ""
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("draft-writer/write", True, duration_ms)
        
        return {
            "success": True,
            "message": "内容撰写成功",
            "data": {
                "draft_content": draft_content,
                "revision_count": result_state.revision_count or 0,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("draft-writer/write", False, duration_ms)
        raise handle_agent_error("DraftWriter", e)


@router.post(
    "/revise",
    summary="修改内容草稿",
    description="根据审核意见修改内容草稿",
)
async def revise_draft(
    query: str,
    draft_content: str,
    critique: str,
    session_id: str = None,
    writer: DraftWriterAgent = Depends(get_draft_writer),
):
    """
    内容修改接口
    
    功能：
    1. 根据审核意见修改草稿
    2. 改进内容质量
    """
    start_time = time.time()
    
    try:
        query = validate_query(query)
        log_request("draft-writer/revise", {"query": query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=session_id or "default",
            user_query=query,
            draft_content=draft_content,
            critique=critique,
            is_satisfactory=False,
        )
        
        # 执行修改
        result_state = await writer.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "内容修改失败",
            )
        
        # 提取修改后的内容
        revised_content = result_state.draft_content or ""
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("draft-writer/revise", True, duration_ms)
        
        return {
            "success": True,
            "message": "内容修改成功",
            "data": {
                "draft_content": revised_content,
                "revision_count": result_state.revision_count or 0,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("draft-writer/revise", False, duration_ms)
        raise handle_agent_error("DraftWriter", e)

