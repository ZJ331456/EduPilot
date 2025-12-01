#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识检索器智能体
从nano-graphrag知识库中检索相关信息
"""

import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.infrastructure.utils import BaseAgent, AgentState, QueryType
from src.infrastructure.nano_graphrag import GraphRAG, QueryParam


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
		# from config import get_knowledge_base_config
        
		# kb_config = get_knowledge_base_config()
        # 		# 默认配置
		kb_config = {
			'root_dir': "concept_knowledge_bases",
			'default_kb': "default",
			'embedding_model': "sentence-transformers/all-MiniLM-L6-v2",
			'vector_db': "hnswlib",
			'graph_db': "networkx"
		}
		# 使用相对路径指向项目根目录
		# 从 src/domain/agents/knowledge_retriever/agent.py 到项目根需要5层parent
		# agent.py -> knowledge_retriever/ -> agents/ -> domain/ -> src/ -> 项目根
		project_root = Path(__file__).parent.parent.parent.parent.parent
		kb_dir = knowledge_base_dir or kb_config.get('root_dir', "concept_knowledge_bases")
		self.knowledge_base_dir = project_root / kb_dir
        
		# 检查知识库目录是否存在
		if not self.knowledge_base_dir.exists():
			self.logger.warning(f"Knowledge base directory not found: {self.knowledge_base_dir}")
			# 尝试使用绝对路径
			self.knowledge_base_dir = Path(kb_dir).resolve()
			if not self.knowledge_base_dir.exists():
				self.logger.warning(f"Knowledge base directory still not found: {self.knowledge_base_dir}")
        
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
						from infrastructure.nano_graphrag._utils import EmbeddingFunc
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
			from infrastructure.nano_graphrag._utils import EmbeddingFunc
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
		# 放宽条件：允许在各种情况下执行知识检索
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
		"""识别目标概念（增强版：支持模糊匹配和分词）"""
		# 收集所有可能的关键词
		keywords = []
		if state.interpretation and "keywords" in state.interpretation:
			keywords.extend(state.interpretation["keywords"])
		
		# 添加原始查询作为关键词
		keywords.append(state.user_query)
		
		# 概念匹配得分
		concept_scores = {}
		
		for concept_name in self._concept_databases.keys():
			max_score = 0.0
			
			for keyword in keywords:
				# 方法1: 完整字符串包含匹配（高权重）
				if concept_name.lower() in keyword.lower():
					max_score = max(max_score, 1.0)
					continue
				if keyword.lower() in concept_name.lower():
					max_score = max(max_score, 0.9)
					continue
				
				# 方法2: 分词部分匹配（中权重）
				concept_chars = list(concept_name)
				keyword_lower = keyword.lower()
				
				# 检查概念名称的每个字是否在关键词中
				matches = sum(1 for char in concept_chars if char in keyword_lower)
				if matches > 0:
					char_match_score = matches / len(concept_chars) * 0.8
					max_score = max(max_score, char_match_score)
				
				# 方法3: 模糊字符串相似度（低权重）
				similarity = SequenceMatcher(None, concept_name.lower(), keyword.lower()).ratio()
				if similarity > 0.5:  # 相似度阈值
					max_score = max(max_score, similarity * 0.7)
			
			if max_score > 0.4:  # 最低匹配阈值
				concept_scores[concept_name] = max_score
		
		# 按得分排序，返回前5个
		sorted_concepts = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)
		target_concepts = [concept for concept, score in sorted_concepts[:5]]
		
		if target_concepts:
			self.logger.info(f"识别到相关概念: {target_concepts} (得分: {[f'{s:.2f}' for _, s in sorted_concepts[:5]]})")
		else:
			self.logger.warning(f"未能识别到相关概念，查询: {state.user_query}")
		
		return target_concepts

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
		"""🔧 增强的相关性计算算法"""
		try:
			if not query or not content:
				return 0.0
			
			query_lower = query.lower()
			content_lower = content.lower()
			
			# 1. 词汇匹配分数（基础分数）
			word_match_score = self._calculate_word_match_score(query_lower, content_lower)
			
			# 2. 语义相似度分数
			semantic_score = self._calculate_semantic_similarity(query_lower, content_lower)
			
			# 3. 结构化匹配分数（针对特定格式）
			structural_score = self._calculate_structural_match_score(query_lower, content_lower)
			
			# 4. 上下文相关性分数
			context_score = self._calculate_context_relevance(query_lower, content_lower)
			
			# 5. 内容质量分数
			quality_score = self._calculate_content_quality_score(content)
			
			# 综合计算最终分数
			final_score = (
				word_match_score * 0.4 +
				semantic_score * 0.25 +
				structural_score * 0.15 +
				context_score * 0.15 +
				quality_score * 0.05
			)
			
			# 应用长度调整
			length_adjustment = self._calculate_length_adjustment(query, content)
			final_score = final_score * length_adjustment
			
			return min(max(final_score, 0.0), 1.0)
			
		except Exception as e:
			self.logger.warning(f"相关性计算失败: {e}")
			return 0.1  # 降低默认分数
	
	def _calculate_word_match_score(self, query: str, content: str) -> float:
		"""计算词汇匹配分数（增强版）"""
		query_words = set(query.split())
		content_words = set(content.split())
		
		if not query_words:
			return 0.0
		
		# 精确匹配
		exact_matches = query_words.intersection(content_words)
		exact_score = len(exact_matches) / len(query_words)
		
		# 部分匹配（子字符串）
		partial_matches = 0
		for q_word in query_words:
			if q_word not in exact_matches:
				for c_word in content_words:
					if q_word in c_word or c_word in q_word:
						partial_matches += 1
						break
		
		partial_score = partial_matches / len(query_words) * 0.5
		
		return exact_score + partial_score
	
	def _calculate_semantic_similarity(self, query: str, content: str) -> float:
		"""计算语义相似度（简化版）"""
		# 简化的语义相似度计算
		# 在没有复杂NLP模型的情况下，使用关键词语义关联
		
		semantic_keywords = {
			'历史': ['古代', '朝代', '时期', '年代', '历史', '文化', '传统'],
			'政治': ['政治', '政府', '制度', '法律', '统治', '权力'],
			'文化': ['文化', '艺术', '文学', '思想', '哲学', '宗教'],
			'经济': ['经济', '贸易', '商业', '农业', '工业', '财政'],
			'社会': ['社会', '民族', '人民', '阶级', '等级', '身份']
		}
		
		query_themes = set()
		content_themes = set()
		
		# 识别查询和内容的主题
		for theme, keywords in semantic_keywords.items():
			if any(keyword in query for keyword in keywords):
				query_themes.add(theme)
			if any(keyword in content for keyword in keywords):
				content_themes.add(theme)
		
		if not query_themes:
			return 0.3  # 无法识别主题时给予基础分数
		
		# 计算主题重叠度
		theme_overlap = len(query_themes.intersection(content_themes))
		semantic_score = theme_overlap / len(query_themes)
		
		return semantic_score
	
	def _calculate_structural_match_score(self, query: str, content: str) -> float:
		"""计算结构化匹配分数"""
		structural_score = 0.0
		
		# 检查是否包含查询的完整短语
		query_phrases = self._extract_phrases(query)
		for phrase in query_phrases:
			if phrase in content:
				structural_score += 0.3
		
		# 检查是否有定义性内容
		definition_patterns = ['是一', '指的是', '定义为', '含义', '概念']
		if any(pattern in content for pattern in definition_patterns):
			structural_score += 0.2
		
		# 检查是否有详细说明
		explanation_patterns = ['因为', '所以', '由于', '原因', '影响', '作用']
		explanation_count = sum(1 for pattern in explanation_patterns if pattern in content)
		structural_score += min(explanation_count * 0.1, 0.3)
		
		return min(structural_score, 1.0)
	
	def _calculate_context_relevance(self, query: str, content: str) -> float:
		"""计算上下文相关性"""
		context_score = 0.0
		
		# 检查内容长度合理性
		content_length = len(content)
		if 100 <= content_length <= 2000:
			context_score += 0.3
		elif content_length > 2000:
			context_score += 0.2
		
		# 检查信息密度
		info_density = self._calculate_information_density(content)
		context_score += info_density * 0.4
		
		# 检查是否包含具体信息
		concrete_patterns = ['时间', '地点', '人物', '数字', '年', '月']
		concrete_count = sum(1 for pattern in concrete_patterns if pattern in content)
		context_score += min(concrete_count * 0.05, 0.3)
		
		return min(context_score, 1.0)
	
	def _calculate_content_quality_score(self, content: str) -> float:
		"""计算内容质量分数"""
		quality_score = 0.5  # 基础分数
		
		# 检查内容完整性
		if '...' not in content and '更多' not in content:
			quality_score += 0.2
		
		# 检查信息来源
		if '来源:' in content or 'http' in content:
			quality_score += 0.2
		
		# 检查结构化程度
		if any(marker in content for marker in ['1.', '2.', '一、', '二、', '（1）', '（2）']):
			quality_score += 0.1
		
		return min(quality_score, 1.0)
	
	def _calculate_information_density(self, content: str) -> float:
		"""计算信息密度"""
		# 简单的信息密度计算
		words = content.split()
		if not words:
			return 0.0
		
		# 计算实词比例
		meaningful_words = [word for word in words if len(word) > 1 and word not in ['的', '了', '是', '在', '有', '和']]
		density = len(meaningful_words) / len(words)
		
		return min(density, 1.0)
	
	def _extract_phrases(self, text: str) -> List[str]:
		"""提取短语"""
		# 简单的短语提取
		phrases = []
		words = text.split()
		
		# 提取2-3个词的短语
		for i in range(len(words) - 1):
			if i + 2 <= len(words):
				phrase2 = ' '.join(words[i:i+2])
				if len(phrase2) > 3:
					phrases.append(phrase2)
			
			if i + 3 <= len(words):
				phrase3 = ' '.join(words[i:i+3])
				if len(phrase3) > 5:
					phrases.append(phrase3)
		
		return phrases
	
	def _calculate_length_adjustment(self, query: str, content: str) -> float:
		"""计算长度调整系数"""
		query_len = len(query)
		content_len = len(content)
		
		# 基础调整系数
		adjustment = 1.0
		
		# 内容太短惩罚
		if content_len < 50:
			adjustment *= 0.8
		# 内容适中奖励
		elif 100 <= content_len <= 1000:
			adjustment *= 1.1
		# 内容过长轻微惩罚
		elif content_len > 2000:
			adjustment *= 0.95
		
		# 查询复杂度调整
		if query_len > 10:
			# 复杂查询需要更丰富的内容
			if content_len > 200:
				adjustment *= 1.05
		
		return adjustment

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
		all_concepts = list(self._concept_databases.keys())
        
		# 1. 从决策代理的核心概念中获取
		if (hasattr(state, 'retrieval_decision') and 
			'core_concepts' in state.retrieval_decision):
			core_concepts = state.retrieval_decision['core_concepts']
            
			for concept in core_concepts:
				for concept_name in all_concepts:
					if (concept.lower() in concept_name.lower() or 
						concept_name.lower() in concept.lower()):
						if concept_name not in target_concepts:
							target_concepts.append(concept_name)
        
		# 2. 从解释结果中获取关键词
		if state.interpretation and "keywords" in state.interpretation:
			keywords = state.interpretation["keywords"]
            
			for keyword in keywords:
				for concept_name in all_concepts:
					if (keyword.lower() in concept_name.lower() or 
						concept_name.lower() in keyword.lower()):
						if concept_name not in target_concepts:
							target_concepts.append(concept_name)
        
		# 3. 如果没有找到匹配的概念，尝试从查询中直接匹配
		if not target_concepts:
			query_lower = state.user_query.lower()
			for concept_name in all_concepts:
				if concept_name.lower() in query_lower:
					target_concepts.append(concept_name)
        
		# 4. 🔧 改进：如果仍然没有找到，进行更智能的语义匹配
		if not target_concepts:
			# 提取查询中的关键词（去除停用词）
			query_words = re.findall(r'[\u4e00-\u9fa5]+', state.user_query)  # 提取中文
			query_words = [w for w in query_words if len(w) >= 2]  # 过滤单字
			
			# 停用词列表
			stop_words = {'什么', '怎么', '如何', '为什么', '哪些', '请', '解释', '说明', '介绍', '历史', '时代'}
			query_keywords = [w for w in query_words if w not in stop_words]
			
			if query_keywords:
				# 计算每个概念与查询的相似度
				concept_scores = []
				for concept_name in all_concepts:
					score = sum(1 for kw in query_keywords if kw in concept_name)
					if score > 0:
						concept_scores.append((concept_name, score))
				
				# 按相似度排序并选择top概念
				if concept_scores:
					concept_scores.sort(key=lambda x: x[1], reverse=True)
					target_concepts = [c[0] for c in concept_scores[:5]]
					self.logger.info(f"通过语义匹配找到概念: {target_concepts}")
        
		# 5. 🔧 最后fallback：不返回固定的前3个，而是返回空列表
		# 让全局搜索来处理
		if not target_concepts:
			self.logger.warning(f"未能识别到相关概念，查询: {state.user_query}")
			return []  # ✅ 返回空列表而非固定前3个
        
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
        
		concept_candidates = list(self._concept_databases.keys())[:max(search_limit, 1)]
        
		for concept_name in concept_candidates:
			result = self._retrieve_from_concept_enhanced(concept_name, query, strategy, 0.5)
			if result:
				results.append(result)
        
		return results

	async def _execute_concurrent_retrieval(self, optimized_queries: List[Dict[str, Any]],
						 target_concepts: List[str]) -> List[Dict[str, Any]]:
		"""并发执行检索任务"""
		if not optimized_queries or not target_concepts:
			return []

		tasks: List[asyncio.Task] = []
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

		results: List[Dict[str, Any]] = []
		completed, pending = await asyncio.wait(tasks, timeout=15)

		for task in completed:
			try:
				result = task.result()
				if result:
					results.append(result)
			except Exception as e:
				self.logger.debug(f"Task failed: {e}")

		for task in pending:
			task.cancel()

		return results

	async def _retrieve_with_timeout(self, concept: str, query: str, strategy: str, priority: float):
		try:
			return await asyncio.wait_for(
				self._retrieve_async(concept, query, strategy, priority),
				timeout=8
			)
		except asyncio.TimeoutError:
			self.logger.debug(f"Retrieval timed out for {concept}")
			return None

	async def _retrieve_async(self, concept: str, query: str, strategy: str, priority: float):
		loop = asyncio.get_running_loop()
		return await loop.run_in_executor(
			self._executor,
			self._retrieve_from_concept_enhanced,
			concept,
			query,
			strategy,
			priority
		)

	def _calculate_enhanced_relevance_score(self, query: str, content: str,
										   strategy: str, priority: float) -> float:
		"""计算增强相关性分数"""
		base_score = self._calculate_relevance_score(query, content)
        
		strategy_weights = {
			'exact_match': 1.0,
			'concept_match': 0.9,
			'multi_concept_match': 0.85,
			'semantic_expansion': 0.8,
			'keyword_search': 0.7
		}
        
		strategy_bonus = strategy_weights.get(strategy, 0.75)
		length_bonus = min(len(content) / 1000, 0.2)
		priority_bonus = min(priority, 1.0) * 0.1
        
		final_score = base_score * strategy_bonus + length_bonus + priority_bonus
		return min(final_score, 1.0)

	def _rank_and_deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""对结果排序并去重"""
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

	def _get_query_param_by_strategy(self, strategy: str):
		"""根据策略返回对应的QueryParam"""
		strategy_mapping = {
			'exact_match': QueryParam(mode="hybrid", top_k=5),
			'concept_match': QueryParam(mode="global", top_k=5),
			'multi_concept_match': QueryParam(mode="local", top_k=4),
			'semantic_expansion': QueryParam(mode="hybrid", top_k=6),
			'keyword_search': QueryParam(mode="naive", top_k=5)
		}
        
		return strategy_mapping.get(strategy, QueryParam(mode="hybrid", top_k=5))

	def summarize_retrieval(self, retrieval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""总结检索结果"""
		if not retrieval_results:
			return {
				"summary": "未找到相关信息",
				"key_points": [],
				"sources": [],
				"confidence": 0.0
			}
        
		key_points = []
		sources = set()
		total_score = 0
        
		for result in retrieval_results[:5]:
			content = result.get('content', '')
			if content:
				# 提取前几句作为要点
				sentences = content.split('。')
				key_points.append(sentences[0].strip())
			sources.add(result.get('source', 'unknown'))
			total_score += result.get('relevance_score', 0)
        
		avg_score = total_score / len(retrieval_results) if retrieval_results else 0
        
		return {
			"summary": "；".join(key_points[:3]),
			"key_points": key_points,
			"sources": list(sources),
			"confidence": min(avg_score + 0.1, 1.0)
		}

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

	# ============================================================================
	# API 支持方法
	# ============================================================================

	def list_knowledge_bases(self) -> List[Dict[str, Any]]:
		"""获取所有可用的知识库列表
		
		Returns:
			List[Dict]: 知识库信息列表
		"""
		try:
			knowledge_bases = []
			
			# 遍历知识库目录
			if self.knowledge_base_dir.exists():
				for kb_dir in self.knowledge_base_dir.iterdir():
					if kb_dir.is_dir() and not kb_dir.name.startswith('.'):
						# 检查是否有知识文件
						knowledge_file = kb_dir / "knowledge.txt"
						graphrag_cache = kb_dir / "graphrag_cache"
						
						if knowledge_file.exists():
							kb_info = {
								"name": kb_dir.name,
								"path": str(kb_dir),
								"type": "GraphRAG" if graphrag_cache.exists() else "Text",
								"has_cache": graphrag_cache.exists(),
								"file_size": knowledge_file.stat().st_size if knowledge_file.exists() else 0,
							}
							knowledge_bases.append(kb_info)
			
			self.logger.info(f"找到 {len(knowledge_bases)} 个知识库")
			return knowledge_bases
			
		except Exception as e:
			self.logger.error(f"获取知识库列表失败: {e}")
			return []

	def get_knowledge_base_info(self, knowledge_base_name: str) -> Optional[Dict[str, Any]]:
		"""获取指定知识库的详细信息
		
		Args:
			knowledge_base_name: 知识库名称
			
		Returns:
			Dict: 知识库详细信息，如果不存在则返回 None
		"""
		try:
			kb_dir = self.knowledge_base_dir / knowledge_base_name
			
			if not kb_dir.exists():
				self.logger.warning(f"知识库不存在: {knowledge_base_name}")
				return None
			
			knowledge_file = kb_dir / "knowledge.txt"
			graphrag_cache = kb_dir / "graphrag_cache"
			
			if not knowledge_file.exists():
				return None
			
			# 读取文件内容获取统计信息
			with open(knowledge_file, 'r', encoding='utf-8') as f:
				content = f.read()
				lines = content.split('\n')
				char_count = len(content)
				
			# 构建详细信息
			kb_info = {
				"name": knowledge_base_name,
				"path": str(kb_dir),
				"type": "GraphRAG" if graphrag_cache.exists() else "Text",
				"has_cache": graphrag_cache.exists(),
				"file_size": knowledge_file.stat().st_size,
				"char_count": char_count,
				"line_count": len(lines),
				"last_modified": knowledge_file.stat().st_mtime,
			}
			
			# 如果有图数据库缓存，获取更多信息
			if graphrag_cache.exists():
				graph_file = graphrag_cache / "graph_chunk_entity_relation.graphml"
				if graph_file.exists():
					kb_info["graph_file"] = str(graph_file)
					kb_info["graph_size"] = graph_file.stat().st_size
			
			return kb_info
			
		except Exception as e:
			self.logger.error(f"获取知识库信息失败: {e}")
			return None

	def get_related_concepts(self, concept_name: str, limit: int = 10) -> List[Dict[str, Any]]:
		"""获取与指定概念相关的其他概念
		
		Args:
			concept_name: 概念名称
			limit: 返回的最大数量
			
		Returns:
			List[Dict]: 相关概念列表
		"""
		try:
			related_concepts = []
			
			# 使用知识图谱查找相关概念
			for kb_name, rag_instance in self._concept_databases.items():
				try:
					# 使用全局模式查询相关概念
					query = f"{concept_name}的相关概念"
					result = rag_instance.query(query, param=QueryParam(mode="global", top_k=limit))
					
					# 解析结果，提取概念
					if result:
						# 简单处理：从内容中提取可能的概念名称
						content = result.split('\n')
						for line in content[:limit]:
							if line.strip() and len(line.strip()) < 50:
								related_concepts.append({
									"concept": line.strip(),
									"source": kb_name,
									"relevance": 0.8  # 默认相关度
								})
				except Exception as e:
					self.logger.warning(f"从 {kb_name} 获取相关概念失败: {e}")
					continue
			
			# 去重和排序
			unique_concepts = {}
			for concept in related_concepts:
				concept_text = concept["concept"]
				if concept_text not in unique_concepts:
					unique_concepts[concept_text] = concept
			
			result_list = list(unique_concepts.values())[:limit]
			return result_list
			
		except Exception as e:
			self.logger.error(f"获取相关概念失败: {e}")
			return []

	def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
		"""根据输入获取搜索建议
		
		Args:
			query: 搜索查询
			limit: 返回的最大数量
			
		Returns:
			List[str]: 搜索建议列表
		"""
		try:
			suggestions = []
			query_lower = query.lower()
			
			# 从知识库目录名称中匹配
			if self.knowledge_base_dir.exists():
				for kb_dir in self.knowledge_base_dir.iterdir():
					if kb_dir.is_dir() and not kb_dir.name.startswith('.'):
						kb_name = kb_dir.name
						# 模糊匹配
						if query_lower in kb_name.lower():
							suggestions.append(kb_name)
			
			# 如果建议不够，添加一些常见历史概念
			if len(suggestions) < limit:
				common_concepts = [
					"大化改新", "古坟时代", "奈良时代", "平安时代",
					"镰仓幕府", "德川幕府", "明治维新", "新罗", "高丽"
				]
				for concept in common_concepts:
					if query_lower in concept.lower() and concept not in suggestions:
						suggestions.append(concept)
						if len(suggestions) >= limit:
							break
			
			return suggestions[:limit]
			
		except Exception as e:
			self.logger.error(f"获取搜索建议失败: {e}")
			return []

	# ============================================================================
	# 资源清理
	# ============================================================================

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