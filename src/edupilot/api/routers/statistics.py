"""统计接口：系统监控和性能数据。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from edupilot.services.storage import get_statistics_store

router = APIRouter(prefix="/statistics", tags=["statistics"])


# ==================== 请求/响应模型 ====================

class GlobalStatsResponse(BaseModel):
    total_requests: int
    total_errors: int
    total_sessions_created: int
    total_sessions_ended: int
    total_users: int
    total_agents_executed: int
    start_time: str
    last_updated: str
    known_users: List[str] = []


class APIEndpointStats(BaseModel):
    total_calls: int
    total_errors: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    methods: Dict[str, Dict[str, int]]
    status_codes: Dict[str, int]


class ResponseTimeDistribution(BaseModel):
    buckets: Dict[str, int]


class ErrorRecord(BaseModel):
    timestamp: str
    error_type: str
    message: str
    endpoint: Optional[str] = None
    user_id: Optional[str] = None


class ErrorStatsResponse(BaseModel):
    errors: List[ErrorRecord]
    error_counts: Dict[str, int]
    total_errors: int


class UserActivityResponse(BaseModel):
    user_id: str
    first_seen: str
    last_active: str
    total_actions: int
    actions: Dict[str, int]


class AgentStatsResponse(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    modes: Dict[str, Dict[str, int]]


class FullStatisticsResponse(BaseModel):
    global_stats: GlobalStatsResponse
    api_stats: Dict[str, APIEndpointStats]
    response_time_distribution: Dict[str, Dict[str, Any]]
    error_stats: ErrorStatsResponse
    user_activity: Dict[str, UserActivityResponse]
    agent_stats: Dict[str, AgentStatsResponse]
    active_users_24h: List[str]
    active_users_7d: List[str]
    generated_at: str


class ResetStatisticsResponse(BaseModel):
    ok: bool
    message: str


# ==================== API 端点 ====================

@router.get("", response_model=FullStatisticsResponse)
async def get_statistics():
    """
    获取完整系统统计信息。
    
    包含：全局统计、API 调用统计、响应时间分布、错误统计、用户活跃度、Agent 执行统计。
    """
    store = get_statistics_store()
    stats = store.get_full_statistics()
    
    # 构建响应
    global_stats = stats["global"]
    active_users_24h = stats.get("active_users_24h", [])
    active_users_7d = stats.get("active_users_7d", [])
    
    # 处理 API 统计
    api_stats = stats.get("api", {})
    
    # 处理响应时间分布
    response_times = stats.get("response_times", {})
    
    # 处理错误统计
    errors_data = stats.get("errors", {})
    error_stats = ErrorStatsResponse(
        errors=[ErrorRecord(**e) for e in errors_data.get("errors", [])[-50:]],  # 最近 50 条
        error_counts=errors_data.get("error_counts", {}),
        total_errors=sum(errors_data.get("error_counts", {}).values())
    )
    
    # 处理用户活跃度
    user_activity = stats.get("user_activity", {})
    formatted_user_activity = {
        uid: UserActivityResponse(
            user_id=uid,
            first_seen=data.get("first_seen", ""),
            last_active=data.get("last_active", ""),
            total_actions=data.get("total_actions", 0),
            actions=data.get("actions", {})
        )
        for uid, data in user_activity.items()
    }
    
    # 处理 Agent 统计
    agent_stats = stats.get("agents", {})
    
    from datetime import datetime, timezone
    return FullStatisticsResponse(
        global_stats=GlobalStatsResponse(**global_stats),
        api_stats={k: APIEndpointStats(**v) for k, v in api_stats.items()},
        response_time_distribution=response_times.get("buckets", {}),
        error_stats=error_stats,
        user_activity=formatted_user_activity,
        agent_stats={k: AgentStatsResponse(**v) for k, v in agent_stats.items()},
        active_users_24h=active_users_24h,
        active_users_7d=active_users_7d,
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/global", response_model=GlobalStatsResponse)
async def get_global_stats():
    """获取全局统计信息。"""
    store = get_statistics_store()
    return GlobalStatsResponse(**store.get_global_stats())


@router.get("/api", response_model=Dict[str, APIEndpointStats])
async def get_api_stats(endpoint: Optional[str] = Query(None, description="筛选特定端点")):
    """获取 API 调用统计。"""
    store = get_statistics_store()
    stats = store.get_api_stats()
    
    if endpoint:
        if endpoint in stats:
            return {endpoint: APIEndpointStats(**stats[endpoint])}
        return {}
    
    return {k: APIEndpointStats(**v) for k, v in stats.items()}


@router.get("/response-times", response_model=Dict[str, Dict[str, Any]])
async def get_response_time_distribution(endpoint: Optional[str] = Query(None)):
    """获取响应时间分布统计。"""
    store = get_statistics_store()
    data = store.get_response_time_stats()
    buckets = data.get("buckets", {})
    
    if endpoint:
        if endpoint in buckets:
            return {endpoint: buckets[endpoint]}
        return {}
    
    return buckets


@router.get("/errors", response_model=ErrorStatsResponse)
async def get_error_stats(limit: int = Query(50, ge=1, le=500)):
    """获取错误统计（最近 N 条）。"""
    store = get_statistics_store()
    data = store.get_error_stats()
    
    return ErrorStatsResponse(
        errors=[ErrorRecord(**e) for e in data.get("errors", [])[-limit:]],
        error_counts=data.get("error_counts", {}),
        total_errors=sum(data.get("error_counts", {}).values())
    )


@router.get("/users", response_model=Dict[str, UserActivityResponse])
async def get_user_activity(user_id: Optional[str] = Query(None)):
    """获取用户活跃度统计。"""
    store = get_statistics_store()
    data = store.get_user_activity(user_id)
    
    if user_id:
        if data:
            return {user_id: UserActivityResponse(
                user_id=user_id,
                first_seen=data.get("first_seen", ""),
                last_active=data.get("last_active", ""),
                total_actions=data.get("total_actions", 0),
                actions=data.get("actions", {})
            )}
        return {}
    
    return {
        uid: UserActivityResponse(
            user_id=uid,
            first_seen=data.get("first_seen", ""),
            last_active=data.get("last_active", ""),
            total_actions=data.get("total_actions", 0),
            actions=data.get("actions", {})
        )
        for uid, data in data.items()
    }


@router.get("/agents", response_model=Dict[str, AgentStatsResponse])
async def get_agent_stats(agent_name: Optional[str] = Query(None)):
    """获取 Agent 执行统计。"""
    store = get_statistics_store()
    data = store.get_agent_stats()
    
    if agent_name:
        if agent_name in data:
            return {agent_name: AgentStatsResponse(**data[agent_name])}
        return {}
    
    return {k: AgentStatsResponse(**v) for k, v in data.items()}


@router.get("/active-users")
async def get_active_users(hours: int = Query(24, ge=1, le=168)):
    """获取指定时间段内活跃的用户列表。"""
    store = get_statistics_store()
    return {
        "hours": hours,
        "active_users": store.get_active_users(hours=hours),
        "count": len(store.get_active_users(hours=hours))
    }


@router.post("/reset", response_model=ResetStatisticsResponse)
async def reset_statistics():
    """重置所有统计数据。谨慎使用！"""
    store = get_statistics_store()
    store.reset_statistics()
    return ResetStatisticsResponse(
        ok=True,
        message="所有统计数据已重置"
    )