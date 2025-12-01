#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询分析器API路由
对应 core.agents.query_analyzer 模块

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
    QueryAnalysisRequest,
    QueryAnalysisResponse,
    IntentCandidateModel,
    RetrievalPlanModel,
)
from ..dependencies import (
    get_query_analyzer,
    handle_agent_error,
    log_request,
    log_response,
)
from src.core.agents import QueryAnalyzerAgent, AgentState


logger = logging.getLogger("EduPilotAPI.QueryAnalyzer")
router = APIRouter()


@router.post(
    "/analyze",
    response_model=QueryAnalysisResponse,
    summary="查询分析",
    description="分析用户查询，识别意图和查询类型，并制定检索计划",
)
async def analyze_query(
    request: QueryAnalysisRequest,
    analyzer: QueryAnalyzerAgent = Depends(get_query_analyzer),
):
    """
    查询分析接口
    
    功能：
    1. 意图识别：启发式 + LLM 精修
    2. 查询类型判断
    3. 检索决策
    4. 查询优化
    """
    start_time = time.time()
    
    try:
        log_request("query-analyzer/analyze", {"query": request.query[:100]})
        
        # 创建智能体状态
        state = AgentState(
            session_id=request.session_id or "default",
            user_query=request.query,
        )
        
        # 设置元数据
        state.metadata["user_id"] = request.user_id or "anonymous"
        
        # 执行分析
        result_state = await analyzer.execute(state)
        
        # 检查执行结果
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "查询分析失败",
            )
        
        # 提取分析结果
        analysis_data = result_state.query_analysis or {}
        intent = analysis_data.get("intent", "unknown")
        query_type_str = analysis_data.get("query_type", "open_ended")
        confidence = analysis_data.get("confidence", 0.0)
        
        # 构建候选意图列表
        candidates = []
        for candidate_data in analysis_data.get("candidates", []):
            candidates.append(IntentCandidateModel(
                name=candidate_data.get("name", ""),
                score=candidate_data.get("score", 0.0),
                source=candidate_data.get("source", ""),
                rationale=candidate_data.get("rationale", ""),
                signals=candidate_data.get("signals", {}),
            ))
        
        # 构建检索计划
        retrieval_plan = None
        if "retrieval_plan" in analysis_data:
            plan_data = analysis_data["retrieval_plan"]
            retrieval_plan = RetrievalPlanModel(
                need_retrieval=plan_data.get("need_retrieval", False),
                confidence=plan_data.get("confidence", 0.0),
                reason=plan_data.get("reason", ""),
                core_concepts=plan_data.get("core_concepts", []),
                related_queries=plan_data.get("related_queries", []),
                optimized_queries=plan_data.get("optimized_queries", []),
                query_strategy=plan_data.get("query_strategy", {}),
            )
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("query-analyzer/analyze", True, duration_ms)
        
        return QueryAnalysisResponse(
            success=True,
            message="查询分析成功",
            data=analysis_data,
            intent=intent,
            query_type=query_type_str,
            confidence=confidence,
            candidates=candidates,
            retrieval_plan=retrieval_plan,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("query-analyzer/analyze", False, duration_ms)
        raise handle_agent_error("QueryAnalyzer", e)

