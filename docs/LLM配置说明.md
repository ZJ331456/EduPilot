# LLM配置说明

## 双模型架构

本系统采用双模型架构：

1. **Agent对话生成**：使用Qwen API进行智能体对话
2. **嵌入检索**：使用本地Ollama进行知识库检索

## 配置概览

```yaml
llm:
  default_client: "qwen"  # 默认使用Qwen进行对话
  
  # Agent对话生成 - Qwen API
  qwen:
    enabled: true
    api_key: "sk-0680b9634a644828a3a9622143c0c079"
    default_model: "qwen-plus"
    temperature: 0.7
    max_tokens: 2000
  
  # 嵌入检索 - 本地Ollama
  ollama:
    enabled: true
    embedding_model: "bge-m3:latest"
    temperature: 0.3
    max_tokens: 1000
```

## 验证配置

```bash
python scripts/validate_dual_model_config.py
python scripts/test_llm_config.py
```

## 常见问题

1. **Qwen连接失败**：检查API密钥和网络
2. **Ollama连接失败**：确保`ollama serve`正在运行
3. **嵌入模型失败**：运行`ollama pull bge-m3:latest` 