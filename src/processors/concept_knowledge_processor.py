#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概念知识库处理节点
提供概念数据处理和知识库构建功能
"""

import os
import sys
import pandas as pd
import logging
import asyncio
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import shutil
import time
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# 添加nano-graphrag路径
sys.path.append("./nano-graphrag")

from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash

# 导入统一的LLM管理器
from utils.llm import get_llm_manager, create_unified_processor_functions

class BaseProcessor(ABC):
    """数据处理节点基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def process(self, *args, **kwargs):
        """处理数据的抽象方法"""
        pass
    
    @abstractmethod
    def validate_input(self, *args, **kwargs) -> bool:
        """验证输入数据的抽象方法"""
        pass

class ConceptKnowledgeProcessor(BaseProcessor):
    """概念知识库处理节点"""
    
    # 默认配置
    DEFAULT_LLM_MODEL = "qwen2.5:ctx32k"
    DEFAULT_EMBEDDING_MODEL = "bge-m3:latest"
    DEFAULT_EMBEDDING_DIM = 1024
    DEFAULT_EMBEDDING_MAX_TOKENS = 8192
    
    def __init__(
        self,
        name: str = "ConceptKnowledgeProcessor",
        llm_client_name: str = None,
        embedding_client_name: str = None,
        llm_model: str = None,
        embedding_model: str = None,
        embedding_dim: int = None,
        embedding_max_tokens: int = None,
        output_base_dir: str = "../concept_knowledge_bases"
    ):
        super().__init__(name)
        
        # 客户端配置
        self.llm_client_name = llm_client_name or "ollama"
        self.embedding_client_name = embedding_client_name or "ollama"
        
        # 模型配置
        self.llm_model = llm_model or self.DEFAULT_LLM_MODEL
        self.embedding_model = embedding_model or self.DEFAULT_EMBEDDING_MODEL
        self.embedding_dim = embedding_dim or self.DEFAULT_EMBEDDING_DIM
        self.embedding_max_tokens = embedding_max_tokens or self.DEFAULT_EMBEDDING_MAX_TOKENS
        
        # 输出目录配置
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)
        
        # 统计信息
        self.start_time = None
        self.concept_times = {}
        self.total_concepts = 0
        self.successful_concepts = 0
        
        # 获取LLM管理器
        self.llm_manager = get_llm_manager()
        
        # 初始化函数
        self._init_functions()
    
    def _init_functions(self):
        """初始化LLM和embedding函数"""
        try:
            # 使用统一的函数创建器
            self.llm_func, self.embedding_func = create_unified_processor_functions(
                llm_client_name=self.llm_client_name,
                embedding_client_name=self.embedding_client_name,
                embedding_model=self.embedding_model,
                embedding_dim=self.embedding_dim,
                max_token_size=self.embedding_max_tokens,
                force_chinese=True
            )
            self.logger.info(f"成功初始化LLM和embedding函数")
        except Exception as e:
            self.logger.error(f"初始化LLM和embedding函数失败: {e}")
            # 使用默认的fallback函数
            self._init_fallback_functions()
    
    def _init_fallback_functions(self):
        """初始化fallback函数"""
        async def fallback_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return "LLM函数初始化失败，无法生成回复。"
        
        async def fallback_embedding_func(texts: List[str]) -> np.ndarray:
            return np.array([[0.0] * self.embedding_dim] * len(texts))
        
        self.llm_func = fallback_llm_func
        self.embedding_func = fallback_embedding_func
    
    def validate_input(self, csv_file: str) -> bool:
        """验证输入文件"""
        if not os.path.exists(csv_file):
            self.logger.error(f"CSV文件不存在: {csv_file}")
            return False
        
        try:
            # 尝试读取CSV文件的前几行
            df = pd.read_csv(csv_file, encoding='utf-8', nrows=5)
            required_columns = ['concept_id', 'information']
            
            for col in required_columns:
                if col not in df.columns:
                    self.logger.error(f"CSV文件缺少必需的列: {col}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"读取CSV文件时出错: {e}")
            return False
    
    def check_models(self) -> Tuple[bool, List[str]]:
        """检查模型可用性"""
        try:
            # 获取LLM客户端
            llm_client = self.llm_manager.get_client(self.llm_client_name)
            embedding_client = self.llm_manager.get_client(self.embedding_client_name)
            
            if not llm_client or not embedding_client:
                available_clients = self.llm_manager.list_clients()
                self.logger.error(f"客户端不可用。可用客户端: {available_clients}")
                return False, []
            
            # 检查模型列表（如果支持）
            model_names = []
            if hasattr(llm_client, 'list_models'):
                model_names = llm_client.list_models()
            
            # 测试连接
            llm_test = llm_client.test_connection()
            embedding_test = True  # 假设embedding可用，实际使用时会检测
            
            if hasattr(embedding_client, 'generate_embeddings'):
                try:
                    test_embeddings = embedding_client.generate_embeddings(["测试文本"], self.embedding_model)
                    embedding_test = len(test_embeddings) > 0
                except:
                    embedding_test = False
            
            success = llm_test.get('success', False) and embedding_test
            
            if not success:
                self.logger.warning(f"模型测试失败: LLM={llm_test.get('success', False)}, Embedding={embedding_test}")
            
            return success, model_names
            
        except Exception as e:
            self.logger.error(f"检查模型可用性时出错: {e}")
            return False, []
    
    def load_and_group_data(self, csv_file: str, limit_rows: int = None) -> Dict[str, List[Dict]]:
        """读取CSV数据并按concept_id分组"""
        self.logger.info("正在读取CSV数据...")
        
        try:
            if limit_rows:
                df = pd.read_csv(csv_file, encoding='utf-8', nrows=limit_rows)
                self.logger.info(f"成功读取前 {len(df)} 条记录（限制：{limit_rows}条）")
            else:
                df = pd.read_csv(csv_file, encoding='utf-8')
                self.logger.info(f"成功读取 {len(df)} 条记录")
            
            # 按concept_id分组
            grouped_data = {}
            for _, row in df.iterrows():
                concept_id = row['concept_id']
                if concept_id not in grouped_data:
                    grouped_data[concept_id] = []
                
                grouped_data[concept_id].append({
                    'information': row['information'],
                    'source': row['source'] if pd.notna(row['source']) else ''
                })
            
            self.logger.info(f"共发现 {len(grouped_data)} 个不同的概念")
            return grouped_data
            
        except Exception as e:
            self.logger.error(f"读取CSV文件时出错: {e}")
            return {}
    
    def create_concept_files(self, grouped_data: Dict[str, List[Dict]]) -> Dict[str, str]:
        """为每个concept_id创建文本文件"""
        concept_files = {}
        
        for concept_id, records in grouped_data.items():
            # 清理概念ID，用作文件夹名
            safe_concept_id = "".join(c for c in concept_id if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_concept_id = safe_concept_id.replace(' ', '_')
            
            if not safe_concept_id:
                safe_concept_id = f"concept_{hash(concept_id) % 10000}"
            
            # 创建概念文件夹
            concept_dir = self.output_base_dir / safe_concept_id
            concept_dir.mkdir(exist_ok=True)
            
            # 合并所有信息到一个文本文件
            text_file = concept_dir / "knowledge.txt"
            
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"概念: {concept_id}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, record in enumerate(records, 1):
                    f.write(f"信息片段 {i}:\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"{record['information']}\n")
                    if record['source']:
                        f.write(f"来源: {record['source']}\n")
                    f.write("\n" + "-" * 50 + "\n\n")
            
            concept_files[concept_id] = str(text_file)
            self.logger.info(f"为概念 '{concept_id}' 创建了知识文件: {text_file}")
        
        return concept_files
    
    def clean_working_dir(self, working_dir: str):
        """清理工作目录"""
        files_to_remove = [
            "vdb_entities.json",
            "kv_store_full_docs.json", 
            "kv_store_text_chunks.json",
            "kv_store_community_reports.json",
            "graph_chunk_entity_relation.graphml"
        ]
        
        for file in files_to_remove:
            file_path = os.path.join(working_dir, file)
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def build_concept_knowledge_base(self, concept_id: str, text_file: str) -> bool:
        """为单个概念构建知识库"""
        concept_start_time = time.time()
        
        # 清理概念ID用作目录名
        safe_concept_id = "".join(c for c in concept_id if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_concept_id = safe_concept_id.replace(' ', '_')
        
        if not safe_concept_id:
            safe_concept_id = f"concept_{hash(concept_id) % 10000}"
        
        working_dir = self.output_base_dir / safe_concept_id / "graphrag_cache"
        
        # 确保目录存在
        working_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理之前的文件
        self.clean_working_dir(str(working_dir))
        
        self.logger.info(f"开始处理概念: {concept_id}")
        self.logger.info(f"工作目录: {working_dir}")
        
        try:
            # 读取文本内容
            with open(text_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # 创建GraphRAG实例
            rag = GraphRAG(
                working_dir=str(working_dir),
                enable_llm_cache=True,
                best_model_func=self.llm_func,
                cheap_model_func=self.llm_func,
                embedding_func=self.embedding_func,
            )
            
            # 插入知识
            self.logger.info(f"正在为概念 '{concept_id}' 构建知识图谱...")
            rag.insert(text_content)
            
            self.logger.info(f"概念 '{concept_id}' 的知识库构建完成！")
            
            # 测试查询
            self.logger.info(f"测试查询概念 '{concept_id}'...")
            result = rag.query(
                f"请简要介绍{concept_id}的主要内容", 
                param=QueryParam(mode="global")
            )
            self.logger.info(f"查询结果: {result}")
            
            # 记录成功处理的概念时间
            concept_end_time = time.time()
            concept_duration = concept_end_time - concept_start_time
            self.concept_times[concept_id] = concept_duration
            self.successful_concepts += 1
            
            self.logger.info(f"概念 '{concept_id}' 处理耗时: {self._format_duration(concept_duration)}")
            
            return True
            
        except Exception as e:
            # 记录失败的概念时间
            concept_end_time = time.time()
            concept_duration = concept_end_time - concept_start_time
            self.concept_times[f"{concept_id}(失败)"] = concept_duration
            
            self.logger.error(f"处理概念 '{concept_id}' 时出错: {e}")
            self.logger.info(f"概念 '{concept_id}' 处理耗时: {self._format_duration(concept_duration)} (失败)")
            return False
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}分{remaining_seconds:.2f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}小时{minutes}分{remaining_seconds:.2f}秒"
    
    def print_time_statistics(self):
        """打印时间统计信息"""
        if not self.start_time:
            return
            
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("知识库构建时间统计报告")
        print("=" * 80)
        
        print(f"总耗时: {self._format_duration(total_time)}")
        print(f"处理概念数: {self.total_concepts}")
        print(f"成功构建: {self.successful_concepts}")
        print(f"失败数量: {self.total_concepts - self.successful_concepts}")
        
        if self.successful_concepts > 0:
            successful_times = [time for concept, time in self.concept_times.items() if not concept.endswith('(失败)')]
            avg_time = sum(successful_times) / len(successful_times)
            print(f"平均每个概念耗时: {self._format_duration(avg_time)}")
            print(f"最快处理时间: {self._format_duration(min(successful_times))}")
            print(f"最慢处理时间: {self._format_duration(max(successful_times))}")
        
        print("\n各概念详细耗时:")
        print("-" * 60)
        for concept_id, duration in self.concept_times.items():
            status = "[失败]" if concept_id.endswith('(失败)') else "[成功]"
            clean_concept_id = concept_id.replace('(失败)', '')
            print(f"{status} {clean_concept_id}: {self._format_duration(duration)}")
        
        print("=" * 80)
    
    def process(
        self, 
        csv_file: str, 
        limit_rows: Optional[int] = None,
        check_models: bool = True
    ) -> Dict[str, any]:
        """处理概念数据并构建知识库
        
        Args:
            csv_file: CSV文件路径
            limit_rows: 限制处理的行数，None表示处理全部数据
            check_models: 是否检查模型可用性
            
        Returns:
            处理结果字典
        """
        # 记录开始时间
        self.start_time = time.time()
        start_datetime = datetime.now()
        
        self.logger.info(f"开始构建知识库 - {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 验证输入
        if not self.validate_input(csv_file):
            return {
                "success": False,
                "error": "输入验证失败",
                "processed_concepts": 0,
                "successful_concepts": 0
            }
        
        # 检查模型可用性
        if check_models:
            models_available, available_models = self.check_models()
            if not models_available:
                return {
                    "success": False,
                    "error": f"所需模型不可用。可用模型: {available_models}",
                    "processed_concepts": 0,
                    "successful_concepts": 0
                }
        
        # 1. 加载和分组数据
        grouped_data = self.load_and_group_data(csv_file, limit_rows=limit_rows)
        if not grouped_data:
            return {
                "success": False,
                "error": "没有数据需要处理",
                "processed_concepts": 0,
                "successful_concepts": 0
            }
        
        # 2. 创建概念文件
        concept_files = self.create_concept_files(grouped_data)
        
        # 3. 为每个概念构建知识库
        self.total_concepts = len(concept_files)
        
        self.logger.info(f"预计处理 {self.total_concepts} 个概念")
        
        for i, (concept_id, text_file) in enumerate(concept_files.items(), 1):
            self.logger.info(f"{'='*20} 进度: {i}/{self.total_concepts} {'='*20}")
            
            if not self.build_concept_knowledge_base(concept_id, text_file):
                self.logger.error(f"概念 '{concept_id}' 处理失败")
            
            # 显示当前进度和预估剩余时间
            if i > 0:
                elapsed_time = time.time() - self.start_time
                avg_time_per_concept = elapsed_time / i
                remaining_concepts = self.total_concepts - i
                estimated_remaining_time = avg_time_per_concept * remaining_concepts
                
                self.logger.info(f"当前进度: {i}/{self.total_concepts} ({(i/self.total_concepts)*100:.1f}%)")
                self.logger.info(f"已用时间: {self._format_duration(elapsed_time)}")
                if remaining_concepts > 0:
                    self.logger.info(f"预计剩余时间: {self._format_duration(estimated_remaining_time)}")
                    estimated_finish_time = datetime.now() + timedelta(seconds=estimated_remaining_time)
                    self.logger.info(f"预计完成时间: {estimated_finish_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 打印最终统计
        self.print_time_statistics()
        
        return {
            "success": True,
            "processed_concepts": self.total_concepts,
            "successful_concepts": self.successful_concepts,
            "failed_concepts": self.total_concepts - self.successful_concepts,
            "total_time": time.time() - self.start_time,
            "output_directory": str(self.output_base_dir)
        }

# 便捷函数
def create_concept_processor(
    llm_client_name: str = None,
    embedding_client_name: str = None,
    llm_model: str = None,
    embedding_model: str = None,
    output_base_dir: str = "../concept_knowledge_bases"
) -> ConceptKnowledgeProcessor:
    """创建概念知识库处理器"""
    return ConceptKnowledgeProcessor(
        llm_client_name=llm_client_name,
        embedding_client_name=embedding_client_name,
        llm_model=llm_model,
        embedding_model=embedding_model,
        output_base_dir=output_base_dir
    )

def process_concept_data(
    csv_file: str,
    output_base_dir: str = None,
    max_concepts: int = None,
    enable_enhanced_processing: bool = True,
    enable_llm_enhancement: bool = False,
    llm_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    处理概念数据并构建知识库
    
    Args:
        csv_file: CSV文件路径
        output_base_dir: 输出基础目录，默认为项目根目录下的concept_knowledge_bases
        max_concepts: 最大处理概念数量
        enable_enhanced_processing: 是否启用增强处理
        enable_llm_enhancement: 是否启用LLM增强
        llm_config: LLM配置
        
    Returns:
        处理结果统计
    """
    # 使用相对路径指向项目根目录
    project_root = Path(__file__).parent.parent.parent
    if output_base_dir is None:
        output_base_dir = project_root / "concept_knowledge_bases"
    else:
        output_base_dir = Path(output_base_dir)

    processor = create_concept_processor(
        llm_client_name=llm_config.get("llm_client_name"),
        embedding_client_name=llm_config.get("embedding_client_name"),
        llm_model=llm_config.get("llm_model"),
        embedding_model=llm_config.get("embedding_model"),
        output_base_dir=output_base_dir
    )
    return processor.process(csv_file, limit_rows=max_concepts)