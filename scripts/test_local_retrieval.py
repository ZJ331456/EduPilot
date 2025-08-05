#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地知识检索测试脚本
测试KnowledgeRetrieverAgent的真实检索功能
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# 添加src目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from agents.knowledge_retriever import KnowledgeRetrieverAgent
from utils import AgentState, QueryType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_retrieval.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class RetrievalTester:
    """知识检索测试器"""
    
    def __init__(self):
        self.retriever = None
        self.test_queries = [
            "三国史记的主要内容是什么？",
            "什么是律令制？",
            "日本古代的政治制度",
            "朝鲜半岛的历史发展",
            "东亚文化圈的特点",
            "古代日本的社会结构",
            "新罗的建国过程",
            "高句丽与中国的关系"
        ]
    
    def setup_retriever(self):
        """初始化知识检索器"""
        try:
            # 使用相对路径指向concept_knowledge_bases
            knowledge_base_dir = project_root / "concept_knowledge_bases"
            
            if not knowledge_base_dir.exists():
                logger.error(f"知识库目录不存在: {knowledge_base_dir}")
                return False
            
            self.retriever = KnowledgeRetrieverAgent(
                knowledge_base_dir=str(knowledge_base_dir)
            )
            
            logger.info(f"知识检索器初始化成功，知识库路径: {knowledge_base_dir}")
            return True
            
        except Exception as e:
            logger.error(f"初始化知识检索器失败: {e}")
            return False
    
    def check_knowledge_bases(self):
        """检查可用的知识库"""
        logger.info("=" * 60)
        logger.info("检查可用的知识库...")
        
        if not self.retriever:
            logger.error("知识检索器未初始化")
            return
        
        available_concepts = self.retriever.get_available_concepts()
        logger.info(f"发现 {len(available_concepts)} 个概念数据库:")
        
        for i, concept in enumerate(available_concepts, 1):
            concept_info = self.retriever.get_concept_info(concept)
            status = "✅ 可用" if concept_info.get("available", False) else "❌ 不可用"
            logger.info(f"  {i:2d}. {concept} - {status}")
            
            if concept_info.get("available", False):
                logger.info(f"      路径: {concept_info.get('path', 'N/A')}")
        
        # 检查nano-graphrag是否可用
        try:
            from nano_graphrag import GraphRAG
            logger.info("✅ nano-graphrag 模块可用")
        except ImportError:
            logger.warning("❌ nano-graphrag 模块不可用，将无法进行真实检索")
    
    def create_test_state(self, query: str) -> AgentState:
        """创建测试用的AgentState"""
        state = AgentState(
            session_id="test_session",
            user_query=query
        )
        
        # 模拟查询解释结果
        state.interpretation = {
            "query_type": "knowledge_retrieval",
            "main_topic": query,
            "keywords": query.split(),
            "intent": "retrieve_information"
        }
        
        state.query_type = QueryType.KNOWLEDGE_RETRIEVAL
        
        # 模拟决策代理的结果
        state.retrieval_decision = {
            "need_retrieval": True,
            "core_concepts": query.split()[:3],  # 前3个词作为核心概念
            "optimized_queries": [
                {
                    "query": query,
                    "type": "original",
                    "priority": 1.0,
                    "strategy": "exact_match"
                }
            ]
        }
        
        return state
    
    async def test_single_query(self, query: str):
        """测试单个查询"""
        logger.info(f"\n{'='*60}")
        logger.info(f"测试查询: {query}")
        logger.info(f"{'='*60}")
        
        try:
            # 创建测试状态
            state = self.create_test_state(query)
            
            # 检查是否可以执行
            can_execute = self.retriever.can_execute(state)
            logger.info(f"可以执行检索: {can_execute}")
            
            if not can_execute:
                logger.warning("无法执行检索，跳过此查询")
                return
            
            # 执行检索
            start_time = asyncio.get_event_loop().time()
            result_state = await self.retriever.execute(state)
            end_time = asyncio.get_event_loop().time()
            
            execution_time = end_time - start_time
            logger.info(f"检索耗时: {execution_time:.2f}秒")
            
            # 分析结果
            if hasattr(result_state, 'retrieved_knowledge') and result_state.retrieved_knowledge:
                knowledge = result_state.retrieved_knowledge
                logger.info(f"✅ 检索成功!")
                logger.info(f"   目标概念: {knowledge.get('target_concepts', [])}")
                logger.info(f"   成功源数: {len(knowledge.get('successful_sources', []))}")
                logger.info(f"   结果总数: {knowledge.get('total_results', 0)}")
                logger.info(f"   检索策略: {knowledge.get('retrieval_strategy', 'unknown')}")
                
                # 显示前2个结果的详细信息
                results = knowledge.get('results', [])
                for i, result in enumerate(results[:2], 1):
                    logger.info(f"\n   📄 结果 {i}:")
                    logger.info(f"      概念: {result.get('concept', 'N/A')}")
                    logger.info(f"      相关性: {result.get('relevance_score', 0):.3f}")
                    logger.info(f"      策略: {result.get('strategy', 'N/A')}")
                    logger.info(f"      内容长度: {result.get('content_length', 0)}字符")
                    
                    content = result.get('content', '')
                    preview = content[:200] + "..." if len(content) > 200 else content
                    logger.info(f"      内容预览: {preview}")
                    
                    if result.get('real_retrieval'):
                        logger.info(f"      ✅ 真实检索结果")
                    else:
                        logger.info(f"      ⚠️  非真实检索结果")
                
            else:
                logger.warning("❌ 检索失败或无结果")
                if hasattr(result_state, 'errors') and result_state.errors:
                    logger.error(f"   错误信息: {result_state.errors}")
        
        except Exception as e:
            logger.error(f"查询执行异常: {e}", exc_info=True)
    
    async def test_all_queries(self):
        """测试所有预设查询"""
        logger.info(f"\n{'='*80}")
        logger.info("开始批量测试...")
        logger.info(f"{'='*80}")
        
        success_count = 0
        total_queries = len(self.test_queries)
        
        for i, query in enumerate(self.test_queries, 1):
            logger.info(f"\n[{i}/{total_queries}] 处理查询...")
            
            try:
                await self.test_single_query(query)
                success_count += 1
            except Exception as e:
                logger.error(f"查询 '{query}' 测试失败: {e}")
        
        # 测试总结
        logger.info(f"\n{'='*80}")
        logger.info("测试总结")
        logger.info(f"{'='*80}")
        logger.info(f"总查询数: {total_queries}")
        logger.info(f"成功数: {success_count}")
        logger.info(f"失败数: {total_queries - success_count}")
        logger.info(f"成功率: {success_count/total_queries*100:.1f}%")
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        logger.info(f"\n{'='*60}")
        logger.info("测试缓存功能...")
        logger.info(f"{'='*60}")
        
        if not self.retriever:
            logger.error("知识检索器未初始化")
            return
        
        # 获取缓存统计
        cache_stats = self.retriever.get_cache_stats()
        logger.info(f"缓存状态:")
        logger.info(f"  缓存大小: {cache_stats.get('cache_size', 0)}")
        logger.info(f"  最大缓存: {cache_stats.get('max_cache_size', 0)}")
        logger.info(f"  缓存TTL: {cache_stats.get('cache_ttl', 0)}秒")
        logger.info(f"  命中率: {cache_stats.get('hit_ratio', 0)*100:.1f}%")
        
        # 优化缓存
        self.retriever.optimize_cache()
        logger.info("✅ 缓存优化完成")

async def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("知识检索器测试开始")
    logger.info("=" * 80)
    
    tester = RetrievalTester()
    
    # 1. 初始化检索器
    if not tester.setup_retriever():
        logger.error("初始化失败，退出测试")
        return
    
    # 2. 检查知识库
    tester.check_knowledge_bases()
    
    # 3. 测试单个查询
    test_query = "三国史记的主要内容是什么？"
    await tester.test_single_query(test_query)
    
    # 4. 测试缓存功能
    tester.test_cache_functionality()
    
    # 5. 批量测试（可选）
    logger.info(f"\n是否进行批量测试？(需要较长时间)")
    # 取消注释下面这行来启用批量测试
    # await tester.test_all_queries()
    
    # 6. 清理资源
    if tester.retriever:
        tester.retriever.shutdown()
        logger.info("✅ 资源清理完成")
    
    logger.info("\n" + "=" * 80)
    logger.info("测试完成！检查 test_retrieval.log 查看详细日志")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
    except Exception as e:
        logger.error(f"测试程序异常: {e}", exc_info=True)