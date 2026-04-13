"""统计中间件：自动记录所有 API 调用的性能指标。"""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from edupilot.services.storage import get_statistics_store


class StatisticsMiddleware(BaseHTTPMiddleware):
    """统计中间件：记录所有 API 请求的性能指标。"""
    
    # 排除的路径（健康检查等）
    EXCLUDED_PATHS = {
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 排除不需要统计的路径
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        endpoint = request.url.path
        
        try:
            # ���行请求
            response = await call_next(request)
            status_code = response.status_code
            
            # 计算响应时间
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录统计
            store = get_statistics_store()
            store.increment_request()
            store.record_api_call(endpoint, method, status_code, response_time_ms)
            store.record_response_time(endpoint, response_time_ms)
            
            # 记录错误
            if status_code >= 400:
                store.increment_error()
                store.record_error(
                    error_type=f"HTTP_{status_code}",
                    error_message=f"{method} {endpoint} 返回 {status_code}",
                    endpoint=endpoint
                )
            
            return response
            
        except Exception as e:
            # 计算响应时间
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录错误
            store = get_statistics_store()
            store.increment_request()
            store.increment_error()
            store.record_api_call(endpoint, method, 500, response_time_ms)
            store.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                endpoint=endpoint
            )
            raise