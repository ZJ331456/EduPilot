#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主应用程序
多智能体学习助手的FastAPI应用
"""

import os
import sys
import time
import uuid
import traceback
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles  

# 添加src目录到Python路径
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 导入项目模块
try:
    from routers.enhanced_multi_agent_router import enhanced_router as multi_agent_router
    print("Successfully imported enhanced_multi_agent_router")
except ImportError as e:
    print(f"Warning: Failed to import enhanced_multi_agent_router: {e}")
    # 创建一个简单的备用路由
    from fastapi import APIRouter
    multi_agent_router = APIRouter()
    
    @multi_agent_router.get("/health")
    async def health_check():
        return {"status": "service_unavailable", "message": "Multi-agent system not available"}
    
    @multi_agent_router.post("/query")
    async def query_fallback():
        raise HTTPException(status_code=503, detail="Multi-agent system not available")

# 导入日志配置
from config.logging_config import get_logger, setup_logging, LoggerNames

# 全局变量
logger = None

def setup_application_logging():
    """设置应用程序日志配置"""
    global logger
    
    # 初始化日志配置
    setup_logging('hw_agent')
    
    # 获取应用日志器
    logger = get_logger(LoggerNames.APP)
    
    # 设置其他模块的日志器
    agent_logger = get_logger(LoggerNames.AGENT)
    llm_logger = get_logger(LoggerNames.LLM)
    api_logger = get_logger(LoggerNames.API)
    db_logger = get_logger(LoggerNames.DATABASE)
    
    logger.info("Application logging system initialized")
    
    return logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global logger
    logger = setup_application_logging()
    
    # 启动时初始化
    logger.info("Starting Multi-Agent Learning Assistant...")
    
    try:
        # 初始化MongoDB服务
        try:
            from services.mongodb_integration import mongodb_service
            await mongodb_service.initialize()
            logger.info("MongoDB service initialized successfully")
        except Exception as e:
            logger.warning(f"MongoDB service initialization failed: {e}")
        
        # 初始化多智能体系统
        try:
            from agents import initialize_multi_agent_system
            mas_config = {
                "max_iterations": 5,
                "timeout_seconds": 300,
                "enable_learning": True,
                "enable_socratic": True,
                "auto_continue": False,
                "enable_mongodb": True,
                "enable_query_classification": True
            }
            mas = initialize_multi_agent_system(mas_config)
            logger.info("Multi-agent system initialized successfully")
        except Exception as e:
            logger.warning(f"Multi-agent system initialization failed: {e}")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        logger.error(traceback.format_exc())
    
    yield
    
    # 关闭时清理
    logger.info("Shutting down Multi-Agent Learning Assistant...")
    
    try:
        # 关闭MongoDB服务
        try:
            from services.mongodb_integration import mongodb_service
            await mongodb_service.cleanup()
            logger.info("MongoDB service cleanup completed")
        except Exception as e:
            logger.warning(f"MongoDB service cleanup failed: {e}")
        
        # 关闭多智能体系统
        try:
            from agents import get_multi_agent_system
            mas = get_multi_agent_system()
            if mas:
                mas.shutdown()
                logger.info("Multi-agent system shutdown completed")
        except Exception as e:
            logger.warning(f"Multi-agent system shutdown failed: {e}")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 创建应用
    app = FastAPI(
        title="多智能体学习助手",
        description="基于nano-graphrag知识库的智能学习系统",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # 添加中间件
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 请求ID中间件
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """为每个请求添加唯一ID"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 添加到响应头
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录请求日志"""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 记录请求开始
        if logger:
            logger.info(
                f"Request started - {request.method} {request.url} [ID: {request_id}]"
            )
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            if logger:
                logger.info(
                    f"Request completed - {request.method} {request.url} "
                    f"[Status: {response.status_code}] [Time: {process_time:.3f}s] [ID: {request_id}]"
                )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(round(process_time, 3))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # 记录请求错误
            if logger:
                logger.error(
                    f"Request failed - {request.method} {request.url} "
                    f"[Error: {str(e)}] [Time: {process_time:.3f}s] [ID: {request_id}]"
                )
            
            raise
    
    # 全局异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTP异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "HTTPException",
                    "message": exc.detail,
                    "request_id": request_id
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理通用异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        if logger:
            logger.error(
                f"Unhandled exception: {exc}",
                extra={
                    "request_id": request_id,
                    "traceback": traceback.format_exc()
                }
            )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": "Internal server error occurred",
                    "request_id": request_id
                }
            }
        )
    
    # 包含路由
    app.include_router(multi_agent_router, prefix="/api/multi-agent", tags=["多智能体系统"])
    
    # 静态文件服务 - 前后端分离时注释掉
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # 根路径 - 前后端分离时注释掉前端界面
    @app.get("/")
    async def root():
        """提供多智能体学习助手前端界面"""
        static_dir = Path(__file__).parent.parent / "static"
        interface_file = static_dir / "multi_agent_interface.html"
        
        if interface_file.exists():
            return FileResponse(str(interface_file))
        else:
            return JSONResponse(
                status_code=404,
                content={
                      "error": "前端界面文件未找到",
                    "message": "请确保 static/multi_agent_interface.html 文件存在"
                }
            )  
    
    # # 根路径 - 前后端分离时的API信息
    # @app.get("/")
    # async def root():
    #     """API根路径 - 返回服务信息"""
    #     return {
    #         "service": "多智能体学习助手 API",
    #         "version": "2.0.0",
    #         "description": "基于图谱知识库的智能学习系统后端API",
    #         "status": "running",
    #         "endpoints": {
    #             "api_docs": "/docs",
    #             "api_redoc": "/redoc",
    #             "api_spec": "/openapi.json",
    #             "multi_agent": "/api/multi-agent",
    #             "health": "/health"
    #         },
    #         "message": "这是一个纯后端API服务，前端请通过其他方式访问"
    #     }
    
    # API信息端点
    @app.get("/api")
    async def api_info():
        """获取API信息"""
        return {
            "name": "多智能体学习助手 API",
            "version": "2.0.0",
            "description": "基于图谱知识库的智能学习系统",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
                "multi_agent": "/api/multi-agent"
            }
        }
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "多智能体学习助手"
        }
    
    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    # 开发环境配置
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )