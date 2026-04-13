# GraphRAG - 知识图谱检索模块

基于 nano-graphrag 的 GraphRAG 实现，提供本地知识库的构建与语义检索能力。

## 模块概述

GraphRAG 模块是从 [nano-graphrag](https://github.com/gusye1234/nano-graphrag) 项目内嵌而来，经过适配后支持 OpenAI 兼容 API 的所有 LLM 提供商。

## 核心类

### GraphRAG

```python
from edupilot.services.graphrag import GraphRAG, QueryParam
```

主类，负责知识库的构建与查询。

```python
class GraphRAG:
    def __init__(
        self,
        working_dir: str,
        best_model_func: callable,      # 主模型 LLM 函数
        cheap_model_func: callable,     # 轻量模型 LLM 函数
        embedding_func: callable,        # Embedding 函数
        enable_local: bool = True,      # 启用本地图检索
        enable_naive_rag: bool = True,   # 启用朴素 RAG
        best_model_max_async: int = 8,
        cheap_model_max_async: int = 8,
        embedding_func_max_async: int = 8,
        embedding_batch_num: int = 8,
    )
```

### QueryParam

```python
class QueryParam:
    mode: str = "local"        # local / global / naive
    top_k: int = 10            # 返回结果数量
    only_need_context: bool = False
```

## 三种检索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `local` | 社区局部检索（默认） | 具体实体查询、实体关系推理 |
| `global` | 全局总结检索 | 宽泛主题、总结性问题 |
| `naive` | 直接向量相似度 | baseline 对比、快速检索 |

## 工作流程

```
文本输入
    │
    ▼
┌─────────────────────┐
│  文本分块           │  _splitter.SeparatorSplitter
│  • 按段落/句子分块  │
│  • 保留上下文信息  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  实体关系抽取        │  DSPy + LLM
│  • 命名实体识别     │
│  • 关系抽取         │
│  • 社区检测         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  图谱构建           │
│  • NetworkX 图存储 │
│  • 向量索引构建     │
│  • JSON KV 存储    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  语义查询           │
│  • 模式选择         │
│  • 上下文组装       │
│  • LLM 生成答案     │
└─────────────────────┘
```

## 存储后端

### 图存储

| 存储类 | 说明 |
|--------|------|
| `NetworkXStorage` | NetworkX 图数据库（默认） |
| `Neo4jStorage` | Neo4j 图数据库（可选） |

### 向量存储

| 存储类 | 说明 |
|--------|------|
| `NanoVectorDBStorage` | nano-vectordb（默认） |
| `HNSWVectorStorage` | HNSW lib（可选） |

### KV 存储

| 存储类 | 说明 |
|--------|------|
| `JsonKVStorage` | JSON 文件存储（默认） |

## 使用示例

### 构建知识索引

```python
from edupilot.services.graphrag import KnowledgeGraphService

service = KnowledgeGraphService()

# 构建知识索引
result = await service.ensure_index(
    kb_id="my_knowledge_base",
    source_text_path=Path("data/metadata/my_kb/knowledge.txt")
)

print(result)
# {'ok': True, 'kb_id': 'my_knowledge_base', 'indexed': True}
```

### 语义查询

```python
from edupilot.services.graphrag import KnowledgeGraphService

service = KnowledgeGraphService()

# local 模式查询
answer = await service.query(
    kb_id="my_knowledge_base",
    question="什么是神经网络？",
    mode="local"  # local / global / naive
)

print(answer)
```

### 导出图谱可视化

```python
from edupilot.services.graphrag import KnowledgeGraphService

service = KnowledgeGraphService()

# 导出为 ECharts 格式
graph_data = service.export_visual_graph(kb_id="my_knowledge_base")

print(graph_data)
# {'nodes': [...], 'links': [...]}
```

## API 接口

```bash
# 构建知识索引
POST /api/v1/graph/knowledge/{kb_id}/index

# 语义查询
GET /api/v1/graph/knowledge/{kb_id}/query?question=...&mode=local

# 获取图谱数据
GET /api/v1/graph/knowledge/{kb_id}
```

## 目录结构

```
graphrag/
├── graphrag.py           # GraphRAG 主类
├── base.py              # 存储抽象基类
├── _llm.py             # LLM 适配
├── _op.py              # 核心操作
├── _splitter.py        # 文本分块
├── _utils.py           # 工具函数
├── entity_extraction/  # 实体关系抽取（DSPy）
├── prompt_output_cn.py  # 中文提示词
└── _storage/           # 存储后端
    ├── kv_json.py
    ├── vdb_nanovectordb.py
    ├── vdb_hnswlib.py
    └── gdb_networkx.py
```

## 相关模块

- [Builtin Tools - RAGTool](../../agents/tools/) - RAG 检索工具
- [KnowledgeView.vue](../../../web/src/views/KnowledgeView.vue) - 前端知识检索界面
- [GraphExplorer.vue](../../../web/src/views/GraphExplorer.vue) - 前端图谱可视化界面
