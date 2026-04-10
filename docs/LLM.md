# 统一 LLM 调用说明

## 设计

所有供应商在代码侧统一为 **OpenAI 兼容 HTTP 端点**，通过官方 `openai` 包的 `AsyncOpenAI` 访问：

- 对话：`chat.completions.create`
- 向量：`embeddings.create`

业务代码通过 `edupilot.services.llm.get_llm_client()` 获取 `UnifiedOpenAIClient`，GraphRAG 通过 `build_graphrag_functions` 注入 `best_model_func` 与 `embedding_func`。

## 环境变量

| 变量 | 含义 |
|------|------|
| LLM_PROVIDER | siliconflow、bailian、local_vllm、local_ollama |
| LLM_API_KEY | 密钥 |
| LLM_BASE_URL | 非百炼时自定义兼容端点根路径（含 /v1） |
| LLM_MODEL | 对话模型名 |
| EMBEDDING_MODEL | 嵌入模型名 |
| EMBEDDING_DIM | 与嵌入向量维度一致（如 bge-m3 常为 1024） |
| DASHSCOPE_API_KEY | 可选，百炼单独密钥 |

## 各形态说明

- **SiliconFlow**：默认 `https://api.siliconflow.cn/v1`，模型名与控制台一致。
- **阿里百炼**：兼容模式 `https://dashscope.aliyuncs.com/compatible-mode/v1`，模型名使用控制台 OpenAI 兼容名称。
- **本地 vLLM**：一般为 `http://127.0.0.1:8000/v1`，按部署修改端口。
- **Ollama OpenAI 兼容**：常见 `http://127.0.0.1:11434/v1`。

切换供应商时只需改 `LLM_PROVIDER` 与对应 `LLM_BASE_URL`、模型名，无需改业务智能体代码。
