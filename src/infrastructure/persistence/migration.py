#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化层迁移工具
从 LocalStorageManager 迁移到 Repository 模式
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.core.agents.memory_manager.storage import LocalStorageManager, StorageConfig
from src.infrastructure.persistence import (
    FileStorageAdapter,
    UserProfileRepository,
    SessionRepository,
    LearningRecordRepository
)
from src.infrastructure.persistence.repositories.user_profile_repository import UserProfile
from src.infrastructure.persistence.repositories.session_repository import Session
from src.infrastructure.persistence.repositories.learning_record_repository import LearningRecord


class PersistenceMigrator:
    """持久化数据迁移工具
    
    将数据从 LocalStorageManager（简单文件存储）
    迁移到 Repository 模式（支持多后端）
    """
    
    def __init__(self, old_base_dir: str = "data/memory_data", 
                 new_base_dir: str = "data/storage"):
        """初始化迁移工具
        
        Args:
            old_base_dir: 旧的LocalStorageManager数据目录
            new_base_dir: 新的Repository层数据目录
        """
        # 旧存储
        self.old_storage = LocalStorageManager(
            StorageConfig.create_default(old_base_dir)
        )
        
        # 新存储
        self.new_adapter = FileStorageAdapter(base_dir=new_base_dir)
        
        self.stats = {
            "user_profiles": 0,
            "sessions": 0,
            "learning_records": 0,
            "errors": []
        }
        
    async def migrate_all(self, dry_run: bool = False):
        """执行完整迁移
        
        Args:
            dry_run: 是否为演习模式（不实际写入）
        """
        print("=" * 60)
        print("🚀 持久化层迁移工具")
        print("=" * 60)
        
        if dry_run:
            print("⚠️  演习模式：不会实际写入数据")
        
        print(f"\n📂 源目录: {self.old_storage.config.base_dir}")
        print(f"📂 目标目录: {self.new_adapter.base_dir}")
        print()
        
        # 连接新存储
        await self.new_adapter.connect()
        
        # 创建仓储
        user_repo = UserProfileRepository(self.new_adapter)
        session_repo = SessionRepository(self.new_adapter)
        learning_repo = LearningRecordRepository(self.new_adapter)
        
        # 迁移用户画像
        print("📊 迁移用户画像...")
        await self._migrate_user_profiles(user_repo, dry_run)
        
        # 迁移会话记忆
        print("\n💬 迁移会话记忆...")
        await self._migrate_sessions(session_repo, dry_run)
        
        # 迁移学习记录
        print("\n📚 迁移学习记录...")
        await self._migrate_learning_records(learning_repo, dry_run)
        
        # 关闭连接
        await self.new_adapter.disconnect()
        
        # 显示统计
        self._print_statistics()
        
    async def _migrate_user_profiles(self, repo: UserProfileRepository, dry_run: bool = False):
        """迁移用户画像"""
        user_ids = self.old_storage.list_user_profiles()
        print(f"   发现 {len(user_ids)} 个用户画像")
        
        for user_id in user_ids:
            try:
                old_data = self.old_storage.load_user_profile(user_id)
                if not old_data:
                    continue
                
                # 转换为新格式
                profile = UserProfile(
                    id=user_id,
                    user_id=user_id,
                    triples=old_data.get("knowledge_graph", {}).get("triples", []),
                    topics=old_data.get("knowledge_graph", {}).get("topics", []),
                    entities=old_data.get("knowledge_graph", {}).get("entities", []),
                    relations=old_data.get("knowledge_graph", {}).get("relations", []),
                    recent_queries=old_data.get("interaction_patterns", {}).get("recent_queries", []),
                    learning_style=old_data.get("learning_patterns", {}).get("style", ""),
                    knowledge_level=old_data.get("learning_patterns", {}).get("level", "中级"),
                    total_sessions=old_data.get("interaction_patterns", {}).get("total_sessions", 0),
                    emotions=[],
                    metadata={
                        "migrated_from": "LocalStorageManager",
                        "migrated_at": datetime.now().isoformat(),
                        "original_data": old_data
                    }
                )
                
                if not dry_run:
                    await repo.save(profile)
                
                print(f"   ✓ 迁移用户: {user_id}")
                self.stats["user_profiles"] += 1
                
            except Exception as e:
                error_msg = f"迁移用户 {user_id} 失败: {str(e)}"
                print(f"   ✗ {error_msg}")
                self.stats["errors"].append(error_msg)
    
    async def _migrate_sessions(self, repo: SessionRepository, dry_run: bool = False):
        """迁移会话记忆"""
        session_dir = self.old_storage.config.session_memory_dir
        if not session_dir.exists():
            print("   ⚠️  会话目录不存在")
            return
            
        session_files = list(session_dir.glob("session_*.json"))
        print(f"   发现 {len(session_files)} 个会话记录")
        
        for file_path in session_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                
                data = old_data.get("data", {})
                
                # 转换为新格式
                session = Session(
                    id=data.get("session_id", file_path.stem),
                    session_id=data.get("session_id", ""),
                    user_id=data.get("user_id", ""),
                    query=data.get("query", ""),
                    dialogue_history=data.get("dialogue_history", []),
                    query_analysis=data.get("query_analysis", {}),
                    knowledge_retrieval=data.get("knowledge_retrieval", {}),
                    socratic_questions=data.get("socratic_dialogue", {}).get("questions", []),
                    user_responses=data.get("socratic_dialogue", {}).get("user_responses", []),
                    conversation_round=data.get("socratic_dialogue", {}).get("total_rounds", 0),
                    metadata={
                        "migrated_from": "LocalStorageManager",
                        "migrated_at": datetime.now().isoformat(),
                        "source_file": file_path.name
                    }
                )
                
                if not dry_run:
                    await repo.save(session)
                
                print(f"   ✓ 迁移会话: {session.session_id[:30]}...")
                self.stats["sessions"] += 1
                
            except Exception as e:
                error_msg = f"迁移会话 {file_path.name} 失败: {str(e)}"
                print(f"   ✗ {error_msg}")
                self.stats["errors"].append(error_msg)
    
    async def _migrate_learning_records(self, repo: LearningRecordRepository, dry_run: bool = False):
        """迁移学习记录"""
        learning_dir = self.old_storage.config.learning_records_dir
        if not learning_dir.exists():
            print("   ⚠️  学习记录目录不存在")
            return
            
        record_files = list(learning_dir.glob("learning_*.json"))
        print(f"   发现 {len(record_files)} 个学习记录")
        
        for file_path in record_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                
                data = old_data.get("data", {})
                
                # 转换为新格式
                record = LearningRecord(
                    id=f"record_{file_path.stem}",
                    user_id=old_data.get("user_id", ""),
                    session_id=data.get("session_id", ""),
                    query=data.get("query", ""),
                    concepts_learned=data.get("concepts", []),
                    skills_improved=data.get("skills", []),
                    understanding_level=data.get("understanding_level", ""),
                    knowledge_gaps=data.get("knowledge_gaps", []),
                    learning_path=data.get("learning_path", []),
                    metadata={
                        "migrated_from": "LocalStorageManager",
                        "migrated_at": datetime.now().isoformat(),
                        "source_file": file_path.name
                    }
                )
                
                if not dry_run:
                    await repo.save(record)
                
                print(f"   ✓ 迁移记录: {record.id}")
                self.stats["learning_records"] += 1
                
            except Exception as e:
                error_msg = f"迁移记录 {file_path.name} 失败: {str(e)}"
                print(f"   ✗ {error_msg}")
                self.stats["errors"].append(error_msg)
    
    def _print_statistics(self):
        """打印迁移统计"""
        print("\n" + "=" * 60)
        print("📈 迁移统计")
        print("=" * 60)
        print(f"✅ 用户画像: {self.stats['user_profiles']} 个")
        print(f"✅ 会话记忆: {self.stats['sessions']} 个")
        print(f"✅ 学习记录: {self.stats['learning_records']} 个")
        
        if self.stats['errors']:
            print(f"\n❌ 错误: {len(self.stats['errors'])} 个")
            for error in self.stats['errors'][:5]:  # 只显示前5个
                print(f"   • {error}")
            if len(self.stats['errors']) > 5:
                print(f"   ... 还有 {len(self.stats['errors']) - 5} 个错误")
        else:
            print("\n🎉 迁移完成！无错误")


async def main():
    """主函数"""
    import sys
    
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    migrator = PersistenceMigrator()
    await migrator.migrate_all(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())

