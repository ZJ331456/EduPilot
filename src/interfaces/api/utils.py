#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 工具函数
包含重试、超时、并发控制等
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, TypeVar
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')

# ============================================================================
# 异步重试装饰器
# ============================================================================

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    异步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增因子
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_attempts}): {str(e)}, "
                            f"{current_delay}秒后重试..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数")
            
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================================
# 超时控制
# ============================================================================

def with_timeout(seconds: float):
    """
    超时装饰器
    
    Args:
        seconds: 超时时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} 超时 ({seconds}秒)")
                raise TimeoutError(f"操作超时: {func.__name__}")
        
        return wrapper
    return decorator


# ============================================================================
# 并发控制
# ============================================================================

class ConcurrencyLimiter:
    """并发限制器"""
    
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run(self, coro):
        """在并发限制下运行协程"""
        async with self.semaphore:
            return await coro


# 全局并发限制器
workflow_limiter = ConcurrencyLimiter(max_concurrent=10)  # 最多10个并发工作流


# ============================================================================
# 批量操作优化
# ============================================================================

async def batch_process(
    items: list,
    processor: Callable,
    batch_size: int = 10,
    max_concurrent: int = 5
):
    """
    批量处理项目
    
    Args:
        items: 待处理项目列表
        processor: 处理函数（async）
        batch_size: 批次大小
        max_concurrent: 最大并发数
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(item):
        async with semaphore:
            return await processor(item)
    
    # 分批处理
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_limit(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)
    
    return results


# ============================================================================
# 缓存装饰器
# ============================================================================

class AsyncLRUCache:
    """异步 LRU 缓存"""
    
    def __init__(self, maxsize: int = 128, ttl: Optional[int] = None):
        self.cache = {}
        self.maxsize = maxsize
        self.ttl = ttl  # 过期时间（秒）
        self.access_order = []
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key = self._make_key(func.__name__, args, kwargs)
            
            # 检查缓存
            if key in self.cache:
                value, timestamp = self.cache[key]
                # 检查是否过期
                if self.ttl is None or (datetime.now() - timestamp).seconds < self.ttl:
                    # 更新访问顺序
                    self.access_order.remove(key)
                    self.access_order.append(key)
                    return value
                else:
                    del self.cache[key]
                    self.access_order.remove(key)
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            self.cache[key] = (result, datetime.now())
            self.access_order.append(key)
            
            # 检查缓存大小
            while len(self.cache) > self.maxsize:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            return result
        
        return wrapper
    
    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        key_dict = {
            "func": func_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()


# ============================================================================
# 响应数据优化
# ============================================================================

def compress_response_data(data: dict, max_length: int = 1000) -> dict:
    """
    压缩响应数据（截断过长的字符串）
    
    Args:
        data: 响应数据
        max_length: 字符串最大长度
    """
    if isinstance(data, dict):
        return {k: compress_response_data(v, max_length) for k, v in data.items()}
    elif isinstance(data, list):
        return [compress_response_data(item, max_length) for item in data]
    elif isinstance(data, str) and len(data) > max_length:
        return data[:max_length] + "... (truncated)"
    else:
        return data


# ============================================================================
# 健康检查优化
# ============================================================================

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = None
        self.last_result = None
        self.cache_ttl = 10  # 缓存10秒
    
    def register_check(self, name: str, check_func: Callable):
        """注册健康检查"""
        self.checks[name] = check_func
    
    async def run_checks(self, use_cache: bool = True) -> dict:
        """运行所有健康检查"""
        # 检查缓存
        if use_cache and self.last_result and self.last_check_time:
            if (datetime.now() - self.last_check_time).seconds < self.cache_ttl:
                return self.last_result
        
        results = {}
        all_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "checked_at": datetime.now().isoformat()
                }
                
                if not result:
                    all_healthy = False
                    
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "checked_at": datetime.now().isoformat()
                }
                all_healthy = False
        
        result = {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "checks": results
        }
        
        # 更新缓存
        self.last_result = result
        self.last_check_time = datetime.now()
        
        return result


# 全局健康检查器
health_checker = HealthChecker()


# ============================================================================
# 请求上下文管理
# ============================================================================

class RequestContext:
    """请求上下文管理器"""
    
    def __init__(self):
        self.context_var = {}
    
    def set(self, key: str, value: Any):
        """设置上下文变量"""
        self.context_var[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文变量"""
        return self.context_var.get(key, default)
    
    def clear(self):
        """清空上下文"""
        self.context_var.clear()


# 全局请求上下文
request_context = RequestContext()


# ============================================================================
# 数据验证优化
# ============================================================================

def validate_and_sanitize(data: dict, schema: dict) -> dict:
    """
    验证和清理数据
    
    Args:
        data: 输入数据
        schema: 验证模式
    """
    cleaned_data = {}
    
    for key, rules in schema.items():
        if key not in data:
            if rules.get("required", False):
                raise ValueError(f"缺少必需字段: {key}")
            continue
        
        value = data[key]
        
        # 类型检查
        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            raise TypeError(f"字段 {key} 类型错误，期望 {expected_type}")
        
        # 长度检查
        if "max_length" in rules and isinstance(value, str):
            if len(value) > rules["max_length"]:
                value = value[:rules["max_length"]]
        
        # 范围检查
        if "min_value" in rules and value < rules["min_value"]:
            raise ValueError(f"字段 {key} 值过小")
        if "max_value" in rules and value > rules["max_value"]:
            raise ValueError(f"字段 {key} 值过大")
        
        cleaned_data[key] = value
    
    return cleaned_data

