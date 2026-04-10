# chat_direct 智能体

## 作用

面向「直接答疑」场景：用户提问后，模型以清晰中文给出解释与步骤，不强制采用苏格拉底式追问。

## 输入输出

- 输入由 API 层拼装为 `context` 字符串（近期对话与用户当前句）。
- 输出为模型自然语言回复。

## 提示词位置

`prompts/zh/prompts.yaml`，仅包含 `system` 与 `user` 模板，可按学科微调语气与篇幅。

## 依赖

统一 LLM 客户端 `edupilot.services.llm.get_llm_client`，底层由 `.env` 中的 `LLM_PROVIDER` 决定 SiliconFlow、百炼或本地兼容端点。
