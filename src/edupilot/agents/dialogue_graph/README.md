# DialogueGraph - 对话图谱模块

对话图谱模块，负责从对话内容中实时抽取实体和关系，构建结构化的知识网络。

## 模块概述

该模块目前处于待开发状态，计划实现以下功能：

- 对话内容实体识别
- 实体关系抽取
- 图谱动态更新
- 知识融合与推理

## 核心服务

### DialogueGraphService

对话图谱服务，负责对话内容到图谱结构的转换。

```python
class DialogueGraphService:
    async def extract(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        从文本中抽取节点和边

        Returns:
            Tuple[List[Dict], List[Dict]]: (nodes, edges)
        """
```

## 数据结构

### 节点 (Node)

```python
@dataclass
class GraphNode:
    id: str              # 节点唯一标识
    label: str          # 节点标签
    node_type: str      # 节点类型: concept/entity/question
    properties: Dict     # 节点属性
    weight: float       # 节点权重
```

### 边 (Edge)

```python
@dataclass
class GraphEdge:
    source: str         # 源节点 ID
    target: str         # 目标节点 ID
    relation: str       # 关系类型
    weight: float       # 边权重
    properties: Dict     # 边属性
```

### 对话图谱 (DialogueGraph)

```python
@dataclass
class DialogueGraph:
    nodes: List[GraphNode]   # 节点列表
    edges: List[GraphEdge]   # 边列表
    metadata: Dict           # 元数据
```

## 工作流程

```
对话消息
    │
    ▼
┌─────────────────────┐
│  文本预处理          │
│  • 分句             │
│  • 命名实体识别      │
│  • 关键词抽取       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  实体抽取           │
│  • 概念实体         │
│  • 关系实体         │
│  • 事件实体         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  关系抽取           │
│  • 因果关系         │
│  • 包含关系         │
│  • 对比关系         │
│  • 时序关系         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  图谱构建           │
│  • 节点去重         │
│  • 边聚合           │
│  • 权重计算         │
└─────────────────────┘
```

## 关系类型

| 关系类型 | 说明 | 示例 |
|----------|------|------|
| `is_a` | 概念从属 | "机器学习 is_a 人工智能" |
| `part_of` | 部分整体 | "神经元 part_of 神经网络" |
| `causes` | 因果关系 | "梯度消失 causes 训练困难" |
| `depends_on` | 依赖关系 | "深度学习 depends_on 大量数据" |
| `similar_to` | 相似关系 | "CNN similar_to RNN" |
| `opposite_to` | 对比关系 | "监督学习 opposite_to 无监督学习" |

## 存储结构

对话图谱以 JSON 格式存储：

```json
{
  "session_id": "xxx",
  "user_id": "xxx",
  "created_at": "2024-01-01T00:00:00Z",
  "nodes": [
    {
      "id": "node_1",
      "label": "机器学习",
      "node_type": "concept",
      "properties": {"frequency": 5},
      "weight": 0.8
    }
  ],
  "edges": [
    {
      "source": "node_1",
      "target": "node_2",
      "relation": "is_a",
      "weight": 1.0
    }
  ]
}
```

## 存储路径

```
data/
└── sessions/
    └── {session_id}.json    # 包含 dialogue_graph 字段
```

## 使用示例

### 抽取对话图谱

```python
from edupilot.services.graph import DialogueGraphService

service = DialogueGraphService()

# 从对话历史抽取图谱
dialogue_history = """
用户：什么是机器学习？
助手：机器学习是人工智能的一个分支...

用户：它和深度学习有什么关系？
助手：深度学习是机器学习的一个子领域...
"""

nodes, edges = await service.extract(dialogue_history)
print(f"抽取到 {len(nodes)} 个节点, {len(edges)} 条边")
```

### 合并到用户长期图谱

```python
from edupilot.services.storage import UserGraphStore

store = UserGraphStore()

# 合并会话图谱到用户长期图谱
store.merge_from_session(
    user_id="user_123",
    nodes=nodes,
    edges=edges
)
```

## 集成使用

ChatAgent 在处理对话时会自动调用对话图谱服务：

```python
# agents/chat/agent.py
if req.update_graph:
    tail = store.merge_messages_tail(sid, max_turns=16)
    nodes, edges = await dgraph.extract(tail)
    store.update_dialogue_graph(sid, nodes, edges)
    ug.merge_from_session(req.user_id, nodes, edges)
```

## 扩展计划

- [ ] 实现基于 LLM 的实体识别
- [ ] 实现基于规则的实体抽取
- [ ] 实现图谱可视化接口
- [ ] 实现图谱查询语言
- [ ] 支持知识推理与补全

## 相关模块

- [ChatAgent](chat/README.md) - 对话智能体
- [UserGraphStore](../services/storage/user_graph_store.py) - 用户长期图谱存储
- [KnowledgeGraphService](../services/graph/knowledge_graph_service.py) - 知识库图谱服务
