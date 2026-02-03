#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot API主入口
FastAPI应用配置和路由注册
"""

import time
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from .config import get_settings
from .dependencies import get_api_state, APIState
from .models import HealthCheckResponse, ErrorResponse
from .middleware import response_cache, rate_limiter, performance_monitor
from .utils import health_checker, workflow_limiter


# ============================================================================
# 配置日志
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("EduPilotAPI")
settings = get_settings()
# 将动态配置同步到工具实例
response_cache.ttl = settings.cache_ttl_seconds
response_cache.max_entries = settings.cache_max_entries
rate_limiter.rate = settings.rate_limit_per_minute
rate_limiter.per = 60


# ============================================================================
# 路由注册函数（需要在 lifespan 之前定义）
# ============================================================================

def register_routers(app_instance: FastAPI):
    """
    注册所有子路由
    
    路由结构与 core 模块严格对齐：
    - /workflow/         ↔ core.workflow (主流程，包含所有10个agent)
    
    独立 Agent 接口（所有10个agent，调试/测试用）：
    - /query-analyzer/   ↔ core.agents.query_analyzer
    - /orchestrator/     ↔ core.agents.orchestrator
    - /draft-writer/     ↔ core.agents.draft_writer
    - /reviewer/         ↔ core.agents.reviewer
    - /curriculum-designer/ ↔ core.agents.curriculum_designer
    - /quiz-master/      ↔ core.agents.quiz_master
    - /tool-specialist/  ↔ core.agents.tool_specialist
    - /knowledge-manager/ ↔ core.agents.knowledge_manager
    - /socratic-guide/   ↔ core.agents.socratic_guide
    - /memory-manager/   ↔ core.agents.memory_manager
    """
    try:
        from .routers import (
            workflow,
            query_analyzer,
            orchestrator,
            socratic_guide,
            knowledge_manager,
            memory_manager,
            draft_writer,
            reviewer,
            curriculum_designer,
            quiz_master,
            tool_specialist,
        )
        
        # 主流程接口
        app_instance.include_router(
            workflow.router,
            prefix="/api/agent/v1/workflow",
            tags=["Workflow - 主流程"],
        )
        
        # 流式响应接口
        from .routers import workflow_streaming
        app_instance.include_router(
            workflow_streaming.router,
            prefix="/api/agent/v1/workflow",
            tags=["Workflow - 流式响应"],
        )
        
        # 独立 Agent 接口（所有10个agent，与 core.agents 对齐）
        app_instance.include_router(
            query_analyzer.router,
            prefix="/api/agent/v1/query-analyzer",
            tags=["QueryAnalyzer - 查询分析"],
        )
        
        app_instance.include_router(
            orchestrator.router,
            prefix="/api/agent/v1/orchestrator",
            tags=["Orchestrator - 学习规划"],
        )
        
        app_instance.include_router(
            draft_writer.router,
            prefix="/api/agent/v1/draft-writer",
            tags=["DraftWriter - 内容撰写"],
        )
        
        app_instance.include_router(
            reviewer.router,
            prefix="/api/agent/v1/reviewer",
            tags=["Reviewer - 内容审核"],
        )
        
        app_instance.include_router(
            curriculum_designer.router,
            prefix="/api/agent/v1/curriculum-designer",
            tags=["CurriculumDesigner - 课程设计"],
        )
        
        app_instance.include_router(
            quiz_master.router,
            prefix="/api/agent/v1/quiz-master",
            tags=["QuizMaster - 测试题生成"],
        )
        
        app_instance.include_router(
            tool_specialist.router,
            prefix="/api/agent/v1/tool-specialist",
            tags=["ToolSpecialist - 工具调用"],
        )
        
        app_instance.include_router(
            knowledge_manager.router,
            prefix="/api/agent/v1/knowledge-manager",
            tags=["KnowledgeManager - 知识管理"],
        )
        
        app_instance.include_router(
            socratic_guide.router,
            prefix="/api/agent/v1/socratic-guide",
            tags=["SocraticGuide - 苏格拉底引导"],
        )
        
        app_instance.include_router(
            memory_manager.router,
            prefix="/api/agent/v1/memory-manager",
            tags=["MemoryManager - 记忆管理"],
        )
        
        logger.info("✅ 所有路由已注册（10个agent全部包含，结构与 core 模块对齐）")
        
    except Exception as e:
        logger.error(f"注册路由失败: {e}", exc_info=True)


# ============================================================================
# 应用生命周期管理
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 EduPilot API 正在启动...")
    
    api_state = get_api_state()
    api_state.start_time = time.time()
    
    # 启动后台会话清理任务
    if api_state.session_cleanup_task is None:
        api_state.session_cleanup_task = asyncio.create_task(_session_cleanup_loop(api_state))
    
    # 初始化工作流（延迟加载）
    logger.info("✅ API 已就绪，等待请求...")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 EduPilot API 正在关闭...")
    
    # 清理资源
    if api_state.workflow_instance:
        logger.info("清理工作流资源...")
    
    if api_state.session_cleanup_task:
        api_state.session_cleanup_task.cancel()
        try:
            await api_state.session_cleanup_task
        except asyncio.CancelledError:
            pass
    
    logger.info("👋 API 已关闭")


# ============================================================================
# 创建FastAPI应用
# ============================================================================

app = FastAPI(
    title="EduPilot Agent API",
    description="智能教育助手API - 提供查询分析、学习规划、知识检索等功能",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/api/agent/v1/docs",
    redoc_url="/api/agent/v1/redoc",
    openapi_url="/api/agent/v1/openapi.json",
)

# 立即注册路由
register_routers(app)

# 后台会话清理任务
async def _session_cleanup_loop(api_state: APIState):
    """后台定期清理过期会话，避免内存占用"""
    try:
        interval = max(int(settings.session_ttl_hours * 3600 / 3), 600)
    except Exception:
        interval = 1800
    while True:
        await asyncio.sleep(interval)
        try:
            if api_state.workflow_instance:
                api_state.workflow_instance.cleanup_expired_sessions(settings.session_ttl_hours)
        except Exception as e:
            logger.warning(f"会话清理失败: {e}")


# ============================================================================
# 中间件配置
# ============================================================================

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 权限控制中间件（暂未实现）
# ⚠️ 在生产环境中启用，开发环境可以禁用
# app.add_middleware(
#     permission_middleware,
#     enable_permission_check=False,
# )


# 闭环限流
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    identifier = request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "unknown")
    if not rate_limiter.is_allowed(identifier):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "message": "请求过于频繁，请稍后再试",
                "error_code": "RATE_LIMITED",
            },
        )
    return await call_next(request)


# 轻量缓存只作用于 GET 的健康/统计类接口
@app.middleware("http")
async def cache_get_requests(request: Request, call_next):
    if not settings.cache_enabled or request.method != "GET":
        return await call_next(request)
    
    cacheable_prefixes = ("/api/agent/v1/health", "/api/agent/v1/stats")
    if not any(request.url.path.startswith(prefix) for prefix in cacheable_prefixes):
        return await call_next(request)
    
    cache_key = response_cache.get_cache_key(request)
    cached = response_cache.get(cache_key)
    if cached:
        headers, body, status_code, media_type = cached
        return Response(content=body, status_code=status_code, headers=headers, media_type=media_type)
    
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if response.status_code < 300 and "text/event-stream" not in content_type:
        body = b"".join([chunk async for chunk in response.body_iterator])
        response = Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
        response_cache.set(cache_key, (dict(response.headers), body, response.status_code, response.media_type))
    return response


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    start_time = time.time()
    
    # 记录请求
    logger.info(f"收到请求: {request.method} {request.url.path}")
    
    # 更新统计
    api_state = get_api_state()
    api_state.request_count += 1
    api_state.stats["total_requests"] += 1
    
    # 处理请求
    try:
        response = await call_next(request)
        
        # 计算耗时
        duration = (time.time() - start_time) * 1000
        
        # 记录响应
        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"状态={response.status_code} 耗时={duration:.2f}ms"
        )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(duration)
        response.headers["X-Request-ID"] = str(api_state.request_count)
        
        # 更新平均耗时 & 性能监控
        total = max(api_state.stats["total_requests"], 1)
        prev_avg = api_state.stats.get("average_response_time", 0.0)
        api_state.stats["average_response_time"] = ((prev_avg * (total - 1)) + duration) / total
        performance_monitor.record_request(request.url.path, duration, response.status_code, settings.slow_request_ms)
        
        # 更新统计
        if response.status_code < 400:
            api_state.stats["successful_requests"] += 1
        else:
            api_state.stats["failed_requests"] += 1
        
        return response
        
    except Exception as e:
        logger.error(f"请求处理错误: {str(e)}", exc_info=True)
        api_state.stats["failed_requests"] += 1
        raise


# ============================================================================
# 异常处理器
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger.warning(f"请求验证失败: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "请求参数验证失败",
            "error_code": "VALIDATION_ERROR",
            "error_detail": {
                "errors": exc.errors(),
                "body": str(exc.body),
            },
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error_code": "INTERNAL_ERROR",
            "error_detail": {
                "error": str(exc),
                "type": type(exc).__name__,
            },
            "timestamp": datetime.now().isoformat(),
        },
    )


# ============================================================================
# 基础路由
# ============================================================================

@app.get("/")
async def root():
    """根路径重定向"""
    return {
        "message": "欢迎使用 EduPilot API",
        "version": "3.0.0",
        "docs": "/api/agent/v1/docs",
    }


@app.get("/api/agent/v1/health", response_model=HealthCheckResponse)
async def health_check():
    """健康检查端点"""
    api_state = get_api_state()
    
    uptime = 0
    if api_state.start_time:
        uptime = time.time() - api_state.start_time
    
    # 检查各智能体状态
    agents_status = {}
    if api_state.workflow_instance:
        try:
            # 使用 nodes.agents 而不是 registry（LangGraph 版本）
            agents = api_state.workflow_instance.nodes.agents
            for agent_id in agents.keys():
                agents_status[agent_id] = "healthy"
        except Exception as e:
            logger.error(f"检查智能体状态失败: {e}")
            agents_status["error"] = str(e)
    
    return HealthCheckResponse(
        success=True,
        message="系统运行正常",
        status="healthy",
        version="3.0.0",
        agents_status=agents_status,
        uptime_seconds=uptime,
    )


@app.get("/api/agent/v1/stats")
async def get_stats():
    """获取系统统计信息"""
    api_state = get_api_state()
    
    stats = api_state.stats.copy()
    
    # 添加工作流统计
    if api_state.workflow_instance:
        stats["workflow_stats"] = api_state.workflow_instance.system_stats
    
    return {
        "success": True,
        "message": "统计信息",
        "data": stats,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/agent/v1/stats/performance")
async def get_performance_stats():
    """获取性能统计信息"""
    return {
        "success": True,
        "message": "性能统计",
        "data": performance_monitor.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/agent/v1/stats/cache")
async def get_cache_stats():
    """获取缓存统计信息"""
    cache_size = len(response_cache.cache)
    
    return {
        "success": True,
        "message": "缓存统计",
        "data": {
            "cache_size": cache_size,
            "cache_ttl": response_cache.ttl,
            "cache_limit": response_cache.max_entries,
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/agent/v1/cache/clear")
async def clear_cache():
    """清空缓存"""
    response_cache.clear()
    
    return {
        "success": True,
        "message": "缓存已清空",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# 路由已在应用创建后立即注册（见上方 register_routers(app) 调用）
# ============================================================================


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # 使用完整模块路径避免 reload 时找不到 main 模块
    uvicorn.run(
        "src.interfaces.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info",
    )

