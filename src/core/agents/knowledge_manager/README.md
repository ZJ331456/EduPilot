# 知识管理智能体

## 概述

`KnowledgeManagerAgent` 是一个统一的知识库管理智能体，它不仅能够检索本地知识库，还能够自动处理索引构建的完整pipeline。

## 核心功能

### 1. 自动索引处理 Pipeline

智能体会自动检测知识库目录中的 `knowledge.txt` 文件，并自动构建 GraphRAG 索引：

- **自动检测**：监控知识库目录，发现新的或更新的 `knowledge.txt` 文件
- **自动索引**：使用 GraphRAG 自动进行文档分块、实体提取、图构建等处理
- **状态管理**：跟踪索引状态，避免重复索引
- **增量更新**：检测文件修改时间，只对更新的文件重新索引

### 2. 知识检索功能

保留并增强了原有的检索功能：

- **多策略检索**：支持精确匹配、概念匹配、语义扩展等多种检索策略
- **并发检索**：并发执行多个检索任务，提高效率
- **智能缓存**：缓存检索结果，减少重复计算
- **相关性评分**：对检索结果进行相关性评分和排序

## 使用方法

### 基本使用

```python
from src.core.agents.knowledge_manager import KnowledgeManagerAgent

# 创建智能体实例（默认启用自动索引）
agent = KnowledgeManagerAgent(
    knowledge_base_dir="concept_knowledge_bases",  # 可选，默认使用concept_knowledge_bases
    auto_index=True  # 是否启用自动索引，默认True
)

# 执行检索（与原有接口兼容）
state = await agent.execute(state)
```

### 手动触发索引

```python
# 手动触发某个知识库的索引
success = await agent.index_knowledge_base("概念名称")

# 查看索引状态
status = agent.get_index_status("概念名称")
print(status)
# {
#     "indexed": True,
#     "indexing": False,
#     "last_indexed_time": "2024-01-01T12:00:00",
#     "paragraph_count": 100,
#     "content_length": 50000
# }
```

### 列出所有知识库

```python
# 列出所有知识库及其索引状态
knowledge_bases = agent.list_knowledge_bases()
for kb in knowledge_bases:
    print(f"{kb['name']}: 已索引={kb['indexed']}, 正在索引={kb['indexing']}")
```

## 知识库目录结构

```
concept_knowledge_bases/
├── 概念1/
│   ├── knowledge.txt          # 知识库源文件
│   └── graphrag_cache/        # 自动生成的索引目录
│       ├── kv_store_full_docs.json
│       ├── kv_store_text_chunks.json
│       └── graph_chunk_entity_relation.graphml
├── 概念2/
│   ├── knowledge.txt
│   └── graphrag_cache/
└── ...
```

## 索引状态管理

智能体会在 `data/knowledge_index_status.json` 中保存索引状态：

```json
{
  "概念名称": {
    "indexed": true,
    "indexing": false,
    "last_indexed_mtime": 1704067200.0,
    "last_indexed_time": "2024-01-01T12:00:00",
    "paragraph_count": 100,
    "content_length": 50000
  }
}
```

## 与原有智能体的关系

- **向后兼容**：保留了 `KnowledgeRetrieverAgent`，确保现有代码不受影响
- **推荐使用**：新项目推荐使用 `KnowledgeManagerAgent`，它包含了检索功能并增加了索引处理能力
- **自动切换**：在 executor 中，如果注册了 `knowledge_manager`，会优先使用；如果没有，则使用 `knowledge_retriever`（向后兼容）

## 配置选项

### 初始化参数

- `knowledge_base_dir` (str, optional): 知识库根目录，默认为 "concept_knowledge_bases"
- `auto_index` (bool, optional): 是否启用自动索引，默认为 True

### 自动索引行为

- **启动时检查**：智能体初始化时会检查所有知识库，对需要索引的自动触发索引
- **后台监控**：启用自动索引时，会每5分钟检查一次是否有新的或更新的知识库需要索引
- **并发控制**：同时最多处理一个知识库的索引任务，避免资源竞争

## 注意事项

1. **首次索引耗时**：首次索引大型知识库可能需要较长时间，请耐心等待
2. **文件编码**：确保 `knowledge.txt` 文件使用 UTF-8 编码
3. **索引目录**：`graphrag_cache` 目录由智能体自动创建和管理，请勿手动修改
4. **资源清理**：使用完毕后调用 `agent.shutdown()` 清理资源

## 使用说明

### 基本导入

```python
from src.core.agents.knowledge_manager import KnowledgeManagerAgent
```

### 实例化

```python
agent = KnowledgeManagerAgent()
```

### 注册到 Executor

```python
executor.register_tool_agents({
    "knowledge_manager": agent
})
```

## 技术细节

### 索引流程

1. **文件检测**：检查 `knowledge.txt` 是否存在及修改时间
2. **状态检查**：检查索引状态文件，判断是否需要索引
3. **内容读取**：读取知识库内容并按段落分割
4. **GraphRAG索引**：调用 GraphRAG 的 `ainsert` 方法进行索引
5. **状态更新**：更新索引状态文件

### 检索流程

1. **查询优化**：根据查询生成多个优化查询策略
2. **概念识别**：识别目标概念知识库
3. **并发检索**：并发执行多个检索任务
4. **结果排序**：按相关性评分排序和去重
5. **缓存结果**：缓存检索结果以提高性能

## 性能优化

- **延迟加载**：GraphRAG 实例按需加载，减少内存占用
- **并发检索**：使用异步并发提高检索效率
- **智能缓存**：缓存检索结果，避免重复计算
- **批量索引**：索引时按批次处理，避免内存溢出

