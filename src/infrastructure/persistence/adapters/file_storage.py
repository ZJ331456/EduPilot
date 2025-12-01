#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件存储适配器
基于 JSON 文件的简单存储实现
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

from ..base import StorageAdapter


class FileStorageAdapter(StorageAdapter):
    """文件存储适配器
    
    使用 JSON 文件存储数据
    适用于开发和小规模部署
    """
    
    def __init__(self, base_dir: str = "data/storage"):
        """初始化文件存储
        
        Args:
            base_dir: 存储基础目录
        """
        self.base_dir = Path(base_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ensure_directory()
    
    def _ensure_directory(self):
        """确保存储目录存在"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """连接存储（文件存储无需连接）"""
        self._ensure_directory()
        self.logger.info(f"文件存储已初始化: {self.base_dir}")
    
    async def disconnect(self):
        """断开存储连接（文件存储无需断开）"""
        pass
    
    def _get_file_path(self, key: str) -> Path:
        """获取文件路径
        
        Args:
            key: 数据键
            
        Returns:
            Path: 文件路径
        """
        # 清理键名，避免路径问题
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_dir / f"{safe_key}.json"
    
    async def save_data(self, key: str, data: Dict[str, Any]) -> bool:
        """保存数据到文件
        
        Args:
            key: 数据键
            data: 数据内容
            
        Returns:
            bool: 是否保存成功
        """
        try:
            file_path = self._get_file_path(key)
            
            # 添加元数据
            save_data = {
                "key": key,
                "data": data,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # 异步写入文件
            await asyncio.to_thread(
                self._write_json,
                file_path,
                save_data
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {key}, 错误: {e}")
            return False
    
    def _write_json(self, file_path: Path, data: Dict[str, Any]):
        """写入 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """从文件加载数据
        
        Args:
            key: 数据键
            
        Returns:
            Optional[Dict]: 数据内容，不存在返回 None
        """
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
            
            # 异步读取文件
            saved_data = await asyncio.to_thread(
                self._read_json,
                file_path
            )
            
            return saved_data.get("data")
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {key}, 错误: {e}")
            return None
    
    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """读取 JSON 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def delete_data(self, key: str) -> bool:
        """删除数据文件
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            file_path = self._get_file_path(key)
            
            if file_path.exists():
                await asyncio.to_thread(file_path.unlink)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"删除数据失败: {key}, 错误: {e}")
            return False
    
    async def exists_data(self, key: str) -> bool:
        """检查数据是否存在
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否存在
        """
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """列出所有键
        
        Args:
            pattern: 键名模式（简单的前缀匹配）
            
        Returns:
            List[str]: 键列表
        """
        try:
            all_files = self.base_dir.glob("*.json")
            keys = [f.stem for f in all_files]
            
            if pattern:
                keys = [k for k in keys if k.startswith(pattern)]
            
            return keys
            
        except Exception as e:
            self.logger.error(f"列出键失败: {e}")
            return []

