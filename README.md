# EduPilot

在 `DeepTutor` 的「服务分层加按模块智能体」思路下重构的教育场景项目：统一 LLM 接入、本地 GraphRAG（nano_graphrag）、对话与知识两套图谱、会话与用户级存储、画像与学习计划、学习评测。

## 目录说明

- `src/edupilot`：FastAPI、智能体、业务服务。
- `src/nano_graphrag`：自 EduAgent 迁入的图谱 RAG 实现。
- `web`：Vue 前端（对话与图谱页已对接新后端 `/api/v1`）。
- `data`：运行时数据统一目录，说明见 `docs/DATA.md`。
- `config`：预留全局 YAML（当前以环境变量为主）。

## 环境

1. 使用 Conda 环境 `studyagent`（或自建 Python 3.10 以上环境）。
2. 复制 `.env.example` 为 `.env`，填写 `LLM_API_KEY` 等。**切勿将真实密钥提交到版本库。**
3. 安装依赖：

```bash
cd edupilot
pip install -r requirements.txt
```

4. 将 `src` 加入 `PYTHONPATH` 并启动后端：

```bash
set PYTHONPATH=src
python -m edupilot
```

默认监听 `http://127.0.0.1:8000`，接口前缀 `http://127.0.0.1:8000/api/v1`。

5. 前端：

```bash
cd web
npm install
npm run dev
```

浏览器访问 `http://localhost:5173`，对话页会调用 `POST /api/v1/chat`，图谱页为 `/graph`。

## LLM 接入形态

通过环境变量 `LLM_PROVIDER` 选择：

- `siliconflow`：默认 `LLM_BASE_URL=https://api.siliconflow.cn/v1`
- `bailian`：兼容模式 `https://dashscope.aliyuncs.com/compatible-mode/v1`，可用 `DASHSCOPE_API_KEY`
- `local_vllm`：OpenAI 兼容本地服务，自定义 `LLM_BASE_URL`
- `local_ollama`：常见为 `http://127.0.0.1:11434/v1`

对话与嵌入均走同一 `AsyncOpenAI` 兼容客户端，便于切换供应商。

## 与 EduAgent 的关系

本仓库为独立项目目录 `edupilot`，不强制替换原 `EduAgent`；你可并行保留旧工程，逐步迁移业务。
