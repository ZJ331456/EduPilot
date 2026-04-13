# Agent 模块 (agents/)

## 概述

Agent 模块是 EduPilot 的核心智能体系统，采用分层架构设计，支持流式响应和工具系统。

## 架构设计

```
agents/
├── __init__.py           # 统一导出
├── base/                 # Agent 基类
│   └── agent.py
├── chat/                # 统一对话 Agent
│   ├── __init__.py
│   ├── agent.py
│   └── prompts/zh/prompts.yaml
├── tools/               # 内置工具
│   └── builtin.py
├── user_profile/        # 用户画像 Agent
├── learning_planner/     # 学习计划 Agent
├── evaluation/          # 学习评测 Agent
└── dialogue_graph/       # 对话图谱抽取
```

## ChatAgent 统一对话 Agent

### 特点

1. **多模式支持**：直接回答（direct）和苏格拉底式引导（socratic）
2. **意图分析**：自动理解用户查询意图
3. **智能路由**：根据意图选择最佳响应策略
4. **流式输出**：支持实时流式响应

### 使用示例

```python
from edupilot.agents.chat.agent import ChatAgent
from edupilot.core.protocol import AgentMode, UnifiedContext
from edupilot.core.stream import ResponseBuilder, StreamBus

agent = ChatAgent()
bus = StreamBus()
builder = ResponseBuilder(bus, "session_1", "ChatAgent")
ctx = UnifiedContext(
    session_id="session_1",
    user_id="user_1",
    user_message="什么是机器学习？",
    mode=AgentMode.DIRECT
)
result = await agent.execute(ctx, builder=builder)
```

### 模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `direct` | 直接回答问题 | 知识问答、概念解释 |
| `socratic` | 苏格拉底式提问引导 | 启发式教学、培养批判性思维 |

## BaseAgent 统一基类

所有智能体继承 `BaseAgent`，获得统一的消息处理流程。

### Agent 类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `BaseAgent` | 抽象基类 | 定义标准接口 |
| `SingleTurnAgent` | 单轮对话 | 简单问答、用户画像分析 |
| `MultiTurnAgent` | 多轮对话 | 复杂任务、工具调用 |
| `OrchestratorAgent` | 编排器 | 多子 Agent 协作 |

## 内置工具系统

### 工具列表

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| `rag_retrieve` | 知识库检索 | query, mode, top_k |
| `brainstorm` | 头脑风暴 | topic, count |
| `reason` | 深度推理 | problem, method |
| `summarize` | 文本摘要 | text, max_length |
| `explain_code` | 代码解释 | code, language |

### 使用示例

```python
from edupilot.agents.tools.builtin import get_tool

tool = get_tool("rag_retrieve")
result = await tool.execute(query="什么是机器学习")
```

## 其他 Agent

### UserProfileAgent 用户画像

基于对话历史和知识图谱生成结构化 JSON 画像。

### LearningPlannerAgent 学习计划

结合用户画像生成结构化周计划 JSON。

### EvaluationAgent 学习评测

评估用户学习掌握程度，输出分数和详细建议。

### DialogueGraphAgent 对话图谱

从对话中抽取实体和关系，构建知识网络。

## 导出

```python
from edupilot.agents import (
    ChatAgent,
    ChatMode,
    RAGTool,
    BrainstormTool,
    ReasonTool,
    SummaryTool,
    CodeExplainTool
)
```
