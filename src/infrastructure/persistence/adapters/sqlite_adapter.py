#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 存储适配器
基于 SQLite 数据库的存储实现
"""

import logging
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from ..base import StorageAdapter


class SQLiteAdapter(StorageAdapter):
    """SQLite 存储适配器
    
    使用 SQLite 数据库存储数据
    提供结构化存储和查询能力
    """
    
    def __init__(self, db_path: str = "data/edupilot.db"):
        """初始化 SQLite 存储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._conn: Optional[sqlite3.Connection] = None
        
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """连接到 SQLite 数据库"""
        try:
            self._conn = await asyncio.to_thread(
                sqlite3.connect,
                str(self.db_path),
                check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            
            # 创建表
            await self._create_tables()
            
            self.logger.info(f"SQLite 数据库已连接: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"连接数据库失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self._conn:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
            self.logger.info("SQLite 数据库已断开")
    
    async def _create_tables(self):
        """创建数据表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS storage (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        
        await self._execute(create_table_sql)
        await self._commit()
    
    async def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行 SQL 语句"""
        if not self._conn:
            raise RuntimeError("数据库未连接")
        
        return await asyncio.to_thread(
            self._conn.execute,
            sql,
            params
        )
    
    async def _commit(self):
        """提交事务"""
        if self._conn:
            await asyncio.to_thread(self._conn.commit)
    
    async def save_data(self, key: str, data: Dict[str, Any]) -> bool:
        """保存数据到 SQLite
        
        Args:
            key: 数据键
            data: 数据内容
            
        Returns:
            bool: 是否保存成功
        """
        try:
            now = datetime.now().isoformat()
            data_json = json.dumps(data, ensure_ascii=False)
            
            # 使用 INSERT OR REPLACE
            sql = """
            INSERT OR REPLACE INTO storage (key, data, created_at, updated_at)
            VALUES (?, ?, 
                COALESCE((SELECT created_at FROM storage WHERE key = ?), ?),
                ?)
            """
            
            await self._execute(sql, (key, data_json, key, now, now))
            await self._commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {key}, 错误: {e}")
            return False
    
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """从 SQLite 加载数据
        
        Args:
            key: 数据键
            
        Returns:
            Optional[Dict]: 数据内容，不存在返回 None
        """
        try:
            sql = "SELECT data FROM storage WHERE key = ?"
            cursor = await self._execute(sql, (key,))
            row = await asyncio.to_thread(cursor.fetchone)
            
            if row:
                return json.loads(row[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {key}, 错误: {e}")
            return None
    
    async def delete_data(self, key: str) -> bool:
        """删除数据
        
        Args:
            key: 数据键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            sql = "DELETE FROM storage WHERE key = ?"
            await self._execute(sql, (key,))
            await self._commit()
            
            return True
            
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
        try:
            sql = "SELECT 1 FROM storage WHERE key = ? LIMIT 1"
            cursor = await self._execute(sql, (key,))
            row = await asyncio.to_thread(cursor.fetchone)
            
            return row is not None
            
        except Exception as e:
            self.logger.error(f"检查数据存在性失败: {key}, 错误: {e}")
            return False
    
    async def list_keys(self, pattern: Optional[str] = None) -> List[str]:
        """列出所有键
        
        Args:
            pattern: 键名模式（SQL LIKE 模式）
            
        Returns:
            List[str]: 键列表
        """
        try:
            if pattern:
                sql = "SELECT key FROM storage WHERE key LIKE ?"
                cursor = await self._execute(sql, (f"{pattern}%",))
            else:
                sql = "SELECT key FROM storage"
                cursor = await self._execute(sql)
            
            rows = await asyncio.to_thread(cursor.fetchall)
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"列出键失败: {e}")
            return []

