#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理工具
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
import pickle

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "./cache", max_size: int = 1000, ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size
        self.ttl = ttl
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._memory_cache = {}
        self._cache_metadata = {}
        
        # 加载现有缓存
        self._load_cache()
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存键
        
        Args:
            key: 原始键
            
        Returns:
            缓存键
        """
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存文件路径
        """
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        cache_key = self._get_cache_key(key)
        
        # 检查内存缓存
        if cache_key in self._memory_cache:
            metadata = self._cache_metadata.get(cache_key, {})
            if time.time() - metadata.get('timestamp', 0) < self.ttl:
                return self._memory_cache[cache_key]
            else:
                # 过期，从内存中移除
                del self._memory_cache[cache_key]
                del self._cache_metadata[cache_key]
        
        # 检查文件缓存
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                
                # 检查是否过期
                if time.time() - data.get('timestamp', 0) < self.ttl:
                    # 加载到内存缓存
                    self._memory_cache[cache_key] = data['value']
                    self._cache_metadata[cache_key] = {
                        'timestamp': data['timestamp'],
                        'size': len(str(data['value']))
                    }
                    return data['value']
                else:
                    # 过期，删除文件
                    cache_path.unlink()
            except Exception as e:
                # 文件损坏，删除
                cache_path.unlink()
        
        return None
    
    def set(self, key: str, value: Any) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            
        Returns:
            是否设置成功
        """
        try:
            cache_key = self._get_cache_key(key)
            timestamp = time.time()
            
            # 检查缓存大小限制
            if len(self._memory_cache) >= self.max_size:
                self._evict_oldest()
            
            # 设置内存缓存
            self._memory_cache[cache_key] = value
            self._cache_metadata[cache_key] = {
                'timestamp': timestamp,
                'size': len(str(value))
            }
            
            # 保存到文件缓存
            cache_path = self._get_cache_path(cache_key)
            data = {
                'value': value,
                'timestamp': timestamp,
                'key': key
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            return True
            
        except Exception as e:
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            cache_key = self._get_cache_key(key)
            
            # 从内存缓存中删除
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                del self._cache_metadata[cache_key]
            
            # 删除文件缓存
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            
            return True
            
        except Exception as e:
            return False
    
    def clear(self) -> bool:
        """清空所有缓存
        
        Returns:
            是否清空成功
        """
        try:
            # 清空内存缓存
            self._memory_cache.clear()
            self._cache_metadata.clear()
            
            # 删除所有缓存文件
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            
            return True
            
        except Exception as e:
            return False
    
    def _evict_oldest(self):
        """驱逐最旧的缓存条目"""
        if not self._cache_metadata:
            return
        
        # 找到最旧的条目
        oldest_key = min(
            self._cache_metadata.keys(),
            key=lambda k: self._cache_metadata[k]['timestamp']
        )
        
        # 删除最旧的条目
        self.delete(oldest_key)
    
    def _load_cache(self):
        """加载现有缓存到内存"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    cache_key = self._get_cache_key(data['key'])
                    
                    # 检查是否过期
                    if time.time() - data['timestamp'] < self.ttl:
                        self._memory_cache[cache_key] = data['value']
                        self._cache_metadata[cache_key] = {
                            'timestamp': data['timestamp'],
                            'size': len(str(data['value']))
                        }
                    else:
                        # 过期，删除文件
                        cache_file.unlink()
                        
                except Exception as e:
                    # 文件损坏，删除
                    cache_file.unlink()
                    
        except Exception as e:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_size = sum(meta['size'] for meta in self._cache_metadata.values())
        
        return {
            'memory_entries': len(self._memory_cache),
            'total_size': total_size,
            'max_size': self.max_size,
            'ttl': self.ttl,
            'cache_dir': str(self.cache_dir)
        }
    
    def cleanup_expired(self) -> int:
        """清理过期缓存
        
        Returns:
            清理的条目数量
        """
        current_time = time.time()
        expired_keys = []
        
        # 检查内存缓存
        for cache_key, metadata in self._cache_metadata.items():
            if current_time - metadata['timestamp'] >= self.ttl:
                expired_keys.append(cache_key)
        
        # 删除过期条目
        for cache_key in expired_keys:
            self.delete(cache_key)
        
        return len(expired_keys)

# 全局缓存管理器实例
_global_cache_manager = None

def get_cache_manager(cache_dir: str = "./cache", max_size: int = 1000, ttl: int = 3600) -> CacheManager:
    """获取全局缓存管理器
    
    Args:
        cache_dir: 缓存目录
        max_size: 最大缓存条目数
        ttl: 缓存生存时间（秒）
        
    Returns:
        缓存管理器实例
    """
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(cache_dir, max_size, ttl)
    
    return _global_cache_manager 