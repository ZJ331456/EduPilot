#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流流式响应API路由
提供Server-Sent Events (SSE)支持，实时推送工作流执行状态
"""

import json
import logging
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..models import LearningSessionRequest
from ..dependencies import get_learning_workflow_instance
from src.core.workflow.learning import LangGraphLearningWorkflow


logger = logging.getLogger("EduPilotAPI.WorkflowStreaming")
router = APIRouter()


async def stream_workflow_execution(
    workflow: LangGraphLearningWorkflow,
    user_query: str,
    user_id: str,
    session_id: str,
    workflow_config: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """流式执行工作流并推送中间状态
    
    Args:
        workflow: 工作流实例
        user_query: 用户查询
        user_id: 用户ID
        session_id: 会话ID
        workflow_config: 工作流配置
        
    Yields:
        SSE格式的事件数据
    """
    try:
        # 发送开始事件
        yield f"data: {json.dumps({'type': 'workflow_start', 'message': '工作流开始执行', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
        
        # 创建异步任务执行工作流
        async def execute_workflow():
            return await workflow.process_query(
                user_query=user_query,
                session_id=session_id,
                user_context={"user_id": user_id},
                workflow_config=workflow_config
            )
        
        # 发送分析阶段事件
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'query_analysis', 'message': '正在分析查询意图...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)  # 短暂延迟，让前端有时间渲染
        
        # 执行工作流（这里可以进一步拆分为更细粒度的状态推送）
        result = await execute_workflow()
        
        # 发送规划阶段事件
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'planning', 'message': '正在制定学习计划...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)
        
        # 发送执行阶段事件
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'execution', 'message': '正在执行计划...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)
        
        # 发送完成事件
        yield f"data: {json.dumps({'type': 'workflow_complete', 'result': result, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False, default=str)}\n\n"
        
    except Exception as e:
        logger.error(f"流式执行工作流失败: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"


@router.post("/session/start/stream")
async def start_learning_session_stream(
    request: LearningSessionRequest,
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    启动学习会话（流式响应）
    
    使用Server-Sent Events (SSE)实时推送工作流执行状态
    """
    import uuid
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        workflow_config = request.workflow_config or {}
        
        return StreamingResponse(
            stream_workflow_execution(
                workflow=workflow,
                user_query=request.query,
                user_id=request.user_id,
                session_id=session_id,
                workflow_config=workflow_config
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用nginx缓冲
            }
        )
    except Exception as e:
        logger.error(f"启动流式会话失败: {e}", exc_info=True)
        raise

