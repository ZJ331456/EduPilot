#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正的LangGraph工作流测试
验证新的LangGraph工作流是否正常工作
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_langgraph_workflow_import():
    """测试LangGraph工作流导入"""
    logger.info("测试LangGraph工作流导入...")
    
    try:
        from workflow.langgraph_workflow import LangGraphEduWorkflow, create_langgraph_workflow
        logger.info("✅ LangGraph工作流导入成功")
        return True
    except Exception as e:
        logger.error(f"❌ LangGraph工作流导入失败: {e}")
        return False


async def test_workflow_creation():
    """测试工作流创建"""
    logger.info("测试工作流创建...")
    
    try:
        from workflow.langgraph_workflow import create_langgraph_workflow
        
        # 创建基础工作流
        workflow = create_langgraph_workflow()
        logger.info("✅ 基础工作流创建成功")
        
        # 创建带配置的工作流
        config = {
            "max_rounds": 15,
            "enable_debug": True
        }
        workflow_with_config = create_langgraph_workflow(config)
        logger.info("✅ 配置工作流创建成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 工作流创建失败: {e}")
        return False


async def test_simple_query():
    """测试简单查询"""
    logger.info("测试简单查询...")
    
    try:
        from workflow.langgraph_workflow import create_langgraph_workflow
        
        workflow = create_langgraph_workflow()
        
        # 测试简单查询
        result = await workflow.execute(
            user_query="什么是人工智能？",
            session_id="test_langgraph_001"
        )
        
        logger.info("✅ 简单查询执行成功")
        logger.info(f"成功: {result['success']}")
        logger.info(f"会话ID: {result['session_id']}")
        logger.info(f"执行时间: {result['execution_time']:.2f}秒")
        logger.info(f"对话阶段: {result['conversation_stage']}")
        logger.info(f"理解水平: {result['understanding_level']}")
        logger.info(f"查询类型: {result.get('query_type', 'unknown')}")
        
        if result['success']:
            if 'execution_result' in result:
                execution_result = result['execution_result']
                logger.info(f"执行结果类型: {type(execution_result)}")
                if isinstance(execution_result, dict):
                    logger.info(f"执行结果键: {list(execution_result.keys())}")
            
            if 'learning_feedback' in result:
                feedback = result['learning_feedback']
                logger.info(f"学习反馈: {type(feedback)}")
                if isinstance(feedback, dict):
                    logger.info(f"学习反馈键: {list(feedback.keys())}")
            
            if 'socratic_questions' in result:
                questions = result['socratic_questions']
                logger.info(f"苏格拉底问题数量: {len(questions)}")
                if questions:
                    logger.info(f"第一个问题: {questions[0][:100]}...")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"❌ 简单查询失败: {e}")
        return False


async def test_different_query_types():
    """测试不同查询类型"""
    logger.info("测试不同查询类型...")
    
    try:
        from workflow.langgraph_workflow import create_langgraph_workflow
        
        workflow = create_langgraph_workflow()
        
        # 测试不同类型的查询
        test_queries = [
            ("什么是机器学习？", "概念解释"),
            ("如何训练神经网络？", "程序性知识"),
            ("为什么深度学习有效？", "因果知识"),
            ("你好", "问候"),
            ("你能做什么？", "能力询问")
        ]
        
        results = []
        for query, query_type in test_queries:
            logger.info(f"测试查询: {query} ({query_type})")
            
            result = await workflow.execute(
                user_query=query,
                session_id=f"test_{query_type}_{datetime.now().strftime('%H%M%S')}"
            )
            
            results.append(result['success'])
            
            if result['success']:
                logger.info(f"✅ {query_type} 查询成功")
                logger.info(f"查询类型: {result.get('query_type', 'unknown')}")
                logger.info(f"对话阶段: {result.get('conversation_stage', 'unknown')}")
            else:
                logger.warning(f"⚠️ {query_type} 查询失败: {result.get('error', 'unknown')}")
        
        success_count = sum(results)
        logger.info(f"查询类型测试结果: {success_count}/{len(test_queries)} 成功")
        
        return success_count == len(test_queries)
        
    except Exception as e:
        logger.error(f"❌ 查询类型测试失败: {e}")
        return False


async def test_user_context():
    """测试用户上下文"""
    logger.info("测试用户上下文...")
    
    try:
        from workflow.langgraph_workflow import create_langgraph_workflow
        
        workflow = create_langgraph_workflow()
        
        # 测试带用户上下文的查询
        user_context = {
            "interests": ["人工智能", "机器学习"],
            "learning_style": "visual",
            "difficulty_preference": "advanced"
        }
        
        result = await workflow.execute(
            user_query="请解释深度学习的工作原理",
            session_id="test_context_001",
            user_id="user_123",
            user_context=user_context
        )
        
        logger.info("✅ 用户上下文测试执行成功")
        logger.info(f"成功: {result['success']}")
        logger.info(f"用户ID: {result.get('user_id', 'none')}")
        
        if result['success'] and 'user_profile' in result:
            profile = result['user_profile']
            logger.info(f"用户画像: {profile}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"❌ 用户上下文测试失败: {e}")
        return False


async def test_performance():
    """测试性能"""
    logger.info("测试性能...")
    
    try:
        from workflow.langgraph_workflow import create_langgraph_workflow
        
        workflow = create_langgraph_workflow()
        
        # 执行多个查询测试性能
        start_time = datetime.now()
        
        tasks = []
        for i in range(3):
            task = workflow.execute(
                user_query=f"测试查询 {i+1}",
                session_id=f"perf_test_{i+1}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        logger.info("✅ 性能测试完成")
        logger.info(f"总执行时间: {total_time:.2f}秒")
        logger.info(f"平均每个查询: {total_time/len(tasks):.2f}秒")
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"成功率: {success_count}/{len(tasks)}")
        
        # 获取统计信息
        stats = workflow.get_stats()
        logger.info(f"工作流统计: {stats}")
        
        return success_count == len(tasks)
        
    except Exception as e:
        logger.error(f"❌ 性能测试失败: {e}")
        return False


async def test_agent_integration():
    """测试智能体集成"""
    logger.info("测试智能体集成...")
    
    try:
        from workflow.langgraph_workflow import create_langgraph_workflow
        
        workflow = create_langgraph_workflow()
        
        # 测试一个需要多个智能体协作的查询
        result = await workflow.execute(
            user_query="请详细解释什么是机器学习，并给我一些学习建议",
            session_id="test_integration_001"
        )
        
        logger.info("✅ 智能体集成测试执行成功")
        logger.info(f"成功: {result['success']}")
        
        if result['success']:
            # 检查各个智能体的输出
            if 'execution_result' in result:
                logger.info("✅ 执行智能体工作正常")
            
            if 'learning_feedback' in result:
                logger.info("✅ 学习分析智能体工作正常")
            
            if 'socratic_questions' in result:
                logger.info("✅ 苏格拉底引导智能体工作正常")
            
            if 'knowledge_sources' in result:
                logger.info("✅ 知识检索智能体工作正常")
            
            if 'user_profile' in result:
                logger.info("✅ 用户画像智能体工作正常")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"❌ 智能体集成测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("开始真正的LangGraph工作流测试...")
    
    tests = [
        ("导入测试", test_langgraph_workflow_import),
        ("工作流创建测试", test_workflow_creation),
        ("简单查询测试", test_simple_query),
        ("查询类型测试", test_different_query_types),
        ("用户上下文测试", test_user_context),
        ("智能体集成测试", test_agent_integration),
        ("性能测试", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"{test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果总结")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        logger.info("🎉 所有测试通过！真正的LangGraph工作流运行正常！")
    else:
        logger.warning("⚠️ 部分测试失败，需要进一步调试")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
