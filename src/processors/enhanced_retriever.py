#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版知识检索器
实现本地知识库的RAG检索和内容融合
"""

import os
import logging
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    retrieved_context: List[str]
    relevance_scores: List[float]
    source_documents: List[str]
    total_score: float
    retrieval_time: float


@dataclass
class DocumentChunk:
    """文档片段"""
    content: str
    source: str
    chunk_id: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


class EnhancedKnowledgeRetriever:
    """增强版知识检索器"""
    
    def __init__(self, knowledge_base_path: str = None):
        """
        初始化增强检索器
        
        Args:
            knowledge_base_path: 知识库路径，默认为项目根目录下的concept_knowledge_bases
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 使用相对路径指向项目根目录
        project_root = Path(__file__).parent.parent.parent
        if knowledge_base_path is None:
            self.knowledge_base_path = project_root / "concept_knowledge_bases"
        else:
            self.knowledge_base_path = Path(knowledge_base_path)
        self.cache_path = project_root / "data" / "retrieval_cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # 检索配置
        self.chunk_size = 500  # 文档分块大小
        self.chunk_overlap = 50  # 分块重叠
        self.max_results = 10  # 最大检索结果数
        self.relevance_threshold = 0.3  # 相关性阈值
        self.cache_ttl = 3600  # 缓存时间（秒）
        
        # 文档库
        self.document_chunks: List[DocumentChunk] = []
        self.embeddings_cache = {}
        
        # 缓存
        self.query_cache = {}
        
        # 初始化
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """初始化知识库"""
        try:
            self.logger.info("Initializing knowledge base...")
            
            # 加载文档
            self._load_documents()
            
            # 加载或生成embeddings
            self._load_embeddings()
            
            self.logger.info(f"Knowledge base initialized with {len(self.document_chunks)} chunks")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge base: {e}")
    
    def _load_documents(self):
        """加载文档"""
        self.document_chunks = []
        
        if not self.knowledge_base_path.exists():
            self.logger.warning(f"Knowledge base path not found: {self.knowledge_base_path}")
            return
        
        # 遍历概念目录
        for concept_dir in self.knowledge_base_path.iterdir():
            if not concept_dir.is_dir():
                continue
            
            knowledge_file = concept_dir / "knowledge.txt"
            if not knowledge_file.exists():
                continue
            
            try:
                # 读取知识文档
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 分块处理
                chunks = self._split_document(content, concept_dir.name)
                self.document_chunks.extend(chunks)
                
            except Exception as e:
                self.logger.error(f"Failed to load document {knowledge_file}: {e}")
    
    def _split_document(self, content: str, source: str) -> List[DocumentChunk]:
        """文档分块"""
        chunks = []
        
        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # 如果当前块加上新段落会超过限制
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # 保存当前块
                chunk_id = f"{source}_{chunk_index}"
                chunks.append(DocumentChunk(
                    content=current_chunk.strip(),
                    source=source,
                    chunk_id=chunk_id,
                    metadata={
                        "concept": source,
                        "chunk_index": chunk_index,
                        "length": len(current_chunk)
                    }
                ))
                
                # 开始新块（带重叠）
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + paragraph
                chunk_index += 1
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 保存最后一块
        if current_chunk:
            chunk_id = f"{source}_{chunk_index}"
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                source=source,
                chunk_id=chunk_id,
                metadata={
                    "concept": source,
                    "chunk_index": chunk_index,
                    "length": len(current_chunk)
                }
            ))
        
        return chunks
    
    def _load_embeddings(self):
        """加载或生成embeddings"""
        embeddings_file = self.cache_path / "embeddings.pkl"
        
        # 尝试加载缓存的embeddings
        if embeddings_file.exists():
            try:
                with open(embeddings_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    
                # 检查是否需要更新
                if self._is_embeddings_valid(cached_data):
                    self.embeddings_cache = cached_data['embeddings']
                    self._assign_embeddings_to_chunks()
                    self.logger.info("Loaded cached embeddings")
                    return
            except Exception as e:
                self.logger.warning(f"Failed to load cached embeddings: {e}")
        
        # 生成新的embeddings
        self._generate_embeddings()
    
    def _is_embeddings_valid(self, cached_data: Dict) -> bool:
        """检查缓存的embeddings是否有效"""
        # 检查文档数量是否匹配
        if len(cached_data.get('chunk_ids', [])) != len(self.document_chunks):
            return False
        
        # 检查chunk_id是否匹配
        cached_ids = set(cached_data.get('chunk_ids', []))
        current_ids = set(chunk.chunk_id for chunk in self.document_chunks)
        
        return cached_ids == current_ids
    
    def _generate_embeddings(self):
        """生成embeddings"""
        try:
            # 这里使用简化的向量化方法
            # 在实际应用中应该使用句子向量模型
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            # 提取文档内容
            texts = [chunk.content for chunk in self.document_chunks]
            chunk_ids = [chunk.chunk_id for chunk in self.document_chunks]
            
            # 生成TF-IDF向量
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=None,  # 中文停用词需要额外处理
                ngram_range=(1, 2)
            )
            
            embeddings = vectorizer.fit_transform(texts).toarray()
            
            # 存储embeddings
            self.embeddings_cache = {}
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                self.embeddings_cache[chunk_id] = embedding
            
            # 分配到chunks
            self._assign_embeddings_to_chunks()
            
            # 缓存到文件
            self._save_embeddings_cache(chunk_ids, vectorizer)
            
            self.logger.info(f"Generated embeddings for {len(self.document_chunks)} chunks")
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            # 使用随机向量作为备用
            self._generate_random_embeddings()
    
    def _assign_embeddings_to_chunks(self):
        """将embeddings分配给chunks"""
        for chunk in self.document_chunks:
            chunk.embedding = self.embeddings_cache.get(chunk.chunk_id)
    
    def _save_embeddings_cache(self, chunk_ids: List[str], vectorizer):
        """保存embeddings缓存"""
        try:
            cache_data = {
                'embeddings': self.embeddings_cache,
                'chunk_ids': chunk_ids,
                'vectorizer': vectorizer,
                'timestamp': time.time()
            }
            
            embeddings_file = self.cache_path / "embeddings.pkl"
            with open(embeddings_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
        except Exception as e:
            self.logger.error(f"Failed to save embeddings cache: {e}")
    
    def _generate_random_embeddings(self):
        """生成随机embeddings（备用方案）"""
        self.logger.warning("Using random embeddings as fallback")
        for chunk in self.document_chunks:
            chunk.embedding = np.random.rand(100)  # 100维随机向量
    
    async def retrieve(self, query: str, max_results: Optional[int] = None) -> RetrievalResult:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            
        Returns:
            RetrievalResult: 检索结果
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key = self._get_cache_key(query)
        if cache_key in self.query_cache:
            cached_result = self.query_cache[cache_key]
            if time.time() - cached_result['timestamp'] < self.cache_ttl:
                self.logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result['result']
        
        try:
            # 生成查询向量
            query_embedding = await self._encode_query(query)
            
            # 计算相似度
            similarities = self._calculate_similarities(query_embedding)
            
            # 筛选和排序结果
            results = self._rank_and_filter_results(similarities, max_results or self.max_results)
            
            retrieval_time = time.time() - start_time
            
            # 构建结果
            result = RetrievalResult(
                retrieved_context=[chunk.content for chunk, _ in results],
                relevance_scores=[score for _, score in results],
                source_documents=[chunk.source for chunk, _ in results],
                total_score=np.mean([score for _, score in results]) if results else 0.0,
                retrieval_time=retrieval_time
            )
            
            # 缓存结果
            self.query_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            self.logger.debug(f"Retrieved {len(results)} relevant chunks in {retrieval_time:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve documents: {e}")
            return RetrievalResult(
                retrieved_context=[],
                relevance_scores=[],
                source_documents=[],
                total_score=0.0,
                retrieval_time=time.time() - start_time
            )
    
    async def _encode_query(self, query: str) -> np.ndarray:
        """编码查询"""
        try:
            # 使用同样的TF-IDF向量化器
            # 这里简化处理，实际应该使用相同的vectorizer
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            # 创建临时向量化器
            all_texts = [chunk.content for chunk in self.document_chunks] + [query]
            vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
            vectors = vectorizer.fit_transform(all_texts)
            
            return vectors[-1].toarray()[0]  # 返回查询的向量
            
        except Exception as e:
            self.logger.error(f"Failed to encode query: {e}")
            return np.random.rand(100)  # 随机向量作为备用
    
    def _calculate_similarities(self, query_embedding: np.ndarray) -> List[Tuple[DocumentChunk, float]]:
        """计算相似度"""
        similarities = []
        
        for chunk in self.document_chunks:
            if chunk.embedding is None:
                continue
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            similarities.append((chunk, similarity))
        
        return similarities
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm_a = np.linalg.norm(vec1)
            norm_b = np.linalg.norm(vec2)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except:
            return 0.0
    
    def _rank_and_filter_results(self, similarities: List[Tuple[DocumentChunk, float]], 
                                max_results: int) -> List[Tuple[DocumentChunk, float]]:
        """排序和筛选结果"""
        # 过滤低相关性结果
        filtered = [(chunk, score) for chunk, score in similarities 
                   if score >= self.relevance_threshold]
        
        # 按相似度排序
        sorted_results = sorted(filtered, key=lambda x: x[1], reverse=True)
        
        # 限制结果数量
        return sorted_results[:max_results]
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def add_document(self, content: str, source: str, metadata: Optional[Dict] = None):
        """动态添加文档"""
        chunks = self._split_document(content, source)
        
        # 为新chunks生成embeddings
        for chunk in chunks:
            chunk.metadata.update(metadata or {})
        
        self.document_chunks.extend(chunks)
        
        # 异步生成embeddings
        asyncio.create_task(self._generate_embeddings_for_chunks(chunks))
    
    async def _generate_embeddings_for_chunks(self, chunks: List[DocumentChunk]):
        """为指定chunks生成embeddings"""
        # 这里应该使用相同的向量化方法
        # 简化实现
        for chunk in chunks:
            chunk.embedding = np.random.rand(100)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        return {
            "total_chunks": len(self.document_chunks),
            "cache_size": len(self.query_cache),
            "concepts_count": len(set(chunk.source for chunk in self.document_chunks)),
            "average_chunk_length": np.mean([len(chunk.content) for chunk in self.document_chunks]) if self.document_chunks else 0,
            "embeddings_cached": len(self.embeddings_cache)
        }
