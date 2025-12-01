# EduPilot 智能学习助手系统

> **项目版本**: v3.0  
> **项目周期**: 2024年 - 2025年  
> **开发角色**: 全栈开发工程师 / 核心架构设计

---

## 📋 项目概述

**EduPilot** 是一个基于多智能体协作架构的智能教育系统，采用苏格拉底式教学法，通过问题引导而非直接给出答案的方式，帮助学习者深入理解知识。系统融合了图检索增强生成（GraphRAG）、多智能体工作流编排、个性化学习分析等前沿技术，为学习者提供个性化的交互式学习体验。

### 核心特性

- **🎯 多智能体协作架构**: 10个专业化Agent协同工作，基于LangGraph工作流编排
- **🧠 苏格拉底式教学**: 8种问题类型，5级理解水平评估，MARS优化质量验证机制
- **📚 智能知识检索**: 基于nano-graphrag构建60+概念知识图谱，并发检索优化
- **👤 个性化学习**: 用户画像系统，情感分析和学习模式识别
- **💬 多轮对话管理**: 会话状态持久化，支持API重启后状态恢复
- **✍️ 内容生成与审核**: DraftWriter生成内容，Reviewer质量审核，QuizMaster生成测试题
- **🎨 现代化UI**: Vue3 + 玻璃态设计，响应式布局，GPU加速动画

---

## 🏗️ 系统架构

### 架构演进

**v3.0 新架构**（当前版本）：
```
用户查询
    ↓
┌─────────────────────────────────────┐
│ QueryAnalyzer (查询分析)             │
│ - 意图识别                          │
│ - 检索决策                          │
│ - 核心概念提取                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Orchestrator (任务编排)              │
│ - 分析上下文和资源需求               │
│ - 决定需要调用的Worker Agents        │
│ - 生成调度指令 (next_workers)        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ [条件路由 - Fan-out]                │
│ ├─ KnowledgeManager (知识检索)      │
│ ├─ ToolSpecialist (工具调用)        │
│ ├─ CurriculumDesigner (课程设计)    │
│ ├─ SocraticGuide (苏格拉底引导)      │
│ └─ MemoryManager (记忆管理)         │
└─────────────────────────────────────┘
    ↓ [Fan-in]
┌─────────────────────────────────────┐
│ DraftWriter (内容撰写)               │
│ - 整合多源信息生成内容               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Reviewer (质量审核)                  │
│ - 检查内容质量                       │
│ - 决定是否通过或修改                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ QuizMaster (生成测试题)              │
│ - 根据内容生成测试题                 │
└─────────────────────────────────────┘
```

**架构优势**：
- ✅ 基于LangGraph的状态图工作流，清晰的可视化和调试能力
- ✅ 10个专业化Agent，职责明确，高度解耦
- ✅ 动态路由机制，根据意图智能调度Agent
- ✅ Fan-out/Fan-in模式，支持并行执行和结果汇聚
- ✅ 内容生成与审核循环，确保输出质量

---

## 💻 技术栈

### 后端技术

- **框架**: FastAPI、LangGraph（工作流编排）、asyncio（异步编程）
- **AI/ML**: LangChain、Ollama/Qwen API（LLM调用）、nano-graphrag（图检索增强生成）
- **数据处理**: Pydantic（数据验证）、dataclasses-json（序列化）
- **存储**: MongoDB、JSON文件系统（会话记忆、学习记录）

### 前端技术

- **框架**: Vue 3（Composition API）、Vue Router、Pinia（状态管理）
- **UI组件**: Element Plus
- **样式**: CSS Variables、CSS Animations、Backdrop Filter（玻璃态效果）
- **构建工具**: Vite

### 核心技术亮点

- **LangGraph工作流**: 基于状态图的工作流编排，支持可视化调试
- **动态路由机制**: Orchestrator根据意图智能调度，Fan-out/Fan-in模式
- **内容生成与审核循环**: DraftWriter生成内容，Reviewer审核，确保质量
- **图检索增强**: 基于GraphRAG的知识图谱构建和语义检索
- **状态管理**: 统一的LearningWorkflowState，支持持久化和恢复

---

## 🔧 核心组件详解

### 10个核心智能体

#### 1. QueryAnalyzerAgent
**职责**: 查询分析和意图识别  
**核心功能**: 意图识别、检索决策、概念提取、查询优化

#### 2. OrchestratorAgent (原Planner)
**职责**: 任务编排与动态调度  
**核心功能**: 分析上下文、决定Agent调度、生成next_workers指令

#### 3. DraftWriterAgent
**职责**: 内容撰稿  
**核心功能**: 整合多源信息生成初稿、根据Reviewer意见修改草稿

#### 4. ReviewerAgent
**职责**: 质量审核  
**核心功能**: 检查内容质量、决定是否通过、提供修改意见

#### 5. CurriculumDesignerAgent
**职责**: 课程设计  
**核心功能**: 生成系统化学习路径、输出思维导图结构

#### 6. QuizMasterAgent
**职责**: 测评与出题  
**核心功能**: 生成测试题、评估用户掌握度、提供反馈

#### 7. ToolSpecialistAgent
**职责**: 工具专家  
**核心功能**: 执行数学计算、网络搜索、代码解释

#### 8. KnowledgeManagerAgent (原KnowledgeRetriever)
**职责**: 知识检索和图检索  
**核心功能**: 并发检索、多策略融合、相关性评分、图结构检索

#### 9. SocraticGuideAgent
**职责**: 苏格拉底式引导  
**核心功能**: 8种问题类型、5级理解水平评估、MARS质量验证机制

#### 10. MemoryManagerAgent
**职责**: 记忆管理和用户画像  
**核心功能**: 用户画像构建、学习记录分析、会话记忆持久化

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- MongoDB（可选，用于持久化）

### 后端启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp env_example.txt .env
# 编辑 .env 文件，填入 OLLAMA_BASE_URL、QWEN_API_KEY 等

# 3. 启动API服务
python -m src.interfaces.api.main
# 或使用 uvicorn
uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 访问API文档
# http://localhost:8000/api/agent/v1/docs
```

### 前端启动

```bash
# 1. 进入前端目录
cd src/interfaces/web/edupliot-vue

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 访问应用
# http://localhost:5173
```

### API使用示例

```python
import requests

# 启动新会话
response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/start",
    json={
        "user_id": "user_001",
        "query": "什么是大化改新？",
        "workflow_config": {
            "enable_socratic": True,
            "enable_learning": True,
            "feature_flags": {
                "enable_knowledge_retriever": True,
                "enable_memory_manager": True,
                "enable_socratic_guide": True
            }
        }
    }
)

result = response.json()
print(f"会话ID: {result['session_id']}")
print(f"响应: {result['response']}")

# 继续会话（回答苏格拉底问题）
response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/continue",
    json={
        "session_id": result['session_id'],
        "user_id": "user_001",
        "user_response": "我认为大化改新是日本古代的重要政治改革"
    }
)
```

---

## 📊 项目成果

### 技术指标

- **代码规模**: 核心代码6700+行，前端代码5000+行
- **知识图谱**: 60+概念知识库，覆盖历史、文化等领域
- **性能提升**: 架构优化后响应时间减少40%（简单查询从6秒降至3.5秒）
- **测试覆盖**: 12种测试场景，100%通过率

### 架构优化效果

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 工作流步骤 | 6步固定流程 | 3步核心流程 | -50% |
| 代码行数 | 2879行 | 2629行 | -8.7% |
| 响应时间（简单查询） | ~6秒 | ~3.5秒 | -42% |
| 响应时间（复杂查询） | ~10秒 | ~9秒 | -10% |
| Agent调用次数（直接回答） | 6个 | 3步+1个 | -50% |

### 获奖情况

- 🏆 **省级人工智能创新大赛一等奖**

---

## 🎨 前端UI设计

### 设计理念

- **主题定位**: 科技感 + 学术感 + 未来感
- **配色方案**: 深色主题，蓝紫渐变为主色调
- **设计原则**: 现代、专业、高级、符合AI教育系统定位

### 核心特性

- **玻璃态设计（Glassmorphism）**: 磨砂玻璃效果，半透明背景
- **动态背景**: 3个渐变光球漂浮动画
- **流畅动画**: 页面切换、元素进入、悬浮效果
- **响应式布局**: 完美适配移动端、平板、桌面
- **GPU加速**: 使用transform和opacity触发GPU加速

### 主要页面

1. **首页（HomePage）**: Hero区域、功能卡片、工作流程可视化、技术栈展示
2. **对话页面（ChatView）**: 玻璃态消息容器、打字动画、侧边栏
3. **个人中心（ProfileView）**: 用户画像、学习记录、统计分析
4. **知识库（KnowledgeView）**: 知识图谱可视化、概念检索
5. **性能监控（PerformanceView）**: 系统统计、性能分析

---

## 📁 项目结构

```
EduPilot/
├── src/
│   ├── core/                    # 核心模块
│   │   ├── agents/              # 10个核心Agent
│   │   │   ├── query_analyzer/  # 查询分析Agent
│   │   │   ├── orchestrator/    # 编排器Agent（原planner）
│   │   │   ├── draft_writer/    # 内容撰写Agent
│   │   │   ├── reviewer/        # 质量审核Agent
│   │   │   ├── curriculum_designer/  # 课程设计Agent
│   │   │   ├── quiz_master/     # 测验生成Agent
│   │   │   ├── tool_specialist/ # 工具专家Agent
│   │   │   ├── knowledge_manager/  # 知识管理Agent（原knowledge_retriever）
│   │   │   ├── socratic_guide/ # 苏格拉底引导Agent
│   │   │   └── memory_manager/ # 记忆管理Agent
│   │   └── workflow/            # 工作流系统（LangGraph）
│   │       ├── learning.py      # 学习工作流主类
│   │       ├── nodes.py         # 节点定义
│   │       ├── routing.py       # 路由逻辑
│   │       └── state.py         # 状态管理
│   ├── infrastructure/          # 基础设施
│   │   ├── llm/                 # LLM客户端（Ollama/Qwen）
│   │   ├── nano_graphrag/       # 图检索增强生成
│   │   ├── config/              # 配置管理
│   │   └── persistence/         # 持久化存储
│   └── interfaces/              # 接口层
│       ├── api/                 # FastAPI接口
│       └── web/                 # Vue3前端
│           └── edupliot-vue/
├── concept_knowledge_bases/     # 知识图谱数据（60+概念）
├── data/                        # 运行时数据
│   ├── memory_data/             # 会话记忆、用户画像
│   └── retrieval_cache/         # 检索缓存
├── docs/                        # 文档
├── integration_tests/            # 集成测试脚本（可执行）
│   ├── run_learning_workflow_test.py  # 完整测试套件
│   ├── test_learning_workflow.py      # 交互式测试
│   └── test_langgraph_workflow.py     # LangGraph测试
├── src/tests/                   # 单元测试（pytest）
├── test_result/                 # 测试结果和日志
└── requirements.txt             # Python依赖
```

---

## 🔬 核心算法

### 1. 检索决策算法

```python
retrieval_score = intent_confidence * 0.6 + query_complexity * 0.3
need_retrieval = retrieval_score > threshold
```

### 2. 理解水平评估

5级评估体系：
- **无知（Ignorant）**: 无相关回答或完全错误
- **模糊（Vague）**: 有概念但表达不清
- **部分（Partial）**: 部分正确但不完整
- **清晰（Clear）**: 基本正确且表达清晰
- **精通（Proficient）**: 深入理解且能扩展

评估依据：
- 用户响应长度
- 关键词匹配度
- 上下文分析
- 概念关联度

### 3. 苏格拉底问题生成策略

根据理解水平和对话阶段选择问题类型：

| 理解水平 | 推荐问题类型 | 目的 |
|---------|------------|------|
| 无知 | 澄清、证据 | 引导基础理解 |
| 模糊 | 假设、含义 | 深化概念 |
| 部分 | 视角、因果 | 扩展思维 |
| 清晰 | 类比、综合 | 应用迁移 |
| 精通 | 综合、视角 | 批判性思维 |

---

## 🧪 测试

### 测试场景

系统包含12种测试场景：

1. 基础概念查询
2. 详细概念解释
3. 知识检索类查询
4. 比较分析查询
5. 历史事件查询
6. 学习指导类查询
7. 多轮对话测试（概念深入）
8. 多轮对话测试（苏格拉底式引导）
9. 复杂综合查询
10. 文化历史查询
11. 简短直接查询
12. 关联概念查询

### 运行测试

```bash
# 运行完整集成测试套件
python integration_tests/run_learning_workflow_test.py

# 运行交互式集成测试
python integration_tests/test_learning_workflow.py

# 运行LangGraph工作流测试
python integration_tests/test_langgraph_workflow.py

# 运行单元测试（pytest）
pytest src/tests/
```

---

## 📈 性能优化

### 架构优化

- **动态Agent调用**: 按需执行，减少不必要的Agent调用
- **并发检索**: 多概念并行检索，提升效率
- **状态缓存**: 统一的AgentState缓存机制
- **错误恢复**: 完善的错误处理和恢复机制

### 前端优化

- **GPU加速动画**: 使用transform和opacity触发GPU加速
- **虚拟滚动**: 长列表虚拟滚动（如需要）
- **代码分割**: 路由懒加载，减少初始加载大小
- **请求优化**: 防抖、节流、缓存机制

---

## 🔮 未来规划

### 短期（1-2个月）

- [ ] 完善CI/CD流程
- [ ] Docker容器化部署
- [ ] 性能监控面板
- [ ] 单元测试覆盖率提升

### 中期（3-6个月）

- [ ] 多模态支持（图片、音频）
- [ ] 自适应难度调整
- [ ] 知识图谱可视化
- [ ] 移动端APP

### 长期（6个月+）

- [ ] 多语言支持
- [ ] 协作学习功能
- [ ] AI模型微调
- [ ] 开放API平台

---

## 📚 相关文档

### 技术文档

- **后端与API技术文档**: `docs/后端与API技术文档.md` - 详细的后端架构、API设计、核心模块实现说明
- **前端技术文档**: `docs/前端技术文档.md` - 详细的前端架构、组件设计、状态管理、UI设计说明

### 其他文档

- **知识库说明**: `concept_knowledge_bases/README.md`
- **测试结果说明**: `test_result/README.md`
- **API使用示例**: `src/interfaces/api/API_使用示例.md`
- **API快速开始**: `src/interfaces/api/QUICK_START.md`

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 👥 作者

EduPilot 开发团队

---

**EduPilot - 让学习更智能，让知识更深入** 🚀

