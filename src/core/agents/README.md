# Agents 模块说明文档

本文档详细说明 EduPilot 系统中所有智能体（Agent）的功能、职责和使用方法。

## 📋 目录

- [架构概览](#架构概览)
- [Agent 列表](#agent-列表)
  - [1. QueryAnalyzerAgent - 查询分析器](#1-queryanalyzeragent---查询分析器)
  - [2. OrchestratorAgent - 任务编排器](#2-orchestratoragent---任务编排器)
  - [3. KnowledgeManagerAgent - 知识管理器](#3-knowledgemanageragent---知识管理器)
  - [4. ToolSpecialistAgent - 工具专家](#4-toolspecialistagent---工具专家)
  - [5. DraftWriterAgent - 内容撰稿人](#5-draftwriteragent---内容撰稿人)
  - [6. ReviewerAgent - 质量审核员](#6-revieweragent---质量审核员)
  - [7. CurriculumDesignerAgent - 课程设计师](#7-curriculumdesigneragent---课程设计师)
  - [8. QuizMasterAgent - 测评与出题官](#8-quizmasteragent---测评与出题官)
  - [9. SocraticGuideAgent - 苏格拉底引导者](#9-socraticguideagent---苏格拉底引导者)
  - [10. MemoryManagerAgent - 记忆管理器](#10-memorymanageragent---记忆管理器)
- [工作流程](#工作流程)
- [使用示例](#使用示例)

---

## 架构概览

EduPilot 采用多智能体协作架构，各个 Agent 各司其职，通过 `AgentState` 共享状态，实现完整的教学对话流程。

```
用户查询
    ↓
[QueryAnalyzer] → 意图识别、检索决策
    ↓
[Orchestrator] → 任务编排、Agent调度
    ↓
┌─────────────────────────────────────┐
│  并行执行（根据编排结果）              │
├─────────────────────────────────────┤
│  [KnowledgeManager] 知识检索          │
│  [ToolSpecialist]   工具调用          │
│  [CurriculumDesigner] 课程设计        │
│  [SocraticGuide]    问题生成          │
│  [MemoryManager]    记忆管理          │
└─────────────────────────────────────┘
    ↓
[DraftWriter] → 内容生成
    ↓
[Reviewer] → 质量审核
    ↓
[QuizMaster] → 测试题生成（可选）
    ↓
最终响应
```

---

## Agent 列表

### 1. QueryAnalyzerAgent - 查询分析器

**职责**: 统一的查询理解入口，整合意图识别和检索决策

**核心功能**:
- ✅ **意图识别**: 启发式 + LLM 精修，识别用户真实意图
- ✅ **检索决策**: 基于意图和查询特征，判断是否需要知识检索
- ✅ **查询优化**: 提取核心概念，生成优化查询，构建检索策略
- ✅ **路由建议**: 为下游 agent 提供执行路径建议

**主要特性**:
- 统一的查询理解入口：一次分析完成意图识别和检索决策
- 信息复用：避免重复的文本分析和特征提取
- 联合优化：意图和检索策略相互关联，统一决策
- 性能优化：减少状态传递，降低序列化开销

**输出状态字段**:
- `state.interpretation`: 意图识别结果
- `state.query_type`: 查询类型（CONCEPT_EXPLANATION, DIRECT_ANSWER 等）
- `state.retrieval_decision`: 检索决策（是否需要检索、核心概念、优化查询等）

**使用场景**:
- 所有用户查询的第一处理环节
- 需要理解用户意图的场景
- 需要决定是否检索知识的场景

---

### 2. OrchestratorAgent - 任务编排器

**职责**: 分析用户意图，动态调度下游 Agent

**核心功能**:
- ✅ **任务编排**: 接收 QueryAnalyzer 的分析结果，生成调度指令
- ✅ **动态调度**: 根据查询类型和上下文，决定激活哪些 Worker Agent
- ✅ **计划生成**: 生成执行计划（Plan），包含 `next_workers` 列表
- ✅ **资源评估**: 评估查询复杂度、知识可用性、用户参与度

**调度决策逻辑**:
- **课程设计**: 用户想要系统学习 → 调用 `curriculum_designer`
- **工具调用**: 计算、搜索、实时信息 → 调用 `tool_specialist`
- **知识检索**: 大多数情况都需要 → 调用 `knowledge_manager`
- **苏格拉底引导**: 引导学习模式 → 调用 `socratic_guide`
- **记忆管理**: 几乎总是需要 → 调用 `memory_manager`

**输出状态字段**:
- `state.plan`: 执行计划（包含 `next_workers` 列表）
- `state.plan_type`: 计划类型（DIRECT_ANSWER, GUIDED_LEARNING 等）

**使用场景**:
- 在 QueryAnalyzer 之后，决定后续执行路径
- 需要动态调度多个 Agent 的场景

---

### 3. KnowledgeManagerAgent - 知识管理器

**职责**: 统一的知识库管理，集成自动索引构建和智能知识检索

**核心功能**:
- ✅ **自动索引**: 自动检测并构建 GraphRAG 索引
- ✅ **知识检索**: 多策略并发检索，支持精确匹配、概念匹配、语义扩展等
- ✅ **相关性评分**: 多维度相关性评分算法，确保结果质量
- ✅ **智能缓存**: 缓存检索结果（24小时TTL），减少重复计算
- ✅ **知识库管理**: 完整的知识库生命周期管理

**检索策略**:
- 精确匹配（Exact Match）
- 概念匹配（Concept Match）
- 语义扩展（Semantic Expansion）
- 图结构检索（Graph Retrieval）
- 全局搜索（Global Search）

**输出状态字段**:
- `state.retrieved_knowledge`: 检索结果（包含 results、target_concepts、successful_sources 等）

**使用场景**:
- 需要从知识库检索信息的场景
- 概念解释、知识问答等场景
- 需要构建知识索引的场景

**详细文档**: 参见 `knowledge_manager/README.md`

---

### 4. ToolSpecialistAgent - 工具专家

**职责**: 调用外部工具，处理计算、搜索等任务

**核心功能**:
- ✅ **计算器**: 执行数学计算和逻辑运算
- ✅ **网络搜索**: 获取实时信息和新闻
- ✅ **工具选择**: 根据意图自动选择合适的工具
- ✅ **结果格式化**: 将工具输出格式化为可读文本

**支持的工具**:
- **CalculatorTool**: 数学计算（支持基本运算、函数、表达式解析）
- **WebSearchTool**: 网络搜索（支持实时信息获取）

**输出状态字段**:
- `state.tool_outputs`: 工具执行结果（包含 calculator、web_search 等）

**使用场景**:
- 用户需要计算（"算一下 123+456"）
- 用户需要实时信息（"搜索最新的新闻"）
- 需要调用外部工具的场景

---

### 5. DraftWriterAgent - 内容撰稿人

**职责**: 根据规划和工具执行结果生成内容草稿，或根据 Reviewer 的意见修改草稿

**核心功能**:
- ✅ **初稿生成**: 整合 RAG 检索结果、工具输出生成初稿
- ✅ **草稿修改**: 根据 Reviewer 的 Critique 修改草稿
- ✅ **个性化适配**: 根据用户水平调整内容难度和风格
- ✅ **上下文整合**: 整合知识库内容、工具输出、用户画像等

**生成流程**:
1. 收集上下文（知识库内容、工具输出、用户画像）
2. 构建 Prompt（根据是初稿还是修改）
3. 调用 LLM 生成内容
4. 更新状态

**输出状态字段**:
- `state.draft_content`: 生成的草稿内容
- `state.revision_count`: 修改次数

**使用场景**:
- 生成教学内容初稿
- 根据审核意见修改内容
- 整合多源信息生成回答

---

### 6. ReviewerAgent - 质量审核员

**职责**: 审核 DraftWriter 生成的内容，确保准确性、教学性和结构清晰

**核心功能**:
- ✅ **质量检查**: 检查幻觉、语气、难度匹配度
- ✅ **审核决策**: 决定是否通过或需要重写
- ✅ **修改意见**: 给出具体的修改建议（Critique）
- ✅ **防死循环**: 限制修改次数（最多3次）

**审核维度**:
- **准确性**: 检查事实错误、幻觉
- **教学性**: 评估教学价值和清晰度
- **难度匹配**: 检查内容难度是否适合用户水平
- **结构清晰**: 评估内容结构和逻辑

**输出状态字段**:
- `state.is_satisfactory`: 是否通过审核
- `state.critique`: 修改意见（如果不通过）
- `state.revision_count`: 修改次数

**使用场景**:
- 在 DraftWriter 生成内容后审核
- 确保内容质量符合标准
- 提供改进建议

---

### 7. CurriculumDesignerAgent - 课程设计师

**职责**: 生成系统化的学习路径（思维导图结构）

**核心功能**:
- ✅ **课程设计**: 当用户想要系统学习时，生成知识树结构
- ✅ **思维导图**: 输出 JSON 格式的 MindMap 数据
- ✅ **模块化设计**: 生成模块、主题、描述等结构化内容
- ✅ **大纲格式化**: 将 JSON 结构格式化为文本大纲

**输出格式**:
```json
{
  "topic": "课程主题",
  "modules": [
    {
      "name": "模块名称",
      "description": "模块描述",
      "topics": [
        {
          "name": "主题名称",
          "description": "主题描述"
        }
      ]
    }
  ]
}
```

**输出状态字段**:
- `state.curriculum_plan`: 课程计划（JSON 格式）
- `state.tool_outputs["curriculum_outline"]`: 格式化的文本大纲

**使用场景**:
- 用户想要系统学习某个主题
- 需要生成学习路径的场景
- 需要思维导图结构的场景

---

### 8. QuizMasterAgent - 测评与出题官

**职责**: 在知识点讲解后生成测试题，评估用户掌握度

**核心功能**:
- ✅ **题目生成**: 根据讲解内容生成单选题
- ✅ **难度适配**: 根据用户水平和内容难度生成合适题目
- ✅ **格式输出**: 输出 JSON 格式的题目数据
- ✅ **文本格式化**: 将题目格式化为可读文本

**题目格式**:
```json
{
  "questions": [
    {
      "id": 1,
      "question": "问题内容",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct_index": 0,
      "explanation": "解释"
    }
  ]
}
```

**输出状态字段**:
- `state.tool_outputs["quiz_data"]`: 题目数据（JSON 格式）
- `state.draft_content`: 追加格式化的题目文本

**使用场景**:
- 内容审核通过后生成测试题
- 需要评估学习效果的场景
- 提供练习题的场景

---

### 9. SocraticGuideAgent - 苏格拉底引导者

**职责**: 生成苏格拉底式问题，引导用户批判性思考

**核心功能**:
- ✅ **问题生成**: 生成8种类型的苏格拉底式问题
- ✅ **质量验证**: MARS 优化版，确保问题符合苏格拉底风格
- ✅ **个性化分析**: 基于用户理解水平和学习状态调整问题
- ✅ **自动重试**: 质量不达标自动重新生成
- ✅ **理解评估**: 评估用户理解水平（5个等级）

**8种问题类型**:
1. **澄清型** (Clarification): "你能详细说明一下...吗？"
2. **假设型** (Assumption): "你假设了什么？"
3. **证据型** (Evidence): "你有什么证据支持这个观点？"
4. **视角型** (Perspective): "从另一个角度看会怎样？"
5. **含义型** (Implication): "这意味着什么？"
6. **元认知型** (Meta): "你是怎么得出这个结论的？"
7. **综合型** (Synthesis): "这些观点如何联系起来？"
8. **应用型** (Application): "这如何应用到实际中？"

**理解水平等级**:
- `NO_UNDERSTANDING`: 无理解
- `SURFACE_UNDERSTANDING`: 表面理解
- `BASIC_UNDERSTANDING`: 基础理解
- `GOOD_UNDERSTANDING`: 良好理解
- `DEEP_UNDERSTANDING`: 深度理解

**输出状态字段**:
- `state.socratic_question`: 当前生成的苏格拉底问题
- `state.socratic_questions`: 问题历史列表
- `state.understanding_level`: 用户理解水平
- `state.conversation_stage`: 对话阶段

**使用场景**:
- 引导式学习模式
- 需要培养批判性思维的场景
- 多轮对话中的引导环节

---

### 10. MemoryManagerAgent - 记忆管理器

**职责**: 统一的记忆管理，整合短期记忆、长期记忆和元认知分析

**核心功能**:
- ✅ **短期记忆**: 分析当前会话的交互质量
- ✅ **长期记忆**: 提取并持久化用户画像信息
- ✅ **元认知分析**: 识别学习模式、知识缺口、生成学习反馈
- ✅ **用户画像**: 构建三元组知识图谱、情感历史、学习模式
- ✅ **记忆检索**: 获取用户画像、会话历史、学习记录

**三层记忆架构**:
1. **短期记忆层**: 当前会话分析、交互质量评估、即时反馈生成
2. **长期记忆层**: 用户画像持久化、三元组知识图谱、情感历史追踪
3. **元认知层**: 学习模式识别、知识缺口分析、个性化学习路径

**输出状态字段**:
- `state.metadata["memory_analysis"]`: 记忆分析结果
  - `interaction`: 交互质量分析
  - `profile_update`: 用户画像更新
  - `learning_feedback`: 学习反馈
  - `knowledge_gaps`: 知识缺口

**使用场景**:
- 需要个性化教学的场景
- 需要追踪用户学习状态的场景
- 需要生成学习反馈的场景

**详细文档**: 参见 `memory_manager/README.md`

---

## 工作流程

### 典型查询流程

```
1. 用户查询: "什么是大化改新？"
   ↓
2. QueryAnalyzer: 识别意图为 CONCEPT_EXPLANATION，决定需要检索
   ↓
3. Orchestrator: 决定调用 KnowledgeManager 和 MemoryManager
   ↓
4. KnowledgeManager: 从知识库检索相关信息
   ↓
5. MemoryManager: 读取用户画像，个性化分析
   ↓
6. DraftWriter: 整合信息生成初稿
   ↓
7. Reviewer: 审核内容质量
   ↓
8. 如果通过 → QuizMaster: 生成测试题（可选）
   ↓
9. 返回最终响应
```

### 苏格拉底引导流程

```
1. 用户查询: "为什么秦始皇是暴君？"
   ↓
2. QueryAnalyzer: 识别为 SOCRATIC_DIALOGUE
   ↓
3. Orchestrator: 决定调用 SocraticGuide
   ↓
4. SocraticGuide: 生成苏格拉底问题
   ↓
5. 用户回答: "因为他焚书坑儒"
   ↓
6. SocraticGuide: 评估理解水平，生成下一个问题
   ↓
7. 循环直到达到理解目标或最大轮次
```

### 课程设计流程

```
1. 用户查询: "我想系统学习日本历史"
   ↓
2. QueryAnalyzer: 识别为结构学习需求
   ↓
3. Orchestrator: 决定调用 CurriculumDesigner
   ↓
4. CurriculumDesigner: 生成课程结构和思维导图
   ↓
5. DraftWriter: 根据课程大纲生成详细内容
   ↓
6. Reviewer: 审核内容质量
   ↓
7. 返回课程计划
```

---

## 使用示例

### 基本使用

```python
from src.core.agents import (
    QueryAnalyzerAgent,
    OrchestratorAgent,
    KnowledgeManagerAgent,
    DraftWriterAgent,
    ReviewerAgent
)
from src.infrastructure.utils import AgentState

# 创建 Agent 实例
query_analyzer = QueryAnalyzerAgent()
orchestrator = OrchestratorAgent()
knowledge_manager = KnowledgeManagerAgent()
draft_writer = DraftWriterAgent()
reviewer = ReviewerAgent()

# 创建初始状态
state = AgentState(user_query="什么是大化改新？")

# 执行流程
state = await query_analyzer.execute(state)
state = await orchestrator.execute(state)

# 根据编排结果执行
if "knowledge_manager" in state.plan.get("next_workers", []):
    state = await knowledge_manager.execute(state)

state = await draft_writer.execute(state)
state = await reviewer.execute(state)

# 获取最终结果
if state.is_satisfactory:
    print(state.draft_content)
```

### 苏格拉底引导示例

```python
from src.core.agents import SocraticGuideAgent
from src.infrastructure.utils import AgentState, UnderstandingLevel

# 创建 Agent
socratic_guide = SocraticGuideAgent(config={
    "max_questions": 5,
    "enable_quality_check": True
})

# 创建状态
state = AgentState(
    user_query="为什么秦始皇是暴君？",
    understanding_level=UnderstandingLevel.NO_UNDERSTANDING
)

# 生成问题
state = await socratic_guide.execute(state)
print(f"问题: {state.socratic_question}")

# 处理用户回答
state.user_responses.append("因为他焚书坑儒")
state = await socratic_guide.execute(state)
print(f"下一个问题: {state.socratic_question}")
```

### 工具调用示例

```python
from src.core.agents import ToolSpecialistAgent
from src.infrastructure.utils import AgentState

# 创建 Agent
tool_specialist = ToolSpecialistAgent()

# 计算任务
state = AgentState(user_query="算一下 123 + 456")
state = await tool_specialist.execute(state)
print(state.tool_outputs["calculator"]["result"])

# 搜索任务
state = AgentState(user_query="搜索最新的AI新闻")
state = await tool_specialist.execute(state)
print(state.tool_outputs["web_search"]["results"])
```

---

## 注意事项

1. **状态传递**: 所有 Agent 通过 `AgentState` 共享状态，确保信息一致性
2. **错误处理**: 每个 Agent 都有错误处理机制，失败不应阻断主流程
3. **资源管理**: KnowledgeManager 和 MemoryManager 需要管理资源，记得调用 `shutdown()`
4. **配置管理**: 各 Agent 支持配置参数，可根据需求调整
5. **并发执行**: Orchestrator 可以调度多个 Agent 并行执行，提高效率

---

## 扩展开发

### 添加新 Agent

1. 继承 `BaseAgent` 基类
2. 实现 `execute()` 方法
3. 可选实现 `can_execute()` 方法
4. 在 `__init__.py` 中注册导出
5. 在 Orchestrator 中添加调度逻辑

### 最佳实践

- 保持 Agent 职责单一
- 通过 `AgentState` 共享状态，避免直接修改其他 Agent 的状态
- 实现适当的错误处理和日志记录
- 提供清晰的配置选项
- 编写单元测试和集成测试

---

## 相关文档

- [Base Agent 基类说明](base.py)
- [KnowledgeManager 详细文档](knowledge_manager/README.md)
- [MemoryManager 详细文档](memory_manager/README.md)
- [工作流说明](../../core/workflow/README.md)

---

**最后更新**: 2024年

