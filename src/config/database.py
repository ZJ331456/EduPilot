#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置和连接管理
"""

import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# 使用统一的日志配置
from .logging_config import get_logger, LoggerNames

logger = get_logger(LoggerNames.DATABASE)

class DatabaseConfig:
    """数据库配置"""
    
    def __init__(self):
        # MongoDB连接配置
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "hw_agent_db")
        
        # 集合名称
        self.conversations_collection = "conversations"
        self.user_profiles_collection = "user_profiles"
        self.knowledge_queries_collection = "knowledge_queries"
        self.system_metrics_collection = "system_metrics"
        
        # 连接池配置
        self.min_pool_size = int(os.getenv("DB_MIN_POOL_SIZE", "10"))
        self.max_pool_size = int(os.getenv("DB_MAX_POOL_SIZE", "100"))
        self.max_idle_time_ms = int(os.getenv("DB_MAX_IDLE_TIME_MS", "30000"))

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        
    async def connect(self):
        """连接数据库"""
        try:
            self.client = AsyncIOMotorClient(
                self.config.mongodb_url,
                minPoolSize=self.config.min_pool_size,
                maxPoolSize=self.config.max_pool_size,
                maxIdleTimeMS=self.config.max_idle_time_ms
            )
            
            # 测试连接
            await self.client.admin.command('ping')
            
            # 获取数据库
            self.database = self.client[self.config.database_name]
            
            logger.info(f"Successfully connected to MongoDB: {self.config.database_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def initialize_beanie(self, document_models: list):
        """初始化Beanie ODM"""
        try:
            await init_beanie(
                database=self.database,
                document_models=document_models
            )
            logger.info("Beanie ODM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Beanie: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def get_collection(self, collection_name: str):
        """获取集合"""
        if self.database is None:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]

# 全局数据库管理器实例
db_manager = DatabaseManager()

async def get_database():
    """获取数据库实例"""
    if db_manager.database is None:
        await db_manager.connect()
    return db_manager.database
