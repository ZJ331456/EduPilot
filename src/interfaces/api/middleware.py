#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 中间件
性能优化、缓存、限流等
"""

import time
import hashlib
from functools import wraps
from typing import Optional, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import asyncio

# ============================================================================
# 响应缓存中间件
# ============================================================================

class ResponseCache:
    """简单的响应缓存"""
    
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl  # 缓存时间（秒）
    
    def get_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        # 基于 URL 和查询参数生成键
        key_str = f"{request.method}:{request.url.path}:{request.url.query}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()


# 全局缓存实例
response_cache = ResponseCache(ttl=60)  # 60秒缓存


# ============================================================================
# 请求限流中间件
# ============================================================================

class RateLimiter:
    """简单的令牌桶限流器"""
    
    def __init__(self, rate: int = 10, per: int = 60):
        """
        Args:
            rate: 允许的请求数
            per: 时间窗口（秒）
        """
        self.rate = rate
        self.per = per
        self.allowance = {}
        self.last_check = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求"""
        current = time.time()
        
        if identifier not in self.allowance:
            self.allowance[identifier] = self.rate
            self.last_check[identifier] = current
            return True
        
        time_passed = current - self.last_check[identifier]
        self.last_check[identifier] = current
        
        # 补充令牌
        self.allowance[identifier] += time_passed * (self.rate / self.per)
        
        if self.allowance[identifier] > self.rate:
            self.allowance[identifier] = self.rate
        
        if self.allowance[identifier] < 1.0:
            return False
        
        self.allowance[identifier] -= 1.0
        return True


# 全局限流器实例
rate_limiter = RateLimiter(rate=100, per=60)  # 每分钟100个请求


# ============================================================================
# 请求压缩中间件
# ============================================================================

async def gzip_response_middleware(request: Request, call_next):
    """响应压缩中间件"""
    response = await call_next(request)
    
    # 检查是否支持 gzip
    accept_encoding = request.headers.get("accept-encoding", "")
    if "gzip" in accept_encoding and response.status_code == 200:
        # 这里可以添加 gzip 压缩逻辑
        # 实际生产环境建议使用 Nginx 处理
        pass
    
    return response


# ============================================================================
# 批处理请求优化
# ============================================================================

class BatchRequestHandler:
    """批量请求处理器"""
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = []
        self.batch_task = None
    
    async def add_request(self, request_data):
        """添加请求到批处理队列"""
        future = asyncio.Future()
        self.pending_requests.append((request_data, future))
        
        # 如果达到批大小，立即处理
        if len(self.pending_requests) >= self.batch_size:
            await self._process_batch()
        elif self.batch_task is None:
            # 启动超时任务
            self.batch_task = asyncio.create_task(self._wait_and_process())
        
        return await future
    
    async def _wait_and_process(self):
        """等待超时后处理批次"""
        await asyncio.sleep(self.batch_timeout)
        await self._process_batch()
    
    async def _process_batch(self):
        """处理批次"""
        if not self.pending_requests:
            return
        
        batch = self.pending_requests[:]
        self.pending_requests.clear()
        self.batch_task = None
        
        # 这里执行批处理逻辑
        # 例如：批量调用 LLM、批量数据库查询等
        
        # 示例：将结果返回给各个请求
        for request_data, future in batch:
            # 处理单个请求
            result = await self._process_single(request_data)
            future.set_result(result)
    
    async def _process_single(self, request_data):
        """处理单个请求（示例）"""
        # 实际处理逻辑
        return {"processed": True, "data": request_data}


# ============================================================================
# 连接池优化
# ============================================================================

class ConnectionPool:
    """连接池管理（用于复用 LLM 客户端连接）"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = []
        self.in_use = set()
    
    async def acquire(self):
        """获取连接"""
        if self.connections:
            conn = self.connections.pop()
        else:
            conn = await self._create_connection()
        
        self.in_use.add(id(conn))
        return conn
    
    async def release(self, conn):
        """释放连接"""
        if id(conn) in self.in_use:
            self.in_use.remove(id(conn))
            if len(self.connections) < self.max_connections:
                self.connections.append(conn)
            else:
                await self._close_connection(conn)
    
    async def _create_connection(self):
        """创建新连接"""
        # 实际创建逻辑
        return object()
    
    async def _close_connection(self, conn):
        """关闭连接"""
        # 实际关闭逻辑
        pass


# ============================================================================
# 响应时间监控
# ============================================================================

class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self):
        self.metrics = {
            "endpoint_timings": {},
            "slow_requests": [],
            "error_count": 0,
        }
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """记录请求"""
        if endpoint not in self.metrics["endpoint_timings"]:
            self.metrics["endpoint_timings"][endpoint] = []
        
        self.metrics["endpoint_timings"][endpoint].append(duration)
        
        # 记录慢请求（> 1秒）
        if duration > 1000:
            self.metrics["slow_requests"].append({
                "endpoint": endpoint,
                "duration": duration,
                "timestamp": time.time()
            })
        
        # 记录错误
        if status_code >= 400:
            self.metrics["error_count"] += 1
    
    def get_stats(self):
        """获取统计信息"""
        stats = {}
        for endpoint, timings in self.metrics["endpoint_timings"].items():
            if timings:
                stats[endpoint] = {
                    "avg": sum(timings) / len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "count": len(timings)
                }
        
        return {
            "endpoint_stats": stats,
            "slow_requests_count": len(self.metrics["slow_requests"]),
            "error_count": self.metrics["error_count"]
        }


# 全局性能监控实例
performance_monitor = PerformanceMonitor()

