"""GraphRAG 模块：基于 nano-graphrag 的知识图谱检索与知识库构建。"""

from .graphrag import GraphRAG, QueryParam
from .knowledge_graph_service import KnowledgeGraphService
from ._llm import qwen_complete, qwen_complete_if_cache, qwen_embedding

__version__ = "0.0.8.2"
__author__ = "Jianbai Ye"
__url__ = "https://github.com/gusye1234/nano-graphrag"

__all__ = ["GraphRAG", "QueryParam", "KnowledgeGraphService"]
