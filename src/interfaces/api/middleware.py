#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 中间件
封装缓存、限流、性能监控等通用逻辑。
"""

import asyncio
import hashlib
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse

# ============================================================================
# 响应缓存
# ============================================================================


class ResponseCache:
    """带 TTL 与 LRU 淘汰的轻量缓存（进程内）"""

    def __init__(self, ttl: int = 300, max_entries: int = 256):
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.ttl = ttl
        self.max_entries = max_entries

    def get_cache_key(self, request: Request) -> str:
        key_str = f"{request.method}:{request.url.path}:{request.url.query}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _evict_expired(self) -> None:
        now = time.time()
        expired_keys = [k for k, (_, ts) in self.cache.items() if now - ts > self.ttl]
        for key in expired_keys:
            self.cache.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        self._evict_expired()
        if key in self.cache:
            value, ts = self.cache.pop(key)
            # 触碰一次，刷新到末尾
            self.cache[key] = (value, ts)
            return value
        return None

    def set(self, key: str, value: Any) -> None:
        self._evict_expired()
        if key in self.cache:
            self.cache.pop(key, None)
        self.cache[key] = (value, time.time())
        while len(self.cache) > self.max_entries:
            self.cache.popitem(last=False)

    def clear(self) -> None:
        self.cache.clear()


# 全局缓存实例，默认 60 秒 TTL + LRU 256
response_cache = ResponseCache(ttl=60, max_entries=256)


# ============================================================================
# 请求限流
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
        """检查当前请求是否被允许"""
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


# 全局限流器，具体速率在主程序中覆写
rate_limiter = RateLimiter(rate=100, per=60)


# ============================================================================
# 请求压缩（占位）
# ============================================================================


async def gzip_response_middleware(request: Request, call_next):
    """响应压缩示例（生产建议交由网关/Nginx 处理）"""
    response = await call_next(request)
    # 这里只保留占位，避免在应用层重复压缩
    return response


# ============================================================================
# 批量请求处理（占位）
# ============================================================================


class BatchRequestHandler:
    """批处理工具：收敛高频小请求到单次大调用"""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = []
        self.batch_task = None

    async def add_request(self, request_data):
        """将请求加入批处理队列"""
        future = asyncio.Future()
        self.pending_requests.append((request_data, future))

        if len(self.pending_requests) >= self.batch_size:
            await self._process_batch()
        elif self.batch_task is None:
            self.batch_task = asyncio.create_task(self._wait_and_process())

        return await future

    async def _wait_and_process(self):
        await asyncio.sleep(self.batch_timeout)
        await self._process_batch()

    async def _process_batch(self):
        if not self.pending_requests:
            return

        batch = self.pending_requests[:]
        self.pending_requests.clear()
        self.batch_task = None

        for request_data, future in batch:
            result = await self._process_single(request_data)
            future.set_result(result)

    async def _process_single(self, request_data):
        return {"processed": True, "data": request_data}


# ============================================================================
# 连接池（占位）
# ============================================================================


class ConnectionPool:
    """面向外部服务（如 LLM）的简单连接池示意"""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = []
        self.in_use = set()

    async def acquire(self):
        if self.connections:
            conn = self.connections.pop()
        else:
            conn = await self._create_connection()

        self.in_use.add(id(conn))
        return conn

    async def release(self, conn):
        if id(conn) in self.in_use:
            self.in_use.remove(id(conn))
            if len(self.connections) < self.max_connections:
                self.connections.append(conn)
            else:
                await self._close_connection(conn)

    async def _create_connection(self):
        return object()

    async def _close_connection(self, conn):
        # 资源清理占位
        pass


# ============================================================================
# 性能监控
# ============================================================================


class PerformanceMonitor:
    """聚合接口耗时与错误计数"""

    def __init__(self):
        self.metrics = {
            "endpoint_timings": {},
            "slow_requests": [],
            "error_count": 0,
        }

    def record_request(self, endpoint: str, duration: float, status_code: int, slow_threshold_ms: int = 1000):
        if endpoint not in self.metrics["endpoint_timings"]:
            self.metrics["endpoint_timings"][endpoint] = []
        self.metrics["endpoint_timings"][endpoint].append(duration)

        if duration > slow_threshold_ms:
            self.metrics["slow_requests"].append(
                {"endpoint": endpoint, "duration": duration, "timestamp": time.time()}
            )

        if status_code >= 400:
            self.metrics["error_count"] += 1

    def get_stats(self):
        stats = {}
        for endpoint, timings in self.metrics["endpoint_timings"].items():
            if timings:
                stats[endpoint] = {
                    "avg": sum(timings) / len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "count": len(timings),
                }

        return {
            "endpoint_stats": stats,
            "slow_requests_count": len(self.metrics["slow_requests"]),
            "error_count": self.metrics["error_count"],
        }


performance_monitor = PerformanceMonitor()

