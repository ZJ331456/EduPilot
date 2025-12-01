# EduPilot API 启动说明

## ✅ 已完成的工作

所有 API 接口已经创建完成，使用 `api/agent/v1` 作为统一前缀！

### 📁 文件结构

```
src/interfaces/api/
├── __init__.py              # API模块初始化
├── __main__.py              # 模块启动入口（支持 python -m）
├── main.py                  # FastAPI主应用
├── models.py                # 请求/响应数据模型
├── dependencies.py          # 依赖注入
├── README.md                # 完整API文档
├── QUICK_START.md           # 快速启动指南
├── example_client.py        # Python客户端示例
└── routers/                 # 路由模块
    ├── __init__.py
    ├── agents.py            # 智能体路由
    ├── workflow.py          # 工作流路由
    ├── memory.py            # 记忆管理路由
    └── knowledge.py         # 知识检索路由
```

### 🚀 API路由列表

#### 1. 基础路由
- `GET /` - API欢迎页
- `GET /api/agent/v1/health` - 健康检查
- `GET /api/agent/v1/stats` - 系统统计

#### 2. 工作流路由（`/api/agent/v1/workflow`）
- `POST /session/start` - 启动完整学习会话★
- `POST /session/continue` - 继续会话
- `GET /session/{session_id}` - 获取会话信息
- `DELETE /session/{session_id}` - 结束会话
- `GET /sessions/active` - 获取活跃会话列表

#### 3. 智能体路由（`/api/agent/v1/agents`）
- `POST /query-analyzer` - 查询分析
- `POST /planner` - 学习规划
- `POST /executor` - 执行计划
- `POST /socratic-guide` - 苏格拉底引导

#### 4. 记忆管理路由（`/api/agent/v1/memory`）
- `GET /profile/{user_id}` - 获取用户画像
- `POST /profile/{user_id}/update` - 更新用户画像
- `GET /session/{session_id}` - 获取会话记忆
- `POST /session/analyze` - 分析会话记忆
- `GET /learning-records/{user_id}` - 获取学习记录
- `GET /knowledge-graph/{user_id}` - 获取知识图谱

#### 5. 知识检索路由（`/api/agent/v1/knowledge`）
- `POST /retrieve` - 检索知识
- `GET /concept/{concept_name}` - 获取概念详情
- `GET /related/{concept_name}` - 获取相关概念
- `GET /bases` - 获取知识库列表
- `GET /bases/{knowledge_base_name}` - 获取知识库详情
- `GET /suggestions` - 获取搜索建议

## 📦 依赖安装

### 方法1：安装完整依赖（推荐）

```bash
pip install -r requirements.txt
```

### 方法2：仅安装API核心依赖

```bash
# 核心依赖
pip install fastapi uvicorn requests pydantic python-dotenv

# 如果需要生产环境部署
pip install gunicorn
```

### 方法3：处理可选依赖问题

如果遇到 `aioboto3`、`nano-graphrag` 等依赖缺失，可以：

**选项A：安装所有依赖**
```bash
pip install -r requirements.txt
```

**选项B：临时禁用相关功能**
修改 `requirements.txt`，将相关依赖改为可选：
```
# aioboto3>=12.0.0  # 临时注释
```

## 🎯 启动API服务

### 最简单的方式

```bash
# 默认启动（127.0.0.1:8000）
python -m src.interfaces.api
```

### 自定义端口

```bash
# 方式1：使用 --port 参数
python -m src.interfaces.api --port 8080

# 方式2：使用简写 -p
python -m src.interfaces.api -p 8080
```

### 开发模式（自动重载）

```bash
python -m src.interfaces.api --reload
```

### 生产模式（多进程）

```bash
python -m src.interfaces.api --host 0.0.0.0 --port 8000 --workers 4
```

### 完整参数示例

```bash
python -m src.interfaces.api \
  --host 0.0.0.0 \
  --port 8080 \
  --reload \
  --log-level DEBUG
```

## 📖 查看帮助

```bash
python -m src.interfaces.api --help
```

## 🌐 访问API文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/api/agent/v1/docs
- **ReDoc**: http://localhost:8000/api/agent/v1/redoc
- **健康检查**: http://localhost:8000/api/agent/v1/health

## 🧪 快速测试

### 使用 curl

```bash
# 健康检查
curl http://localhost:8000/api/agent/v1/health

# 启动学习会话
curl -X POST http://localhost:8000/api/agent/v1/workflow/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query": "什么是大化改新？"
  }'
```

### 使用Python

```python
import requests

# 启动学习会话
response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/start",
    json={
        "user_id": "test_user",
        "query": "什么是大化改新？"
    }
)

print(response.json())
```

### 使用示例客户端

```bash
python src/interfaces/api/example_client.py
```

## 🔧 常见问题

### Q1: ModuleNotFoundError: No module named 'xxx'

**解决方案**：
```bash
pip install -r requirements.txt
```

### Q2: 端口被占用

**解决方案**：
```bash
# 更换端口
python -m src.interfaces.api --port 8001
```

### Q3: 外部无法访问

**解决方案**：
```bash
# 监听所有网卡
python -m src.interfaces.api --host 0.0.0.0
```

### Q4: 导入错误

**原因**：所有导入路径已修复为使用 `src.` 前缀

**检查**：
- `from src.core.workflow import ...` ✅
- `from src.domain.agents import ...` ✅  
- `from src.infrastructure.utils import ...` ✅

## 📚 更多文档

- [完整API文档](src/interfaces/api/README.md)
- [快速启动指南](src/interfaces/api/QUICK_START.md)
- [客户端示例](src/interfaces/api/example_client.py)

## 🎉 开始使用

```bash
# 1. 安装依赖
pip install fastapi uvicorn requests pydantic

# 2. 启动服务
python -m src.interfaces.api

# 3. 打开浏览器
# http://localhost:8000/api/agent/v1/docs
```

---

**版本**: 3.0.0  
**创建日期**: 2025-10-09

