#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌入模型管理器 - 负责管理和创建嵌入函数
"""

import logging
import asyncio
from typing import Optional


class EmbeddingManager:
    """嵌入模型管理器
    
    职责：
    1. 创建嵌入函数
    2. 管理嵌入模型
    3. 提供统一的嵌入接口
    """
    
    def __init__(self, embedding_dim: int = 1024):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.embedding_dim = embedding_dim
        self._embedding_func = None
    
    def get_embedding_func(self):
        """获取嵌入函数（懒加载）"""
        if self._embedding_func is None:
            self._embedding_func = self._create_embedding_func()
        return self._embedding_func
    
    def _create_embedding_func(self):
        """创建嵌入函数
        
        尝试顺序：
        1. sentence_transformers（推荐）
        2. 简单哈希嵌入（降级）
        """
        try:
            # 尝试使用 sentence_transformers
            embedding_func = self._create_sentence_transformer_embedding()
            if embedding_func:
                return embedding_func
        except Exception as e:
            self.logger.warning(f"sentence_transformers 不可用: {e}")
        
        # 降级到简单嵌入
        self.logger.info("使用简单哈希嵌入")
        return self._create_simple_embedding()
    
    def _create_sentence_transformer_embedding(self):
        """创建 sentence_transformers 嵌入函数"""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            # 尝试多个模型
            model_candidates = [
                "all-MiniLM-L6-v2",  # 384维
                "all-MiniLM-L12-v2", # 384维
                "paraphrase-MiniLM-L6-v2", # 384维
            ]
            
            for model_name in model_candidates:
                try:
                    model = SentenceTransformer(model_name)
                    
                    async def sentence_transformer_embedding(texts):
                        """异步嵌入函数"""
                        if isinstance(texts, str):
                            texts = [texts]
                        
                        loop = asyncio.get_event_loop()
                        embeddings = await loop.run_in_executor(
                            None, model.encode, texts, {"convert_to_numpy": True}
                        )
                        
                        # 调整到目标维度
                        if embeddings.shape[1] < self.embedding_dim:
                            padding_size = self.embedding_dim - embeddings.shape[1]
                            padding = np.zeros((embeddings.shape[0], padding_size))
                            embeddings = np.concatenate([embeddings, padding], axis=1)
                        elif embeddings.shape[1] > self.embedding_dim:
                            embeddings = embeddings[:, :self.embedding_dim]
                        
                        return embeddings
                    
                    # 创建 EmbeddingFunc
                    from src.infrastructure.nano_graphrag._utils import EmbeddingFunc
                    embedding_func = EmbeddingFunc(
                        embedding_dim=self.embedding_dim,
                        max_token_size=512,
                        func=sentence_transformer_embedding
                    )
                    
                    self.logger.info(f"使用嵌入模型: {model_name} (调整到 {self.embedding_dim}维)")
                    return embedding_func
                    
                except Exception as e:
                    self.logger.warning(f"模型 {model_name} 加载失败: {e}")
                    continue
                    
        except ImportError:
            self.logger.warning("sentence_transformers 未安装")
        
        return None
    
    def _create_simple_embedding(self):
        """创建简单哈希嵌入函数（降级方案）"""
        import numpy as np
        import hashlib
        
        async def simple_embedding_func(texts):
            """简单的嵌入函数（基于文本哈希）"""
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = []
            for text in texts:
                # 基于文本内容生成确定性嵌入
                text_hash = hashlib.md5(text.encode()).hexdigest()
                hash_nums = [int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)]
                
                # 创建目标维度向量
                embedding = np.zeros(self.embedding_dim)
                for i, num in enumerate(hash_nums):
                    if i < self.embedding_dim:
                        embedding[i] = (num - 128) / 128.0  # 归一化到[-1, 1]
                
                # 添加文本长度特征
                text_len_norm = min(len(text) / 1000.0, 1.0)
                embedding[self.embedding_dim - 1] = text_len_norm
                
                embeddings.append(embedding)
            
            return np.array(embeddings)
        
        # 创建 EmbeddingFunc
        from src.infrastructure.nano_graphrag._utils import EmbeddingFunc
        embedding_func = EmbeddingFunc(
            embedding_dim=self.embedding_dim,
            max_token_size=512,
            func=simple_embedding_func
        )
        
        self.logger.info(f"使用简单哈希嵌入 ({self.embedding_dim}维)")
        return embedding_func

