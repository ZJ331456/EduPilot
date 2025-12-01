#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理器使用示例
演示MemoryManagerAgent的核心功能
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from domain.agents.memory_manager import MemoryManagerAgent
from infrastructure.utils import AgentState


async def demo_basic_usage():
    """基本使用演示"""
    print("\n" + "="*60)
    print("示例 1: 基本使用")
    print("="*60)
    
    # 创建记忆管理器
    memory_agent = MemoryManagerAgent()
    
    # 创建测试状态
    state = AgentState(
        session_id="demo_session_001",
        user_query="我叫张三，我喜欢编程和阅读，我擅长Python和机器学习，我想要深入学习深度学习",
        user_responses=[
            "是的，我对AI很感兴趣",
            "我已经学过一些基础的机器学习算法",
            "我想了解更多关于神经网络的知识"
        ]
    )
    
    # 设置用户ID
    state.metadata['user_id'] = 'demo_user_001'
    
    # 模拟一些检索结果
    state.retrieved_knowledge = {
        'results': [
            {'content': '深度学习是机器学习的一个分支...', 'relevance_score': 0.89},
            {'content': 'Python是深度学习最常用的编程语言...', 'relevance_score': 0.82},
            {'content': '神经网络的基本原理...', 'relevance_score': 0.78}
        ],
        'successful_sources': ['知识库A', '知识库B', '知识库C']
    }
    
    # 模拟执行结果
    state.execution_result = {
        'execution_summary': {
            'success_rate': 0.85,
            'total_actions': 6,
            'successful_actions': 5
        }
    }
    
    # 模拟苏格拉底问题
    state.socratic_questions = [
        "你为什么对深度学习感兴趣？",
        "你认为深度学习和传统机器学习的主要区别是什么？",
        "你打算如何开始学习神经网络？"
    ]
    
    state.query_type = "explanation"
    state.interpretation = {'keywords': ['深度学习', 'Python', '神经网络']}
    
    # 执行记忆管理
    print("\n正在执行记忆管理...")
    result = await memory_agent.execute(state)
    
    # 显示结果
    memory_analysis = result.metadata['memory_analysis']
    
    print(f"\n✓ 执行状态: {result.status}")
    print("\n【交互分析】")
    print(f"  - 质量分数: {memory_analysis['interaction']['quality_score']:.2f}")
    print(f"  - 参与度: {memory_analysis['interaction']['engagement_level']:.2f}")
    print(f"  - 学习价值: {memory_analysis['interaction']['learning_value']:.2f}")
    print(f"  - 知识覆盖度: {memory_analysis['interaction']['knowledge_coverage']:.2f}")
    print(f"  - 响应效果: {memory_analysis['interaction']['response_effectiveness']:.2f}")
    
    print("\n【用户画像更新】")
    print(f"  - 新增三元组: {len(memory_analysis['profile_update']['triples'])}")
    for triple in memory_analysis['profile_update']['triples']:
        print(f"    • {triple['subject']} - {triple['predicate']} - {triple['object']}")
    
    print(f"\n  - 主要情感: {memory_analysis['profile_update']['emotions']['primary_emotion']}")
    print(f"  - 情感置信度: {memory_analysis['profile_update']['emotions']['confidence']:.2f}")
    
    print(f"\n  - 学习模式数量: {len(memory_analysis['profile_update']['learning_patterns'])}")
    for pattern in memory_analysis['profile_update']['learning_patterns']:
        print(f"    • {pattern['pattern']}: {pattern['score']} (置信度: {pattern['confidence']:.2f})")
    
    print("\n【学习反馈】")
    feedback = memory_analysis['learning_feedback']
    print(f"  - 总体评分: {feedback['overall_score']:.2f}")
    
    if feedback['strengths']:
        print(f"\n  优势:")
        for strength in feedback['strengths']:
            print(f"    ✓ {strength}")
    
    if feedback['areas_for_improvement']:
        print(f"\n  改进领域:")
        for area in feedback['areas_for_improvement']:
            print(f"    → {area}")
    
    if feedback['recommendations']:
        print(f"\n  建议:")
        for rec in feedback['recommendations']:
            print(f"    💡 {rec}")
    
    print("\n【知识缺口】")
    gaps = memory_analysis['knowledge_gaps']
    print(f"  - 识别缺口数量: {len(gaps)}")
    for gap in gaps:
        print(f"\n  • {gap['type']}")
        print(f"    描述: {gap['description']}")
        print(f"    严重程度: {gap['severity']}")
        print(f"    优先级: {gap['priority']:.2f}")
        if gap['suggestions']:
            print(f"    建议:")
            for suggestion in gap['suggestions']:
                print(f"      - {suggestion}")


async def demo_user_profile_retrieval():
    """用户画像检索演示"""
    print("\n" + "="*60)
    print("示例 2: 用户画像检索")
    print("="*60)
    
    memory_agent = MemoryManagerAgent()
    
    # 获取用户画像
    user_id = 'demo_user_001'
    profile = memory_agent.get_user_profile(user_id)
    
    if profile:
        print(f"\n✓ 成功加载用户画像: {user_id}")
        print(f"\n  - 创建时间: {profile.get('created_at', 'N/A')}")
        print(f"  - 更新时间: {profile.get('updated_at', 'N/A')}")
        print(f"  - 三元组数量: {len(profile.get('triples', []))}")
        print(f"  - 情感记录数: {len(profile.get('emotions', []))}")
        print(f"  - 学习模式数: {len(profile.get('learning_patterns', []))}")
        print(f"  - 洞察数量: {len(profile.get('insights', []))}")
        
        # 显示最新的洞察
        insights = profile.get('insights', [])
        if insights:
            print("\n  最新洞察:")
            for insight in insights[-3:]:
                print(f"    • [{insight['type']}] {insight['description']}")
    else:
        print(f"\n✗ 用户画像不存在: {user_id}")


def demo_memory_statistics():
    """记忆统计演示"""
    print("\n" + "="*60)
    print("示例 3: 记忆统计")
    print("="*60)
    
    memory_agent = MemoryManagerAgent()
    
    # 获取统计信息
    stats = memory_agent.get_memory_statistics()
    
    print("\n【记忆统计】")
    print(f"  - 缓存大小: {stats['cache_size']} 个用户")
    print(f"  - 实体数量: {stats['entity_count']} 个")
    print(f"  - 三元组数量: {stats['triples_count']} 个")
    
    print("\n【存储统计】")
    storage_stats = stats['storage_stats']
    print(f"  - 用户画像数: {storage_stats.get('user_profiles_count', 0)}")
    print(f"  - 会话记录数: {storage_stats.get('session_memories_count', 0)}")
    print(f"  - 学习记录数: {storage_stats.get('learning_records_count', 0)}")
    print(f"  - 总存储大小: {storage_stats.get('total_size_mb', 0)} MB")


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("记忆管理器 (MemoryManagerAgent) 使用示例")
    print("="*70)
    
    try:
        # 示例1: 基本使用
        await demo_basic_usage()
        
        # 示例2: 用户画像检索
        await demo_user_profile_retrieval()
        
        # 示例3: 记忆统计
        demo_memory_statistics()
        
        print("\n" + "="*70)
        print("所有示例运行完成！")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

