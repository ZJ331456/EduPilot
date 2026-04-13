# API 模块 (api/)

## 概述

API 模块基于 FastAPI 构建，提供 RESTful 和 WebSocket 两种接口，支持流式响应和事件推送。

## 目录结构

```
api/
├── __init__.py
├── main.py              # FastAPI 应用入口
└── routers/
    ├── __init__.py
    ├── health.py        # 健康检查
    ├── chat.py          # 对话接口
    ├── graph.py         # 图谱接口
    ├── profile.py       # 用户画像
    ├── plan.py          # 学习计划
    ├── evaluation.py    # 学习评测
    └── ws.py            # WebSocket/SSE 流式接口
```

## 主要接口

### 1. 健康检查

```
GET /api/v1/health
```

响应示例：
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. 对话接口

#### 发送消息

```
POST /api/v1/chat
```

请求体：
```json
{
  "user_id": "user_123",
  "session_id": "session_456",  // 可选，自动创建
  "message": "什么是机器学习？",
  "mode": "direct",             // direct | socratic
  "update_graph": true          // 是否更新图谱
}
```

响应：
```json
{
  "reply": "机器学习是...",
  "session_id": "session_456",
  "mode": "direct",
  "dialogue_nodes": 5,
  "dialogue_edges": 3
}
```

#### 结束会话

```
POST /api/v1/chat/sessions/{session_id}/end
```

### 3. 图谱接口

| 端点 | 方法 | 功能 |
|------|------|------|
| `/graph/knowledge/{kb_id}` | GET | 获取知识库图谱 |
| `/graph/knowledge/{kb_id}/index` | POST | 构建知识库索引 |
| `/graph/knowledge/{kb_id}/query` | GET | 查询知识库 |
| `/graph/session/{session_id}` | GET | 获取会话图谱 |
| `/graph/user/{user_id}/long_term` | GET | 获取用户长期图谱 |

### 4. 用户画像

```
POST /api/v1/profile/analyze
GET /api/v1/profile/{user_id}
```

### 5. 学习计划

```
POST /api/v1/plan/generate
GET /api/v1/plan/{user_id}
```

### 6. 学习评测

```
POST /api/v1/evaluation/run
```

## WebSocket/SSE 流式接口

### SSE 接口

```
GET /api/v1/ws/chat/{client_id}
```

使用 EventSource 客户端连接，支持以下事件：

| 事件类型 | 说明 | 数据结构 |
|----------|------|----------|
| `content` | 内容片段 | `{chunk, is_final, full_content}` |
| `thinking` | 思考过程 | `{thought}` |
| `tool_start` | 工具开始 | `{tool_name, tool_input}` |
| `tool_end` | 工具结束 | `{tool_name, tool_output}` |
| `step_start` | 步骤开始 | `{step_name, agent_name}` |
| `step_end` | 步骤结束 | `{step_name, result}` |
| `message_start` | 消息开始 | `{session_id, mode}` |
| `message_end` | 消息结束 | `{session_id, full_content}` |
| `error` | 错误 | `{error, error_code}` |

### WebSocket 接口

```
WS /api/v1/ws/chat/ws/{user_id}
```

支持双向通信：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/chat/ws/user_123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

// 发送消息
ws.send(JSON.stringify({
  type: 'chat',
  message: '你好',
  mode: 'direct',
  session_id: null
}));
```

## 启动服务

```python
from edupilot.api.main import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

或使用命令行：

```bash
set PYTHONPATH=src
python -m edupilot
```

## CORS 配置

通过 `CORS_ORIGINS` 环境变量配置允许的跨域来源，默认：

```
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
