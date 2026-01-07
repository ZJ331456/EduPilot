# 测试和示例文件结构说明

本文档说明项目中的测试和示例文件的组织结构。

## 📁 目录结构

```
EduPilot/
├── src/tests/              # 单元测试目录（pytest）
├── integration_tests/      # 集成测试目录
├── examples/               # 示例代码目录
└── test_result/            # 测试结果和文档目录
```

## 📂 src/tests/ - 单元测试

**用途**: 包含所有使用 pytest 框架的单元测试文件

**特点**:
- 使用 mock 和 stub 进行隔离测试
- 不依赖外部服务（如数据库、API等）
- 运行速度快
- 适合 CI/CD 自动化测试

**文件列表**:
- `conftest.py` - pytest 配置和共享 fixtures
- `test_*.py` - 各个组件的单元测试
  - `test_query_analyzer_agent.py` - 查询分析器测试
  - `test_knowledge_manager_agent.py` - 知识管理器测试
  - `test_knowledge_retriever_agent.py` - 知识检索器测试（使用 mock）
  - `test_planner_agent.py` - 规划器测试
  - `test_executor_agent.py` - 执行器测试
  - `test_socratic_guide_agent.py` - 苏格拉底引导测试
  - `test_memory_manager_agent.py` - 记忆管理器测试
  - `test_tool_specialist_agent.py` - 工具专家测试
  - `test_learning_workflow.py` - 学习工作流单元测试（使用 stub agents）
  - `test_llm_providers.py` - LLM 提供商测试

**运行方式**:
```bash
# 运行所有单元测试
pytest src/tests/

# 运行特定测试文件
pytest src/tests/test_query_analyzer_agent.py

# 运行特定测试函数
pytest src/tests/test_query_analyzer_agent.py::test_specific_function
```

## 📂 integration_tests/ - 集成测试

**用途**: 包含端到端的集成测试，测试完整的工作流程

**特点**:
- 测试真实的工作流和组件交互
- 可能需要外部依赖（数据库、知识库等）
- 运行时间较长
- 适合手动验证和完整功能测试

**文件列表**:
- `test_learning_workflow.py` - 学习工作流集成测试（实际运行工作流）
- `test_langgraph_workflow.py` - LangGraph 工作流测试
- `test_knowledge_retrieval.py` - 知识检索集成测试（实际检索）
- `run_learning_workflow_test.py` - 批量测试运行器

**运行方式**:
```bash
# 运行集成测试
python integration_tests/test_learning_workflow.py

# 运行批量测试
python integration_tests/run_learning_workflow_test.py

# 运行知识检索测试
python integration_tests/test_knowledge_retrieval.py
```

## 📂 examples/ - 示例代码

**用途**: 包含各种使用示例，帮助开发者理解如何使用各个组件

**文件列表**:
- `socratic_guide_demo.py` - 苏格拉底引导 Agent 使用示例
- `memory_manager_demo.py` - 记忆管理器使用示例
- `llm_examples.py` - LLM 客户端（Ollama/Qwen）使用示例

**运行方式**:
```bash
# 运行苏格拉底引导示例
python examples/socratic_guide_demo.py

# 运行记忆管理器示例
python examples/memory_manager_demo.py

# 运行 LLM 示例
python examples/llm_examples.py
```

## 📂 test_result/ - 测试结果和文档

**用途**: 存储测试结果、日志和文档

**文件列表**:
- `README.md` - 测试结果说明文档
- `学习模式触发问题示例.md` - 学习模式触发问题示例文档

**注意**: 临时测试结果文件（如 `.json`、`.txt`）会在测试后自动生成，不应提交到版本控制。

## 🔄 测试文件整合说明

### 已整合的内容

1. **示例文件整合**:
   - 将 `src/tests/simple_ollama_example.py` 和 `src/tests/simple_qwen_example.py` 整合到 `examples/llm_examples.py`
   - 删除了重复的简单示例文件

2. **集成测试整合**:
   - 将 `src/tests/test_knowledge_retrival.py` 移到 `integration_tests/test_knowledge_retrieval.py`
   - 区分了单元测试和集成测试的职责

3. **临时文件清理**:
   - 删除了 `test_result/` 中的临时测试结果文件
   - 保留了文档和说明文件

### 文件职责划分

| 文件类型 | 位置 | 特点 |
|---------|------|------|
| 单元测试 | `src/tests/` | 使用 mock，快速，隔离 |
| 集成测试 | `integration_tests/` | 真实运行，完整流程 |
| 示例代码 | `examples/` | 演示用法，可运行 |
| 测试结果 | `test_result/` | 文档和临时结果 |

## 🚀 快速开始

### 运行单元测试
```bash
pytest src/tests/ -v
```

### 运行集成测试
```bash
python integration_tests/test_learning_workflow.py
```

### 查看示例
```bash
python examples/socratic_guide_demo.py
```

## 📝 注意事项

1. **单元测试** 应该快速且独立，不依赖外部服务
2. **集成测试** 可能需要配置环境变量和外部依赖
3. **示例代码** 主要用于学习和演示，可能需要实际的服务配置
4. 测试结果文件不应提交到版本控制（已在 `.gitignore` 中配置）

## 🔧 维护建议

1. 新增单元测试应放在 `src/tests/` 目录
2. 新增集成测试应放在 `integration_tests/` 目录
3. 新增示例代码应放在 `examples/` 目录
4. 定期清理 `test_result/` 中的临时文件
5. 保持测试文件的命名一致性：`test_*.py` 用于 pytest，其他用于集成测试

