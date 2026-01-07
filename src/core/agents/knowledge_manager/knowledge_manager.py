#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识管理智能体 - 统一的知识库管理

核心功能：
1. 自动索引处理pipeline：检测并处理新的知识库文件
2. 知识检索：从已索引的知识库中检索信息
3. 知识库管理：管理知识库的完整生命周期

设计理念：
- 不仅能够检索，还能自动处理索引
- 智能体内部包含知识检索功能
- 统一管理知识库的索引和检索
"""

import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
        logging.getLogger(__name__).info(f"已加载环境变量文件: {env_path}")
except ImportError:
    logging.getLogger(__name__).warning("python-dotenv 未安装，将使用系统环境变量")
except Exception as e:
    logging.getLogger(__name__).warning(f"加载 .env 文件失败: {e}")

from src.infrastructure.utils import BaseAgent, AgentState, QueryType
from src.infrastructure.nano_graphrag import GraphRAG, QueryParam

# 导入模块化组件
from .embedding_manager import EmbeddingManager
from .relevance_scorer import RelevanceScorer


class KnowledgeManagerAgent(BaseAgent):
    """知识管理智能体
    
    统一管理知识库的索引和检索功能：
    1. 自动索引处理：检测knowledge.txt文件变化并自动构建索引
    2. 知识检索：从已索引的知识库中检索相关信息
    3. 知识库管理：管理知识库的完整生命周期
    
    架构设计：
    - 索引处理pipeline：自动检测、处理、构建GraphRAG索引
    - 检索模块：复用现有检索逻辑，从已索引知识库检索
    - 状态管理：跟踪索引状态，避免重复索引
    """
    
    def __init__(self, knowledge_base_dir: str = None, auto_index: bool = True):
        super().__init__(
            name="KnowledgeManager",
            description="统一的知识库管理和检索智能体"
        )
        
        # 配置
        kb_config = {
            'root_dir': "data/concept_knowledge_bases",
            'default_kb': "default",
        }
        
        # 知识库路径
        project_root = Path(__file__).parent.parent.parent.parent.parent
        kb_dir = knowledge_base_dir or kb_config.get('root_dir', "data/concept_knowledge_bases")
        self.knowledge_base_dir = project_root / kb_dir
        
        if not self.knowledge_base_dir.exists():
            self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建知识库目录: {self.knowledge_base_dir}")
        
        # 索引配置
        self.auto_index = auto_index
        self.index_status_file = project_root / "data/knowledge_index_status.json"
        self.index_status_file.parent.mkdir(parents=True, exist_ok=True)
        self._index_status = self._load_index_status()
        
        # 缓存配置
        self.cache_enabled = True
        self.cache_dir = project_root / "data/retrieval_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._query_cache = {}
        self._cache_ttl = 24 * 3600  # 24小时
        self._max_cache_size = 1000
        
        # 概念数据库（延迟加载）
        self._concept_databases = {}
        
        # 并发控制
        self._max_workers = 4
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        
        # 索引任务队列
        self._indexing_tasks: Dict[str, asyncio.Task] = {}
        
        # 初始化模块化组件
        self.embedding_manager = EmbeddingManager(embedding_dim=1024)
        self.relevance_scorer = RelevanceScorer()
        
        # 初始化数据库
        self._initialize_databases()
        
        # 如果启用自动索引，检查并处理未索引的知识库
        if self.auto_index:
            asyncio.create_task(self._auto_index_check())
        
        self.logger.info("知识管理智能体初始化完成")
    
    def _load_index_status(self) -> Dict[str, Dict[str, Any]]:
        """加载索引状态"""
        if not self.index_status_file.exists():
            return {}
        
        try:
            with open(self.index_status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载索引状态失败: {e}")
            return {}
    
    def _save_index_status(self):
        """保存索引状态"""
        try:
            with open(self.index_status_file, 'w', encoding='utf-8') as f:
                json.dump(self._index_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存索引状态失败: {e}")
    
    def _initialize_databases(self):
        """初始化概念数据库（延迟加载）"""
        try:
            if not self.knowledge_base_dir.exists():
                self.logger.warning(f"知识库目录不存在: {self.knowledge_base_dir}")
                return
            
            for concept_dir in self.knowledge_base_dir.iterdir():
                if concept_dir.is_dir():
                    knowledge_file = concept_dir / "knowledge.txt"
                    graphrag_cache_dir = concept_dir / "graphrag_cache"
                    
                    # 检查是否有knowledge.txt文件
                    if knowledge_file.exists():
                        # 检查是否需要索引
                        needs_index = self._needs_indexing(concept_dir.name, knowledge_file)
                        
                        if needs_index and self.auto_index:
                            # 异步触发索引
                            asyncio.create_task(self._index_knowledge_base(concept_dir.name))
                        
                        # 如果已有索引，注册数据库
                        if graphrag_cache_dir.exists():
                            try:
                                self._concept_databases[concept_dir.name] = {
                                    "path": str(graphrag_cache_dir),
                                    "loaded": False,
                                    "rag_instance": None,
                                    "knowledge_file": str(knowledge_file),
                                    "last_modified": knowledge_file.stat().st_mtime
                                }
                                self.logger.debug(f"注册概念数据库: {concept_dir.name}")
                            except Exception as e:
                                self.logger.warning(f"注册概念失败 {concept_dir.name}: {e}")
            
            self.logger.info(f"初始化 {len(self._concept_databases)} 个概念数据库")
            
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
    
    def _needs_indexing(self, concept_name: str, knowledge_file: Path) -> bool:
        """检查是否需要索引"""
        try:
            file_mtime = knowledge_file.stat().st_mtime
            
            # 检查索引状态
            if concept_name in self._index_status:
                status = self._index_status[concept_name]
                indexed_mtime = status.get('last_indexed_mtime', 0)
                
                # 如果文件未修改，不需要重新索引
                if file_mtime <= indexed_mtime:
                    return False
                
                # 如果正在索引中，不需要重复索引
                if status.get('indexing', False):
                    return False
            
            # 检查是否有索引目录
            graphrag_cache_dir = knowledge_file.parent / "graphrag_cache"
            if not graphrag_cache_dir.exists():
                return True
            
            # 检查索引是否完整
            required_files = [
                "kv_store_full_docs.json",
                "kv_store_text_chunks.json",
                "graph_chunk_entity_relation.graphml"
            ]
            
            for required_file in required_files:
                if not (graphrag_cache_dir / required_file).exists():
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"检查索引状态失败 {concept_name}: {e}")
            return True
    
    async def _auto_index_check(self):
        """自动索引检查（后台任务）"""
        await asyncio.sleep(5)  # 延迟启动，避免阻塞初始化
        
        while True:
            try:
                await self._check_and_index_all()
                await asyncio.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                self.logger.error(f"自动索引检查失败: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def _check_and_index_all(self):
        """检查所有知识库并触发索引"""
        if not self.knowledge_base_dir.exists():
            return
        
        for concept_dir in self.knowledge_base_dir.iterdir():
            if concept_dir.is_dir():
                knowledge_file = concept_dir / "knowledge.txt"
                if knowledge_file.exists():
                    if self._needs_indexing(concept_dir.name, knowledge_file):
                        if concept_dir.name not in self._indexing_tasks:
                            self.logger.info(f"发现需要索引的知识库: {concept_dir.name}")
                            task = asyncio.create_task(self._index_knowledge_base(concept_dir.name))
                            self._indexing_tasks[concept_dir.name] = task
    
    async def _index_knowledge_base(self, concept_name: str) -> bool:
        """索引知识库
        
        Args:
            concept_name: 概念名称
            
        Returns:
            是否成功
        """
        try:
            # 更新索引状态
            if concept_name not in self._index_status:
                self._index_status[concept_name] = {}
            
            self._index_status[concept_name]['indexing'] = True
            self._index_status[concept_name]['last_index_attempt'] = datetime.now().isoformat()
            self._save_index_status()
            
            concept_dir = self.knowledge_base_dir / concept_name
            knowledge_file = concept_dir / "knowledge.txt"
            
            if not knowledge_file.exists():
                self.logger.warning(f"知识库文件不存在: {knowledge_file}")
                self._index_status[concept_name]['indexing'] = False
                self._index_status[concept_name]['error'] = "知识库文件不存在"
                self._save_index_status()
                return False
            
            # 读取知识库内容
            self.logger.info(f"开始索引知识库: {concept_name}")
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                self.logger.warning(f"知识库文件为空: {concept_name}")
                self._index_status[concept_name]['indexing'] = False
                self._index_status[concept_name]['error'] = "知识库文件为空"
                self._save_index_status()
                return False
            
            # 创建GraphRAG工作目录
            graphrag_cache_dir = concept_dir / "graphrag_cache"
            graphrag_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否使用 Qwen
            qwen_api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
            qwen_model = os.getenv("QWEN_MODEL", "qwen-plus")
            
            # 配置 LLM 函数
            if qwen_api_key:
                # 使用 Qwen
                from src.infrastructure.nano_graphrag._llm import qwen_complete_if_cache
                
                async def qwen_best_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
                    return await qwen_complete_if_cache(
                        qwen_model, prompt, system_prompt=system_prompt, history_messages=history_messages, **kwargs
                    )
                
                best_model_func = qwen_best_model_func
                cheap_model_func = qwen_best_model_func  # 使用同一个模型
                self.logger.info(f"使用 Qwen 模型进行索引: {qwen_model}")
            else:
                # 使用默认的 OpenAI（需要 OPENAI_API_KEY）
                from src.infrastructure.nano_graphrag._llm import gpt_4o_complete, gpt_4o_mini_complete
                best_model_func = gpt_4o_complete
                cheap_model_func = gpt_4o_mini_complete
                self.logger.info("使用默认 OpenAI 模型进行索引")
            
            # 创建GraphRAG实例
            rag = GraphRAG(
                working_dir=str(graphrag_cache_dir),
                enable_llm_cache=False,
                enable_naive_rag=True,
                enable_local=False,
                embedding_func_max_async=16,
                embedding_batch_num=512,
                embedding_func=self.embedding_manager.get_embedding_func(),
                best_model_func=best_model_func,
                cheap_model_func=cheap_model_func
            )
            
            # 执行索引
            self.logger.info(f"正在索引 {concept_name}，内容长度: {len(content)} 字符")
            
            # 将内容按段落分割（每段作为一个文档）
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if not paragraphs:
                paragraphs = [content]
            
            # 批量插入（避免一次性插入过多内容）
            batch_size = 10
            for i in range(0, len(paragraphs), batch_size):
                batch = paragraphs[i:i+batch_size]
                await rag.ainsert(batch)
                self.logger.debug(f"已索引 {min(i+batch_size, len(paragraphs))}/{len(paragraphs)} 个段落")
            
            # 更新索引状态
            file_mtime = knowledge_file.stat().st_mtime
            self._index_status[concept_name] = {
                'indexing': False,
                'indexed': True,
                'last_indexed_mtime': file_mtime,
                'last_indexed_time': datetime.now().isoformat(),
                'paragraph_count': len(paragraphs),
                'content_length': len(content)
            }
            self._save_index_status()
            
            # 注册到数据库
            self._concept_databases[concept_name] = {
                "path": str(graphrag_cache_dir),
                "loaded": False,
                "rag_instance": None,
                "knowledge_file": str(knowledge_file),
                "last_modified": file_mtime
            }
            
            # 清理索引任务
            if concept_name in self._indexing_tasks:
                del self._indexing_tasks[concept_name]
            
            self.logger.info(f"✅ 成功索引知识库: {concept_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"索引知识库失败 {concept_name}: {e}", exc_info=True)
            if concept_name in self._index_status:
                self._index_status[concept_name]['indexing'] = False
                self._index_status[concept_name]['error'] = str(e)
                self._save_index_status()
            
            if concept_name in self._indexing_tasks:
                del self._indexing_tasks[concept_name]
            
            return False
    
    def _load_concept_database(self, concept_name: str) -> Optional[GraphRAG]:
        """加载指定概念的数据库"""
        if concept_name not in self._concept_databases:
            return None
        
        db_info = self._concept_databases[concept_name]
        
        # 如果已加载，直接返回
        if db_info["loaded"] and db_info["rag_instance"]:
            return db_info["rag_instance"]
        
        try:
            working_dir = db_info["path"]
            working_path = Path(working_dir)
            
            if not working_path.exists():
                self.logger.warning(f"工作目录不存在: {working_dir}")
                return None
            
            # 检查必要文件
            required_files = [
                "kv_store_full_docs.json",
                "kv_store_text_chunks.json",
                "graph_chunk_entity_relation.graphml"
            ]
            
            missing_files = [f for f in required_files if not (working_path / f).exists()]
            if missing_files:
                self.logger.warning(f"缺少必要文件 {concept_name}: {missing_files}")
                # 如果缺少文件，尝试重新索引
                if self.auto_index:
                    asyncio.create_task(self._index_knowledge_base(concept_name))
                return None
            
            # 创建 GraphRAG 实例
            rag = GraphRAG(
                working_dir=working_dir,
                enable_llm_cache=False,
                enable_naive_rag=True,
                enable_local=False,
                embedding_func_max_async=16,
                embedding_batch_num=512,
                embedding_func=self.embedding_manager.get_embedding_func()
            )
            
            # 缓存实例
            db_info["rag_instance"] = rag
            db_info["loaded"] = True
            
            self.logger.info(f"✅ 成功加载概念数据库: {concept_name}")
            return rag
            
        except Exception as e:
            self.logger.error(f"加载概念数据库失败 {concept_name}: {e}")
            return None
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行知识管理
        
        根据状态决定执行索引还是检索：
        - 如果state中有index_request，执行索引
        - 否则执行检索
        """
        try:
            # 检查是否有索引请求
            if hasattr(state, 'index_request') and state.index_request:
                return await self._execute_indexing(state)
            else:
                return await self._execute_retrieval(state)
                
        except Exception as e:
            self.logger.error(f"知识管理执行失败: {e}")
            state.set_error("knowledge_management_error", f"执行失败: {str(e)}")
            return state
    
    async def _execute_indexing(self, state: AgentState) -> AgentState:
        """执行索引任务"""
        try:
            index_request = state.index_request
            concept_name = index_request.get('concept_name')
            
            if not concept_name:
                state.set_error("index_error", "缺少concept_name参数")
                return state
            
            self.logger.info(f"收到索引请求: {concept_name}")
            
            success = await self._index_knowledge_base(concept_name)
            
            if success:
                state.index_result = {
                    "success": True,
                    "concept_name": concept_name,
                    "message": f"成功索引知识库: {concept_name}"
                }
            else:
                state.set_error("index_error", f"索引失败: {concept_name}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"索引执行失败: {e}")
            state.set_error("index_error", f"索引执行失败: {str(e)}")
            return state
    
    async def _execute_retrieval(self, state: AgentState) -> AgentState:
        """执行知识检索（复用原有检索逻辑）"""
        try:
            # 1. 获取优化查询策略
            optimized_queries = self._get_optimized_queries(state)
            
            # 2. 确定目标概念
            target_concepts = self._identify_target_concepts(state)
            
            if not target_concepts:
                self.logger.warning("未识别到相关概念")
                state.retrieved_knowledge = {
                    "concepts": [],
                    "results": [],
                    "message": "未能识别出相关概念"
                }
                return state
            
            # 3. 检查缓存
            main_query = state.user_query
            cache_key = self._get_cache_key(main_query, ":".join(target_concepts))
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                self.logger.info("返回缓存的检索结果")
                state.retrieved_knowledge = cached_result
                state.knowledge_sources = cached_result.get('successful_sources', [])
                return state
            
            # 4. 并发执行检索
            retrieval_results = await self._execute_concurrent_retrieval(
                optimized_queries, target_concepts
            )
            successful_sources = list(set([r.get('source', '') for r in retrieval_results if r.get('source')]))
            
            # 5. 如果没有结果，尝试全局搜索
            if not retrieval_results:
                for query_info in optimized_queries[:2]:
                    global_results = self._global_search(query_info['query'])
                    if global_results:
                        retrieval_results.extend(global_results)
                        if "global_search" not in successful_sources:
                            successful_sources.append("global_search")
            
            # 6. 按相关性排序和去重
            retrieval_results = self._rank_and_deduplicate_results(retrieval_results)
            
            # 7. 整理结果并缓存
            knowledge_result = {
                "target_concepts": target_concepts,
                "successful_sources": successful_sources,
                "results": retrieval_results,
                "total_results": len(retrieval_results),
                "optimized_queries_used": len(optimized_queries),
                "retrieval_strategy": "enhanced_multi_query_cached",
                "message": f"从 {len(successful_sources)} 个知识源检索到 {len(retrieval_results)} 条相关信息"
            }
            
            # 缓存结果
            self._set_cache(cache_key, knowledge_result)
            state.retrieved_knowledge = knowledge_result
            state.knowledge_sources = successful_sources
            
            self.logger.info(f"✅ 检索完成: {len(retrieval_results)} 条结果，来自 {len(successful_sources)} 个源")
            
            return state
            
        except Exception as e:
            self.logger.error(f"知识检索失败: {e}")
            state.set_error("knowledge_retrieval_error", f"检索失败: {str(e)}")
            return state
    
    def _get_optimized_queries(self, state: AgentState) -> List[Dict[str, Any]]:
        """获取优化查询"""
        if (hasattr(state, 'retrieval_decision') and 
            'optimized_queries' in state.retrieval_decision):
            return state.retrieval_decision['optimized_queries']
        
        return [{
            'query': state.user_query,
            'type': 'original',
            'priority': 1.0,
            'strategy': 'exact_match'
        }]
    
    def _identify_target_concepts(self, state: AgentState) -> List[str]:
        """识别目标概念（增强版）"""
        target_concepts = []
        all_concepts = list(self._concept_databases.keys())
        
        # 1. 从决策代理获取
        if (hasattr(state, 'retrieval_decision') and 
            'core_concepts' in state.retrieval_decision):
            core_concepts = state.retrieval_decision['core_concepts']
            
            for concept in core_concepts:
                for concept_name in all_concepts:
                    if (concept.lower() in concept_name.lower() or 
                        concept_name.lower() in concept.lower()):
                        if concept_name not in target_concepts:
                            target_concepts.append(concept_name)
        
        # 2. 从解释结果获取
        if state.interpretation and "keywords" in state.interpretation:
            keywords = state.interpretation["keywords"]
            
            for keyword in keywords:
                for concept_name in all_concepts:
                    if (keyword.lower() in concept_name.lower() or 
                        concept_name.lower() in keyword.lower()):
                        if concept_name not in target_concepts:
                            target_concepts.append(concept_name)
        
        # 3. 从查询直接匹配
        if not target_concepts:
            query_lower = state.user_query.lower()
            for concept_name in all_concepts:
                if concept_name.lower() in query_lower:
                    target_concepts.append(concept_name)
        
        # 4. 语义匹配
        if not target_concepts:
            query_words = re.findall(r'[\u4e00-\u9fa5]+', state.user_query)
            query_words = [w for w in query_words if len(w) >= 2]
            
            stop_words = {'什么', '怎么', '如何', '为什么', '哪些', '请', '解释', '说明', '介绍', '历史', '时代'}
            query_keywords = [w for w in query_words if w not in stop_words]
            
            if query_keywords:
                concept_scores = []
                for concept_name in all_concepts:
                    score = sum(1 for kw in query_keywords if kw in concept_name)
                    if score > 0:
                        concept_scores.append((concept_name, score))
                
                if concept_scores:
                    concept_scores.sort(key=lambda x: x[1], reverse=True)
                    target_concepts = [c[0] for c in concept_scores[:5]]
                    self.logger.info(f"通过语义匹配找到概念: {target_concepts}")
        
        if not target_concepts:
            self.logger.warning(f"未能识别到相关概念，查询: {state.user_query}")
            return []
        
        return target_concepts[:5]
    
    async def _execute_concurrent_retrieval(
        self, 
        optimized_queries: List[Dict[str, Any]],
        target_concepts: List[str]
    ) -> List[Dict[str, Any]]:
        """并发执行检索任务"""
        if not optimized_queries or not target_concepts:
            return []
        
        tasks = []
        for query_info in optimized_queries:
            query = query_info['query']
            strategy = query_info.get('strategy', 'exact_match')
            priority = query_info.get('priority', 0.5)
            
            for concept in target_concepts:
                tasks.append(asyncio.create_task(
                    self._retrieve_with_timeout(concept, query, strategy, priority)
                ))
        
        if not tasks:
            return []
        
        results = []
        completed, pending = await asyncio.wait(tasks, timeout=15)
        
        for task in completed:
            try:
                result = task.result()
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.debug(f"任务失败: {e}")
        
        for task in pending:
            task.cancel()
        
        return results
    
    async def _retrieve_with_timeout(self, concept: str, query: str, strategy: str, priority: float):
        """带超时的检索"""
        try:
            return await asyncio.wait_for(
                self._retrieve_async(concept, query, strategy, priority),
                timeout=8
            )
        except asyncio.TimeoutError:
            self.logger.debug(f"检索超时: {concept}")
            return None
    
    async def _retrieve_async(self, concept: str, query: str, strategy: str, priority: float):
        """异步检索"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._retrieve_from_concept,
            concept,
            query,
            strategy,
            priority
        )
    
    def _retrieve_from_concept(
        self, 
        concept_name: str, 
        query: str, 
        strategy: str, 
        priority: float
    ) -> Optional[Dict[str, Any]]:
        """从概念检索"""
        try:
            rag = self._load_concept_database(concept_name)
            if not rag:
                return None
            
            # 根据策略选择查询参数
            query_param = self._get_query_param_by_strategy(strategy)
            
            # 执行同步查询
            result = self._execute_sync_query(rag, query, query_param)
            
            if not result or not str(result).strip():
                return None
            
            result_str = str(result).strip()
            
            # 计算相关性分数
            relevance_score = self.relevance_scorer.calculate_score(query, result_str)
            
            if relevance_score < 0.1:
                return None
            
            return {
                "concept": concept_name,
                "query": query,
                "content": result_str,
                "source": f"concept_database:{concept_name}",
                "strategy": strategy,
                "priority": priority,
                "relevance_score": relevance_score,
                "content_length": len(result_str),
                "real_retrieval": True
            }
            
        except Exception as e:
            self.logger.warning(f"检索失败 {concept_name}: {e}")
            return None
    
    def _execute_sync_query(self, rag: GraphRAG, query: str, query_param: QueryParam):
        """执行同步GraphRAG查询"""
        try:
            def run_async_query():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(rag.aquery(query, param=query_param))
                finally:
                    loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_query)
                result = future.result(timeout=30)
                return result
                
        except Exception as e:
            self.logger.error(f"同步查询执行失败: {e}")
            raise e
    
    def _global_search(self, query: str) -> List[Dict[str, Any]]:
        """全局搜索"""
        results = []
        concept_names = list(self._concept_databases.keys())[:3]
        
        for concept_name in concept_names:
            result = self._retrieve_from_concept(concept_name, query, 'exact_match', 0.5)
            if result and result.get("relevance_score", 0) > 0.3:
                results.append(result)
        
        return results
    
    def _rank_and_deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """排序并去重"""
        unique_results = {}
        
        for result in results:
            content_hash = hashlib.md5(result.get('content', '').encode('utf-8')).hexdigest()
            if content_hash not in unique_results or unique_results[content_hash]['relevance_score'] < result.get('relevance_score', 0):
                unique_results[content_hash] = result
        
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: (
                x.get('relevance_score', 0),
                len(x.get('content', '')),
                1 if x.get('strategy') == 'concept_match' else 0
            ),
            reverse=True
        )
        
        return sorted_results[:10]
    
    def _get_query_param_by_strategy(self, strategy: str) -> QueryParam:
        """根据策略返回QueryParam"""
        strategy_mapping = {
            'exact_match': QueryParam(mode="hybrid", top_k=5),
            'concept_match': QueryParam(mode="global", top_k=5),
            'multi_concept_match': QueryParam(mode="local", top_k=4),
            'semantic_expansion': QueryParam(mode="hybrid", top_k=6),
            'keyword_search': QueryParam(mode="naive", top_k=5)
        }
        
        return strategy_mapping.get(strategy, QueryParam(mode="hybrid", top_k=5))
    
    # ========== 缓存管理 ==========
    
    def _get_cache_key(self, query: str, concept: str = None) -> str:
        """生成缓存键"""
        cache_str = f"{query}:{concept}" if concept else query
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取"""
        if cache_key not in self._query_cache:
            return None
        
        cached_data = self._query_cache[cache_key]
        if time.time() - cached_data['timestamp'] > self._cache_ttl:
            del self._query_cache[cache_key]
            return None
        
        return cached_data['result']
    
    def _set_cache(self, cache_key: str, result: Dict[str, Any]):
        """设置缓存"""
        if len(self._query_cache) >= self._max_cache_size:
            oldest_key = min(self._query_cache.keys(), 
                           key=lambda k: self._query_cache[k]['timestamp'])
            del self._query_cache[oldest_key]
        
        self._query_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    # ========== 公共接口 ==========
    
    def get_available_concepts(self) -> List[str]:
        """获取可用概念列表"""
        return list(self._concept_databases.keys())
    
    def get_index_status(self, concept_name: str = None) -> Dict[str, Any]:
        """获取索引状态"""
        if concept_name:
            return self._index_status.get(concept_name, {})
        return self._index_status
    
    async def index_knowledge_base(self, concept_name: str) -> bool:
        """手动触发索引（公共接口）"""
        return await self._index_knowledge_base(concept_name)
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """列出所有知识库"""
        try:
            knowledge_bases = []
            if not self.knowledge_base_dir.exists():
                return knowledge_bases
            
            for kb_path in self.knowledge_base_dir.iterdir():
                if kb_path.is_dir() and (kb_path / "knowledge.txt").exists():
                    kb_name = kb_path.name
                    index_status = self.get_index_status(kb_name)
                    kb_info = {
                        "name": kb_name,
                        "path": str(kb_path),
                        "has_cache": (kb_path / "graphrag_cache").exists(),
                        "indexed": index_status.get('indexed', False),
                        "indexing": index_status.get('indexing', False),
                        "last_indexed": index_status.get('last_indexed_time'),
                    }
                    knowledge_bases.append(kb_info)
            
            return knowledge_bases
        except Exception as e:
            self.logger.error(f"列出知识库失败: {e}")
            return []
    
    def shutdown(self):
        """清理资源"""
        try:
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=True)
            self._query_cache.clear()
            self._save_index_status()
            self.logger.info("知识管理智能体已清理完成")
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")

