# LearningPlannerAgent - 学习规划智能体

学习规划智能体，负责根据用户画像和学习目标，生成个性化的学习计划。

## 模块概述

LearningPlannerAgent 是一个单轮对话智能体，结合用户画像分析结果，生成结构化的学习路径和计划。

## 核心类

### LearningPlannerAgent

学习规划智能体，继承自 `SingleTurnAgent`。

```python
class LearningPlannerAgent(SingleTurnAgent):
    def _default_config(self) -> AgentConfig:
        return AgentConfig(
            name="LearningPlannerAgent",
            temperature=0.5,  # 中等温度，平衡创意与确定性
            max_tokens=3072,  # 较长输出，支持详细计划
            streaming_enabled=False,
            tools_enabled=False
        )
```

## 工作流程

```
输入数据
├── user_profile: 用户画像 (从 metadata 获取)
├── topic: 学习主题
└── duration: 计划时长
    │
    ▼
┌─────────────────────┐
│  加载用户画像        │  从 metadata 读取
│  • 学习风格         │
│  • 知识基础         │
│  • 学习偏好         │
│  • 时间可用性       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  加载规划提示词      │  prompt/learning_planner/
│  • 计划格式要求     │
│  • 个性化指导       │
│  • 时间分配建议     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LLM 生成计划       │  temperature=0.5
│  • 周计划结构       │
│  • 每日目标         │
│  • 资源推荐         │
│  • 进度指标         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  返回结构化计划     │
│  • 周计划 JSON      │
│  • 发送 ANALYSIS 事件│
└─────────────────────┘
```

## 学习计划结构

### 周计划 (WeeklyPlan)

```python
@dataclass
class WeeklyPlan:
    week_number: int              # 第几周
    theme: str                    # 本周主题
    goals: List[str]              # 本周目标
    daily_plans: List[DailyPlan]  # 每日计划
    resources: List[Resource]     # 推荐资源
    milestones: List[str]          # 里程碑
    evaluation_criteria: str       # 评估标准
```

### 每日计划 (DailyPlan)

```python
@dataclass
class DailyPlan:
    day: str                      # 星期几
    date: str                     # 日期
    objectives: List[str]         # 学习目标
    activities: List[Activity]     # 学习活动
    duration_minutes: int         # 建议时长
    breaks: List[Break]           # 休息安排
```

### 学习活动 (Activity)

```python
@dataclass
class Activity:
    type: str                     # activity_type: reading/practice/project/review
    title: str                    # 活动标题
    description: str              # 活动描述
    duration_minutes: int         # 预计时长
    resources: List[str]          # 所需资源
    exercises: List[str]          # 练习题
```

## 个性化策略

### 基于学习风格的计划调整

| 学习风格 | 特点 | 计划调整 |
|----------|------|----------|
| 视觉型 | 喜欢图表、视频 | 增加可视化内容 |
| 听觉型 | 喜欢听讲、讨论 | 增加音频/视频资源 |
| 读写型 | 喜欢阅读、笔记 | 增加文档、写作 |
| 动手型 | 喜欢实践、项目 | 增加动手练习 |

### 基于知识基础的调整

- **零基础**：从基础概念开始，循序渐进
- **有基础**：快速回顾后进入核心内容
- **进阶**：聚焦高级主题和实践应用

### 基于时间可用性的调整

- **碎片时间多**：适合短时高频学习
- **整块时间多**：适合深度学习和项目实践

## API 接口

### REST API

```bash
# POST /api/v1/plan/generate
curl -X POST http://localhost:8000/api/v1/plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "topic": "机器学习",
    "duration_weeks": 4,
    "daily_hours": 2
  }'
```

### 函数式接口

```python
from edupilot.agents.learning_planner.agent import LearningPlannerAgent

agent = LearningPlannerAgent()

# 加载用户画像
profile = {
    "learning_style": "visual",
    "knowledge_level": "beginner",
    "available_hours_per_day": 2
}

# 生成学习计划
plan = await agent.plan(
    profile=profile,
    goal_hint="掌握机器学习基础"
)

print(plan)
```

## 学习计划示例

```json
{
  "week_number": 1,
  "theme": "机器学习入门与基础概念",
  "goals": [
    "理解机器学习的基本定义和应用场景",
    "掌握监督学习和无监督学习的区别",
    "了解常见的机器学习算法分类"
  ],
  "daily_plans": [
    {
      "day": "周一",
      "objectives": ["了解机器学习定义", "认识应用场景"],
      "activities": [
        {
          "type": "reading",
          "title": "机器学习概述",
          "duration_minutes": 30
        },
        {
          "type": "video",
          "title": "机器学习入门视频",
          "duration_minutes": 20
        }
      ]
    }
  ],
  "resources": [
    {"title": "机器学习简介", "type": "article"},
    {"title": "吴恩达 ML 课程", "type": "video"}
  ],
  "milestones": ["完成入门测试", "提交学习笔记"],
  "evaluation_criteria": "能够用自己的话解释机器学习"
}
```

## 提示词设计

提示词位于 `prompts/learning_planner/` 目录：

```
prompts/
└── learning_planner/
    └── zh/
        └── prompts.yaml
```

### 提示词模板

```yaml
system: |
  你是一个专业的学习规划师。请根据用户的学习风格、
  知识基础和学习目标，制定个性化的学习计划。

template: |
  用户信息：
  - 学习风格：{learning_style}
  - 知识基础：{knowledge_level}
  - 每日可用时间：{daily_hours}小时

  学习主题：{topic}
  计划时长：{duration_weeks}周

  请制定一个详细的学习计划，包括：
  1. 每周主题和目标
  2. 每日具体安排
  3. 推荐学习资源
  4. 进度评估标准

  请以 JSON 格式返回。
```

## 使用场景

### 1. 新用户首次学习规划

```python
# 根据用户画像生成初始计划
plan = await agent.plan(
    profile=await get_user_profile(user_id),
    goal_hint="Python 编程入门"
)
```

### 2. 阶段性学习规划

```python
# 根据当前进度规划下一阶段
plan = await agent.plan(
    profile=user_profile,
    goal_hint="深度学习进阶"
)
```

### 3. 考前冲刺规划

```python
# 短期高效复习计划
plan = await agent.plan(
    profile=user_profile,
    goal_hint="数据结构与算法考前冲刺"
)
```

## 集成工作流

```
用户画像分析
    │
    ▼
┌─────────────────────┐
│  UserProfileAgent   │
│  生成用户画像       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ LearningPlannerAgent│
│ 生成学习计划       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ChatAgent         │
│  提供学习指导       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ EvaluationAgent     │
│ 评估学习效果       │
└─────────────────────┘
```

## 配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| temperature | 0.5 | 中等温度 |
| max_tokens | 3072 | 较长输出 |
| streaming_enabled | False | 不使用流式 |
| tools_enabled | False | 不使用工具 |

## 相关模块

- [ChatAgent](../chat/README.md) - 对话智能体
- [UserProfileAgent](../user_profile/README.md) - 用户画像智能体
- [EvaluationAgent](../evaluation/README.md) - 学习评测智能体
