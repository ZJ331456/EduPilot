#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的多智能体对话系统
演示苏格拉底式教学的完整流程
"""

import asyncio
import logging
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.multi_agent_system import MultiAgentSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def simulate_conversation():
    """模拟一个完整的对话流程"""
    
    # 初始化多智能体系统
    config = {
        "enable_enhanced_mode": True,
        "max_conversation_rounds": 8,
        "target_understanding_level": "good_understanding"
    }
    
    system = MultiAgentSystem(config)
    
    print("🤖 智能学习助手已启动！")
    print("=" * 50)
    
    # 模拟对话场景
    conversations = [
        {
            "query": "什么是三国演义？",
            "responses": [
                "三国演义是一本书",
                "讲的是三国时期的故事，有刘备、关羽、张飞这些人物",
                "它体现了忠义仁德的传统价值观，通过战争和政治斗争展现了人性的复杂",
                "我觉得三国演义不仅是历史小说，也是中国文化的重要载体"
            ]
        }
    ]
    
    for conversation in conversations:
        session_id = None
        
        print(f"👤 用户: {conversation['query']}")
        print("-" * 30)
        
        # 处理初始查询
        result = await system.process_query(conversation['query'])
        session_id = result.get('session_id')
        
        print(f"🤖 助手: {result.get('response', '抱歉，处理失败')}")
        print(f"📊 状态: 轮次 {result.get('round', 0)}, 阶段 {result.get('conversation_stage', 'unknown')}")
        print()
        
        # 如果需要用户回应，继续对话
        if result.get('waiting_for_user', False) and not result.get('conversation_complete', False):
            for i, user_response in enumerate(conversation['responses']):
                print(f"👤 用户: {user_response}")
                print("-" * 30)
                
                # 处理用户回应
                result = await system.process_query(user_response, session_id)
                
                print(f"🤖 助手: {result.get('response', '抱歉，处理失败')}")
                
                if result.get('conversation_complete', False):
                    print(f"✅ 对话完成！总共进行了 {result.get('total_rounds', 0)} 轮")
                    if result.get('conversation_summary'):
                        summary = result['conversation_summary']
                        print(f"📈 对话摘要: 理解水平 {summary.get('understanding_level', 'unknown')}")
                    break
                else:
                    print(f"📊 状态: 轮次 {result.get('round', 0)}, 阶段 {result.get('conversation_stage', 'unknown')}")
                
                print()
        
        print("=" * 50)

async def interactive_mode():
    """交互模式"""
    
    # 初始化系统
    config = {
        "enable_enhanced_mode": True,
        "max_conversation_rounds": 10,
        "target_understanding_level": "good_understanding"
    }
    
    system = MultiAgentSystem(config)
    session_id = None
    
    print("🤖 智能学习助手 - 交互模式")
    print("输入 'quit' 退出，输入 'new' 开始新对话")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if user_input.lower() in ['new', '新对话']:
                session_id = None
                print("🆕 开始新对话")
                continue
            
            if not user_input:
                print("请输入您的问题或回答")
                continue
            
            # 处理用户输入
            result = await system.process_query(user_input, session_id)
            
            if not session_id:
                session_id = result.get('session_id')
            
            print(f"\n🤖 助手: {result.get('response', '抱歉，处理失败')}")
            
            # 显示状态信息
            if result.get('conversation_stage'):
                stage_map = {
                    'initial_query': '初始查询',
                    'socratic_questioning': '苏格拉底式提问',
                    'understanding_check': '理解检查',
                    'deeper_exploration': '深入探索',
                    'comprehension_validation': '理解验证',
                    'conclusion': '结论'
                }
                stage_name = stage_map.get(result['conversation_stage'], result['conversation_stage'])
                print(f"📊 当前阶段: {stage_name}")
            
            if result.get('conversation_complete', False):
                print("✅ 对话完成！")
                if result.get('conversation_summary'):
                    summary = result['conversation_summary']
                    print(f"📈 最终理解水平: {summary.get('understanding_level', 'unknown')}")
                    print(f"📊 总轮次: {summary.get('total_rounds', 0)}")
                session_id = None  # 重置会话
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

def main():
    """主函数"""
    print("选择模式:")
    print("1. 模拟对话")
    print("2. 交互模式")
    
    try:
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "1":
            asyncio.run(simulate_conversation())
        elif choice == "2":
            asyncio.run(interactive_mode())
        else:
            print("无效选择")
    
    except KeyboardInterrupt:
        print("\n程序退出")

if __name__ == "__main__":
    main()