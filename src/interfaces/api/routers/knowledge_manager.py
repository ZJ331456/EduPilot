#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识管理器API路由
对应 core.agents.knowledge_manager 模块

📚 接口说明：
这是工具类接口，主要用于：
1. 知识库管理和查询
2. 概念搜索和检索
3. 相关概念发现
4. 搜索建议生成

在 workflow 执行过程中，KnowledgeManager 会被自动调用。
这些接口主要用于独立的知识查询和管理操作。

使用场景：
- 知识库管理
- 概念查询
- 搜索建议
- 相关概念推荐
"""

import time
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import (
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
)
from ..dependencies import (
    get_knowledge_manager,
    handle_agent_error,
    log_request,
    log_response,
    validate_query,
)
from src.core.agents import KnowledgeManagerAgent, AgentState


logger = logging.getLogger("EduPilotAPI.KnowledgeManager")
router = APIRouter()


# ============================================================================
# 知识检索路由
# ============================================================================

@router.post(
    "/retrieve",
    response_model=KnowledgeRetrievalResponse,
    summary="检索知识",
    description="从知识库中检索相关知识内容",
)
async def retrieve_knowledge(
    request: KnowledgeRetrievalRequest,
    manager: KnowledgeManagerAgent = Depends(get_knowledge_manager),
):
    """
    知识检索接口
    
    功能：
    1. 语义检索
    2. 关键词检索
    3. 混合检索策略
    4. 结果排序和过滤
    """
    start_time = time.time()
    
    try:
        query = validate_query(request.query)
        
        log_request("knowledge-manager/retrieve", {
            "query": query[:100],
            "top_k": request.top_k,
            "strategy": request.retrieval_strategy,
        })
        
        # 创建智能体状态
        state = AgentState(
            session_id="default",
            user_query=query,
        )
        
        # 设置检索参数（使用 metadata 字段）
        state.metadata.update({
            "user_id": "anonymous",
            "top_k": request.top_k,
            "retrieval_strategy": request.retrieval_strategy or "hybrid",
            "filters": request.filters or {},
        })
        
        # 执行检索
        result_state = await manager.execute(state)
        
        # 检查是否有错误
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "知识检索失败",
            )
        
        # 从状态中提取检索结果
        retrieved_knowledge = result_state.retrieved_knowledge or {}
        results = retrieved_knowledge.get("results", [])
        total_count = len(results)
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/retrieve", True, duration_ms)
        
        return KnowledgeRetrievalResponse(
            success=True,
            message="知识检索成功",
            query=query,
            results=results,
            total_count=total_count,
            retrieval_time_ms=duration_ms,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/retrieve", False, duration_ms)
        raise handle_agent_error("KnowledgeManager", e)


# ============================================================================
# 概念查询路由
# ============================================================================

@router.get(
    "/concept/{concept_name}",
    summary="获取概念详情",
    description="获取指定概念的详细信息",
)
async def get_concept_details(
    concept_name: str,
    manager: KnowledgeManagerAgent = Depends(get_knowledge_manager),
):
    """
    概念详情接口
    
    功能：
    1. 获取概念定义
    2. 获取相关知识
    3. 获取关联概念
    """
    start_time = time.time()
    
    try:
        log_request("knowledge-manager/concept", {"concept": concept_name})
        
        # 创建智能体状态
        state = AgentState(
            session_id="default",
            user_query=f"什么是{concept_name}?",
        )
        
        # 设置检索参数（使用 metadata 字段）
        state.metadata.update({
            "user_id": "anonymous",
            "concept_query": True,
            "concept_name": concept_name,
        })
        
        # 执行检索
        result_state = await manager.execute(state)
        
        # 检查错误
        if result_state.has_error():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到概念: {concept_name}",
            )
        
        # 提取概念信息
        retrieved_knowledge = result_state.retrieved_knowledge or {}
        results = retrieved_knowledge.get("results", [])
        concept_data = results[0] if results else {}
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/concept", True, duration_ms)
        
        return {
            "success": True,
            "message": "概念信息获取成功",
            "data": {
                "concept_name": concept_name,
                "definition": concept_data.get("content", ""),
                "related_concepts": concept_data.get("related_concepts", []),
                "knowledge_base": concept_data.get("source", ""),
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/concept", False, duration_ms)
        raise handle_agent_error("KnowledgeManager", e)


# ============================================================================
# 知识库管理路由
# ============================================================================

@router.get(
    "/bases",
    summary="获取知识库列表",
    description="获取所有可用的知识库列表",
)
async def list_knowledge_bases(
    manager: KnowledgeManagerAgent = Depends(get_knowledge_manager),
):
    """
    知识库列表接口
    
    返回：
    - 知识库名称列表
    - 知识库统计信息
    """
    start_time = time.time()
    
    try:
        log_request("knowledge-manager/bases", {})
        
        # 获取知识库列表
        knowledge_bases = manager.list_knowledge_bases()
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/bases", True, duration_ms)
        
        return {
            "success": True,
            "message": "知识库列表获取成功",
            "data": {
                "total_count": len(knowledge_bases),
                "knowledge_bases": knowledge_bases,
            },
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/bases", False, duration_ms)
        raise handle_agent_error("KnowledgeManager", e)


@router.get(
    "/bases/{knowledge_base_name}",
    summary="获取知识库详情",
    description="获取指定知识库的详细信息",
)
async def get_knowledge_base_info(
    knowledge_base_name: str,
    manager: KnowledgeManagerAgent = Depends(get_knowledge_manager),
):
    """
    知识库详情接口
    
    返回：
    - 知识库基本信息
    - 统计数据
    - 最近更新时间
    """
    start_time = time.time()
    
    try:
        log_request("knowledge-manager/bases/info", {"knowledge_base": knowledge_base_name})
        
        # 获取知识库信息
        kb_info = manager.get_knowledge_base_info(knowledge_base_name)
        
        if not kb_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库不存在: {knowledge_base_name}",
            )
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/bases/info", True, duration_ms)
        
        return {
            "success": True,
            "message": "知识库信息获取成功",
            "data": kb_info,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/bases/info", False, duration_ms)
        raise handle_agent_error("KnowledgeManager", e)


# ============================================================================
# 相关概念路由
# ============================================================================

@router.get(
    "/related/{concept_name}",
    summary="获取相关概念",
    description="获取与指定概念相关的其他概念",
)
async def get_related_concepts(
    concept_name: str,
    limit: int = 10,
    manager: KnowledgeManagerAgent = Depends(get_knowledge_manager),
):
    """
    相关概念接口
    
    功能：
    1. 查找相关概念
    2. 计算相关性分数
    3. 排序返回
    """
    start_time = time.time()
    
    try:
        log_request("knowledge-manager/related", {
            "concept": concept_name,
            "limit": limit,
        })
        
        # 获取相关概念
        related_concepts = manager.get_related_concepts(
            concept_name=concept_name,
            limit=limit,
        )
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/related", True, duration_ms)
        
        return {
            "success": True,
            "message": "相关概念获取成功",
            "data": {
                "concept_name": concept_name,
                "related_concepts": related_concepts,
                "total_count": len(related_concepts),
            },
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/related", False, duration_ms)
        raise handle_agent_error("KnowledgeManager", e)


# ============================================================================
# 搜索建议路由
# ============================================================================

@router.get(
    "/suggestions",
    summary="获取搜索建议",
    description="根据输入获取搜索建议",
)
async def get_search_suggestions(
    query: str,
    limit: int = 5,
    manager: KnowledgeManagerAgent = Depends(get_knowledge_manager),
):
    """
    搜索建议接口
    
    功能：
    1. 自动补全
    2. 查询建议
    3. 热门概念
    """
    start_time = time.time()
    
    try:
        log_request("knowledge-manager/suggestions", {
            "query": query[:100],
            "limit": limit,
        })
        
        # 获取搜索建议
        suggestions = manager.get_search_suggestions(
            query=query,
            limit=limit,
        )
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/suggestions", True, duration_ms)
        
        return {
            "success": True,
            "message": "搜索建议获取成功",
            "data": {
                "query": query,
                "suggestions": suggestions,
                "total_count": len(suggestions),
            },
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("knowledge-manager/suggestions", False, duration_ms)
        raise handle_agent_error("KnowledgeManager", e)

