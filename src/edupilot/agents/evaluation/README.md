# EvaluationAgent - 学习评测智能体

学习评测智能体，负责评估用户的学习效果，提供客观的学习反馈和改进建议。

## 模块概述

EvaluationAgent 是一个单轮对话智能体，通过分析用户的回答和学习成果，给出结构化的评测报告。

## 核心类

### EvaluationAgent

学习评测智能体，继承自 `SingleTurnAgent`。

```python
class EvaluationAgent(SingleTurnAgent):
    def _default_config(self) -> AgentConfig:
        return AgentConfig(
            name="EvaluationAgent",
            temperature=0.35,  # 评测采用较低温度，保证客观性
            max_tokens=2048,
            streaming_enabled=False,
            tools_enabled=False
        )
```

## 工作流程

```
输入数据
├── summary: 学习内容摘要
├── goals: 学习目标
└── metadata: 附加信息
    │
    ▼
┌─────────────────────┐
│  加载评测提示词      │  prompt/evaluation/
│  • 评测标准         │
│  • 评分维度         │
│  • 反馈格式         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LLM 评测分析       │  temperature=0.35
│  • 内容理解度       │
│  • 知识掌握度       │
│  • 应用能力         │
│  • 综合评价         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  返回结构化结果     │
│  • 评测报告 JSON   │
│  • 发送 ANALYSIS 事件│
└─────────────────────┘
```

## 评测维度

### 1. 内容理解度

评估用户对学习内容的理解深度。

```json
{
  "dimension": "content_understanding",
  "score": 0.85,
  "description": "用户能够准确理解核心概念",
  "suggestions": ["可深入学习相关拓展内容"]
}
```

### 2. 知识掌握度

评估用户对知识点的掌握程度。

| 等级 | 分值 | 描述 |
|------|------|------|
| 精通 | 90-100 | 完全掌握，能够灵活运用 |
| 熟练 | 75-89 | 掌握较好，能独立应用 |
| 理解 | 60-74 | 基本理解，需要巩固 |
| 初步 | 40-59 | 有初步认识，需加强 |
| 薄弱 | 0-39 | 理解不足，需要重新学习 |

### 3. 应用能力

评估用户将知识应用于实际问题的能力。

- 能否举一反三
- 能否解决变式问题
- 能否与已有知识关联

### 4. 综合评价

综合以上维度给出整体评价和改进建议。

## 数据结构

### 评测结果

```python
@dataclass
class EvaluationResult:
    overall_score: float          # 综合得分 0-100
    dimensions: List[Dimension]   # 各维度评分
    strengths: List[str]         # 优势领域
    weaknesses: List[str]        # 薄弱环节
    suggestions: List[str]       # 改进建议
    next_steps: List[str]        # 下一步学习建议
```

### Dimension

```python
@dataclass
class Dimension:
    name: str              # 维度名称
    score: float           # 得分 0-100
    description: str       # 描述
    evidence: List[str]    # 支撑证据
```

## API 接口

### REST API

```bash
# POST /api/v1/evaluation/run
curl -X POST http://localhost:8000/api/v1/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "summary": "用户学习了机器学习基础概念...",
    "goals": "掌握监督学习和无监督学习的区别",
    "context": {
      "topic": "机器学习",
      "difficulty": "入门"
    }
  }'
```

### 函数式接口

```python
from edupilot.agents.evaluation.agent import evaluate

result = await evaluate(
    summary="用户学习了梯度下降算法...",
    goals="理解并能应用梯度下降"
)

print(result)
# {
#   "overall_score": 85,
#   "dimensions": [...],
#   "strengths": [...],
#   "suggestions": [...]
# }
```

## 评测提示词

评测提示词位于 `prompts/evaluation/` 目录：

```
prompts/
└── evaluation/
    └── zh/
        └── prompts.yaml    # 中文评测提示词
```

### 提示词结构

```yaml
system: |
  你是一个专业的学习评测专家。请根据用户的学习内容和回答，
  给出客观、具体的评测反馈。

template: |
  请评测以下学习内容：

  学习摘要：{summary}
  学习目标：{goals}

  请从以下维度进行评测：
  1. 内容理解度
  2. 知识掌握度
  3. 应用能力
  4. 综合评价

  请以 JSON 格式返回评测结果。
```

## 使用场景

### 1. 课程学习评测

```python
# 课程结束后进行评测
result = await evaluate(
    summary="用户完成了"神经网络基础"课程学习...",
    goals="理解神经网络基本原理"
)
```

### 2. 问答测试评测

```python
# 回答问题后进行评测
result = await evaluate(
    summary="用户回答了关于梯度下降的问题...",
    goals="掌握梯度下降算法"
)
```

### 3. 作业评测

```python
# 作业提交后评测
result = await evaluate(
    summary="用户完成了机器学习作业...",
    goals="掌握 scikit-learn 基础用法"
)
```

## 扩展开发

### 添加新的评测维度

1. 在 `EvaluationResult` 中添加新的维度字段
2. 在提示词中添加新的评测标准
3. 在结果解析中添加新的提取逻辑

### 自定义评测标准

```python
# 针对特定学科定制评测
class MathEvaluationAgent(EvaluationAgent):
    def _load_prompt(self) -> str:
        # 使用数学特定的评测提示词
        return load_prompt("prompts/evaluation/math/")
```

## 配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| temperature | 0.35 | 较低温度，保证客观 |
| max_tokens | 2048 | 最大输出长度 |
| streaming_enabled | False | 不使用流式 |
| tools_enabled | False | 不使用工具 |

## 相关模块

- [ChatAgent](../chat/README.md) - 对话智能体
- [LearningPlannerAgent](../learning_planner/README.md) - 学习规划智能体
- [UserProfileAgent](../user_profile/README.md) - 用户画像智能体
