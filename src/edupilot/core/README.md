# 核心模块 (core/)

## 概述

核心模块定义了 EduPilot 的基础协议和事件流系统，为整个应用提供统一的数据结构和通信机制。

## 主要组件

### 1. StreamEvent 事件流协议

定义在 `stream.py` 中，实现了 SSE (Server-Sent Events) 流式响应机制。

#### 事件类型 (EventType)

```python
class EventType(str, Enum):
    # 内容事件
    CONTENT = "content"          # 主内容片段（流式）
    THINKING = "thinking"       # 思考过程
    TOOL_START = "tool_start"   # 工具开始执行
    TOOL_END = "tool_end"       # 工具执行完成
    TOOL_ERROR = "tool_error"   # 工具执行错误
    STEP_START = "step_start"   # 步骤开始
    STEP_END = "step_end"       # 步骤完成
    # 元事件
    MESSAGE_START = "message_start"    # 消息开始
    MESSAGE_END = "message_end"        # 消息结束
    ERROR = "error"                   # 错误
    HEARTBEAT = "heartbeat"           # 心跳保活
    # 分析事件
    ANALYSIS = "analysis"             # 查询分析结果
```

#### 使用示例

```python
from edupilot.core.stream import StreamEvent, EventType, StreamBus

bus = StreamBus()

# 发布事件
await bus.publish(StreamEvent(
    type=EventType.CONTENT,
    data={"chunk": "Hello", "is_final": False}
))

# 订阅事件
async for event in bus.subscribe("client_123"):
    print(event.type, event.data)
```

### 2. StreamBus 事件总线

异步事件流总线，支持多订阅者、事件发布与消费。

```python
class StreamBus:
    async def subscribe(subscriber_id: str) -> AsyncGenerator[StreamEvent, None]
    async def publish(event: StreamEvent) -> None
    async def broadcast(event: StreamEvent) -> None
    async def close(subscriber_id: str) -> None
```

### 3. ResponseBuilder 响应构建器

逐步组装流式响应，支持多阶段事件。

```python
builder = ResponseBuilder(bus, session_id, agent_name)

await builder.start_message()
await builder.start_step("llm_call")
await builder.send_content("Hello")
await builder.end_step("llm_call")
await builder.end_message()
```

### 4. UnifiedContext 统一上下文

贯穿所有 Agent 组件的单一数据对象。

```python
ctx = UnifiedContext(
    session_id="session_123",
    user_id="user_456",
    user_message="什么是机器学习？",
    mode=AgentMode.DIRECT
)
ctx.add_history("user", "你好")
```

### 5. AgentMode 对话模式

```python
class AgentMode(str, Enum):
    DIRECT = "direct"              # 直接回答模式
    SOCRATIC = "socratic"         # 苏格拉底式提问模式
    DEEP_SOLVE = "deep_solve"     # 深度问题解决模式
    RESEARCH = "research"          # 深度研究模式
    QUIZ = "quiz"                 # 测验生成模式
```

## 导出

```python
from edupilot.core import (
    EventType, StreamEvent, StreamBus, ResponseBuilder,
    AgentMode, ToolDefinition, ToolResult,
    UnifiedContext, AgentResponse, BaseTool
)
```
