# EduPilot API 使用示例

## 快速开始

### 1. 启动 API 服务

```bash
# 方法1: 直接运行
python -m src.interfaces.api

# 方法2: 使用 uvicorn
uvicorn src.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000

# 方法3: 使用启动脚本
python -m src.interfaces.api.__main__
```

访问 API 文档：
- Swagger UI: http://localhost:8000/api/agent/v1/docs
- ReDoc: http://localhost:8000/api/agent/v1/redoc

### 2. 健康检查

```bash
curl http://localhost:8000/api/agent/v1/health
```

响应：
```json
{
  "success": true,
  "message": "系统运行正常",
  "status": "healthy",
  "version": "3.0.0",
  "agents_status": {
    "query_analyzer": "healthy",
    "planner": "healthy",
    "executor": "healthy"
  },
  "uptime_seconds": 1234.56
}
```

## 主流程接口使用

### 1. 开始学习会话（推荐）

这是最常用的接口，执行完整的学习工作流。

```bash
curl -X POST http://localhost:8000/api/agent/v1/workflow/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "student_001",
    "query": "什么是大化改新？它对日本历史有什么影响？"
  }'
```

**Python 示例：**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/start",
    json={
        "user_id": "student_001",
        "query": "什么是大化改新？它对日本历史有什么影响？"
    }
)

result = response.json()
print(f"会话ID: {result['session_id']}")
print(f"系统响应: {result['response']}")
print(f"等待用户输入: {result['waiting_for_user']}")

# 如果有苏格拉底问题，显示给用户
if result['waiting_for_user']:
    print(f"引导问题: {result['response']}")
```

**JavaScript 示例：**
```javascript
const response = await fetch('http://localhost:8000/api/agent/v1/workflow/session/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'student_001',
    query: '什么是大化改新？它对日本历史有什么影响？'
  })
});

const result = await response.json();
console.log('会话ID:', result.session_id);
console.log('系统响应:', result.response);

// 检查是否需要用户继续对话
if (result.waiting_for_user) {
  console.log('请回答以下问题:', result.response);
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "学习会话启动成功",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "student_001",
  "query": "什么是大化改新？",
  "response": "大化改新是日本历史上一次重要的政治改革...\n\n💭 你能说说你对'改革'这个概念的理解吗？",
  "workflow_steps": [
    {
      "step_name": "query_analysis",
      "agent_name": "QueryAnalyzer",
      "status": "success",
      "result": {...},
      "duration_ms": 123.45
    },
    {
      "step_name": "planning",
      "agent_name": "Planner",
      "status": "success",
      "result": {...},
      "duration_ms": 234.56
    },
    {
      "step_name": "execution",
      "agent_name": "Executor",
      "status": "success",
      "result": {...},
      "duration_ms": 345.67
    }
  ],
  "analysis": {
    "intent": "concept_explanation",
    "query_type": "concept_explanation",
    "confidence": 0.92
  },
  "plan": {
    "plan_type": "explanation_with_guidance",
    "action_items": [...]
  },
  "execution_summary": {
    "actions_completed": ["knowledge_retrieval", "response_generation", "socratic_guidance"],
    "knowledge_retrieved": true,
    "socratic_question_generated": true
  },
  "next_suggestions": [
    "你可以询问大化改新的具体内容",
    "你可以了解大化改新的历史背景",
    "你可以探讨大化改新的深远影响"
  ],
  "workflow_complete": false,
  "waiting_for_user": true,
  "conversation_stage": "socratic_dialogue",
  "understanding_level": "basic_understanding",
  "conversation_round": 1
}
```

### 2. 继续学习会话

当用户回答了苏格拉底问题后，使用此接口继续对话。

```bash
curl -X POST http://localhost:8000/api/agent/v1/workflow/session/continue \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "student_001",
    "user_response": "改革就是改变旧的制度，建立新的制度。"
  }'
```

**Python 示例：**
```python
response = requests.post(
    "http://localhost:8000/api/agent/v1/workflow/session/continue",
    json={
        "session_id": session_id,  # 从上一步获得
        "user_id": "student_001",
        "user_response": "改革就是改变旧的制度，建立新的制度。"
    }
)

result = response.json()
print(f"系统响应: {result['response']}")
print(f"对话完成: {result['workflow_complete']}")
```

### 3. 获取会话信息

查询当前会话的状态和历史。

```bash
curl http://localhost:8000/api/agent/v1/workflow/session/550e8400-e29b-41d4-a716-446655440000
```

**带完整状态查询：**
```bash
curl "http://localhost:8000/api/agent/v1/workflow/session/550e8400-e29b-41d4-a716-446655440000?include_state=true"
```

**响应示例：**
```json
{
  "success": true,
  "message": "会话信息获取成功",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "student_001",
    "started_at": "2024-01-01T10:00:00",
    "last_activity": "2024-01-01T10:05:00",
    "interaction_count": 3,
    "current_stage": "socratic_dialogue",
    "understanding_level": "good_understanding",
    "workflow_complete": false,
    "waiting_for_user": true,
    "next_step": "wait_for_user",
    "current_node": "executor"
  }
}
```

### 4. 结束会话

```bash
curl -X DELETE http://localhost:8000/api/agent/v1/workflow/session/550e8400-e29b-41d4-a716-446655440000
```

### 5. 获取活跃会话列表

```bash
curl http://localhost:8000/api/agent/v1/workflow/sessions/active
```

## 工具接口使用

### 记忆管理接口

#### 1. 获取用户画像

```bash
curl http://localhost:8000/api/agent/v1/memory/profile/student_001
```

**带扩展信息：**
```bash
curl "http://localhost:8000/api/agent/v1/memory/profile/student_001?include_triples=true&include_emotions=true&include_patterns=true"
```

#### 2. 获取学习记录

```bash
curl "http://localhost:8000/api/agent/v1/memory/learning-records/student_001?limit=10&offset=0"
```

#### 3. 获取知识图谱

```bash
curl http://localhost:8000/api/agent/v1/memory/knowledge-graph/student_001
```

**响应示例：**
```json
{
  "success": true,
  "message": "知识图谱获取成功",
  "data": {
    "user_id": "student_001",
    "graph": {
      "nodes": [
        {"id": "大化改新", "label": "大化改新", "type": "concept"},
        {"id": "律令制", "label": "律令制", "type": "concept"}
      ],
      "edges": [
        {
          "source": "大化改新",
          "target": "律令制",
          "relation": "建立了",
          "confidence": 0.95
        }
      ]
    },
    "statistics": {
      "total_nodes": 45,
      "total_edges": 67,
      "total_triples": 89
    }
  }
}
```

### 知识检索接口

#### 1. 检索知识

```bash
curl -X POST http://localhost:8000/api/agent/v1/knowledge/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "大化改新",
    "top_k": 5,
    "retrieval_strategy": "hybrid"
  }'
```

#### 2. 获取概念详情

```bash
curl http://localhost:8000/api/agent/v1/knowledge/concept/大化改新
```

#### 3. 获取相关概念

```bash
curl "http://localhost:8000/api/agent/v1/knowledge/related/大化改新?limit=10"
```

#### 4. 获取知识库列表

```bash
curl http://localhost:8000/api/agent/v1/knowledge/bases
```

#### 5. 搜索建议

```bash
curl "http://localhost:8000/api/agent/v1/knowledge/suggestions?query=大化&limit=5"
```

## 调试接口使用

⚠️ **这些接口仅用于开发和测试，生产环境请使用 workflow 接口。**

### 1. 测试查询分析器

```bash
curl -X POST http://localhost:8000/api/agent/v1/agents/query-analyzer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "query": "什么是大化改新？",
    "use_llm_refinement": true
  }'
```

### 2. 测试规划器

```bash
curl -X POST http://localhost:8000/api/agent/v1/agents/planner \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "query": "什么是大化改新？",
    "query_type": "concept_explanation",
    "retrieved_knowledge": {...}
  }'
```

### 3. 测试执行器

```bash
curl -X POST http://localhost:8000/api/agent/v1/agents/executor \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "query": "什么是大化改新？",
    "plan": {...},
    "retrieved_knowledge": {...}
  }'
```

### 4. 测试苏格拉底引导

```bash
curl -X POST http://localhost:8000/api/agent/v1/agents/socratic-guide \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "user_query": "什么是大化改新？",
    "user_response": "是日本的一次改革",
    "guidance_level": "moderate"
  }'
```

## 完整使用流程示例

### Python 完整示例

```python
import requests
import time

# API 基础 URL
BASE_URL = "http://localhost:8000/api/agent/v1"

class EduPilotClient:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session_id = None
    
    def start_learning(self, query: str):
        """开始学习会话"""
        response = requests.post(
            f"{BASE_URL}/workflow/session/start",
            json={
                "user_id": self.user_id,
                "query": query
            }
        )
        result = response.json()
        self.session_id = result["session_id"]
        return result
    
    def continue_learning(self, user_response: str):
        """继续学习会话"""
        response = requests.post(
            f"{BASE_URL}/workflow/session/continue",
            json={
                "session_id": self.session_id,
                "user_id": self.user_id,
                "user_response": user_response
            }
        )
        return response.json()
    
    def get_user_profile(self):
        """获取用户画像"""
        response = requests.get(f"{BASE_URL}/memory/profile/{self.user_id}")
        return response.json()
    
    def get_knowledge_graph(self):
        """获取知识图谱"""
        response = requests.get(f"{BASE_URL}/memory/knowledge-graph/{self.user_id}")
        return response.json()
    
    def search_concept(self, concept_name: str):
        """搜索概念"""
        response = requests.get(f"{BASE_URL}/knowledge/concept/{concept_name}")
        return response.json()


# 使用示例
def main():
    client = EduPilotClient(user_id="student_001")
    
    # 1. 开始学习
    print("=" * 50)
    print("开始学习会话")
    print("=" * 50)
    
    result = client.start_learning("什么是大化改新？")
    print(f"会话ID: {result['session_id']}")
    print(f"\n系统响应:\n{result['response']}")
    
    # 2. 如果需要继续对话
    if result['waiting_for_user']:
        print("\n" + "=" * 50)
        print("继续对话")
        print("=" * 50)
        
        # 模拟用户回答
        user_answer = "改革就是改变旧的制度，建立新的制度。"
        print(f"用户回答: {user_answer}")
        
        result = client.continue_learning(user_answer)
        print(f"\n系统响应:\n{result['response']}")
    
    # 3. 查看用户画像
    print("\n" + "=" * 50)
    print("查看用户画像")
    print("=" * 50)
    
    profile = client.get_user_profile()
    print(f"总交互次数: {profile['statistics']['total_interactions']}")
    print(f"平均质量分数: {profile['statistics']['average_quality']}")
    
    # 4. 查看知识图谱
    print("\n" + "=" * 50)
    print("查看知识图谱")
    print("=" * 50)
    
    graph = client.get_knowledge_graph()
    stats = graph['data']['statistics']
    print(f"概念节点数: {stats['total_nodes']}")
    print(f"关系边数: {stats['total_edges']}")


if __name__ == "__main__":
    main()
```

### JavaScript/TypeScript 完整示例

```typescript
class EduPilotClient {
  private baseUrl = 'http://localhost:8000/api/agent/v1';
  private userId: string;
  private sessionId: string | null = null;

  constructor(userId: string) {
    this.userId = userId;
  }

  async startLearning(query: string) {
    const response = await fetch(`${this.baseUrl}/workflow/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: this.userId,
        query: query
      })
    });
    
    const result = await response.json();
    this.sessionId = result.session_id;
    return result;
  }

  async continueLearning(userResponse: string) {
    const response = await fetch(`${this.baseUrl}/workflow/session/continue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: this.sessionId,
        user_id: this.userId,
        user_response: userResponse
      })
    });
    
    return await response.json();
  }

  async getUserProfile() {
    const response = await fetch(`${this.baseUrl}/memory/profile/${this.userId}`);
    return await response.json();
  }

  async getKnowledgeGraph() {
    const response = await fetch(`${this.baseUrl}/memory/knowledge-graph/${this.userId}`);
    return await response.json();
  }
}

// 使用示例
async function main() {
  const client = new EduPilotClient('student_001');
  
  // 开始学习
  const result = await client.startLearning('什么是大化改新？');
  console.log('会话ID:', result.session_id);
  console.log('系统响应:', result.response);
  
  // 如果需要继续对话
  if (result.waiting_for_user) {
    const continueResult = await client.continueLearning('改革就是改变旧的制度');
    console.log('继续响应:', continueResult.response);
  }
}

main();
```

## 错误处理

### 标准错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "error_detail": {
    "details": "详细错误信息"
  },
  "timestamp": "2024-01-01T10:00:00"
}
```

### 常见错误代码

- `VALIDATION_ERROR`: 请求参数验证失败
- `INTERNAL_ERROR`: 服务器内部错误
- `NOT_FOUND`: 资源不存在
- `PERMISSION_DENIED`: 权限不足
- `AUTHENTICATION_REQUIRED`: 需要身份认证
- `RATE_LIMIT_EXCEEDED`: 请求频率超限

### Python 错误处理示例

```python
try:
    response = requests.post(
        f"{BASE_URL}/workflow/session/start",
        json={"user_id": "student_001", "query": "什么是大化改新？"}
    )
    response.raise_for_status()  # 检查 HTTP 状态码
    result = response.json()
    
    if not result.get("success"):
        print(f"请求失败: {result.get('message')}")
        print(f"错误代码: {result.get('error_code')}")
    else:
        print(f"请求成功: {result}")
        
except requests.exceptions.HTTPError as e:
    print(f"HTTP 错误: {e}")
except requests.exceptions.RequestException as e:
    print(f"请求异常: {e}")
```

## 性能优化建议

1. **使用连接池**
```python
import requests
session = requests.Session()
# 复用 session 对象进行多次请求
response = session.post(url, json=data)
```

2. **启用响应缓存**
   - API 已内置缓存机制
   - 相同请求会直接返回缓存结果

3. **并发请求**
```python
import asyncio
import aiohttp

async def fetch_multiple():
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.get(f"{BASE_URL}/knowledge/concept/大化改新"),
            session.get(f"{BASE_URL}/knowledge/concept/律令制"),
        ]
        results = await asyncio.gather(*tasks)
        return results
```

4. **请求超时设置**
```python
response = requests.post(url, json=data, timeout=30)
```

## 监控和统计

### 获取系统统计

```bash
curl http://localhost:8000/api/agent/v1/stats
```

### 获取性能统计

```bash
curl http://localhost:8000/api/agent/v1/stats/performance
```

### 获取缓存统计

```bash
curl http://localhost:8000/api/agent/v1/stats/cache
```

### 清空缓存

```bash
curl -X POST http://localhost:8000/api/agent/v1/cache/clear
```

## 总结

### 推荐的使用模式

1. ✅ **生产环境**: 使用 `/workflow/` 接口
2. 📊 **数据查询**: 使用 `/memory/` 和 `/knowledge/` 接口
3. 🔧 **调试测试**: 使用 `/agents/` 接口（需要开发者权限）

### 最佳实践

- 优先使用 workflow 接口进行完整的学习会话
- 使用会话管理来维护对话状态
- 合理利用工具接口进行数据查询和分析
- 实现适当的错误处理和重试机制
- 监控 API 性能和使用统计

