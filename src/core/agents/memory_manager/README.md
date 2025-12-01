# 记忆管理器 (MemoryManagerAgent)

## 概述

`MemoryManagerAgent` 是一个统一的记忆管理智能体，整合了原有的 `LearnerAgent` 和 `UserProfileAgent` 的功能。它负责管理短期和长期记忆，并提供元认知分析。

## 架构设计

### 三层记忆架构

```
┌─────────────────────────────────────────┐
│        MemoryManagerAgent               │
├─────────────────────────────────────────┤
│  1. 短期记忆层 (Short-term Memory)      │
│     - 当前会话分析                      │
│     - 交互质量评估                      │
│     - 即时反馈生成                      │
├─────────────────────────────────────────┤
│  2. 长期记忆层 (Long-term Memory)       │
│     - 用户画像持久化                    │
│     - 三元组知识图谱                    │
│     - 情感历史追踪                      │
├─────────────────────────────────────────┤
│  3. 元认知层 (Meta-cognitive)           │
│     - 学习模式识别                      │
│     - 知识缺口分析                      │
│     - 个性化学习路径                    │
└─────────────────────────────────────────┘
```

## 核心功能

### 1. 短期记忆管理

分析当前会话的交互质量，评估以下维度：

- **用户参与度**: 基于响应数量和质量
- **知识覆盖度**: 基于检索结果的相关性
- **响应效果**: 基于执行成功率
- **学习价值**: 基于苏格拉底问答和知识连接

### 2. 长期记忆管理

提取并持久化用户画像信息：

- **三元组提取**: 从对话中提取 (主体, 谓语, 客体) 三元组
- **情感分析**: 识别用户的情感状态
- **学习模式**: 识别用户偏好的学习方式
- **画像洞察**: 生成个性化洞察

### 3. 元认知分析

- **知识缺口识别**: 发现学习过程中的不足
- **学习反馈生成**: 提供个性化改进建议
- **学习路径推荐**: 基于用户画像推荐学习路径

## 使用示例

### 基本使用

```python
from domain.agents.memory_manager import MemoryManagerAgent
from infrastructure.utils import AgentState

# 创建记忆管理器
memory_agent = MemoryManagerAgent()

# 创建状态
state = AgentState(
    session_id="session_001",
    user_query="我喜欢编程，擅长Python"
)
state.metadata['user_id'] = 'user_001'

# 执行记忆管理
result = await memory_agent.execute(state)

# 获取分析结果
memory_analysis = result.metadata['memory_analysis']
print(f"质量分数: {memory_analysis['interaction']['quality_score']}")
print(f"新增三元组: {len(memory_analysis['profile_update']['triples'])}")
```

### 获取用户画像

```python
# 获取用户画像
user_profile = memory_agent.get_user_profile('user_001')

# 获取会话历史
session_history = memory_agent.get_session_history('user_001', limit=10)

# 获取学习记录
learning_records = memory_agent.get_learning_records('user_001', limit=20)
```

### 存储统计

```python
# 获取记忆统计信息
stats = memory_agent.get_memory_statistics()
print(f"缓存大小: {stats['cache_size']}")
print(f"实体数量: {stats['entity_count']}")
print(f"三元组数量: {stats['triples_count']}")
```

## 存储结构

### 本地文件存储

数据存储在 `memory_data/` 目录下：

```
memory_data/
├── user_profiles/       # 用户画像
│   ├── user_001.json
│   └── user_002.json
├── session_memory/      # 会话记忆
│   ├── session_xxx_timestamp.json
│   └── ...
└── learning_records/    # 学习记录
    ├── learning_user_001_timestamp.json
    └── ...
```

### 数据格式

#### 用户画像 (user_profile)

```json
{
  "user_id": "user_001",
  "data": {
    "triples": [
      {
        "subject": "用户",
        "predicate": "喜欢",
        "object": "编程",
        "dimension": "interests",
        "confidence": 0.85,
        "timestamp": "2024-01-01T12:00:00"
      }
    ],
    "emotions": [
      {
        "primary_emotion": "positive",
        "confidence": 0.75,
        "timestamp": "2024-01-01T12:00:00"
      }
    ],
    "learning_patterns": [
      {
        "pattern": "visual",
        "score": 3,
        "confidence": 0.6,
        "timestamp": "2024-01-01T12:00:00"
      }
    ]
  },
  "last_updated": "2024-01-01T12:00:00",
  "version": "1.0"
}
```

#### 会话记忆 (session_memory)

```json
{
  "session_id": "session_001",
  "timestamp": "2024-01-01T12:00:00",
  "data": {
    "user_id": "user_001",
    "query": "我想学习机器学习",
    "interaction_analysis": {
      "quality_score": 0.78,
      "engagement_level": 0.85,
      "learning_value": 0.72
    },
    "profile_update": {
      "triples": [...],
      "emotions": {...},
      "learning_patterns": [...]
    }
  },
  "version": "1.0"
}
```

## 配置选项

### 存储配置

```python
from domain.agents.memory_manager import StorageConfig

# 自定义存储配置
config = StorageConfig(
    base_dir=Path("custom_memory_data"),
    user_profiles_dir=Path("custom_memory_data/profiles"),
    session_memory_dir=Path("custom_memory_data/sessions"),
    learning_records_dir=Path("custom_memory_data/records"),
    max_file_age_days=90,  # 数据保留天数
    backup_enabled=True    # 是否启用备份
)

# 使用自定义配置创建Agent
memory_agent = MemoryManagerAgent(config)
```

## 维护操作

### 清理过期数据

```python
# 清理90天前的数据
memory_agent.storage.cleanup_old_data(days=90)

# 获取存储统计
storage_stats = memory_agent.storage.get_storage_statistics()
print(f"用户画像数: {storage_stats['user_profiles_count']}")
print(f"会话记录数: {storage_stats['session_memories_count']}")
print(f"学习记录数: {storage_stats['learning_records_count']}")
print(f"总大小: {storage_stats['total_size_mb']} MB")
```

## 与原有Agent的对比

| 功能 | LearnerAgent | UserProfileAgent | MemoryManagerAgent |
|------|-------------|------------------|-------------------|
| 交互质量分析 | ✓ | ✗ | ✓ (增强) |
| 用户画像提取 | ✗ | ✓ | ✓ |
| 情感分析 | ✗ | ✓ | ✓ |
| 学习模式识别 | ✓ | ✓ | ✓ (统一) |
| 知识缺口识别 | ✓ | ✗ | ✓ |
| 学习反馈生成 | ✓ | ✗ | ✓ (个性化) |
| 三元组知识图谱 | ✗ | ✓ | ✓ |
| 本地文件存储 | ✓ | ✓ | ✓ (优化) |

## 优势

1. **统一接口**: 一个Agent处理所有记忆管理任务
2. **避免重复**: 情感分析和模式识别只执行一次
3. **个性化增强**: 基于用户画像调整学习建议
4. **高效存储**: Repository模式封装，支持缓存
5. **易于扩展**: 清晰的三层架构，易于添加新功能

## 迁移指南

### 从LearnerAgent + UserProfileAgent迁移

```python
# 旧方式
learner_agent = LearnerAgent()
profile_agent = UserProfileAgent()

# 1. 先执行用户画像
state = await profile_agent.execute(state)
# 2. 再执行学习分析
state = await learner_agent.execute(state)

# 新方式 - 一步完成
memory_agent = MemoryManagerAgent()
state = await memory_agent.execute(state)
```

## 测试

运行测试：

```bash
# 运行所有测试
pytest src/tests/test_memory_manager_agent.py -v

# 运行特定测试
pytest src/tests/test_memory_manager_agent.py::TestMemoryManagerAgent::test_interaction_analysis -v
```

## 未来计划

- [ ] 支持数据库存储 (MongoDB/PostgreSQL)
- [ ] 增强的用户画像分析算法
- [ ] 多用户协同学习分析
- [ ] 学习轨迹可视化
- [ ] 自动化的学习路径优化

## 许可证

Copyright © 2024 EduPilot Project

