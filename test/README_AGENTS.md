# EduPilot v4 测试说明（非 pytest）

本目录提供对 **v4 架构**（3 Agents + 2 Services）的独立可运行测试脚本，用于逐个验证效果。**不使用 pytest**，直接 `python test/xxx.py` 即可。

## 环境与路径

- **项目根目录**: `D:\Project\STUAgent\EduPilot`
- **核心代码**: `src/core/agents`（3 Agents）、`src/core/services`（2 Services）、`src/core/workflow`
- **测试代码**: `test/`

运行前请**激活 conda 环境**：

```bash
conda activate studyagent
cd D:\Project\STUAgent\EduPilot
```

## 运行方式

### 运行单个测试

在项目根目录执行：

```bash
conda activate studyagent
python test/test_planner_agent.py
python test/test_teacher_agent.py
python test/test_evaluator_agent.py
python test/test_knowledge_engine.py
python test/test_memory_system.py
```

### 一键运行全部

```bash
conda activate studyagent
python test/run_all_agent_tests.py
```

## 测试文件与说明

| 测试文件 | 对应模块 | 说明 | 依赖 |
|---------|----------|------|------|
| `test_planner_agent.py` | LearningPlannerAgent | 意图识别 + 策略 + 路由 | 可选 LLM（默认关） |
| `test_teacher_agent.py` | TeachingAgent | explain / direct 等模式 | LLM |
| `test_evaluator_agent.py` | EvaluationAgent | 质量评估 + 安全过滤 + 强制通过 | 可选 LLM |
| `test_knowledge_engine.py` | KnowledgeEngineService | 知识检索 | 知识库目录（可选） |
| `test_memory_system.py` | MemorySystemService | 画像加载 + 记忆更新 | 本地 data/memory_data |

公共模拟状态与样本数据在 **`test/agents/mock_state.py`**，使用 v4 的 `LearningWorkflowState`（dict），通过 `make_v4_state()` 构造。

## 注意事项

1. 务必在**项目根目录**执行，保证 `src` 可被导入。
2. 使用 **studyagent** 环境，避免依赖缺失。
3. 依赖 LLM 的测试（Teacher、Evaluator 部分逻辑）需配置好 LLM 服务（Qwen/Ollama），否则会走兜底逻辑。
4. KnowledgeEngine 依赖 `data/concept_knowledge_bases` 下已有知识库，无数据时检索结果为空属正常。
5. MemorySystem 会写入 `data/memory_data`，测试会使用 `test_user_001` / `test-session-001` 等 ID。
