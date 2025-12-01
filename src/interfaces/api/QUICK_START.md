# EduPilot API 快速启动指南

## 🚀 快速启动

### 方式 1: 使用模块启动（推荐）

```bash
# 默认启动（127.0.0.1:8000）
python -m src.interfaces.api

# 自定义端口
python -m src.interfaces.api --port 8080

# 开发模式（自动重载）
python -m src.interfaces.api --reload

# 生产模式（所有网卡，多进程）
python -m src.interfaces.api --host 0.0.0.0 --port 8000 --workers 4
```

### 方式 2: 使用完整参数

```bash
python -m src.interfaces.api \
  --host 0.0.0.0 \
  --port 8080 \
  --reload \
  --log-level DEBUG
```

## 📋 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--host` | - | `127.0.0.1` | 服务器主机地址 |
| `--port` | `-p` | `8000` | 服务器端口 |
| `--reload` | `-r` | `False` | 启用自动重载（开发模式） |
| `--workers` | `-w` | `1` | 工作进程数（生产模式） |
| `--log-level` | - | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL） |
| `--no-access-log` | - | `False` | 禁用访问日志 |

## 📖 使用示例

### 开发环境

```bash
# 开启自动重载，调试级别日志
python -m src.interfaces.api --reload --log-level DEBUG
```

### 测试环境

```bash
# 监听所有网卡，便于外部访问
python -m src.interfaces.api --host 0.0.0.0 --port 8080
```

### 生产环境

```bash
# 多进程模式，提高并发性能
python -m src.interfaces.api --host 0.0.0.0 --port 8000 --workers 4 --log-level WARNING
```

## 🌐 访问地址

启动后可访问以下地址：

- **API文档（Swagger）**: http://localhost:8000/api/agent/v1/docs
- **API文档（ReDoc）**: http://localhost:8000/api/agent/v1/redoc
- **健康检查**: http://localhost:8000/api/agent/v1/health
- **系统统计**: http://localhost:8000/api/agent/v1/stats

## 🧪 快速测试

### 方法 1: 使用浏览器

1. 启动服务：`python -m src.interfaces.api`
2. 打开浏览器访问：http://localhost:8000/api/agent/v1/docs
3. 在 Swagger UI 中测试各个接口

### 方法 2: 使用 curl

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

### 方法 3: 使用 Python 客户端

```python
# 运行示例客户端
python src/interfaces/api/example_client.py
```

## ⚙️ 配置说明

### 环境变量（可选）

可以创建 `.env` 文件配置默认参数：

```bash
API_HOST=127.0.0.1
API_PORT=8000
API_LOG_LEVEL=INFO
```

### 生产环境建议

1. **使用多进程**：`--workers 4`（根据CPU核心数调整）
2. **限制日志级别**：`--log-level WARNING`
3. **配置反向代理**：Nginx 或 Apache
4. **启用 HTTPS**：使用 SSL 证书
5. **添加限流**：防止滥用

## 🐛 故障排查

### 端口被占用

```bash
# 查看端口占用（Windows）
netstat -ano | findstr :8000

# 更换端口
python -m src.interfaces.api --port 8001
```

### 外部无法访问

```bash
# 确保监听所有网卡
python -m src.interfaces.api --host 0.0.0.0

# 检查防火墙设置
```

### 依赖缺失

```bash
# 安装所有依赖
pip install -r requirements.txt

# 仅安装API相关依赖
pip install fastapi uvicorn requests
```

## 📚 更多文档

- [完整 API 文档](./README.md)
- [使用示例](./example_client.py)
- [项目文档](../../../docs/)

## 💡 提示

- 开发时使用 `--reload` 自动重载代码
- 生产环境建议使用 Gunicorn: `pip install gunicorn`
- 使用 `Ctrl+C` 优雅停止服务器
- 查看帮助：`python -m src.interfaces.api --help`

