#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理器API路由
对应 core.agents.memory_manager 模块

📝 接口说明：
这是工具类接口，主要用于：
1. 查询用户画像和学习数据
2. 生成学习分析报告
3. 数据可视化支持

在 workflow 执行过程中，MemoryManager 会被 Executor 自动调用。
这些接口主要用于外部查询和数据管理。

使用场景：
- 用户数据查询
- 学习统计分析
- 知识图谱可视化
- 用户画像管理
"""

import time
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import (
    UserProfileRequest,
    UserProfileResponse,
    SessionMemoryRequest,
    SessionMemoryResponse,
    MemoryAnalysisRequest,
)
from ..dependencies import (
    get_memory_manager,
    handle_agent_error,
    log_request,
    log_response,
    validate_user_id,
    validate_session_id,
)
from src.core.agents import MemoryManagerAgent


logger = logging.getLogger("EduPilotAPI.MemoryManager")
router = APIRouter()


# ============================================================================
# 用户画像路由
# ============================================================================

@router.get(
    "/profile/{user_id}",
    response_model=UserProfileResponse,
    summary="获取用户画像",
    description="获取指定用户的完整画像信息",
)
async def get_user_profile(
    user_id: str,
    include_triples: bool = False,
    include_emotions: bool = False,
    include_patterns: bool = False,
    memory_manager: MemoryManagerAgent = Depends(get_memory_manager),
):
    """
    获取用户画像接口
    
    功能：
    1. 获取用户基本画像
    2. 可选包含知识三元组
    3. 可选包含情感分析
    4. 可选包含学习模式
    """
    start_time = time.time()
    
    try:
        user_id = validate_user_id(user_id)
        
        log_request("memory-manager/profile", {"user_id": user_id})
        
        # 获取用户画像
        profile_data = memory_manager.get_user_profile(user_id)
        
        # 如果用户画像不存在，返回空数据而不是 404（便于前端处理新用户）
        if not profile_data:
            profile_data = {
                "user_id": user_id,
                "total_interactions": 0,
                "average_quality": 0.0,
                "learning_streak": 0,
                "created_at": None,
                "last_activity": None,
            }
            logger.info(f"用户画像不存在，返回空数据: {user_id}")
        
        # 构建响应
        response_data = {
            "user_id": user_id,
            "profile": profile_data,
            "statistics": {
                "total_interactions": profile_data.get("total_interactions", 0),
                "average_quality": profile_data.get("average_quality", 0.0),
                "learning_streak": profile_data.get("learning_streak", 0),
            },
        }
        
        # 可选数据
        triples_data = None
        if include_triples:
            triples_data = memory_manager.get_user_triples(user_id)
            logger.info(f"API - Triples count: {len(triples_data) if triples_data else 0}")
        
        emotions_data = None
        if include_emotions:
            emotions_data = memory_manager.get_user_emotions(user_id)
            logger.info(f"API - Emotions data: {emotions_data is not None}")
        
        patterns_data = None
        if include_patterns:
            patterns_data = memory_manager.get_learning_patterns(user_id)
            logger.info(f"API - Patterns count: {len(patterns_data) if patterns_data else 0}")
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/profile", True, duration_ms)
        
        return UserProfileResponse(
            success=True,
            message="用户画像获取成功",
            user_id=user_id,
            profile=profile_data,
            triples=triples_data,
            emotions=emotions_data,
            learning_patterns=patterns_data,
            statistics=response_data["statistics"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/profile", False, duration_ms)
        raise handle_agent_error("MemoryManager", e)


@router.post(
    "/profile/{user_id}/update",
    summary="更新用户画像",
    description="基于新的交互数据更新用户画像",
)
async def update_user_profile(
    user_id: str,
    update_data: Dict[str, Any],
    memory_manager: MemoryManagerAgent = Depends(get_memory_manager),
):
    """
    更新用户画像接口
    
    功能：
    1. 添加新的三元组
    2. 更新情感状态
    3. 更新学习模式
    4. 更新统计信息
    """
    start_time = time.time()
    
    try:
        user_id = validate_user_id(user_id)
        
        log_request("memory-manager/profile/update", {"user_id": user_id})
        
        # 更新用户画像
        result = memory_manager.update_user_profile(user_id, update_data)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户画像更新失败",
            )
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/profile/update", True, duration_ms)
        
        return {
            "success": True,
            "message": "用户画像更新成功",
            "data": result,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/profile/update", False, duration_ms)
        raise handle_agent_error("MemoryManager", e)


# ============================================================================
# 会话记忆路由
# ============================================================================

@router.get(
    "/session/{session_id}",
    response_model=SessionMemoryResponse,
    summary="获取会话记忆",
    description="获取指定会话的记忆数据",
)
async def get_session_memory(
    session_id: str,
    user_id: str = None,
    memory_manager: MemoryManagerAgent = Depends(get_memory_manager),
):
    """
    获取会话记忆接口
    
    功能：
    1. 获取会话交互历史
    2. 获取会话质量评分
    3. 获取学习洞察
    """
    start_time = time.time()
    
    try:
        session_id = validate_session_id(session_id)
        
        log_request("memory-manager/session", {"session_id": session_id})
        
        # 获取会话记忆
        session_data = memory_manager.get_session_memory(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话记忆不存在: {session_id}",
            )
        
        # 提取会话信息
        interaction_count = len(session_data.get("interactions", []))
        quality_score = session_data.get("quality_score", 0.0)
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/session", True, duration_ms)
        
        return SessionMemoryResponse(
            success=True,
            message="会话记忆获取成功",
            session_id=session_id,
            memory_data=session_data,
            interaction_count=interaction_count,
            quality_score=quality_score,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/session", False, duration_ms)
        raise handle_agent_error("MemoryManager", e)


@router.post(
    "/session/analyze",
    summary="分析会话记忆",
    description="分析会话交互质量并更新用户画像",
)
async def analyze_session_memory(
    request: MemoryAnalysisRequest,
    memory_manager: MemoryManagerAgent = Depends(get_memory_manager),
):
    """
    分析会话记忆接口
    
    功能：
    1. 分析交互质量
    2. 提取学习洞察
    3. 识别知识缺口
    4. 更新用户画像
    """
    start_time = time.time()
    
    try:
        user_id = validate_user_id(request.user_id)
        session_id = validate_session_id(request.session_id)
        
        log_request("memory-manager/session/analyze", {
            "user_id": user_id,
            "session_id": session_id,
        })
        
        # 创建智能体状态
        from src.core.agents import AgentState
        
        state = AgentState(
            session_id=session_id,
        )
        
        # 添加交互数据到状态（使用 metadata 字段）
        state.metadata.update({
            "user_id": user_id,
            **request.interaction_data
        })
        
        # 执行分析
        result_state = await memory_manager.execute(state)
        
        # 检查错误
        if result_state.has_error():
            error_msg = result_state.get_error_messages()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "会话分析失败",
            )
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/session/analyze", True, duration_ms)
        
        return {
            "success": True,
            "message": "会话分析成功",
            "data": {
                "analysis": result_state.memory_analysis,
                "user_id": user_id,
                "session_id": session_id,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/session/analyze", False, duration_ms)
        raise handle_agent_error("MemoryManager", e)


# ============================================================================
# 学习记录路由
# ============================================================================

@router.get(
    "/learning-records/{user_id}",
    summary="获取学习记录",
    description="获取用户的学习历史记录",
)
async def get_learning_records(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
    memory_manager: MemoryManagerAgent = Depends(get_memory_manager),
):
    """
    获取学习记录接口
    
    功能：
    1. 获取学习历史
    2. 分页查询
    3. 提供统计摘要
    """
    start_time = time.time()
    
    try:
        user_id = validate_user_id(user_id)
        
        log_request("memory-manager/learning-records", {
            "user_id": user_id,
            "limit": limit,
            "offset": offset,
        })
        
        # 获取学习记录
        records = memory_manager.get_learning_records(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/learning-records", True, duration_ms)
        
        return {
            "success": True,
            "message": "学习记录获取成功",
            "data": {
                "user_id": user_id,
                "records": records,
                "total_count": len(records),
                "limit": limit,
                "offset": offset,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/learning-records", False, duration_ms)
        raise handle_agent_error("MemoryManager", e)


# ============================================================================
# 知识图谱路由
# ============================================================================

@router.get(
    "/knowledge-graph/{user_id}",
    summary="获取用户知识图谱",
    description="获取用户的知识三元组图谱",
)
async def get_knowledge_graph(
    user_id: str,
    memory_manager: MemoryManagerAgent = Depends(get_memory_manager),
):
    """
    获取知识图谱接口
    
    功能：
    1. 获取用户的知识三元组
    2. 构建知识图谱
    3. 识别知识关联
    """
    start_time = time.time()
    
    try:
        user_id = validate_user_id(user_id)
        
        log_request("memory-manager/knowledge-graph", {"user_id": user_id})
        
        # 获取三元组数据
        triples = memory_manager.get_user_triples(user_id)
        logger.info(f"知识图谱 - 用户 {user_id} 的三元组数量: {len(triples)}")
        if triples:
            logger.debug(f"三元组示例: {triples[0]}")
        
        # 构建图谱结构
        graph_data = {
            "nodes": [],
            "edges": [],
        }
        
        # 提取节点和边
        entities = set()
        for triple in triples:
            subject = triple.get("subject")
            predicate = triple.get("predicate")
            obj = triple.get("object")
            
            entities.add(subject)
            entities.add(obj)
            
            graph_data["edges"].append({
                "source": subject,
                "target": obj,
                "relation": predicate,
                "confidence": triple.get("confidence", 1.0),
            })
        
        # 添加节点
        for entity in entities:
            graph_data["nodes"].append({
                "id": entity,
                "label": entity,
                "type": "concept",
            })
        
        # 记录响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/knowledge-graph", True, duration_ms)
        
        result = {
            "success": True,
            "message": "知识图谱获取成功",
            "data": {
                "user_id": user_id,
                "graph": graph_data,
                "statistics": {
                    "total_nodes": len(graph_data["nodes"]),
                    "total_edges": len(graph_data["edges"]),
                    "total_triples": len(triples),
                },
            },
        }
        
        logger.info(f"知识图谱返回: nodes={len(graph_data['nodes'])}, edges={len(graph_data['edges'])}, triples={len(triples)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("memory-manager/knowledge-graph", False, duration_ms)
        raise handle_agent_error("MemoryManager", e)

