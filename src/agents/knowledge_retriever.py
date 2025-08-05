#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识检索器智能体
从nano-graphrag知识库中检索相关信息
"""

import os
import logging
import asyncio
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import BaseAgent, AgentState, QueryType
try:
    from nano_graphrag import GraphRAG, QueryParam
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GraphRAG = None
    QueryParam = None
    GRAPHRAG_AVAILABLE = False

class KnowledgeRetrieverAgent(BaseAgent):
    """知识检索器智能体
    
    负责从nano-graphrag知识库中检索相关信息
    """
    
    def __init__(self, knowledge_base_dir: str = None):
        super().__init__(
            name="KnowledgeRetriever",
            description="从知识库中检索相关信息"
        )
        
        # 导入配置管理器
        from config import get_knowledge_base_config
        
        kb_config = get_knowledge_base_config()
        
        # 使用相对路径指向项目根目录
        project_root = Path(__file__).parent.parent.parent
        self.knowledge_base_dir = project_root / (knowledge_base_dir or kb_config.get('root_dir', "concept_knowledge_bases"))
        
        # 缓存配置
        cache_config = kb_config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', True)
        self.cache_dir = project_root / cache_config.get('cache_dir', "data/retrieval_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._concept_databases = {}
        
        # 添加缓存机制
        self._query_cache = {}
        self._cache_ttl = cache_config.get('ttl_hours', 24) * 3600  # 转换为秒
        self._max_cache_size = cache_config.get('max_size', 1000)
        
        # 并发控制
        retrieval_config = kb_config.get('retrieval', {})
        self._max_workers = retrieval_config.get('max_concurrent_queries', 4)
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        
        self._initialize_databases()
    
    def _initialize_databases(self):
        """初始化概念数据库"""
        try:
            if not self.knowledge_base_dir.exists():
                self.logger.warning(f"Knowledge base directory not found: {self.knowledge_base_dir}")
                return
            
            # 扫描概念目录
            for concept_dir in self.knowledge_base_dir.iterdir():
                if concept_dir.is_dir():
                    graphrag_cache_dir = concept_dir / "graphrag_cache"
                    if graphrag_cache_dir.exists():
                        try:
                            # 延迟加载，只记录路径
                            self._concept_databases[concept_dir.name] = {
                                "path": str(graphrag_cache_dir),
                                "loaded": False,
                                "rag_instance": None
                            }
                            self.logger.debug(f"Found concept database: {concept_dir.name}")
                        except Exception as e:
                            self.logger.warning(f"Failed to register concept {concept_dir.name}: {e}")
            
            self.logger.info(f"Initialized {len(self._concept_databases)} concept databases")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize databases: {e}")
    
    def _get_1024_embedding_func(self):
        """获取1024维嵌入函数
        
        Returns:
            Compatible 1024-dimension EmbeddingFunc instance
        """
        try:
            # 尝试使用sentence_transformers（如果可用）
            try:
                from sentence_transformers import SentenceTransformer
                
                # 使用产生较小维度嵌入的模型
                model_candidates = [
                    "all-MiniLM-L6-v2",  # 384维
                    "all-MiniLM-L12-v2", # 384维
                    "paraphrase-MiniLM-L6-v2", # 384维
                ]
                
                for model_name in model_candidates:
                    try:
                        model = SentenceTransformer(model_name)
                        
                        async def sentence_transformer_embedding(texts):
                            """异步嵌入函数包装器"""
                            import numpy as np
                            if isinstance(texts, str):
                                texts = [texts]
                            
                            # 在新线程中运行同步编码
                            import asyncio
                            loop = asyncio.get_event_loop()
                            embeddings = await loop.run_in_executor(
                                None, model.encode, texts, {"convert_to_numpy": True}
                            )
                            
                            # 调整到1024维
                            if embeddings.shape[1] < 1024:
                                padding_size = 1024 - embeddings.shape[1]
                                padding = np.zeros((embeddings.shape[0], padding_size))
                                embeddings = np.concatenate([embeddings, padding], axis=1)
                            elif embeddings.shape[1] > 1024:
                                embeddings = embeddings[:, :1024]
                            
                            return embeddings
                        
                        # 创建符合nano-graphrag要求的EmbeddingFunc
                        from nano_graphrag._utils import EmbeddingFunc
                        embedding_func = EmbeddingFunc(
                            embedding_dim=1024,
                            max_token_size=512,
                            func=sentence_transformer_embedding
                        )
                        
                        self.logger.info(f"Using embedding model: {model_name} (adjusted to 1024-dim)")
                        return embedding_func
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load model {model_name}: {e}")
                        continue
                        
            except ImportError:
                self.logger.warning("sentence_transformers not available, using simple embedding")
            
            # 如果sentence_transformers不可用，使用简单的嵌入
            async def simple_embedding_func(texts):
                """简单的嵌入函数（基于文本哈希和长度）"""
                import numpy as np
                import hashlib
                
                if isinstance(texts, str):
                    texts = [texts]
                
                embeddings = []
                for text in texts:
                    # 基于文本内容生成确定性嵌入
                    text_hash = hashlib.md5(text.encode()).hexdigest()
                    hash_nums = [int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)]
                    
                    # 创建1024维向量
                    embedding = np.zeros(1024)
                    for i, num in enumerate(hash_nums):
                        if i < 1024:
                            embedding[i] = (num - 128) / 128.0  # 归一化到[-1, 1]
                    
                    # 添加文本长度特征
                    text_len_norm = min(len(text) / 1000.0, 1.0)  # 归一化文本长度
                    embedding[1023] = text_len_norm
                    
                    embeddings.append(embedding)
                
                return np.array(embeddings)
            
            # 创建符合nano-graphrag要求的EmbeddingFunc
            from nano_graphrag._utils import EmbeddingFunc
            embedding_func = EmbeddingFunc(
                embedding_dim=1024,
                max_token_size=512,
                func=simple_embedding_func
            )
            
            self.logger.info("Using simple hash-based 1024-dim embeddings")
            return embedding_func
            
        except Exception as e:
            self.logger.error(f"Failed to create embedding function: {e}")
            return None
    
    def _execute_sync_query(self, rag, query: str, query_param):
        """执行同步GraphRAG查询，避免事件循环冲突"""
        try:
            import asyncio
            import concurrent.futures
            
            # 创建新的事件循环在单独线程中运行
            def run_async_query():
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(rag.aquery(query, param=query_param))
                finally:
                    loop.close()
            
            # 在线程池中执行异步查询
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_query)
                result = future.result(timeout=30)
                return result
                
        except Exception as e:
            self.logger.error(f"Error in sync query execution: {e}")
            raise e
    
    def _get_direct_content_from_documents(self, concept_name: str, query: str) -> Optional[Dict[str, Any]]:
        """直接从文档文件获取内容"""
        try:
            if concept_name not in self._concept_databases:
                return None
            
            db_info = self._concept_databases[concept_name]
            working_dir = Path(db_info["path"])
            
            # 尝试从full_docs.json读取
            full_docs_file = working_dir / "kv_store_full_docs.json"
            text_chunks_file = working_dir / "kv_store_text_chunks.json"
            
            content_pieces = []
            
            # 读取完整文档
            if full_docs_file.exists():
                try:
                    import json
                    with open(full_docs_file, 'r', encoding='utf-8') as f:
                        full_docs = json.load(f)
                    
                    for doc_id, doc_content in full_docs.items():
                        if isinstance(doc_content, dict):
                            content = doc_content.get('content', '')
                        else:
                            content = str(doc_content)
                        
                        if content and len(content.strip()) > 50:  # 过滤过短的内容
                            content_pieces.append(content.strip())
                            
                except Exception as e:
                    self.logger.debug(f"Failed to read full_docs for {concept_name}: {e}")
            
            # 读取文本块
            if text_chunks_file.exists():
                try:
                    import json
                    with open(text_chunks_file, 'r', encoding='utf-8') as f:
                        text_chunks = json.load(f)
                    
                    for chunk_id, chunk_content in text_chunks.items():
                        if isinstance(chunk_content, dict):
                            content = chunk_content.get('content', '')
                        else:
                            content = str(chunk_content)
                        
                        if content and len(content.strip()) > 50:
                            content_pieces.append(content.strip())
                            
                except Exception as e:
                    self.logger.debug(f"Failed to read text_chunks for {concept_name}: {e}")
            
            if not content_pieces:
                return None
            
            # 合并内容并计算相关性
            combined_content = "\n\n".join(content_pieces[:3])  # 最多使用前3个内容片段
            
            # 计算相关性分数
            relevance_score = self._calculate_relevance_score(query, combined_content)
            
            if relevance_score < 0.1:
                return None
            
            return {
                "concept": concept_name,
                "query": query,
                "content": combined_content,
                "source": f"direct_documents:{concept_name}",
                "strategy": "direct_content",
                "priority": 1.0,
                "relevance_score": relevance_score,
                "content_length": len(combined_content),
                "real_retrieval": True
            }
            
        except Exception as e:
            self.logger.debug(f"Direct content retrieval failed for {concept_name}: {e}")
            return None
    

    
    def _load_concept_database(self, concept_name: str) -> Optional[object]:
        """加载指定概念的数据库（真实实现）"""
        if concept_name not in self._concept_databases:
            return None
        
        if not GRAPHRAG_AVAILABLE:
            self.logger.warning("nano-graphrag not available, cannot load real database")
            return None
        
        db_info = self._concept_databases[concept_name]
        
        # 如果已经加载，直接返回
        if db_info["loaded"] and db_info["rag_instance"]:
            return db_info["rag_instance"]
        
        try:
            working_dir = db_info["path"]
            working_path = Path(working_dir)
            
            # 检查必要文件是否存在
            if not working_path.exists():
                self.logger.warning(f"Working directory not found: {working_dir}")
                return None
            
            # 检查必要的缓存文件
            required_files = [
                "kv_store_full_docs.json",
                "kv_store_text_chunks.json", 
                "graph_chunk_entity_relation.graphml"
            ]
            
            missing_files = []
            for file_name in required_files:
                if not (working_path / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                self.logger.warning(f"Missing required files for {concept_name}: {missing_files}")
                return None
            
            # 创建真实的GraphRAG实例
            # 配置为使用1024维嵌入模型（兼容现有数据库）
            try:
                # 使用1024维嵌入模型配置
                from nano_graphrag import GraphRAG
                
                rag = GraphRAG(
                    working_dir=working_dir,
                    enable_llm_cache=False,  # 禁用LLM缓存
                    enable_naive_rag=True,   # 启用naive模式，直接返回检索内容
                    enable_local=False,      # 禁用local模式
                    # 配置使用1024维嵌入模型
                    embedding_func_max_async=16,
                    embedding_batch_num=512,
                    embedding_func=self._get_1024_embedding_func()
                )
                
                self.logger.info(f"Successfully loaded concept database with 1024-dim embedding: {concept_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load concept database {concept_name}: {e}")
                return None
            
            # 缓存实例
            db_info["rag_instance"] = rag
            db_info["loaded"] = True
            
            self.logger.info(f"Loaded real concept database: {concept_name}")
            return rag
            
        except Exception as e:
            self.logger.error(f"Failed to load concept database {concept_name}: {e}")
            return None
    
    def _get_cache_key(self, query: str, concept: str = None) -> str:
        """生成缓存键"""
        cache_str = f"{query}:{concept}" if concept else query
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取结果"""
        if cache_key not in self._query_cache:
            return None
        
        cached_data = self._query_cache[cache_key]
        # 检查是否过期
        if time.time() - cached_data['timestamp'] > self._cache_ttl:
            del self._query_cache[cache_key]
            return None
        
        return cached_data['result']
    
    def _set_cache(self, cache_key: str, result: Dict[str, Any]):
        """设置缓存"""
        # 限制缓存大小
        if len(self._query_cache) >= self._max_cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self._query_cache.keys(), 
                           key=lambda k: self._query_cache[k]['timestamp'])
            del self._query_cache[oldest_key]
        
        self._query_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def _clear_cache(self):
        """清除缓存"""
        self._query_cache.clear()
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        # 检查决策代理的建议
        if hasattr(state, 'retrieval_decision'):
            if not state.retrieval_decision.get('need_retrieval', True):
                self.logger.debug("Retrieval decision indicates no retrieval needed")
                return False
        
        # 检查基本条件
        if state.interpretation is None:
            self.logger.debug("No interpretation available")
            return False
            
        if state.query_type not in [QueryType.KNOWLEDGE_RETRIEVAL, QueryType.CONCEPT_EXPLANATION]:
            self.logger.debug(f"Query type {state.query_type} not suitable for knowledge retrieval")
            # 放宽条件：如果没有明确的查询类型，也尝试检索
            if state.query_type is None:
                return True
            return False
            
        if len(self._concept_databases) == 0:
            self.logger.debug("No concept databases available")
            # 即使没有数据库，也可以执行（使用模拟数据）
            return True
        
        return True
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行优化的知识检索"""
        try:
            # 1. 获取决策代理的优化查询策略
            optimized_queries = self._get_optimized_queries(state)
            
            # 2. 确定要搜索的概念
            target_concepts = self._identify_target_concepts_enhanced(state)
            
            if not target_concepts:
                self.logger.warning("No target concepts identified for retrieval")
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
            
            # 4. 并发执行检索任务
            retrieval_results = await self._execute_concurrent_retrieval(
                optimized_queries, target_concepts
            )
            successful_sources = list(set([r.get('source', '') for r in retrieval_results if r.get('source')]))
            
            # 4. 如果没有找到相关概念，尝试全局搜索
            if not retrieval_results:
                for query_info in optimized_queries[:2]:  # 只用前2个查询进行全局搜索
                    global_results = self._global_search_enhanced(query_info['query'], query_info['strategy'])
                    if global_results:
                        retrieval_results.extend(global_results)
                        if "global_search" not in successful_sources:
                            successful_sources.append("global_search")
            
            # 5. 按相关性排序和去重
            retrieval_results = self._rank_and_deduplicate_results(retrieval_results)
            
            # 6. 整理检索结果并缓存
            knowledge_result = {
                "target_concepts": target_concepts,
                "successful_sources": successful_sources,
                "results": retrieval_results,
                "total_results": len(retrieval_results),
                "optimized_queries_used": len(optimized_queries),
                "retrieval_strategy": "enhanced_multi_query_cached",
                "message": f"使用 {len(optimized_queries)} 个优化查询从 {len(successful_sources)} 个知识源检索到 {len(retrieval_results)} 条相关信息"
            }
            
            # 缓存结果
            self._set_cache(cache_key, knowledge_result)
            state.retrieved_knowledge = knowledge_result
            
            state.knowledge_sources = successful_sources
            
            self.logger.info(f"Enhanced retrieval: {len(retrieval_results)} results from {len(successful_sources)} sources using {len(optimized_queries)} queries")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Enhanced knowledge retrieval failed: {e}")
            state.set_error(
                "knowledge_retrieval_error",
                f"Failed to retrieve knowledge: {str(e)}"
            )
            return state
    
    def _identify_target_concepts(self, state: AgentState) -> List[str]:
        """识别目标概念"""
        target_concepts = []
        
        # 从解释结果中获取关键词
        if state.interpretation and "keywords" in state.interpretation:
            keywords = state.interpretation["keywords"]
            
            # 匹配概念名称
            for keyword in keywords:
                for concept_name in self._concept_databases.keys():
                    # 简单的字符串匹配
                    if keyword.lower() in concept_name.lower() or concept_name.lower() in keyword.lower():
                        if concept_name not in target_concepts:
                            target_concepts.append(concept_name)
        
        # 如果没有找到匹配的概念，尝试从查询中直接匹配
        if not target_concepts:
            query_lower = state.user_query.lower()
            for concept_name in self._concept_databases.keys():
                if concept_name.lower() in query_lower:
                    target_concepts.append(concept_name)
        
        # 限制概念数量，避免检索过多
        return target_concepts[:5]
    
    def _retrieve_from_concept(self, concept_name: str, query: str) -> Optional[Dict[str, Any]]:
        """从指定概念检索信息"""
        try:
            rag = self._load_concept_database(concept_name)
            if not rag:
                return None
            
            # 执行查询
            result = rag.query(query, param=QueryParam(mode="global"))
            
            return {
                "concept": concept_name,
                "query": query,
                "content": result,
                "source": f"concept_database:{concept_name}",
                "relevance_score": self._calculate_relevance_score(query, result)
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve from concept {concept_name}: {e}")
            return None
    
    def _global_search(self, query: str) -> List[Dict[str, Any]]:
        """全局搜索（在所有概念中搜索）"""
        results = []
        
        # 尝试在前几个概念数据库中搜索
        concept_names = list(self._concept_databases.keys())[:3]  # 限制搜索范围
        
        for concept_name in concept_names:
            try:
                result = self._retrieve_from_concept(concept_name, query)
                if result and result["relevance_score"] > 0.3:  # 只保留相关性较高的结果
                    results.append(result)
            except Exception as e:
                self.logger.debug(f"Global search failed for {concept_name}: {e}")
        
        return results
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """计算相关性分数"""
        try:
            # 简单的相关性计算
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            
            if not query_words:
                return 0.0
            
            # 计算交集比例
            intersection = query_words.intersection(content_words)
            score = len(intersection) / len(query_words)
            
            # 考虑内容长度
            if len(content) > 100:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5  # 默认中等相关性
    
    def get_available_concepts(self) -> List[str]:
        """获取可用的概念列表"""
        return list(self._concept_databases.keys())
    
    def get_concept_info(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """获取概念信息"""
        if concept_name not in self._concept_databases:
            return None
        
        db_info = self._concept_databases[concept_name]
        return {
            "name": concept_name,
            "path": db_info["path"],
            "loaded": db_info["loaded"],
            "available": os.path.exists(db_info["path"])
        }
    
    def reload_databases(self):
        """重新加载数据库"""
        self._concept_databases.clear()
        self._initialize_databases()
        self.logger.info("Reloaded knowledge databases")
    
    def _get_optimized_queries(self, state: AgentState) -> List[Dict[str, Any]]:
        """获取决策代理提供的优化查询
        
        Args:
            state: 当前状态
            
        Returns:
            优化查询列表
        """
        # 如果有决策代理的优化查询，使用它们
        if (hasattr(state, 'retrieval_decision') and 
            'optimized_queries' in state.retrieval_decision):
            return state.retrieval_decision['optimized_queries']
        
        # 否则创建基本查询
        return [{
            'query': state.user_query,
            'type': 'original',
            'priority': 1.0,
            'strategy': 'exact_match'
        }]
    
    def _identify_target_concepts_enhanced(self, state: AgentState) -> List[str]:
        """增强版概念识别
        
        Args:
            state: 当前状态
            
        Returns:
            目标概念列表
        """
        target_concepts = []
        
        # 1. 从决策代理的核心概念中获取
        if (hasattr(state, 'retrieval_decision') and 
            'core_concepts' in state.retrieval_decision):
            core_concepts = state.retrieval_decision['core_concepts']
            
            for concept in core_concepts:
                for concept_name in self._concept_databases.keys():
                    if (concept.lower() in concept_name.lower() or 
                        concept_name.lower() in concept.lower()):
                        if concept_name not in target_concepts:
                            target_concepts.append(concept_name)
        
        # 2. 从解释结果中获取关键词
        if state.interpretation and "keywords" in state.interpretation:
            keywords = state.interpretation["keywords"]
            
            for keyword in keywords:
                for concept_name in self._concept_databases.keys():
                    if (keyword.lower() in concept_name.lower() or 
                        concept_name.lower() in keyword.lower()):
                        if concept_name not in target_concepts:
                            target_concepts.append(concept_name)
        
        # 3. 如果没有找到匹配的概念，尝试从查询中直接匹配
        if not target_concepts:
            query_lower = state.user_query.lower()
            for concept_name in self._concept_databases.keys():
                if concept_name.lower() in query_lower:
                    target_concepts.append(concept_name)
        
        # 4. 如果仍然没有找到，使用所有可用概念（限制数量）
        if not target_concepts:
            target_concepts = list(self._concept_databases.keys())[:3]
        
        return target_concepts[:5]  # 最多返回5个概念
    
    def _retrieve_from_concept_enhanced(self, concept_name: str, query: str, 
                                      strategy: str, priority: float) -> Optional[Dict[str, Any]]:
        """真实概念检索
        
        Args:
            concept_name: 概念名称
            query: 查询字符串
            strategy: 检索策略
            priority: 优先级
            
        Returns:
            检索结果或None
        """
        try:
            rag = self._load_concept_database(concept_name)
            if not rag:
                self.logger.debug(f"No RAG database available for concept: {concept_name}")
                return None
            
            # 根据策略调整查询参数
            query_param = self._get_query_param_by_strategy(strategy)
            
            # 首先尝试直接从文档获取内容
            direct_content = self._get_direct_content_from_documents(concept_name, query)
            if direct_content:
                self.logger.info(f"Found direct content from documents for {concept_name}")
                return direct_content
            
            # 如果直接检索失败，尝试GraphRAG查询
            try:
                # 使用同步查询方法避免事件循环冲突
                result = self._execute_sync_query(rag, query, query_param)
            except Exception as e:
                self.logger.warning(f"GraphRAG query failed for {concept_name}: {e}")
                return None
            
            # 检查结果是否有效
            if not result or not str(result).strip():
                self.logger.debug(f"No valid content returned for {concept_name} with query: {query}")
                return None
            
            result_str = str(result).strip()
            
            # 计算相关性分数
            relevance_score = self._calculate_enhanced_relevance_score(
                query, result_str, strategy, priority
            )
            
            # 过滤低相关性结果
            if relevance_score < 0.1:
                self.logger.debug(f"Low relevance score ({relevance_score:.3f}) for {concept_name}")
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
            self.logger.warning(f"Real retrieval failed for concept {concept_name}: {e}")
            return None
    
    def _global_search_enhanced(self, query: str, strategy: str) -> List[Dict[str, Any]]:
        """真实全局搜索（无模拟）
        
        Args:
            query: 查询字符串
            strategy: 检索策略
            
        Returns:
            检索结果列表
        """
        results = []
        
        # 根据策略选择搜索范围
        if strategy == 'concept_match':
            search_limit = 5
        elif strategy == 'multi_concept_match':
            search_limit = 3
        else:
            search_limit = 2
        
        concept_names = list(self._concept_databases.keys())[:search_limit]
        
        for concept_name in concept_names:
            try:
                result = self._retrieve_from_concept_enhanced(
                    concept_name, query, strategy, 0.5
                )
                if result and result.get("relevance_score", 0) > 0.2:
                    result["search_type"] = "global_real"
                    results.append(result)
            except Exception as e:
                self.logger.debug(f"Real global search failed for {concept_name}: {e}")
        
        if not results:
            self.logger.info(f"No real results found in global search for: {query}")
        else:
            self.logger.info(f"Global search found {len(results)} real results for: {query}")
        
        return results
    
    def _get_query_param_by_strategy(self, strategy: str):
        """根据策略获取查询参数
        
        Args:
            strategy: 检索策略
            
        Returns:
            QueryParam对象
        """
        from nano_graphrag.base import QueryParam
        
        # 使用naive模式直接返回检索到的原始内容，不经过LLM处理
        return QueryParam(
            mode="naive",
            only_need_context=True,  # 只需要上下文，不需要生成回答
            top_k=10
        )
    
    def _calculate_enhanced_relevance_score(self, query: str, content: str, 
                                          strategy: str, priority: float) -> float:
        """计算增强的相关性分数（优化算法）
        
        Args:
            query: 查询字符串
            content: 内容
            strategy: 检索策略
            priority: 优先级
            
        Returns:
            相关性分数 (0.0-1.0)
        """
        try:
            if not content or not query:
                return 0.0
            
            query_lower = query.lower()
            content_lower = content.lower()
            
            # 1. 基础相关性分数
            base_score = self._calculate_relevance_score(query, content)
            
            # 2. 改进的策略权重
            strategy_weights = {
                'exact_match': 1.3,
                'concept_match': 1.2,
                'multi_concept_match': 1.25,
                'keyword_match': 1.0,
                'semantic_match': 1.15
            }
            strategy_weight = strategy_weights.get(strategy, 1.0)
            
            # 3. 关键词匹配分析
            query_words = set(query_lower.split())
            content_words = content_lower.split()
            
            if content_words:
                # 关键词覆盖度
                matched_words = query_words.intersection(set(content_words))
                coverage_score = len(matched_words) / len(query_words) if query_words else 0
                
                # 关键词密度
                keyword_density = sum(content_words.count(word) for word in matched_words) / len(content_words)
                
                # 位置权重（关键词在开头的权重更高）
                position_weight = self._calculate_position_weight_simple(matched_words, content_lower)
            else:
                coverage_score = keyword_density = position_weight = 0.0
            
            # 4. 内容质量评估
            content_quality = self._assess_content_quality(content)
            
            # 5. 长度标准化
            length_factor = min(1.0, len(content) / max(len(query) * 3, 50))
            
            # 6. 综合评分（优化权重分配）
            enhanced_score = (
                base_score * 0.35 +
                coverage_score * 0.25 +
                keyword_density * 0.15 +
                position_weight * 0.10 +
                content_quality * 0.10 +
                length_factor * 0.05
            )
            
            # 7. 应用策略权重和优先级
            final_score = enhanced_score * strategy_weight * min(priority, 1.0)
            
            return min(final_score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"相关性计算异常: {e}")
            return 0.3  # 返回默认分数
    
    def _calculate_position_weight_simple(self, matched_words: set, content: str) -> float:
        """计算位置权重（简化版）"""
        if not matched_words or not content:
            return 0.0
        
        total_weight = 0.0
        content_len = len(content)
        
        for word in matched_words:
            pos = content.find(word)
            if pos >= 0:
                # 越靠前权重越高
                weight = max(0.3, 1.0 - (pos / content_len) * 0.7)
                total_weight += weight
        
        return total_weight / len(matched_words)
    
    def _assess_content_quality(self, content: str) -> float:
        """评估内容质量
        
        Args:
            content: 内容字符串
            
        Returns:
            质量分数
        """
        if not content:
            return 0.0
        
        # 长度评估
        length_score = min(len(content) / 200, 1.0)
        
        # 结构评估（是否包含标点符号等）
        structure_indicators = ['.', '。', ':', '：', '\n', '；', ';']
        structure_score = min(
            sum(1 for indicator in structure_indicators if indicator in content) / 5,
            1.0
        )
        
        # 信息密度评估
        words = content.split()
        unique_words = set(words)
        density_score = len(unique_words) / max(len(words), 1) if words else 0
        
        return (length_score * 0.4 + structure_score * 0.3 + density_score * 0.3)
    
    def _rank_and_deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对结果进行排序和去重
        
        Args:
            results: 原始结果列表
            
        Returns:
            排序去重后的结果列表
        """
        if not results:
            return []
        
        # 去重（基于内容相似性）
        unique_results = []
        seen_contents = set()
        
        for result in results:
            content = result.get('content', '')
            content_hash = hash(content[:100])  # 使用前100个字符的哈希
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        # 按相关性分数排序
        unique_results.sort(
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
        
        # 限制结果数量
        return unique_results[:10]
    
    async def _execute_concurrent_retrieval(self, optimized_queries: List[Dict], target_concepts: List[str]) -> List[Dict[str, Any]]:
        """并发执行检索任务"""
        tasks = []
        
        # 创建检索任务
        for query_info in optimized_queries:
            for concept in target_concepts:
                task = asyncio.create_task(
                    self._retrieve_from_concept_async(
                        concept, 
                        query_info['query'], 
                        query_info['strategy'], 
                        query_info['priority']
                    )
                )
                tasks.append(task)
        
        # 并发执行任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功的结果
        retrieval_results = []
        for result in results:
            if isinstance(result, dict) and result:
                retrieval_results.append(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"检索任务失败: {result}")
        
        return retrieval_results
    
    async def _retrieve_from_concept_async(self, concept: str, query: str, strategy: str, priority: float) -> Optional[Dict[str, Any]]:
        """异步版本的概念检索"""
        try:
            # 在线程池中执行同步检索
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._retrieve_from_concept_enhanced,
                concept, query, strategy, priority
            )
            return result
        except Exception as e:
            self.logger.error(f"异步检索失败 {concept}: {e}")
            return None
    
    async def _execute_global_search(self, query_infos: List[Dict]) -> List[Dict[str, Any]]:
        """并发执行全局搜索"""
        tasks = []
        
        for query_info in query_infos:
            task = asyncio.create_task(
                self._global_search_async(query_info['query'], query_info['strategy'])
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        global_results = []
        for result in results:
            if isinstance(result, list):
                global_results.extend(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"全局搜索失败: {result}")
        
        return global_results
    
    async def _global_search_async(self, query: str, strategy: str) -> List[Dict[str, Any]]:
        """异步版本的全局搜索"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._global_search_enhanced,
                query, strategy
            )
            return result if result else []
        except Exception as e:
            self.logger.error(f"异步全局搜索失败: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self._query_cache),
            "max_cache_size": self._max_cache_size,
            "cache_ttl": self._cache_ttl,
            "hit_ratio": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1)
        }
    
    def optimize_cache(self):
        """优化缓存（清理过期项）"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._query_cache.items()
            if current_time - data['timestamp'] > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._query_cache[key]
        
        self.logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def shutdown(self):
        """清理资源"""
        try:
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=True)
            self._clear_cache()
            self.logger.info("知识检索器已清理完成")
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass  # 避免析构时出错