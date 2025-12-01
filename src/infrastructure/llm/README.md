# LLM 集成层

此模块为 **EduPilot** 提供了一个模块化抽象，用于与不同的大语言模型提供程序交互。目前实现了以下客户端：

- **Ollama** – 通过 [Ollama API](https://www.llamafactory.cn/ollama-docs/api.html) 提供的自托管推理服务
- **阿里巴巴百炼 (Qwen)** – 由 [DashScope 平台](https://bailian.console.aliyun.com/) 提供的 OpenAI 兼容端点

## 包结构

| 文件 | 作用 |
| ---- | ------- |
| `base.py` | 定义共享的数据类（`Message`、`LLMResponse`）和 `BaseLLMClient` 抽象类 |
| `ollama_client.py` | 与 Ollama 实例通信的具体实现（如果 Python SDK 存在兼容性问题，会自动回退到 HTTP 适配器） |
| `qwen_client.py` | 用于 Bailian/Qwen OpenAI 兼容 API 的具体实现 |
| `manager.py` | 提供 `LLMManager` 注册表以及便捷的异步适配器 |
| `settings.py` | 提供轻量级配置数据类和环境变量加载器 |
| `__init__.py` | 模块的公共导出 |

## 快速开始

```python
from infrastructure.llm import (
    get_llm_manager,
    Message,
    MessageRole,
)

manager = get_llm_manager()
reply = manager.generate_response(
    "请介绍一下EduPilot的整体架构。",
    system_prompt="你是一名专业的教学助理。",
)
print(reply)
```

## 配置

默认情况下，设置从环境变量加载。以下是最常用的键：

### Ollama

| 变量 | 默认值 | 描述 |
| -------- | ------- | ----------- |
| `OLLAMA_ENABLED` | `true` | 是否启用自动注册 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务器的端点（**注意**：不要包含 `/api` 后缀） |
| `OLLAMA_MODEL` | `qwen2.5:latest` | 默认模型名称 |
| `OLLAMA_TEMPERATURE` | `0.7` | 采样温度 |
| `OLLAMA_TOP_P` | `0.9` | 核采样参数 |
| `OLLAMA_MAX_TOKENS` | 未设置 | 可选的最大输出 token 数 |

### Qwen（阿里巴巴百炼）

| 变量 | 默认值 | 描述 |
| -------- | ------- | ----------- |
| `QWEN_ENABLED` | `true` | 是否启用自动注册 |
| `QWEN_API_KEY` | – | API 密钥（可回退到 `DASHSCOPE_API_KEY`） |
| `QWEN_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 端点 |
| `QWEN_MODEL` | `qwen-plus` | 默认模型名称 |
| `QWEN_TEMPERATURE` | `0.7` | 采样温度 |
| `QWEN_TOP_P` | `0.9` | 核采样参数 |
| `QWEN_MAX_TOKENS` | `2000` | 最大输出 token 数 |
| `QWEN_EMBEDDING_MODEL` | `text-embedding-v1` | 嵌入模型标识符 |

如果环境变量不适合，您也可以手动实例化设置类并将其传递给相应的客户端构造函数。

## 扩展管理器

要添加新的提供程序，请实现 `BaseLLMClient` 的子类并注册它：

```python
from infrastructure.llm import LLMManager
from my_project.llm.azure_client import AzureOpenAICLient

manager = LLMManager(auto_register=False)
manager.add_client("azure", AzureOpenAICLient(...), set_as_default=True)
```

通过代码添加的客户端可以与自动注册的提供程序共存。

## 故障排除

### Ollama 连接问题

如果您在使用 Ollama 时遇到 502 错误：

1. **检查 URL 配置**：确保 `OLLAMA_BASE_URL` 不包含 `/api` 后缀。客户端会自动附加 API 路径。
   - 正确：`OLLAMA_BASE_URL="http://localhost:11434"`
   - 错误：`OLLAMA_BASE_URL="http://localhost:11434/api"`

2. **Python 包兼容性**：ollama Python 包可能与较新的 Ollama 服务器版本存在兼容性问题。如果 Python 包失败，客户端会自动回退到 HTTP 请求。

3. **模型名称格式**：确保模型名称没有多余的空格：
   - 正确：`OLLAMA_MODEL="qwen3:4b"`
   - 错误：`OLLAMA_MODEL="qwen3:4b "`

4. **服务状态**：验证 Ollama 是否正在运行并可访问：
   ```bash
   ollama --version
   ollama ps
   ```
