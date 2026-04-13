# UserProfileAgent - 用户画像智能体

用户画像智能体，负责分析用户的学习特点、知识基础和行为模式，构建个性化用户画像。

## 模块概述

UserProfileAgent 是一个单轮对话智能体，通过分析对话历史和知识图谱，生成多维度的用户画像。

## 核心类

### UserProfileAgent

用户画像智能体，继承自 `SingleTurnAgent`。

```python
class UserProfileAgent(SingleTurnAgent):
    def _default_config(self) -> AgentConfig:
        return AgentConfig(
            name="UserProfileAgent",
            temperature=0.4,  # 较低温度，保证画像一致性
            max_tokens=2048,
            streaming_enabled=False,
            tools_enabled=False
        )
```

## 工作流程

```
输入数据
├── 对话历史 (ctx.history 或 metadata.summary)
├── 知识图谱摘要 (metadata.graph_summary)
└── 用户基本信息
    │
    ▼
┌─────────────────────┐
│  加载画像提示词      │  prompt/user_profile/
│  • 画像维度         │
│  • 分析标准         │
│  • 输出格式         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LLM 画像分析       │  temperature=0.4
│  • 学习风格         │
│  • 知识基础         │
│  • 薄弱环节         │
│  • 兴趣方向         │
│  • 学习偏好         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  返回结构化画像     │
│  • 用户画像 JSON    │
│  • 发送 ANALYSIS 事件│
└─────────────────────┘
```

## 画像维度

### 1. 学习风格 (LearningStyle)

用户的最佳学习方式。

```json
{
  "primary": "visual",
  "secondary": "kinesthetic",
  "description": "视觉型学习者，偏好图表和视频",
  "recommendations": [
    "推荐使用思维导图整理知识",
    "观看教学视频加深理解"
  ]
}
```

#### 学习风格类型

| 类型 | 特点 | 推荐资源 |
|------|------|----------|
| `visual` | 偏好图表、图像 | 思维导图、视频教程 |
| `auditory` | 偏好听讲、讨论 | 播客、讲座 |
| `reading` | 偏好阅读、笔记 | 文档、书籍 |
| `kinesthetic` | 偏好动手实践 | 编程练习、项目 |

### 2. 知识基础 (KnowledgeBase)

用户的知识储备情况。

```json
{
  "strong_areas": ["Python编程", "数据结构"],
  "weak_areas": ["高等数学", "线性代数"],
  "gaps": ["分布式系统", "算法优化"],
  "level": "intermediate"
}
```

#### 知识等级

| 等级 | 描述 |
|------|------|
| `beginner` | 零基础，刚入门 |
| `elementary` | 掌握基础概念 |
| `intermediate` | 能够独立应用 |
| `advanced` | 深入理解原理 |
| `expert` | 能够创新和教学 |

### 3. 薄弱环节 (Weaknesses)

需要加强的领域。

```json
{
  "topics": [
    {
      "topic": "概率论",
      "difficulty": "high",
      "frequency": "often"
    }
  ],
  "patterns": [
    "对抽象概念理解较慢",
    "缺乏系统性知识框架"
  ]
}
```

### 4. 兴趣方向 (Interests)

用户的兴趣和偏好领域。

```json
{
  "domains": ["机器学习", "数据分析", "Web开发"],
  "projects": ["推荐系统", "数据可视化"],
  "goals": ["求职准备", "技能提升"]
}
```

### 5. 学习偏好 (Preferences)

学习行为偏好。

```json
{
  "pace": "self-paced",
  "session_length": "30-60min",
  "preferred_time": "evening",
  "break_frequency": "every-25min",
  "communication_style": "direct"
}
```

## 完整用户画像

```python
@dataclass
class UserProfile:
    user_id: str                   # 用户 ID
    learning_style: LearningStyle  # 学习风格
    knowledge_base: KnowledgeBase  # 知识基础
    weaknesses: List[Weakness]    # 薄弱环节
    interests: List[str]           # 兴趣方向
    preferences: Preferences       # 学习偏好
    strengths: List[str]          # 优势领域
    goals: List[str]              # 学习目标
    updated_at: str               # 更新时间
```

## API 接口

### REST API

```bash
# POST /api/v1/profile/analyze
curl -X POST http://localhost:8000/api/v1/profile/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "conversation_summary": "用户最近在学习Python编程...",
    "graph_summary": "用户已掌握基础语法..."
  }'
```

### 函数式接口

```python
from edupilot.agents.user_profile.agent import UserProfileAgent

agent = UserProfileAgent()

# 分析用户画像
profile = await agent.analyze(
    conversation_summary="用户最近在学习机器学习...",
    graph_summary="用户已掌握Python基础...",
    user_id="user_123"
)

print(profile)
```

### 获取用户画像

```bash
# GET /api/v1/profile/{user_id}
curl http://localhost:8000/api/v1/profile/user_123
```

## 存储结构

用户画像存储在 `data/users/{user_id}/profile.json`：

```json
{
  "user_id": "user_123",
  "learning_style": {
    "primary": "visual",
    "secondary": "kinesthetic",
    "description": "视觉型学习者"
  },
  "knowledge_base": {
    "strong_areas": ["Python", "数据结构"],
    "weak_areas": ["数学"],
    "level": "intermediate"
  },
  "weaknesses": [
    {
      "topic": "概率论",
      "difficulty": "high"
    }
  ],
  "interests": ["机器学习", "数据分析"],
  "preferences": {
    "pace": "self-paced",
    "session_length": "30-60min"
  },
  "strengths": ["编程思维", "逻辑分析"],
  "goals": ["求职准备"],
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 画像更新机制

### 增量更新

用户画像会随着对话积累而逐步完善：

1. **首次分析**：基于初始对话生成基础画像
2. **增量更新**：根据新对话更新特定维度
3. **定期刷新**：定期全量重新分析

### 更新触发

- 用户完成一定数量对话后
- 用户明确表示学习目标变化
- 系统检测到用户行为模式变化

## 使用场景

### 1. 个性化学习推荐

```python
# 根据画像推荐学习内容
profile = await get_user_profile(user_id)

if profile.learning_style.primary == "visual":
    recommend_video_tutorials()
elif profile.learning_style.primary == "kinesthetic":
    recommend_practice_exercises()
```

### 2. 学习计划个性化

```python
# 根据画像调整学习计划
profile = await get_user_profile(user_id)

plan = await planner.generate_plan(
    topic="机器学习",
    customize_by={
        "learning_style": profile.learning_style,
        "knowledge_level": profile.knowledge_base.level,
        "session_length": profile.preferences.session_length
    }
)
```

### 3. 内容难度适配

```python
# 根据知识基础调整内容难度
profile = await get_user_profile(user_id)

if profile.knowledge_base.level == "beginner":
    content_difficulty = "easy"
elif profile.knowledge_base.level == "intermediate":
    content_difficulty = "medium"
```

## 提示词设计

提示词位于 `prompts/user_profile/` 目录：

```
prompts/
└── user_profile/
    └── zh/
        └── prompts.yaml
```

### 提示词模板

```yaml
system: |
  你是一个专业的学习分析师。请根据用户的对话历史和
  知识掌握情况，分析用户的学习特点和画像。

template: |
  对话摘要：{conversation_summary}
  知识图谱：{graph_summary}

  请分析用户的：
  1. 学习风格（视觉型/听觉型/读写型/动手型）
  2. 知识基础（强项/弱项/缺口）
  3. 薄弱环节
  4. 兴趣方向
  5. 学习偏好

  请以 JSON 格式返回用户画像。
```

## 集成工作流

```
用户对话
    │
    ▼
┌─────────────────────┐
│  ChatAgent         │
│  记录对话内容       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ UserProfileAgent     │
│ 分析用户画像       │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌─────────┐  ┌──────────────┐
│Learning │  │   Content     │
│ Planner │  │  Adaptation   │
└─────────┘  └──────────────┘
```

## 配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| temperature | 0.4 | 较低温度，保证一致性 |
| max_tokens | 2048 | 中等输出长度 |
| streaming_enabled | False | 不使用流式 |
| tools_enabled | False | 不使用工具 |

## 相关模块

- [ChatAgent](../chat/README.md) - 对话智能体
- [LearningPlannerAgent](../learning_planner/README.md) - 学习规划智能体
- [EvaluationAgent](../evaluation/README.md) - 学习评测智能体
- [ProfileStore](../services/storage/profile_store.py) - 画像存储服务
