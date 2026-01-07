# 知识管理智能体 (KnowledgeManagerAgent)

## 概述

`KnowledgeManagerAgent` 是一个统一的知识库管理智能体，集成了**自动索引构建**和**智能知识检索**两大核心功能。它不仅能够从已索引的知识库中检索信息，还能够自动检测、处理和构建 GraphRAG 索引，实现知识库的完整生命周期管理。

## 核心功能

### 1. 自动索引处理 Pipeline

智能体会自动检测知识库目录中的 `knowledge.txt` 文件，并自动构建 GraphRAG 索引：

- **自动检测**：监控知识库目录，发现新的或更新的 `knowledge.txt` 文件
- **自动索引**：使用 GraphRAG 自动进行文档分块、实体提取、图构建等处理
- **状态管理**：跟踪索引状态，避免重复索引
- **增量更新**：检测文件修改时间，只对更新的文件重新索引
- **后台监控**：每5分钟自动检查一次，确保新知识库及时索引
- **批量处理**：支持大文件分批索引，避免内存溢出

**索引流程**：
```
检测knowledge.txt → 检查索引状态 → 读取内容 → 段落分割 → GraphRAG索引 → 状态更新
```

### 2. 知识检索功能

强大的多策略知识检索能力：

- **多策略检索**：支持精确匹配、概念匹配、语义扩展、图结构检索等多种检索策略
- **并发检索**：并发执行多个检索任务，大幅提高检索效率
- **智能缓存**：缓存检索结果（24小时TTL），减少重复计算
- **相关性评分**：多维度相关性评分算法，确保结果质量
- **全局搜索**：当特定概念检索无结果时，自动进行全局搜索
- **结果排序**：按相关性评分排序和去重，返回Top-K结果

**检索流程**：
```
查询优化 → 概念识别 → 并发检索 → 相关性评分 → 结果排序 → 缓存
```

### 3. 知识库管理

完整的知识库生命周期管理：

- **知识库列表**：列出所有知识库及其索引状态
- **索引状态查询**：查询特定知识库的索引状态和详细信息
- **手动索引**：支持手动触发某个知识库的索引
- **延迟加载**：GraphRAG 实例按需加载，减少内存占用
- **资源管理**：自动清理资源，支持优雅关闭

## 使用方法

### 基本使用

```python
from src.core.agents.knowledge_manager import KnowledgeManagerAgent
from src.infrastructure.utils import AgentState

# 创建智能体实例（默认启用自动索引）
agent = KnowledgeManagerAgent(
    knowledge_base_dir="data/concept_knowledge_bases",  # 可选，默认使用data/concept_knowledge_bases
    auto_index=True  # 是否启用自动索引，默认True
)

# 执行检索
state = AgentState(user_query="什么是大化改新？")
state = await agent.execute(state)

# 获取检索结果
if state.retrieved_knowledge:
    results = state.retrieved_knowledge.get('results', [])
    for result in results[:3]:  # 显示前3个结果
        print(f"来源: {result.get('source')}")
        print(f"内容: {result.get('content')[:200]}...")
        print(f"相关性: {result.get('relevance_score', 0):.2f}\n")
```

### 手动触发索引

```python
# 手动触发某个知识库的索引
success = await agent.index_knowledge_base("概念名称")

if success:
    print("索引成功！")
else:
    print("索引失败，请检查日志")

# 查看索引状态
status = agent.get_index_status("概念名称")
print(status)
# {
#     "indexed": True,
#     "indexing": False,
#     "last_indexed_time": "2024-01-01T12:00:00",
#     "last_indexed_mtime": 1704067200.0,
#     "paragraph_count": 100,
#     "content_length": 50000
# }
```

### 列出所有知识库

```python
# 列出所有知识库及其索引状态
knowledge_bases = agent.list_knowledge_bases()
for kb in knowledge_bases:
    print(f"{kb['name']}: 已索引={kb['indexed']}, 正在索引={kb['indexing']}, 路径={kb['path']}")
```

### 获取可用概念

```python
# 获取所有已索引的概念列表
concepts = agent.get_available_concepts()
print(f"可用概念: {concepts}")
```

## 知识库目录结构

```
data/concept_knowledge_bases/
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

## 智能体说明

`KnowledgeManagerAgent` 是统一的知识库管理智能体，集成了索引构建和知识检索功能。它提供了完整的知识库生命周期管理能力。

## 配置选项

### 初始化参数

- `knowledge_base_dir` (str, optional): 知识库根目录，默认为 "data/concept_knowledge_bases"
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
3. **内容读取**：读取知识库内容并按段落分割（`\n\n` 分隔）
4. **GraphRAG索引**：调用 GraphRAG 的 `ainsert` 方法进行批量索引（每批10个段落）
5. **状态更新**：更新索引状态文件，注册到概念数据库

**索引输出**：
- `kv_store_full_docs.json` - 完整文档存储
- `kv_store_text_chunks.json` - 文本块存储
- `graph_chunk_entity_relation.graphml` - 知识图谱文件

### 检索流程

1. **查询优化**：从 `state.retrieval_decision` 获取优化查询策略，或生成默认查询
2. **概念识别**：从 `core_concepts`、`keywords` 或查询文本中识别目标概念
3. **并发检索**：使用 `asyncio.gather` 并发执行多个检索任务（最多4个并发）
4. **相关性评分**：使用多维度评分算法（词汇匹配40% + 语义相似度25% + 结构化匹配15% + 上下文相关性15% + 内容质量5%）
5. **结果排序**：按相关性评分排序和去重，返回Top-10结果
6. **缓存结果**：缓存检索结果（24小时TTL），提高后续查询性能

### 检索策略

支持以下检索策略：

- **exact_match**：精确匹配，使用 `hybrid` 模式，top_k=5
- **concept_match**：概念匹配，使用 `global` 模式，top_k=5
- **multi_concept_match**：多概念匹配，使用 `local` 模式，top_k=4
- **semantic_expansion**：语义扩展，使用 `hybrid` 模式，top_k=6
- **keyword_search**：关键词搜索，使用 `naive` 模式，top_k=5

## 性能优化

- **延迟加载**：GraphRAG 实例按需加载，减少内存占用
- **并发检索**：使用 `asyncio.gather` 并发执行多个检索任务，最多4个并发
- **智能缓存**：缓存检索结果（24小时TTL，最大1000条），避免重复计算
- **批量索引**：索引时按批次处理（每批10个段落），避免内存溢出
- **超时控制**：检索任务设置30秒超时，避免长时间等待
- **状态持久化**：索引状态持久化到文件，支持重启后恢复

## API接口

### 公共方法

```python
# 获取可用概念列表
concepts = agent.get_available_concepts()

# 获取索引状态
status = agent.get_index_status("概念名称")  # 单个概念
all_status = agent.get_index_status()  # 所有概念

# 手动触发索引
success = await agent.index_knowledge_base("概念名称")

# 列出所有知识库
knowledge_bases = agent.list_knowledge_bases()

# 清理资源
agent.shutdown()
```

### AgentState 接口

```python
# 执行检索
state = AgentState(user_query="查询内容")
state = await agent.execute(state)

# 执行索引
state = AgentState()
state.index_request = {"concept_name": "概念名称"}
state = await agent.execute(state)
```

## 测试示例

参考 `src/tests/test_knowledge_manager_agent.py` 查看完整的测试示例。

### 运行测试

**前置条件**：
- 确保已安装所有依赖（见上方"依赖要求"部分）
- 确保 `metadata/shu/books/三国演义.txt` 文件存在

```bash
# 推荐方式: 使用 python -m 运行（从项目根目录）
python -m src.tests.test_knowledge_manager_agent

# 方式2: 使用pytest
pytest src/tests/test_knowledge_manager_agent.py -v

# 方式3: 直接运行（需要确保在项目根目录）
python src/tests/test_knowledge_manager_agent.py
```

### 测试内容

测试脚本会：
1. **准备测试数据**：将 `metadata/shu/books/三国演义.txt` 复制到 `data/concept_knowledge_bases/三国演义/knowledge.txt`
2. **执行索引**：调用 `index_knowledge_base("三国演义")` 构建 GraphRAG 索引
3. **执行检索**：查询"诸葛亮是谁？"，验证检索功能
4. **显示结果**：展示索引状态和检索结果

### 测试输出示例

```
================================================================================
知识管理智能体测试
================================================================================

[步骤1] 准备测试数据...
📄 复制文件: .../三国演义.txt -> .../data/concept_knowledge_bases/三国演义/knowledge.txt
✅ 文件已复制，大小: 2.34 MB

[步骤2] 创建知识管理智能体...
✅ 智能体创建成功

[步骤3] 开始索引知识库...
📚 知识库名称: 三国演义
📄 知识库文件: .../knowledge.txt
✅ 索引成功！

📊 索引状态:
  - 已索引: True
  - 段落数: 1234
  - 内容长度: 1,234,567 字符
  - 索引时间: 2024-01-01T12:00:00

[步骤4] 执行知识检索...
🔍 查询: 诸葛亮是谁？

✅ 检索成功！
📊 检索统计:
  - 目标概念: ['三国演义']
  - 成功来源: ['concept_database:三国演义']
  - 结果数量: 5
  - 使用查询数: 2

📝 检索结果 (显示前3个):
--- 结果 1 ---
来源: concept_database:三国演义
策略: exact_match
相关性: 0.856
内容: 诸葛亮，字孔明，号卧龙，琅琊阳都人，三国时期蜀汉丞相...
```

