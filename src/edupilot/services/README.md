# Services 模块 (services/)

## 概述

Services 模块提供业务逻辑层的核心服务，包括 LLM 客户端、图谱服务、存储服务等。

## 目录结构

```
services/
├── llm/                    # LLM 客户端
│   ├── __init__.py
│   ├── client.py          # 统一 OpenAI 兼容客户端
│   ├── factory.py         # 单例工厂
│   └── graphrag_llm.py   # GraphRAG 函数封装
├── graph/                  # 图谱服务
│   ├── __init__.py
│   ├── knowledge_graph_service.py  # 知识库图谱
│   └── dialogue_graph_service.py   # 对话图谱
├── storage/                # 存储服务
│   ├── __init__.py
│   ├── session_store.py   # 会话存储
│   ├── profile_store.py   # 画像/计划存储
│   └── user_graph_store.py # 用户长期图谱存储
└── prompt/               # 提示词加载器
    └── loader.py
```

## LLM 客户端

### UnifiedOpenAIClient

封装 AsyncOpenAI，支持流式响应和工具调用。

```python
from edupilot.services.llm import get_llm_client

client = get_llm_client()

# 普通对话
response = await client.chat(messages, temperature=0.7)

# 流式对话
async for chunk in client.stream_chat(messages, temperature=0.7):
    print(chunk, end="", flush=True)

# 带工具调用
response = await client.chat_with_tools(messages, tools)

# 向量嵌入
embeddings = await client.embed(texts)
```

### 支持的 LLM 提供商

通过 `LLM_PROVIDER` 环境变量切换：

| 提供商 | base_url | 说明 |
|--------|----------|------|
| `siliconflow` | `https://api.siliconflow.cn/v1` | 默认 |
| `bailian` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 阿里云百炼 |
| `local_vllm` | `http://127.0.0.1:8000/v1` | 本地 vLLM |
| `local_ollama` | `http://127.0.0.1:11434/v1` | 本地 Ollama |

## 图谱服务

### KnowledgeGraphService 知识库图谱

基于 nano_graphrag 实现，支持 GraphRAG 检索。

```python
from edupilot.services.graph import KnowledgeGraphService

kg = KnowledgeGraphService()

# 构建索引
await kg.ensure_index("kb_001", source_text_path="/path/to/text.txt")

# 查询
result = await kg.query("kb_001", "什么是机器学习", mode="local")

# 导出图谱
graph = kg.export_visual_graph("kb_001")
```

### DialogueGraphService 对话图谱

从对话中抽取实体和关系。

```python
from edupilot.services.graph import DialogueGraphService

dgraph = DialogueGraphService()

# 抽取图谱
nodes, edges = await dgraph.extract(dialogue_text)
```

## 存储服务

### SessionStore 会话存储

JSON 格式存储会话数据。

```python
from edupilot.services.storage import SessionStore

store = SessionStore()

# 创建会话
session_id = store.create("user_123", meta={"mode": "direct"})

# 追加消息
store.append_message(session_id, "user", "你好")
store.append_message(session_id, "assistant", "你好，有什么可以帮你的？")

# 获取最后 N 轮对话
tail = store.merge_messages_tail(session_id, max_turns=12)

# 更新图谱
store.update_dialogue_graph(session_id, nodes, edges)

# 标记结束
store.mark_ended(session_id)
```

存储路径：`data/sessions/{session_id}.json`

### UserGraphStore 用户长期图谱

跨会话合并用户知识网络。

```python
from edupilot.services.storage import UserGraphStore

ug = UserGraphStore()

# 合并会话图谱
ug.merge_from_session("user_123", nodes, edges)

# 加载用户图谱
graph = ug.load_graph("user_123")
```

存储路径：`data/users/{user_id}/long_term_graph.json`

### ProfileStore 用户画像

```python
from edupilot.services.storage import ProfileStore

ps = ProfileStore()

# 保存画像
ps.save_profile("user_123", profile_data)

# 加载画像
profile = ps.load_profile("user_123")

# 保存/加载学习计划
ps.save_plan("user_123", plan_data)
plan = ps.load_plan("user_123")
```

存储路径：`data/users/{user_id}/profile.json` / `plan.json`

## 提示词加载器

```python
from edupilot.services.prompt.loader import load_agent_prompt, format_prompt

# 加载提示词
prompts = load_agent_prompt("chat_direct")

# 格式化提示词
text = format_prompt("你好，{name}", name="小明")
```
