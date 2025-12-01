# EduPilot 后端与API技术文档

> **文档版本**: v3.0  
> **最后更新**: 2025年1月  
> **技术栈**: FastAPI + LangGraph + LangChain + nano-graphrag

---

## 📋 目录

1. [系统架构](#系统架构)
2. [技术栈详解](#技术栈详解)
3. [核心模块设计](#核心模块设计)
4. [API接口设计](#api接口设计)
5. [工作流引擎](#工作流引擎)
6. [智能体系统](#智能体系统)
7. [基础设施层](#基础设施层)
8. [数据持久化](#数据持久化)
9. [性能优化](#性能优化)
10. [部署与运维](#部署与运维)

---

## 🏗️ 系统架构

### 整体架构

EduPilot 采用**分层架构设计**，从下到上分为：

```
┌─────────────────────────────────────────┐
│  接口层 (Interfaces)                     │
│  - API路由 (FastAPI)                     │
│  - Web前端 (Vue3)                        │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  核心层 (Core)                           │
│  - 工作流引擎 (LangGraph)                │
│  - 智能体系统 (6个Agent)                 │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  基础设施层 (Infrastructure)             │
│  - LLM客户端 (Ollama/Qwen)               │
│  - 图检索 (nano-graphrag)                │
│  - 配置管理                              │
│  - 持久化存储                            │
└─────────────────────────────────────────┘
```

### 模块划分

```
src/
├── core/                    # 核心业务逻辑
│   ├── agents/              # 6个智能体
│   │   ├── query_analyzer/  # 查询分析Agent
│   │   ├── planner/         # 规划Agent
│   │   ├── executor/        # 执行Agent
│   │   ├── knowledge_retriever/  # 知识检索Agent
│   │   ├── socratic_guide/ # 苏格拉底引导Agent
│   │   └── memory_manager/ # 记忆管理Agent
│   └── workflow/            # 工作流引擎
│       ├── learning.py      # 主工作流类
│       ├── nodes.py         # 节点定义
│       ├── routing.py       # 路由逻辑
│       └── state.py         # 状态管理
├── infrastructure/          # 基础设施
│   ├── llm/                 # LLM客户端
│   ├── nano_graphrag/       # 图检索增强生成
│   ├── config/              # 配置管理
│   ├── persistence/         # 持久化适配器
│   └── utils/               # 工具类
└── interfaces/              # 接口层
    ├── api/                 # FastAPI接口
    └── web/                 # Vue3前端
```

---

## 💻 技术栈详解

### 后端框架

#### 1. FastAPI
- **版本**: 0.104.0+
- **用途**: RESTful API框架
- **特性**:
  - 自动生成OpenAPI文档
  - 基于Pydantic的数据验证
  - 异步请求处理
  - 类型提示支持

#### 2. LangGraph
- **版本**: 0.2.0+
- **用途**: 工作流编排框架
- **特性**:
  - 状态图可视化
  - 条件路由
  - 状态持久化
  - 错误恢复

#### 3. LangChain
- **版本**: 0.3.0+
- **用途**: LLM应用开发框架
- **特性**:
  - 链式调用
  - 提示模板管理
  - 工具集成

### AI/ML技术

#### 1. nano-graphrag
- **用途**: 图检索增强生成
- **功能**:
  - 知识图谱构建
  - 实体关系提取
  - 语义检索
  - 向量存储

#### 2. LLM客户端
- **Ollama**: 本地LLM服务
- **Qwen API**: 阿里云通义千问API
- **统一接口**: 通过LLMManager管理

### 数据处理

#### 1. Pydantic
- **用途**: 数据验证和序列化
- **特性**:
  - 类型验证
  - 自动文档生成
  - JSON序列化

#### 2. dataclasses-json
- **用途**: 数据类序列化

### 存储

#### 1. MongoDB（可选）
- **用途**: 持久化存储
- **场景**: 生产环境

#### 2. JSON文件系统
- **用途**: 开发环境存储
- **存储内容**:
  - 会话记忆
  - 用户画像
  - 学习记录

---

## 🔧 核心模块设计

### 1. 工作流引擎 (core/workflow)

#### LangGraphLearningWorkflow

**核心类**: `LangGraphLearningWorkflow`

**职责**:
- 工作流编排
- 状态管理
- 节点执行
- 错误处理

**工作流图结构**:
```
START
  ↓
query_analyzer (查询分析)
  ↓
planner (Orchestrator - 任务编排)
  ↓
[条件路由 - Fan-out]
  ├─ knowledge_manager (知识检索)
  ├─ tool_specialist (工具调用)
  ├─ curriculum_designer (课程设计)
  ├─ socratic_guide (苏格拉底引导)
  ├─ memory_manager (记忆管理)
  └─ draft_writer (直接撰写)
  ↓
[Fan-in - 所有工具节点汇聚]
  ↓
draft_writer (内容撰写)
  ↓
reviewer (质量审核)
  ↓
[条件路由]
  ├─ quiz_master (生成测试题) → conclusion
  ├─ draft_writer (需要修改) → reviewer (循环)
  └─ conclusion (直接结束)
  ↓
END
```

**关键方法**:
```python
async def process_query(
    user_query: str,
    user_context: Dict[str, Any],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """处理用户查询"""
    
async def continue_session(
    session_id: str,
    user_id: str,
    user_response: str
) -> Dict[str, Any]:
    """继续会话（回答苏格拉底问题）"""
```

**状态管理**:
- 使用 `LearningWorkflowState` 统一管理状态
- 支持状态持久化和恢复
- 状态转换通过条件路由控制

### 2. 智能体系统 (core/agents)

#### 智能体基类

**BaseAgent** (`src/infrastructure/utils/data_models.py`)

```python
class BaseAgent:
    """智能体基类"""
    name: str
    description: str
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行智能体逻辑"""
        
    def can_execute(self, state: AgentState) -> bool:
        """判断是否可以执行"""
```

#### 10个核心智能体

##### 1. QueryAnalyzerAgent

**职责**: 查询分析和意图识别

**核心功能**:
- **启发式意图识别**: 多种意图类型匹配（概念解释、知识检索、学习指导等）
- **LLM精修**: 置信度不足时触发LLM精修
- **检索决策**: 智能判断是否需要知识检索
- **概念提取**: 正则模式匹配提取核心概念
- **查询优化**: 生成多策略查询

**输出结构**:
```python
{
    "intent": "concept_explanation",
    "confidence": 0.85,
    "need_retrieval": True,
    "core_concepts": ["大化改新", "律令制"],
    "optimized_queries": [...]
}
```

##### 2. OrchestratorAgent (原Planner)

**职责**: 任务编排与动态调度

**核心功能**:
- **情况分析**: 分析当前上下文和资源需求
- **计划类型确定**: 根据意图确定计划类型
- **Agent调度决策**: 决定下一步激活哪些Worker Agent
- **动态路由**: 生成调度指令（next_workers）用于LangGraph路由

**输出结构**:
```python
{
    "type": "CONCEPT_BUILDING",
    "next_workers": ["knowledge_manager", "draft_writer"],
    "reasoning": "...",
    "analysis": {...}
}
```

##### 3. DraftWriterAgent

**职责**: 内容撰稿，生成和修改教学内容草稿

**核心功能**:
- **初稿生成**: 整合RAG检索结果、工具输出生成初稿
- **草稿修改**: 根据Reviewer的Critique修改草稿
- **内容整合**: 整合多源信息生成连贯的教学内容

##### 4. ReviewerAgent

**职责**: 质量审核，确保内容准确性、教学性和结构清晰

**核心功能**:
- **质量检查**: 检查幻觉、语气、难度匹配度
- **审核决策**: 决定是否重写或通过
- **修改意见**: 提供详细的修改建议

##### 5. CurriculumDesignerAgent

**职责**: 课程设计，生成系统化的学习路径

**核心功能**:
- **学习路径生成**: 当用户想要系统学习时，生成知识树结构
- **思维导图输出**: 输出JSON格式的MindMap数据
- **结构化课程**: 设计层次化的课程结构

##### 6. QuizMasterAgent

**职责**: 测评与出题，评估用户掌握度

**核心功能**:
- **题目生成**: 根据讲解内容生成测试题（单选题等）
- **难度控制**: 根据用户水平调整题目难度
- **评估反馈**: 评估用户回答并提供反馈

##### 7. ToolSpecialistAgent

**职责**: 工具专家，执行外部工具调用

**核心功能**:
- **计算器**: 执行数学计算和逻辑运算
- **网络搜索**: 获取实时信息和新闻（占位实现）
- **代码解释器**: 安全的代码执行环境

##### 8. KnowledgeManagerAgent (原KnowledgeRetriever)

**职责**: 知识检索和图检索

**核心功能**:
- **并发检索**: 多概念并行检索
- **多策略融合**: 支持多种检索策略
- **相关性评分**: 智能评分算法
- **图检索**: 基于nano-graphrag的图结构检索

**检索流程**:
```
概念提取 → 并发检索 → 相关性评分 → 结果融合 → 返回
```

##### 9. SocraticGuideAgent

**职责**: 苏格拉底式引导

**核心功能**:
- **8种问题类型**: 澄清、假设、含义、证据、视角、因果、类比、综合
- **5级理解水平评估**: 无知→模糊→部分→清晰→精通
- **问题生成策略**: 根据理解水平选择问题类型
- **质量验证机制**: 借鉴MARS的Critic机制，确保问题符合苏格拉底风格
- **对话阶段管理**: 4种对话阶段流转

**问题生成逻辑**:
```python
if understanding_level == "ignorant":
    question_type = "clarifying"  # 澄清问题
elif understanding_level == "vague":
    question_type = "hypothesis"   # 假设问题
# ...
```

##### 10. MemoryManagerAgent

**职责**: 记忆管理和用户画像

**核心功能**:
- **用户画像构建**: 基于三元组知识图谱构建用户画像
- **学习记录分析**: 情感分析和学习模式识别
- **会话记忆持久化**: 支持会话状态持久化和恢复
- **对话历史管理**: 对话历史合并，避免重复

**子模块**:
- `analyzers/`: 情感分析、交互分析、知识缺口检测、学习模式检测
- `extractors/`: 三元组提取、画像洞察生成
- `managers/`: 画像管理、会话管理
- `storage.py`: 存储管理

---

## 🌐 API接口设计

### API架构

**基础路径**: `/api/agent/v1`

**路由结构**:
```
/api/agent/v1/
├── workflow/              # 工作流接口（主流程）
│   ├── session/start      # 启动会话（同步）
│   ├── session/start/stream  # 启动会话（流式响应 SSE）
│   ├── session/continue   # 继续会话
│   └── session/{id}      # 会话信息
├── query-analyzer/        # 查询分析接口
├── orchestrator/          # 编排器接口（原planner）
├── draft-writer/          # 内容撰写接口
├── reviewer/              # 质量审核接口
├── curriculum-designer/   # 课程设计接口
├── quiz-master/           # 测验生成接口
├── tool-specialist/       # 工具调用接口
├── knowledge-manager/     # 知识管理接口（原knowledge-retriever）
├── socratic-guide/        # 苏格拉底引导接口
├── memory-manager/        # 记忆管理接口
├── health                 # 健康检查
└── stats                  # 统计信息
```

### FastAPI应用配置

**主文件**: `src/interfaces/api/main.py`

**应用创建**:
```python
app = FastAPI(
    title="EduPilot Agent API",
    description="智能教育助手API",
    version="3.0.0",
    docs_url="/api/agent/v1/docs",
    redoc_url="/api/agent/v1/redoc",
)
```

**中间件**:
- **CORS**: 跨域资源共享
- **请求日志**: 记录所有请求
- **性能监控**: 记录响应时间
- **错误处理**: 全局异常捕获

### 核心API端点

#### 1. 工作流接口 (`routers/workflow.py`)

##### POST `/workflow/session/start`

**功能**: 启动新的学习会话

**请求体**:
```json
{
    "user_id": "user_001",
    "query": "什么是大化改新？",
    "workflow_config": {
        "enable_socratic": true,
        "enable_learning": true,
        "feature_flags": {
            "enable_knowledge_retriever": true,
            "enable_memory_manager": true,
            "enable_socratic_guide": true
        }
    }
}
```

**响应体**:
```json
{
    "success": true,
    "session_id": "uuid-string",
    "response": "系统响应文本",
    "socratic_dialogue": {
        "is_socratic_mode": true,
        "question": "苏格拉底问题",
        "question_type": "clarifying",
        "understanding_level": "partial"
    },
    "workflow_state": {
        "complete": false,
        "waiting_for_user": true,
        "conversation_stage": "socratic_guidance"
    }
}
```

##### POST `/workflow/session/continue`

**功能**: 继续会话（回答苏格拉底问题）

**请求体**:
```json
{
    "session_id": "uuid-string",
    "user_id": "user_001",
    "user_response": "我认为大化改新是重要的政治改革"
}
```

##### POST `/workflow/session/start/stream`

**功能**: 启动学习会话（流式响应）

**特性**: 使用Server-Sent Events (SSE)实时推送工作流执行状态

**响应格式**: `text/event-stream`

**事件类型**:
- `workflow_start`: 工作流开始
- `stage`: 执行阶段更新（query_analysis, planning, execution）
- `workflow_complete`: 工作流完成
- `error`: 错误信息

**示例**:
```javascript
const eventSource = new EventSource('/api/agent/v1/workflow/session/start/stream', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user_001',
    query: '什么是大化改新？'
  })
})

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('收到事件:', data.type, data.message)
}
```

#### 2. 独立Agent接口

每个Agent都有独立的API端点，支持单独调用（调试/测试用）：

- `POST /query-analyzer/analyze` - 查询分析
- `POST /orchestrator/orchestrate` - 任务编排
- `POST /draft-writer/write` - 内容撰写
- `POST /reviewer/review` - 质量审核
- `POST /curriculum-designer/design` - 课程设计
- `POST /quiz-master/generate` - 生成测试题
- `POST /tool-specialist/execute` - 工具调用
- `POST /knowledge-manager/retrieve` - 知识检索
- `POST /socratic-guide/generate-question` - 生成苏格拉底问题
- `POST /memory-manager/update-profile` - 更新用户画像

### 数据模型

**模型定义**: `src/interfaces/api/models.py`

**核心模型**:
- `BaseResponse`: 基础响应模型
- `LearningSessionRequest`: 会话启动请求
- `LearningSessionResponse`: 会话响应
- `QueryAnalysisRequest`: 查询分析请求
- `SocraticDialogueInfo`: 苏格拉底对话信息

**Pydantic验证**:
- 自动类型验证
- 字段约束检查
- 自动文档生成

### 依赖注入

**依赖管理**: `src/interfaces/api/dependencies.py`

**核心依赖**:
```python
def get_learning_workflow_instance() -> LearningWorkflow:
    """获取工作流实例（单例）"""
    
def validate_user_id(user_id: str) -> str:
    """验证用户ID"""
    
def validate_query(query: str) -> str:
    """验证查询文本"""
```

---

## ⚙️ 基础设施层

### 1. LLM客户端管理

**管理器**: `src/infrastructure/llm/manager.py`

**LLMManager类**:
```python
class LLMManager:
    """LLM客户端管理器"""
    
    def add_client(self, name: str, client: BaseLLMClient):
        """注册LLM客户端"""
        
    def get_client(self, name: Optional[str] = None) -> BaseLLMClient:
        """获取LLM客户端"""
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
```

**支持的客户端**:
- `OllamaLLMClient`: 本地Ollama服务
- `QwenLLMClient`: 阿里云通义千问API

**配置**:
- 从环境变量自动加载
- 支持多个客户端切换
- 统一接口调用

### 2. 图检索增强生成

**模块**: `src/infrastructure/nano_graphrag/`

**核心功能**:
- **知识图谱构建**: 从文本提取实体和关系
- **向量存储**: 使用HNSWlib或NanoVectorDB
- **图存储**: 支持NetworkX和Neo4j
- **语义检索**: 基于嵌入向量的相似度搜索

**使用流程**:
```python
# 1. 构建知识图谱
graphrag = GraphRAG(knowledge_base_path)
graphrag.build()

# 2. 检索相关实体
entities = graphrag.search(query, top_k=5)

# 3. 获取实体关系
relations = graphrag.get_relations(entities)
```

### 3. 配置管理

**配置模块**: `src/infrastructure/config/settings.py`

**配置来源**:
- 环境变量 (`.env`文件)
- 默认配置
- 运行时配置

**配置项**:
- LLM配置 (Ollama/Qwen)
- 工作流配置
- 存储配置
- 日志配置

### 4. 持久化存储

**适配器模式**: `src/infrastructure/persistence/`

**存储适配器**:
- `FileStorageAdapter`: JSON文件存储
- `SQLiteAdapter`: SQLite数据库
- `MongoDBAdapter`: MongoDB（可选）

**仓储模式**:
- `SessionRepository`: 会话存储
- `UserProfileRepository`: 用户画像存储
- `LearningRecordRepository`: 学习记录存储

---

## 💾 数据持久化

### 存储结构

**数据目录**: `data/`

```
data/
├── memory_data/
│   ├── session_memory/      # 会话记忆
│   │   └── session_{id}.json
│   ├── user_profiles/        # 用户画像
│   │   └── profile_{user_id}.json
│   └── learning_records/     # 学习记录
│       └── record_{id}.json
├── checkpoints/              # 状态快照（新增）
│   ├── {session_id}_{checkpoint_id}.json
│   └── {session_id}_index.json
└── retrieval_cache/          # 检索缓存
```

### Checkpoint机制

**模块**: `src/core/workflow/checkpoint.py`

**功能**:
- **状态快照**: 保存工作流执行过程中的关键状态
- **分支管理**: 支持从任意checkpoint创建分支，实现"时光回溯"
- **状态恢复**: 支持从checkpoint恢复会话状态

**使用场景**:
- 用户想回到"苏格拉底提问"之前的某个知识点
- 实验不同的学习路径
- 调试和错误恢复

**API**:
```python
from src.core.workflow.checkpoint import get_checkpoint_manager

checkpoint_manager = get_checkpoint_manager()

# 保存checkpoint
checkpoint_id = checkpoint_manager.save_checkpoint(
    session_id="session_001",
    state=workflow_state,
    metadata={"stage": "after_planning"}
)

# 加载checkpoint
checkpoint_data = checkpoint_manager.load_checkpoint(
    session_id="session_001",
    checkpoint_id=checkpoint_id
)

# 创建分支
branch_id = checkpoint_manager.create_branch(
    session_id="session_001",
    parent_checkpoint_id=checkpoint_id,
    branch_name="alternative_path"
)

# 列出所有checkpoint
checkpoints = checkpoint_manager.list_checkpoints("session_001")
```

### 会话记忆结构

```json
{
    "session_id": "uuid",
    "user_id": "user_001",
    "start_time": "2025-01-01T00:00:00",
    "dialogue_history": [
        {
            "round": 1,
            "timestamp": "2025-01-01T00:00:00",
            "question": {
                "question": "问题文本",
                "type": "clarifying"
            },
            "response": "用户回答"
        }
    ],
    "socratic_questions": [...],
    "user_responses": [...],
    "understanding_level": "partial",
    "conversation_stage": "socratic_guidance"
}
```

### 用户画像结构

```json
{
    "user_id": "user_001",
    "knowledge_graph": {
        "entities": [...],
        "relations": [...]
    },
    "learning_patterns": {
        "preferred_style": "visual",
        "interaction_frequency": "high"
    },
    "emotion_analysis": {
        "dominant_emotion": "curious",
        "emotion_history": [...]
    }
}
```

---

## 🚀 性能优化

### 1. 流式响应（SSE）

**实现**: `src/interfaces/api/routers/workflow_streaming.py`

**优势**:
- 实时推送工作流执行状态，提升用户体验
- 减少用户等待焦虑（显示"正在分析..."等中间状态）
- 支持长时间运行的任务

**使用场景**:
- 复杂查询处理（>3秒）
- 知识图谱构建
- 多轮苏格拉底对话

### 2. 缓存机制

**响应缓存**: `src/interfaces/api/middleware.py`

```python
response_cache = ResponseCache(ttl=60)  # 60秒TTL

@response_cache.cached
async def get_concept(concept_name: str):
    # 缓存响应
    pass
```

### 3. 并发控制

**工作流限流**: `src/interfaces/api/utils.py`

```python
workflow_limiter = WorkflowLimiter(max_concurrent=10)

async with workflow_limiter.semaphore:
    result = await workflow.run(...)
```

### 4. 异步处理

- 所有Agent使用`async/await`
- 并发知识检索
- 异步LLM调用

### 5. 状态缓存与Checkpoint

- AgentState缓存
- 会话状态缓存
- Checkpoint快照（支持快速恢复）
- 减少重复计算

---

## 🔒 安全与错误处理

### 1. 请求验证

- Pydantic自动验证
- 输入清理
- SQL注入防护

### 2. 错误处理

**全局异常处理**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )
```

### 3. 日志记录

- 请求日志
- 错误日志
- 性能日志

---

## 📦 部署与运维

### 启动方式

```bash
# 方式1: 直接运行
python -m src.interfaces.api.main

# 方式2: 使用uvicorn
uvicorn src.interfaces.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
```

### 环境变量

**配置文件**: `env_example.txt`

**关键配置**:
```bash
# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest

# Qwen API配置
QWEN_API_KEY=your_api_key
QWEN_MODEL=qwen-plus

# 系统配置
LOG_LEVEL=INFO
WORKFLOW_TIMEOUT=300
```

### 健康检查

**端点**: `GET /api/agent/v1/health`

**响应**:
```json
{
    "success": true,
    "status": "healthy",
    "version": "3.0.0",
    "agents_status": {
        "query_analyzer": "healthy",
        "planner": "healthy"
    },
    "uptime_seconds": 3600
}
```

### 监控指标

**端点**: `GET /api/agent/v1/stats`

**统计信息**:
- 总请求数
- 成功/失败数
- 平均响应时间
- Agent调用统计

---

## 📚 相关文档

- **API使用示例**: `src/interfaces/api/API_使用示例.md`
- **快速开始**: `src/interfaces/api/QUICK_START.md`
- **工作流详解**: `README.md` (项目主文档)

---

**文档维护**: EduPilot开发团队  
**最后更新**: 2025年1月

