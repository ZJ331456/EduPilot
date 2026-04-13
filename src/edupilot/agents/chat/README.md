# ChatAgent - 核心对话智能体

核心对话智能体，负责用户交互的入口，支持直接回答与苏格拉底式引导两种模式。

## 架构设计

```
ChatAgent
├── QueryAnalyzer      # 意图分析器
├── DialogueRouter    # 对话路由器
└── _generate_response()  # 回复生成器
```

## 核心类

### ChatAgent

主对话智能体，继承自 `MultiTurnAgent`。

```python
class ChatAgent(MultiTurnAgent):
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self.query_analyzer = QueryAnalyzer()
        self.router = DialogueRouter()
```

### ChatMode 枚举

```python
class ChatMode(str, Enum):
    DIRECT = "direct"      # 直接回答模式
    SOCRATIC = "socratic" # 苏格拉底引导模式
```

### QueryAnalyzer

意图分析器，分析用户查询的意图和类型。

```python
@dataclass
class IntentResult:
    intent: str           # 意图类型: question/explanation/summary/plan
    query_type: str       # 查询类型: factual/procedural/conceptual/analytical
    confidence: float     # 置信度
    keywords: List[str]   # 关键词
```

### DialogueRouter

对话路由器，根据意图分析结果选择最优响应策略。

```python
@dataclass
class RouteResult:
    mode: ChatMode                    # 响应模式
    use_rag: bool                    # 是否使用 RAG 检索
    use_tools: bool                  # 是否使用工具
    reasoning_level: str              # 推理深度
```

## 工作流程

```
用户消息
    │
    ▼
┌─────────────────────┐
│  Step 1: 意图分析    │  QueryAnalyzer.analyze()
│  • intent            │  ├── intent: question/explanation/summary/plan
│  • query_type        │  ├── query_type: factual/procedural/conceptual/analytical
│  • confidence        │  ├── confidence: 0.0-1.0
│  • keywords          │  └── keywords: [关键词列表]
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Step 2: 智能路由    │  DialogueRouter.route()
│  • mode             │  └── RouteResult:
│  • use_rag          │      ├── mode: DIRECT/SOCRATIC
│  • use_tools        │      ├── use_rag: bool
│  • reasoning_level  │      ├── use_tools: bool
└─────────┬───────────┘      └── reasoning_level: shallow/deep
          │
          ▼
┌─────────────────────┐
│  Step 3: 回复生成    │  _generate_response()
│  • 加载模式提示词    │
│  • 流式 LLM 调用    │
│  • SSE 事件推送     │
└─────────────────────┘
```

## 路由规则

| 用户意图 | 查询类型 | 默认模式 | 使用 RAG |
|----------|----------|----------|----------|
| question | conceptual/analytical | SOCRATIC | Yes |
| question | procedural/factual | DIRECT | Yes |
| explanation | any | DIRECT | Yes |
| summary | any | DIRECT | No |
| plan | any | DIRECT | Yes |

## 对话模式

### DIRECT 模式 (直接对话)

特点：
- 直接给出答案
- 结构化输出（定义→原理→应用→示例）
- 适合事实性、程序性问题

提示词策略：
- 清晰准确的定义
- 适当的例子
- 结构化的解释

### SOCRATIC 模式 (苏格拉底引导)

特点：
- 通过提问引导用户思考
- 层层递进，由浅入深
- 培养自主学习能力

提示词策略：
- 从简单问题开始
- 逐步深入核心概念
- 引导用户自己得出结论

## 使用示例

### 基本调用

```python
from edupilot.agents.chat.agent import ChatAgent
from edupilot.agents.base.agent import AgentConfig
from edupilot.core.protocol import UnifiedContext, AgentMode

# 创建 Agent
agent = ChatAgent(AgentConfig(
    name="ChatAgent",
    streaming_enabled=True
))

# 构建上下文
ctx = UnifiedContext(
    session_id="session_123",
    user_id="user_456",
    user_message="什么是机器学习？",
    mode=AgentMode.DIRECT,
    history=[]
)

# 执行对话
response = await agent.execute(ctx, builder=None, stream=False)
print(response)
```

### 流式调用

```python
# 流式响应
async for event in agent.execute_stream(ctx):
    print(event.type, event.data)
```

### SSE 事件流

```python
from edupilot.core.stream import ResponseBuilder, StreamBus

bus = StreamBus()
builder = ResponseBuilder(bus, session_id="session_123")

await agent.execute(ctx, builder=builder, stream=True)
# 前端可通过 SSE 订阅 bus 获取实时响应
```

## 集成接口

### REST API

```bash
# POST /api/v1/chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "message": "解释一下梯度下降算法",
    "mode": "direct",
    "update_graph": true
  }'
```

### WebSocket/SSE

```bash
# GET /api/v1/ws/chat/{client_id}
# 通过 SSE 接收流式响应
```

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| temperature | float | 0.7 | LLM 温度参数 |
| max_tokens | int | 4096 | 最大生成 token 数 |
| streaming_enabled | bool | True | 是否启用流式响应 |
| tools_enabled | bool | True | 是否启用工具调用 |
| max_retries | int | 3 | 最大重试次数 |

## 扩展开发

### 添加新的意图类型

1. 在 `QueryAnalyzer.analyze()` 中添加新的意图识别逻辑
2. 在 `DialogueRouter.route()` 中添加对应的路由规则
3. 创建对应的提示词模板

### 添加新的对话模式

1. 在 `ChatMode` 枚举中添加新模式
2. 在提示词目录添加对应的提示词文件
3. 在 `DialogueRouter` 中添加路由规则
