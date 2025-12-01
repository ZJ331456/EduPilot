#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
苏格拉底引导Agent示例（MARS优化版）
展示如何使用新版本的SocraticGuideAgent
"""

import asyncio
import logging
from datetime import datetime

from infrastructure.utils import AgentState, QueryType, ConversationStage, UnderstandingLevel
from domain.agents.socratic_guide import SocraticGuideAgent


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def demo_basic_usage():
    """示例1：基本用法"""
    print("\n" + "="*60)
    print("示例1：基本用法")
    print("="*60)
    
    # 创建Agent（使用默认配置）
    agent = SocraticGuideAgent()
    
    # 创建初始状态
    state = AgentState(
        user_id="demo_user",
        session_id="demo_session_001",
        user_query="什么是光合作用？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        timestamp=datetime.now()
    )
    
    # 生成苏格拉底式问题
    print(f"\n📝 用户查询: {state.user_query}")
    result_state = await agent.execute(state)
    
    if result_state.socratic_question:
        print(f"🤔 苏格拉底式问题: {result_state.socratic_question}")
    else:
        print("⚠️ 问题生成失败")


async def demo_conversation_flow():
    """示例2：完整对话流程"""
    print("\n" + "="*60)
    print("示例2：完整对话流程")
    print("="*60)
    
    # 创建Agent
    agent = SocraticGuideAgent(config={
        "max_questions": 3,
        "enable_quality_check": True
    })
    
    # 初始状态
    state = AgentState(
        user_id="demo_user",
        session_id="demo_session_002",
        user_query="为什么秦始皇是暴君？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        timestamp=datetime.now()
    )
    
    print(f"\n📝 用户查询: {state.user_query}\n")
    
    # 模拟3轮对话
    user_responses = [
        "因为他焚书坑儒，很残暴",
        "我认为主要是因为他压迫百姓，修长城耗费大量人力",
        "确实，评价历史人物需要考虑多个方面，不能简单定性"
    ]
    
    for round_num in range(3):
        # 生成问题
        result_state = await agent.execute(state)
        
        if result_state.socratic_question:
            question = result_state.socratic_question
            print(f"🤔 问题 {round_num + 1}: {question}")
            
            # 模拟用户回答
            if round_num < len(user_responses):
                user_response = user_responses[round_num]
                print(f"💬 用户回答: {user_response}")
                
                # 处理用户响应
                state = agent.process_user_response(state, user_response)
                print()
        else:
            print(f"⚠️ 问题 {round_num + 1} 生成失败\n")
    
    # 显示对话摘要
    summary = agent.get_question_summary(state)
    print(f"\n📊 对话摘要:")
    print(f"   总问题数: {summary['total_questions']}")
    print(f"   总回答数: {summary['total_responses']}")
    print(f"   参与度: {summary['engagement_level']}")


async def demo_quality_validation():
    """示例3：质量验证机制"""
    print("\n" + "="*60)
    print("示例3：质量验证机制")
    print("="*60)
    
    # 启用质量检查和重试
    agent = SocraticGuideAgent(config={
        "max_questions": 5,
        "max_retries": 2,
        "enable_quality_check": True
    })
    
    state = AgentState(
        user_id="demo_user",
        session_id="demo_session_003",
        user_query="牛顿第一定律是什么？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        timestamp=datetime.now()
    )
    
    print(f"\n📝 用户查询: {state.user_query}")
    print(f"🔍 质量检查: 启用")
    print(f"🔄 最大重试次数: {agent.max_retries}\n")
    
    # 生成问题（会自动进行质量验证）
    result_state = await agent.execute(state)
    
    if result_state.socratic_question:
        print(f"✅ 验证通过！")
        print(f"🤔 问题: {result_state.socratic_question}")
    else:
        print(f"❌ 验证失败，已使用备用问题")


async def demo_personalized_questioning():
    """示例4：个性化问题生成"""
    print("\n" + "="*60)
    print("示例4：个性化问题生成（基于理解水平）")
    print("="*60)
    
    agent = SocraticGuideAgent()
    
    # 场景1：理解水平低的学生
    print("\n📚 场景1：理解水平较低")
    state_low = AgentState(
        user_id="student_beginner",
        session_id="demo_session_004a",
        user_query="什么是DNA？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        understanding_level=UnderstandingLevel.NO_UNDERSTANDING,
        timestamp=datetime.now()
    )
    
    state_low.user_responses = ["不太清楚"]  # 简短回答表示理解水平低
    
    result_low = await agent.execute(state_low)
    print(f"🤔 问题（针对初学者）: {result_low.socratic_question}")
    
    # 场景2：理解水平高的学生
    print("\n📚 场景2：理解水平较高")
    state_high = AgentState(
        user_id="student_advanced",
        session_id="demo_session_004b",
        user_query="什么是DNA？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        understanding_level=UnderstandingLevel.DEEP_UNDERSTANDING,
        timestamp=datetime.now()
    )
    
    state_high.user_responses = [
        "DNA是脱氧核糖核酸，是生物遗传信息的载体。它由双螺旋结构组成，包含腺嘌呤、鸟嘌呤、胞嘧啶和胸腺嘧啶四种碱基。"
    ]
    
    result_high = await agent.execute(state_high)
    print(f"🤔 问题（针对高级学习者）: {result_high.socratic_question}")


async def demo_different_question_types():
    """示例5：不同类型的问题"""
    print("\n" + "="*60)
    print("示例5：8种问题类型展示")
    print("="*60)
    
    agent = SocraticGuideAgent(config={
        "max_questions": 8
    })
    
    base_state = AgentState(
        user_id="demo_user",
        session_id="demo_session_005",
        user_query="全球变暖是一个严重问题吗？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        timestamp=datetime.now()
    )
    
    # 模拟用户逐步提升理解水平
    understanding_progression = [
        UnderstandingLevel.NO_UNDERSTANDING,
        UnderstandingLevel.SURFACE_UNDERSTANDING,
        UnderstandingLevel.BASIC_UNDERSTANDING,
        UnderstandingLevel.GOOD_UNDERSTANDING,
        UnderstandingLevel.DEEP_UNDERSTANDING,
    ]
    
    print(f"\n📝 主题: {base_state.user_query}\n")
    
    for i in range(5):
        state = AgentState(
            user_id=base_state.user_id,
            session_id=base_state.session_id,
            user_query=base_state.user_query,
            query_type=base_state.query_type,
            understanding_level=understanding_progression[i],
            timestamp=datetime.now()
        )
        
        # 添加历史问题（模拟对话进展）
        state.socratic_questions = [{"question": f"问题{j+1}"} for j in range(i)]
        
        result = await agent.execute(state)
        
        if result.socratic_question:
            question_type = result.conversation_context.get("last_question_type", "unknown")
            print(f"🔹 问题 {i+1} [{question_type}]:")
            print(f"   {result.socratic_question}\n")


async def demo_performance_comparison():
    """示例6：性能对比（质量检查 vs 无质量检查）"""
    print("\n" + "="*60)
    print("示例6：性能对比")
    print("="*60)
    
    import time
    
    state = AgentState(
        user_id="demo_user",
        session_id="demo_session_006",
        user_query="什么是人工智能？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        timestamp=datetime.now()
    )
    
    # 测试1：启用质量检查
    print("\n🔍 测试1：启用质量检查")
    agent_with_check = SocraticGuideAgent(config={
        "enable_quality_check": True,
        "max_retries": 2
    })
    
    start = time.time()
    result1 = await agent_with_check.execute(state)
    time1 = time.time() - start
    
    print(f"   耗时: {time1:.2f}秒")
    print(f"   问题: {result1.socratic_question}")
    
    # 测试2：禁用质量检查
    print("\n⚡ 测试2：禁用质量检查（快速模式）")
    agent_without_check = SocraticGuideAgent(config={
        "enable_quality_check": False,
        "max_retries": 0
    })
    
    # 清除缓存
    state2 = AgentState(
        user_id="demo_user_2",
        session_id="demo_session_006b",
        user_query="什么是人工智能？",
        query_type=QueryType.CONCEPT_EXPLANATION,
        timestamp=datetime.now()
    )
    
    start = time.time()
    result2 = await agent_without_check.execute(state2)
    time2 = time.time() - start
    
    print(f"   耗时: {time2:.2f}秒")
    print(f"   问题: {result2.socratic_question}")
    
    print(f"\n📊 性能对比:")
    print(f"   质量检查模式: {time1:.2f}秒")
    print(f"   快速模式: {time2:.2f}秒")
    if time1 > 0 and time2 > 0:
        speedup = time1 / time2
        print(f"   速度提升: {speedup:.1f}x")


async def main():
    """运行所有示例"""
    print("\n" + "🎓" * 30)
    print("苏格拉底引导Agent示例集（MARS优化版）")
    print("🎓" * 30)
    
    try:
        # 运行所有示例
        await demo_basic_usage()
        await demo_conversation_flow()
        await demo_quality_validation()
        await demo_personalized_questioning()
        await demo_different_question_types()
        await demo_performance_comparison()
        
        print("\n" + "="*60)
        print("✅ 所有示例运行完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

