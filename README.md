# EduPilot 智能学习助手

基于多智能体协作与 GraphRAG 知识图谱的现代化智能教育平台，融合苏格拉底式教学方法，提供个性化学习体验。

## 核心特性

### 多智能体协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ChatAgent (主对话引擎)                    │
│  QueryAnalyzer → DialogueRouter → 双模式回复生成            │
└─────────────────────────────────────────────────────────────┘
              │                                          │
    ┌─────────┼──────────┐                    ┌─────────┼──────────┐
    ▼         ▼          ▼                    ▼         ▼          ▼
┌─────────┐┌──────────┐┌─────────┐    ┌──────────┐┌─────────┐┌──────────┐
│Evaluation││Learning  ││User     │    │ Builtin  ││知识库   ││对话图谱  │
│  Agent  ││Planner   ││Profile  │    │  Tools   ││GraphRAG ││Dialogue │
│(学习评测)││(学习规划) ││(用户画像)│    │(RAG/推理)││检索     ││Graph    │
└─────────┘└──────────┘└─────────┘    └──────────┘└─────────┘└─────────┘
```

### 智能对话系统

- **双模式支持**：
  - **Direct 模式**：直接回答，结构化输出
  - **Socratic 模式**：苏格拉底式引导，层层提问启发思考

- **三阶段处理流程**：
  1. **意图分析** — 识别问题类型（事实性/概念性/程序性/分析性）
  2. **智能路由** — 选择响应策略（模式、RAG、工具）
  3. **回复生成** — 流式 LLM 调用 + SSE 推送

### GraphRAG 知识图谱

- **nano_graphrag** 驱动，支持三种检索模式
- **local**：社区局部检索，适合具体实体查询
- **global**：全局总结检索，适合宽泛主题
- **naive**：直接向量相似度

### 双图谱系统

| 图谱 | 来源 | 用途 |
|------|------|------|
| 知识库图谱 | GraphRAG 索引构建 | 语义知识检索 |
| 对话图谱 | 实时 LLM 抽取 | 会话结构化 + 用户长期记忆 |

### 事件流框架

- **SSE** 和 **WebSocket** 实时推送
- 完整执行步骤追踪（STEP_START / STEP_END / TOOL_START / TOOL_END）
- 思考过程可视化（THINKING 事件）

## 系统架构

```
edupilot/
├── api/                    # FastAPI REST + SSE + WebSocket
│   ├── routers/
│   │   ├── chat.py        # 对话 / 会话管理
│   │   ├── ws.py          # 流式响应 (SSE + WS)
│   │   ├── graph.py       # 知识库图谱 / GraphRAG
│   │   ├── profile.py     # 用户画像分析
│   │   ├── plan.py        # 学习计划生成
│   │   ├── evaluation.py  # 学习效果评测
│   │   └── statistics.py  # 系统监控统计
│   └── middleware/
│       └── statistics_middleware.py  # 自动记录 API 性能
├── agents/                 # 智能体模块
│   ├── base/              # BaseAgent / SingleTurnAgent / MultiTurnAgent
│   ├── chat/              # ChatAgent (意图分析 + 路由 + 双模式)
│   ├── evaluation/        # EvaluationAgent (学习评测)
│   ├── learning_planner/  # LearningPlannerAgent (学习规划)
│   ├── user_profile/      # UserProfileAgent (用户画像)
│   ├── dialogue_graph/    # DialogueGraphService (对话图谱抽取)
│   └── tools/             # RAG / Brainstorm / Reason / Summary / CodeExplain
├── services/              # 业务服务层
│   ├── llm/              # OpenAI 兼容客户端 + GraphRAG LLM 适配
│   ├── graph/            # KnowledgeGraphService / DialogueGraphService
│   └── storage/          # Session / Profile / UserGraph / Statistics (JSON)
├── core/                  # 核心协议
│   ├── protocol.py       # UnifiedContext / AgentMode / ToolDefinition
│   └── stream.py         # StreamBus / ResponseBuilder / EventType
└── config/
    └── settings.py        # Pydantic Settings (.env 配置)
```

## 技术栈

### 后端

- **框架**：FastAPI + Uvicorn + Pydantic
- **LLM**：OpenAI Compatible API（SiliconFlow / 百炼 / Local VLLM / Ollama）
- **GraphRAG**：nano-graphrag
- **向量**：nano-vectordb
- **图算法**：NetworkX + graspologic
- **流式**：sse-starlette + WebSocket

### 前端

- **框架**：Vue 3 + Composition API + Vite
- **UI 库**：Element Plus
- **图表**：ECharts
- **状态管理**：Pinia

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Conda (推荐)

### 1. 克隆项目

```bash
cd edupilot
```

### 2. 配置后端环境

```bash
# 创建 conda 环境
conda create -n edupilot python=3.10
conda activate edupilot

# 安装依赖
cd src
pip install -r ../requirements.txt

# 配置环境变量
cp .env.example .env
```

`.env` 配置示例：

```env
LLM_PROVIDER=siliconflow
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_EMBEDDING_MODEL=BAAI/bge-m3
LLM_EMBEDDING_DIM=1024
```

### 3. 启动后端服务

```bash
cd src
python -m edupilot
# 服务运行于 http://localhost:8000
```

### 4. 启动前端服务

```bash
cd web
npm install
npm run dev
# 服务运行于 http://localhost:5173
```

### 5. 访问应用

打开浏览器访问 `http://localhost:5173`

## API 接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat` | POST | 对话接口 |
| `/api/v1/chat/sessions/{id}/end` | POST | 结束会话 |
| `/api/v1/ws/chat/{client_id}` | GET | SSE 流式对话 |
| `/api/v1/graph/knowledge/{kb_id}` | GET | 知识库图谱 |
| `/api/v1/graph/knowledge/{kb_id}/query` | GET | GraphRAG 语义查询 |
| `/api/v1/graph/session/{session_id}` | GET | 会话图谱 |
| `/api/v1/graph/user/{user_id}/long_term` | GET | 用户长期图谱 |
| `/api/v1/profile/analyze` | POST | 分析用户画像 |
| `/api/v1/plan/generate` | POST | 生成学习计划 |
| `/api/v1/evaluation/run` | POST | 运行学习评测 |
| `/api/v1/statistics` | GET | 系统统计信息 |
| `/api/v1/health` | GET | 健康检查 |

## Agent 模块

| Agent | 功能 |
|-------|------|
| [ChatAgent](src/edupilot/agents/chat/README.md) | 核心对话交互，意图分析 + 智能路由 + 双模式回复 |
| [EvaluationAgent](src/edupilot/agents/evaluation/README.md) | 学习效果评测与反馈 |
| [LearningPlannerAgent](src/edupilot/agents/learning_planner/README.md) | 个性化学习计划生成 |
| [UserProfileAgent](src/edupilot/agents/user_profile/README.md) | 用户画像分析与学习特点挖掘 |
| [DialogueGraphService](src/edupilot/agents/dialogue_graph/README.md) | 对话图谱构建与实体关系抽取 |
| [Builtin Tools](src/edupilot/agents/tools/README.md) | 通用工具集：GraphRAG 检索、头脑风暴、推理等 |

## 数据目录

```
data/
├── sessions/                    # 会话数据 (JSON)
├── users/{user_id}/            # 用户数据
│   ├── profile.json           # 用户画像
│   ├── learning_plan.json     # 学习计划
│   └── long_term_graph.json   # 长期图谱
├── knowledge_bases/{kb_id}/   # GraphRAG 索引
├── metadata/{kb_id}/          # 建库原始文本
└── statistics/                # 系统监控数据
```

## License

MIT
