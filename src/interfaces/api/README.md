# EduPilot API 文档

## 概述

EduPilot API 是一个基于 FastAPI 的 RESTful API 服务，提供智能教育助手的完整功能访问。

## 特性

- ✅ **完整工作流**: 一键启动学习会话，包含查询分析、规划和执行
- 🤖 **独立智能体**: 可单独调用各个智能体的功能
- 💾 **记忆管理**: 用户画像、学习记录和会话记忆管理
- 📚 **知识检索**: 强大的语义检索和知识库管理
- 🔒 **类型安全**: 使用 Pydantic 模型进行请求/响应验证
- 📖 **自动文档**: 集成 Swagger UI 和 ReDoc

## 架构说明

EduPilot API 严格对齐底层 workflow 和 agents 架构：

```
API 层 (interfaces/api/)
    ↓
Workflow 层 (core/workflow/)
    ↓
Agents 层 (core/agents/)
```

详细说明请参考：
- [API_架构对齐说明.md](./API_架构对齐说明.md) - 完整架构说明
- [API_使用示例.md](./API_使用示例.md) - 使用示例和最佳实践

### 接口分类

#### 1. 主流程接口（推荐）
- `/api/agent/v1/workflow/` - 完整的学习工作流
- 适用场景：生产环境，正式学习会话

#### 2. 工具接口（按需使用）
- `/api/agent/v1/memory/` - 用户画像和记忆管理
- `/api/agent/v1/knowledge/` - 知识检索和管理
- 适用场景：数据查询，分析报告，可视化

#### 3. 调试接口（开发测试）
- `/api/agent/v1/agents/` - 直接调用各个智能体
- 适用场景：开发调试，单元测试，性能分析

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
# 方式1: 直接运行
python -m src.interfaces.api.main

# 方式2: 使用 uvicorn
uvicorn src.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问文档

启动服务后，访问以下地址：

- **Swagger UI**: http://localhost:8000/api/agent/v1/docs
- **ReDoc**: http://localhost:8000/api/agent/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/agent/v1/openapi.json

## API 路由结构

### 基础路由

- `GET /` - 根路径，返回API信息
- `GET /api/agent/v1/health` - 健康检查
- `GET /api/agent/v1/stats` - 系统统计信息

### 智能体路由 (Agents)

**前缀**: `/api/agent/v1/agents`

#### 查询分析器
- `POST /query-analyzer` - 分析用户查询，识别意图和查询类型

#### 规划器
- `POST /planner` - 根据查询制定学习计划

#### 执行器
- `POST /executor` - 执行学习计划并生成响应

#### 苏格拉底引导
- `POST /socratic-guide` - 生成苏格拉底式引导问题

### 工作流路由 (Workflow)

**前缀**: `/api/agent/v1/workflow`

#### 会话管理
- `POST /session/start` - 启动学习会话（完整三步流程）
- `POST /session/continue` - 继续现有会话
- `GET /session/{session_id}` - 获取会话信息
- `DELETE /session/{session_id}` - 结束会话
- `GET /sessions/active` - 获取所有活跃会话

### 记忆管理路由 (Memory)

**前缀**: `/api/agent/v1/memory`

#### 用户画像
- `GET /profile/{user_id}` - 获取用户画像
- `POST /profile/{user_id}/update` - 更新用户画像

#### 会话记忆
- `GET /session/{session_id}` - 获取会话记忆
- `POST /session/analyze` - 分析会话记忆

#### 学习记录
- `GET /learning-records/{user_id}` - 获取学习记录

#### 知识图谱
- `GET /knowledge-graph/{user_id}` - 获取用户知识图谱

### 知识检索路由 (Knowledge)

**前缀**: `/api/agent/v1/knowledge`

#### 检索
- `POST /retrieve` - 检索知识内容

#### 概念查询
- `GET /concept/{concept_name}` - 获取概念详情
- `GET /related/{concept_name}` - 获取相关概念

#### 知识库管理
- `GET /bases` - 获取知识库列表
- `GET /bases/{knowledge_base_name}` - 获取知识库详情

#### 搜索建议
- `GET /suggestions` - 获取搜索建议

## 使用示例

### 1. 启动完整学习会话

这是最常用的API，一次调用完成查询分析、规划和执行全流程。

```python
import requests

response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/start",
    json={
        "user_id": "test_user",
        "query": "什么是大化改新？",
        "workflow_config": {
            "enable_socratic": True,
            "enable_learning": True
        }
    }
)

result = response.json()
print(f"响应: {result['response']}")
print(f"会话ID: {result['session_id']}")
```

### 2. 继续学习会话

```python
response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/continue",
    json={
        "session_id": "your-session-id",
        "user_id": "test_user",
        "user_response": "可以举个例子吗？"
    }
)

result = response.json()
print(f"响应: {result['response']}")
```

### 3. 单独调用查询分析器

```python
response = requests.post(
    "http://localhost:8000/api/agent/v1/agents/query-analyzer",
    json={
        "query": "大化改新是什么时候发生的？",
        "user_id": "test_user",
        "use_llm_refinement": True
    }
)

result = response.json()
print(f"意图: {result['intent']}")
print(f"查询类型: {result['query_type']}")
print(f"置信度: {result['confidence']}")
```

### 4. 检索知识

```python
response = requests.post(
    "http://localhost:8000/api/agent/v1/knowledge/retrieve",
    json={
        "query": "大化改新",
        "top_k": 5,
        "retrieval_strategy": "hybrid"
    }
)

result = response.json()
print(f"找到 {result['total_count']} 条结果")
for item in result['results']:
    print(f"- {item['title']}: {item['content'][:100]}...")
```

### 5. 获取用户画像

```python
response = requests.get(
    "http://localhost:8000/api/agent/v1/memory/profile/test_user",
    params={
        "include_triples": True,
        "include_emotions": True,
        "include_patterns": True
    }
)

result = response.json()
print(f"用户: {result['user_id']}")
print(f"总交互次数: {result['statistics']['total_interactions']}")
```

## 请求/响应模型

### 通用响应格式

所有API响应都遵循统一的格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... },
  "timestamp": "2023-10-09T12:00:00"
}
```

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "error_detail": { ... },
  "timestamp": "2023-10-09T12:00:00"
}
```

## 配置选项

### 工作流配置

```python
workflow_config = {
    "max_iterations": 5,           # 最大迭代次数
    "timeout_seconds": 300,        # 超时时间（秒）
    "enable_learning": True,       # 启用学习分析
    "enable_socratic": True,       # 启用苏格拉底引导
    "auto_continue": False         # 自动继续对话
}
```

### 检索策略

- `"semantic"` - 纯语义检索
- `"keyword"` - 关键词检索
- `"hybrid"` - 混合检索（推荐）

## 性能优化

### 缓存机制

API自动缓存以下内容：
- 工作流实例（单例模式）
- 智能体实例（依赖注入）
- 用户画像（内存缓存）

### 并发处理

FastAPI 基于异步架构，支持高并发请求处理。

### 请求限流

建议在生产环境中添加限流中间件：

```python
# 可选：添加限流
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## 部署建议

### 生产环境部署

```bash
# 使用 gunicorn + uvicorn workers
gunicorn src.interfaces.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300
```

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量

```bash
# .env 文件
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
LOG_LEVEL=INFO
```

## 安全建议

1. **启用 CORS 限制**: 在生产环境中限制允许的域名
2. **添加认证**: 实现 JWT 或 OAuth2 认证
3. **请求验证**: 使用 Pydantic 模型验证所有输入
4. **限流**: 添加请求速率限制
5. **HTTPS**: 使用 HTTPS 加密通信

## 监控和日志

### 日志配置

API使用标准的 Python logging 模块：

```python
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### 监控指标

API自动记录以下指标：
- 请求总数
- 成功/失败请求数
- 平均响应时间
- 各智能体执行统计

访问 `/api/agent/v1/stats` 获取实时统计信息。

## 故障排查

### 常见问题

1. **端口被占用**
   ```bash
   # 更换端口
   uvicorn src.interfaces.api.main:app --port 8001
   ```

2. **依赖缺失**
   ```bash
   pip install -r requirements.txt
   ```

3. **智能体初始化失败**
   - 检查配置文件
   - 确认 LLM 服务可用
   - 查看日志详细信息

## 开发指南

### 添加新路由

1. 在 `routers/` 目录创建新文件
2. 定义路由函数
3. 在 `main.py` 中注册路由

```python
# routers/new_feature.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New feature"}

# main.py
from .routers import new_feature
app.include_router(
    new_feature.router,
    prefix="/api/agent/v1/new-feature",
    tags=["NewFeature"]
)
```

### 添加新模型

在 `models.py` 中定义 Pydantic 模型：

```python
class NewRequest(BaseModel):
    field1: str = Field(..., description="字段描述")
    field2: int = Field(default=0, description="可选字段")

class NewResponse(BaseResponse):
    data: Dict[str, Any] = Field(..., description="响应数据")
```

## 许可证

EduPilot API 使用与主项目相同的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目 Issue: [GitHub Issues]
- 文档: [项目文档]

---

**版本**: 3.0.0  
**更新日期**: 2025-10-09

