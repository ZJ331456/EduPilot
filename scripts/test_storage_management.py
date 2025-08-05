#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储管理功能测试脚本
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.conversation_storage_manager import conversation_storage_manager, StorageType


async def test_storage_management():
    """测试存储管理功能"""
    print("=== 存储管理功能测试 ===")
    
    try:
        # 1. 初始化存储管理器
        print("\n1. 初始化存储管理器...")
        await conversation_storage_manager.initialize()
        print("✓ 存储管理器初始化成功")
        
        # 2. 测试创建会话
        print("\n2. 测试创建会话...")
        session_id = "test_session_001"
        user_id = "test_user_001"
        
        success = await conversation_storage_manager.create_session(session_id, user_id)
        if success:
            print("✓ 会话创建成功")
        else:
            print("✗ 会话创建失败")
        
        # 3. 测试保存对话轮次
        print("\n3. 测试保存对话轮次...")
        metadata = {
            'query_type': 'normal',
            'stage': 'initial',
            'confidence_score': 0.8,
            'topics': ['测试', '存储管理']
        }
        
        success = await conversation_storage_manager.save_conversation_turn(
            session_id=session_id,
            user_input="这是一个测试查询",
            system_response="这是一个测试响应",
            user_id=user_id,
            metadata=metadata
        )
        if success:
            print("✓ 对话轮次保存成功")
        else:
            print("✗ 对话轮次保存失败")
        
        # 4. 测试获取存储统计
        print("\n4. 测试获取存储统计...")
        stats = await conversation_storage_manager.get_storage_stats()
        print(f"✓ 存储统计获取成功:")
        print(f"   - 存储类型: {stats.get('storage_type')}")
        print(f"   - 本地文件统计: {stats.get('local_files', {})}")
        print(f"   - MongoDB状态: {stats.get('mongodb', {})}")
        
        # 5. 测试获取用户会话
        print("\n5. 测试获取用户会话...")
        sessions = await conversation_storage_manager.get_user_sessions(user_id, limit=5)
        print(f"✓ 获取到 {len(sessions)} 个用户会话")
        
        # 6. 测试获取会话历史
        print("\n6. 测试获取会话历史...")
        session_history = await conversation_storage_manager.get_session_history(session_id)
        if session_history:
            print("✓ 会话历史获取成功")
        else:
            print("✗ 会话历史获取失败")
        
        # 7. 测试导出用户数据
        print("\n7. 测试导出用户数据...")
        export_data = await conversation_storage_manager.export_user_data(user_id)
        if "error" not in export_data:
            print("✓ 用户数据导出成功")
            summary = export_data.get("summary", {})
            print(f"   - 总会话数: {summary.get('total_sessions', 0)}")
            print(f"   - 总轮次数: {summary.get('total_turns', 0)}")
        else:
            print("✗ 用户数据导出失败")
        
        # 8. 测试数据备份
        print("\n8. 测试数据备份...")
        backup_path = await conversation_storage_manager.backup_data()
        print(f"✓ 数据备份成功: {backup_path}")
        
        # 9. 测试结束会话
        print("\n9. 测试结束会话...")
        metrics = {
            'final_understanding_level': 'good',
            'session_summary': '测试会话完成',
            'success_score': 0.9
        }
        success = await conversation_storage_manager.end_session(session_id, metrics)
        if success:
            print("✓ 会话结束成功")
        else:
            print("✗ 会话结束失败")
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


async def test_cleanup_function():
    """测试数据清理功能"""
    print("\n=== 数据清理功能测试 ===")
    
    try:
        # 测试清理30天前的数据
        print("清理30天前的数据...")
        await conversation_storage_manager.cleanup_old_sessions(days=30)
        print("✓ 数据清理完成")
        
    except Exception as e:
        print(f"✗ 数据清理失败: {e}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_storage_management())
    asyncio.run(test_cleanup_function()) 