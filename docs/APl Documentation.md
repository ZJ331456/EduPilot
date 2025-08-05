# 多智能体学习助手 API 文档

## 概述

多智能体学习助手是一个基于图谱知识库的智能学习系统，提供苏格拉底式教学和个性化学习体验。本文档详细说明了后端API的使用方法，帮助前端开发者快速集成和开发。

### 基础信息

- **服务名称**: 多智能体学习助手 API
- **版本**: 2.0.0
- **基础URL**: `http://localhost:8000`
- **API前缀**: `/api/multi-agent`
- **文档地址**: `/docs` (Swagger UI)
- **健康检查**: `/health`

### 认证方式

当前版本不需要认证，所有API都是公开访问的。

## 根路径API端点

### 1. 服务信息

#### GET `/`

获取服务基本信息和可用端点。

**响应格式**:
```json
{
  "service": "多智能体学习助手 API",
  "version": "2.0.0",
  "description": "基于图谱知识库的智能学习系统后端API",
  "status": "running",
  "endpoints": {
    "api_docs": "/docs",
    "api_redoc": "/redoc",
    "api_spec": "/openapi.json",
    "multi_agent": "/api/multi-agent",
    "health": "/health"
  },
  "message": "这是一个纯后端API服务，前端请通过其他方式访问"
}
```

**前端调用示例**:
```javascript
async function getServiceInfo() {
  try {
    const response = await fetch('/');
    const data = await response.json();
    console.log('服务信息:', data);
    return data;
  } catch (error) {
    console.error('获取服务信息失败:', error);
  }
}
```

### 2. API信息

#### GET `/api`

获取API详细信息。

**响应格式**:
```json
{
  "name": "多智能体学习助手 API",
  "version": "2.0.0",
  "description": "基于图谱知识库的智能学习系统",
  "endpoints": {
    "docs": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
    "multi_agent": "/api/multi-agent"
  }
}
```

**前端调用示例**:
```javascript
async function getAPIInfo() {
  try {
    const response = await fetch('/api');
    const data = await response.json();
    console.log('API信息:', data);
    return data;
  } catch (error) {
    console.error('获取API信息失败:', error);
  }
}
```

### 3. 基础健康检查

#### GET `/health`

基础健康检查端点。

**响应格式**:
```json
{
  "status": "healthy",
  "timestamp": 1704067200.0,
  "service": "多智能体学习助手"
}
```

**前端调用示例**:
```javascript
async function checkBasicHealth() {
  try {
    const response = await fetch('/health');
    const data = await response.json();
    console.log('基础健康状态:', data.status);
    return data;
  } catch (error) {
    console.error('基础健康检查失败:', error);
  }
}
```

## 核心API端点

### 4. 增强版查询处理

#### POST `/api/multi-agent/enhanced-query`

处理用户查询，返回智能体系统的完整响应。

**请求格式**:
```json
{
  "query": "string",                    // 用户查询内容
  "session_id": "string",              // 会话ID（可选）
  "user_id": "string",                 // 用户ID（可选）
  "user_context": {                    // 用户上下文（可选）
    "user_summary": "string",
    "user_entities": ["string"],
    "entity_count": 0,
    "relation_count": 0
  },
  "config": {                          // 查询配置（可选）
    "max_iterations": 5,
    "timeout_seconds": 300,
    "enable_learning": true,
    "enable_socratic": true
  },
  "force_mode": "string"               // 强制模式：normal或socratic（可选）
}
```

**响应格式**:
```json
{
  "success": true,
  "session_id": "session_1234567890",
  "final_response": "智能体的最终回答",
  "query_classification": {
    "query_mode": "normal",
    "confidence": 0.95,
    "detected_topics": ["历史", "文化"],
    "complexity_level": "intermediate"
  },
  "execution_summary": {
    "steps_completed": ["query_interpreter", "knowledge_retriever"],
    "total_steps": 6,
    "execution_time": 2.5,
    "agents_used": ["QueryInterpreterAgent", "KnowledgeRetrieverAgent"]
  },
  "user_profile_context": {
    "user_summary": "用户对历史和文化感兴趣",
    "user_entities": ["古代日本", "文化"],
    "entity_count": 15,
    "relation_count": 8
  },
  "conversation_saved": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "error": null
}
```

**前端调用示例**:
```javascript
async function sendEnhancedQuery(query, sessionId = null) {
  try {
    const response = await fetch('/api/multi-agent/enhanced-query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        session_id: sessionId,
        user_id: 'anonymous',
        user_context: {
          user_summary: '历史爱好者',
          user_entities: ['古代日本', '文化'],
          entity_count: 15,
          relation_count: 8
        },
        config: {
          max_iterations: 5,
          enable_socratic: true
        }
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 处理成功响应
      displayResponse(result.final_response);
      updateWorkflowSteps(result.execution_summary.steps_completed);
      updateUserProfile(result.user_profile_context);
    } else {
      // 处理错误
      showError(result.error);
    }
  } catch (error) {
    console.error('查询失败:', error);
  }
}
```

### 5. 基础查询处理

#### POST `/api/multi-agent/query`

简化版查询处理，返回基本响应。

**请求格式**:
```json
{
  "query": "string",
  "session_id": "string",
  "user_id": "string",
  "user_context": {}
}
```

**响应格式**:
```json
{
  "success": true,
  "session_id": "session_1234567890",
  "final_response": "智能体回答",
  "socratic_question": "启发式问题",
  "steps_completed": ["query_interpreter", "knowledge_retriever"],
  "state_summary": {
    "current_step": "executor",
    "progress": 0.8
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 6. 用户画像管理

#### GET `/api/multi-agent/user-profile`

获取当前用户画像信息。

**响应格式**:
```json
{
  "success": true,
  "user_id": "anonymous",
  "user_profile": {
    "user_id": "anonymous",
    "graph_statistics": {
      "entity_count": 15,
      "relation_count": 8
    },
    "user_context": {
      "user_summary": "历史爱好者，对古代日本文化感兴趣",
      "user_entities": ["古代日本", "文化", "历史"],
      "entity_count": 15,
      "relation_count": 8,
      "triples": [
        {
          "subject": "用户",
          "predicate": "感兴趣",
          "object": "古代日本"
        }
      ]
    },
    "profile_completeness": 0.75
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET `/api/multi-agent/user-profile/{user_id}`

获取指定用户的画像信息。

**路径参数**:
- `user_id`: 用户ID

**响应格式**: 同上

#### GET `/api/multi-agent/user-profile-graph`

获取用户画像图谱数据（用于图表展示）。

**响应格式**:
```json
{
  "success": true,
  "graph": {
    "nodes": [
      {
        "id": "古代日本",
        "label": "古代日本",
        "type": "entity",
        "size": 20
      }
    ],
    "edges": [
      {
        "source": "用户",
        "target": "古代日本",
        "label": "感兴趣",
        "type": "relation"
      }
    ]
  },
  "statistics": {
    "node_count": 15,
    "edge_count": 8
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**前端调用示例**:
```javascript
async function loadUserProfileGraph() {
  try {
    const response = await fetch('/api/multi-agent/user-profile-graph');
    const data = await response.json();
    
    if (data.success) {
      // 使用图表库渲染图谱
      renderGraph(data.graph.nodes, data.graph.edges);
      updateStatistics(data.statistics);
    }
  } catch (error) {
    console.error('加载用户画像图谱失败:', error);
  }
}
```

#### POST `/api/multi-agent/clear-user-profile`

清空用户画像数据。

**请求格式**:
```json
{
  "user_id": "string"
}
```

**响应格式**:
```json
{
  "success": true,
  "user_id": "anonymous",
  "message": "用户画像已清空",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 7. 会话管理

#### GET `/api/multi-agent/user-sessions/{user_id}`

获取用户会话历史。

**路径参数**:
- `user_id`: 用户ID

**查询参数**:
- `limit`: 返回数量限制（默认10）

**响应格式**:
```json
{
  "success": true,
  "user_id": "anonymous",
  "sessions": [
    {
      "session_id": "session_1234567890",
      "start_time": "2024-01-01T10:00:00Z",
      "end_time": "2024-01-01T11:00:00Z",
      "total_turns": 5,
      "topics": ["历史", "文化"]
    }
  ],
  "total": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET `/api/multi-agent/session-history/{session_id}`

获取会话详细历史。

**路径参数**:
- `session_id`: 会话ID

**响应格式**:
```json
{
  "success": true,
  "session": {
    "session_id": "session_1234567890",
    "user_id": "anonymous",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T11:00:00Z",
    "turns": [
      {
        "turn_id": "turn_1",
        "timestamp": "2024-01-01T10:00:00Z",
        "user_input": "什么是古代日本文化？",
        "system_response": "古代日本文化包括...",
        "metadata": {
          "query_classification": {},
          "execution_summary": {}
        }
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET `/api/multi-agent/session/{session_id}`

获取会话基本信息。

**路径参数**:
- `session_id`: 会话ID

**响应格式**:
```json
{
  "exists": true,
  "session_id": "session_1234567890",
  "status": "active",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 8. 系统状态和监控

#### GET `/api/multi-agent/health`

系统健康检查。

**响应格式**:
```json
{
  "status": "healthy",
  "components": {
    "mongodb": "connected",
    "multi_agent_system": "available"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "多智能体学习助手"
}
```

#### GET `/api/multi-agent/health-enhanced`

增强版健康检查。

**响应格式**:
```json
{
  "status": "healthy",
  "components": {
    "mongodb": "connected",
    "multi_agent_system": "available"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "增强版多智能体学习助手"
}
```

#### GET `/api/multi-agent/stats`

获取系统统计信息。

**响应格式**:
```json
{
  "success_rate": 0.95,
  "total_queries": 1000,
  "active_sessions": 5,
  "system_uptime": 86400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 9. 测试和调试

#### POST `/api/multi-agent/test-classification`

测试查询分类功能。

**请求格式**:
```json
{
  "query": "string"
}
```

**响应格式**:
```json
{
  "success": true,
  "query": "什么是古代日本文化？",
  "classification": {
    "query_mode": "knowledge_query",
    "confidence": 0.9,
    "detected_topics": ["历史", "文化"],
    "complexity_level": "intermediate"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 存储管理API

### 10. 数据清理

#### POST `/api/multi-agent/storage/cleanup`

清理旧数据。

**请求格式**:
```json
{
  "days": 30
}
```

**响应格式**:
```json
{
  "success": true,
  "message": "已清理 30 天前的数据",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 11. 存储统计

#### GET `/api/multi-agent/storage/stats`

获取存储统计信息。

**响应格式**:
```json
{
  "success": true,
  "stats": {
    "total_sessions": 100,
    "total_conversations": 500,
    "total_users": 20,
    "storage_size": "50MB",
    "last_backup": "2024-01-01T10:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 12. 数据导出

#### POST `/api/multi-agent/storage/export-user-data/{user_id}`

导出用户数据。

**路径参数**:
- `user_id`: 用户ID

**响应格式**:
```json
{
  "success": true,
  "user_id": "anonymous",
  "export_data": {
    "profile": {},
    "sessions": [],
    "conversations": []
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 13. 数据备份

#### POST `/api/multi-agent/storage/backup`

备份所有数据。

**响应格式**:
```json
{
  "success": true,
  "backup_path": "/data/backups/backup_20240101_120000",
  "message": "数据备份完成",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### POST `/api/multi-agent/storage/restore`

从备份恢复数据。

**请求格式**:
```json
{
  "backup_dir": "/data/backups/backup_20240101_120000"
}
```

**响应格式**:
```json
{
  "success": true,
  "backup_dir": "/data/backups/backup_20240101_120000",
  "message": "数据恢复完成",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 14. 存储健康检查

#### GET `/api/multi-agent/storage/health`

存储系统健康检查。

**响应格式**:
```json
{
  "status": "healthy",
  "components": {
    "mongodb": "connected",
    "local_storage": "ok",
    "storage_manager": "initialized"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "存储管理系统"
}
```

### 6. 用户会话历史（存储管理）

#### GET `/api/multi-agent/storage/user-sessions/{user_id}`

获取指定用户的会话历史记录。

**路径参数**:
- `user_id`: 用户ID

**查询参数**:
- `limit`: 返回记录数量限制（默认10）

**响应格式**:
```json
{
  "success": true,
  "user_id": "user_123",
  "sessions": [
    {
      "session_id": "session_1234567890",
      "user_id": "user_123",
      "created_at": "2024-01-01T12:00:00Z",
      "last_activity": "2024-01-01T12:30:00Z",
      "turn_count": 5,
      "status": "active"
    }
  ],
  "total_count": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**前端调用示例**:
```javascript
async function getUserSessionHistory(userId, limit = 10) {
  try {
    const response = await fetch(`/api/multi-agent/storage/user-sessions/${userId}?limit=${limit}`);
    const data = await response.json();
    return data.sessions;
  } catch (error) {
    console.error('获取用户会话历史失败:', error);
  }
}
```

### 7. 会话详细信息（存储管理）

#### GET `/api/multi-agent/storage/session/{session_id}`

获取指定会话的详细信息。

**路径参数**:
- `session_id`: 会话ID

**响应格式**:
```json
{
  "success": true,
  "session_id": "session_1234567890",
  "session_data": {
    "session_id": "session_1234567890",
    "user_id": "user_123",
    "created_at": "2024-01-01T12:00:00Z",
    "last_activity": "2024-01-01T12:30:00Z",
    "turns": [
      {
        "turn_id": "turn_1",
        "timestamp": "2024-01-01T12:00:00Z",
        "user_input": "什么是古代日本文化？",
        "system_response": "古代日本文化包括...",
        "metadata": {
          "query_classification": {
            "query_mode": "normal",
            "confidence": 0.95
          },
          "execution_time": 2.5
        }
      }
    ],
    "status": "active"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**前端调用示例**:
```javascript
async function getSessionDetails(sessionId) {
  try {
    const response = await fetch(`/api/multi-agent/storage/session/${sessionId}`);
    const data = await response.json();
    return data.session_data;
  } catch (error) {
    console.error('获取会话详情失败:', error);
  }
}
```

### 8. 清空用户数据

#### DELETE `/api/multi-agent/storage/clear-user-data/{user_id}`

清空指定用户的所有数据，包括用户画像、会话记录等。

**路径参数**:
- `user_id`: 用户ID

**响应格式**:
```json
{
  "success": true,
  "user_id": "user_123",
  "message": "用户数据已清空",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**前端调用示例**:
```javascript
async function clearUserData(userId) {
  try {
    const response = await fetch(`/api/multi-agent/storage/clear-user-data/${userId}`, {
      method: 'DELETE'
    });
    const data = await response.json();
    console.log('用户数据清空结果:', data.message);
    return data;
  } catch (error) {
    console.error('清空用户数据失败:', error);
  }
}
```

## 前端集成指南

### 15. 基础设置

```javascript
class MultiAgentAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.apiPrefix = '/api/multi-agent';
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${this.apiPrefix}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const finalOptions = { ...defaultOptions, ...options };
    
    try {
      const response = await fetch(url, finalOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }
}
```

### 16. 查询处理

```javascript
class QueryHandler {
  constructor(api) {
    this.api = api;
    this.currentSessionId = null;
  }

  async sendQuery(query, options = {}) {
    const requestData = {
      query: query,
      session_id: this.currentSessionId,
      user_id: options.userId || 'anonymous',
      user_context: options.userContext || {},
      config: options.config || {},
      force_mode: options.forceMode || null
    };

    try {
      const response = await this.api.makeRequest('/enhanced-query', {
        method: 'POST',
        body: JSON.stringify(requestData)
      });

      if (response.success) {
        this.currentSessionId = response.session_id;
        return response;
      } else {
        throw new Error(response.error || '查询处理失败');
      }
    } catch (error) {
      console.error('发送查询失败:', error);
      throw error;
    }
  }

  async sendSimpleQuery(query, sessionId = null) {
    const requestData = {
      query: query,
      session_id: sessionId || this.currentSessionId
    };

    try {
      const response = await this.api.makeRequest('/query', {
        method: 'POST',
        body: JSON.stringify(requestData)
      });

      if (response.success) {
        this.currentSessionId = response.session_id;
        return response;
      } else {
        throw new Error(response.error || '查询处理失败');
      }
    } catch (error) {
      console.error('发送简单查询失败:', error);
      throw error;
    }
  }
}

### 17. 用户画像管理

```javascript
class UserProfileManager {
  constructor(api) {
    this.api = api;
  }

  async getUserProfile(userId = null) {
    try {
      const endpoint = userId ? `/user-profile/${userId}` : '/user-profile';
      const response = await this.api.makeRequest(endpoint);
      
      if (response.success) {
        return response.user_profile;
      } else {
        throw new Error('获取用户画像失败');
      }
    } catch (error) {
      console.error('获取用户画像失败:', error);
      throw error;
    }
  }

  async getUserProfileGraph() {
    try {
      const response = await this.api.makeRequest('/user-profile-graph');
      
      if (response.success) {
        return response.graph;
      } else {
        throw new Error('获取用户画像图谱失败');
      }
    } catch (error) {
      console.error('获取用户画像图谱失败:', error);
      throw error;
    }
  }

  async clearUserProfile(userId = 'anonymous') {
    try {
      const response = await this.api.makeRequest('/clear-user-profile', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
      });
      
      if (response.success) {
        return response;
      } else {
        throw new Error('清空用户画像失败');
      }
    } catch (error) {
      console.error('清空用户画像失败:', error);
      throw error;
    }
  }
}
```

### 18. 会话管理

```javascript
class SessionManager {
  constructor(api) {
    this.api = api;
  }

  async getUserSessions(userId, limit = 10) {
    try {
      const response = await this.api.makeRequest(`/user-sessions/${userId}?limit=${limit}`);
      
      if (response.success) {
        return response.sessions;
      } else {
        throw new Error('获取用户会话失败');
      }
    } catch (error) {
      console.error('获取用户会话失败:', error);
      throw error;
    }
  }

  async getSessionHistory(sessionId) {
    try {
      const response = await this.api.makeRequest(`/session-history/${sessionId}`);
      
      if (response.success) {
        return response.session;
      } else {
        throw new Error('获取会话历史失败');
      }
    } catch (error) {
      console.error('获取会话历史失败:', error);
      throw error;
    }
  }

  async getSessionInfo(sessionId) {
    try {
      const response = await this.api.makeRequest(`/session/${sessionId}`);
      return response;
    } catch (error) {
      console.error('获取会话信息失败:', error);
      throw error;
    }
  }
}
```

### 19. 系统监控

```javascript
class SystemMonitor {
  constructor(api) {
    this.api = api;
  }

  async checkHealth() {
    try {
      const response = await this.api.makeRequest('/health');
      return response;
    } catch (error) {
      console.error('健康检查失败:', error);
      throw error;
    }
  }

  async getStats() {
    try {
      const response = await this.api.makeRequest('/stats');
      return response;
    } catch (error) {
      console.error('获取统计信息失败:', error);
      throw error;
    }
  }

  async testClassification(query) {
    try {
      const response = await this.api.makeRequest('/test-classification', {
        method: 'POST',
        body: JSON.stringify({ query: query })
      });
      
      if (response.success) {
        return response.classification;
      } else {
        throw new Error('测试分类失败');
      }
    } catch (error) {
      console.error('测试分类失败:', error);
      throw error;
    }
  }
}
```

### 20. 存储管理

```javascript
class StorageManager {
  constructor(api) {
    this.api = api;
  }

  async cleanupOldData(days = 30) {
    try {
      const response = await this.api.makeRequest('/storage/cleanup', {
        method: 'POST',
        body: JSON.stringify({ days: days })
      });
      
      if (response.success) {
        return response;
      } else {
        throw new Error('清理数据失败');
      }
    } catch (error) {
      console.error('清理数据失败:', error);
      throw error;
    }
  }

  async getStorageStats() {
    try {
      const response = await this.api.makeRequest('/storage/stats');
      
      if (response.success) {
        return response.stats;
      } else {
        throw new Error('获取存储统计失败');
      }
    } catch (error) {
      console.error('获取存储统计失败:', error);
      throw error;
    }
  }

  async exportUserData(userId) {
    try {
      const response = await this.api.makeRequest(`/storage/export-user-data/${userId}`, {
        method: 'POST'
      });
      
      if (response.success) {
        return response.export_data;
      } else {
        throw new Error('导出用户数据失败');
      }
    } catch (error) {
      console.error('导出用户数据失败:', error);
      throw error;
    }
  }

  async backupData() {
    try {
      const response = await this.api.makeRequest('/storage/backup', {
        method: 'POST'
      });
      
      if (response.success) {
        return response.backup_path;
      } else {
        throw new Error('数据备份失败');
      }
    } catch (error) {
      console.error('数据备份失败:', error);
      throw error;
    }
  }

  async restoreData(backupDir) {
    try {
      const response = await this.api.makeRequest('/storage/restore', {
        method: 'POST',
        body: JSON.stringify({ backup_dir: backupDir })
      });
      
      if (response.success) {
        return response;
      } else {
        throw new Error('数据恢复失败');
      }
    } catch (error) {
      console.error('数据恢复失败:', error);
      throw error;
    }
  }

  async getUserSessionHistory(userId, limit = 10) {
    try {
      const response = await this.api.makeRequest(`/storage/user-sessions/${userId}?limit=${limit}`);
      
      if (response.success) {
        return response.sessions;
      } else {
        throw new Error('获取用户会话历史失败');
      }
    } catch (error) {
      console.error('获取用户会话历史失败:', error);
      throw error;
    }
  }

  async getSessionDetails(sessionId) {
    try {
      const response = await this.api.makeRequest(`/storage/session/${sessionId}`);
      
      if (response.success) {
        return response.session_data;
      } else {
        throw new Error('获取会话详情失败');
      }
    } catch (error) {
      console.error('获取会话详情失败:', error);
      throw error;
    }
  }

  async clearUserData(userId) {
    try {
      const response = await this.api.makeRequest(`/storage/clear-user-data/${userId}`, {
        method: 'DELETE'
      });
      
      if (response.success) {
        return response;
      } else {
        throw new Error('清空用户数据失败');
      }
    } catch (error) {
      console.error('清空用户数据失败:', error);
      throw error;
    }
  }

  async checkStorageHealth() {
    try {
      const response = await this.api.makeRequest('/storage/health');
      return response;
    } catch (error) {
      console.error('存储健康检查失败:', error);
      throw error;
    }
  }
}
```

## 完整的前端集成示例

### 21. 主应用类

```javascript
class MultiAgentLearningApp {
  constructor(baseURL = 'http://localhost:8000') {
    // 初始化API客户端
    this.api = new MultiAgentAPI(baseURL);
    
    // 初始化各个管理器
    this.queryHandler = new QueryHandler(this.api);
    this.profileManager = new UserProfileManager(this.api);
    this.sessionManager = new SessionManager(this.api);
    this.systemMonitor = new SystemMonitor(this.api);
    this.storageManager = new StorageManager(this.api);
    
    // 应用状态
    this.currentUser = 'anonymous';
    this.currentSession = null;
    this.isProcessing = false;
    
    // 初始化应用
    this.init();
  }

  async init() {
    try {
      // 检查系统健康状态
      const health = await this.systemMonitor.checkHealth();
      console.log('系统状态:', health);
      
      // 加载用户画像
      await this.loadUserProfile();
      
      // 设置定期健康检查
      this.startHealthCheck();
      
    } catch (error) {
      console.error('应用初始化失败:', error);
      this.showError('系统初始化失败，请刷新页面重试');
    }
  }

  async loadUserProfile() {
    try {
      const profile = await this.profileManager.getUserProfile(this.currentUser);
      this.updateProfileDisplay(profile);
    } catch (error) {
      console.error('加载用户画像失败:', error);
    }
  }

  async sendMessage(message, options = {}) {
    if (this.isProcessing) {
      this.showWarning('正在处理中，请稍候...');
      return;
    }

    this.isProcessing = true;
    this.updateProcessingStatus(true);

    try {
      // 发送查询
      const response = await this.queryHandler.sendQuery(message, {
        userId: this.currentUser,
        userContext: this.getCurrentUserContext(),
        config: options.config || {},
        forceMode: options.forceMode || null
      });

      // 处理响应
      this.handleQueryResponse(response);
      
      // 更新用户画像
      if (response.user_profile_context) {
        this.updateUserProfile(response.user_profile_context);
      }

    } catch (error) {
      console.error('发送消息失败:', error);
      this.showError('发送消息失败: ' + error.message);
    } finally {
      this.isProcessing = false;
      this.updateProcessingStatus(false);
    }
  }

  handleQueryResponse(response) {
    // 显示最终回答
    if (response.final_response) {
      this.displayMessage(response.final_response, 'assistant');
    }

    // 显示苏格拉底问题
    if (response.socratic_question) {
      this.displaySocraticQuestion(response.socratic_question);
    }

    // 更新工作流程状态
    if (response.execution_summary) {
      this.updateWorkflowSteps(response.execution_summary.steps_completed);
    }

    // 更新会话信息
    if (response.session_id) {
      this.currentSession = response.session_id;
      this.updateSessionDisplay();
    }
  }

  displayMessage(content, type) {
    const messageContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = this.formatMessageContent(content);
    messageContainer.appendChild(messageDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  displaySocraticQuestion(questionData) {
    const messageContainer = document.getElementById('chatMessages');
    const questionDiv = document.createElement('div');
    questionDiv.className = 'message assistant socratic';
    
    let questionText = '';
    let purposeText = '';
    
    if (typeof questionData === 'string') {
      questionText = questionData;
    } else if (questionData && typeof questionData === 'object') {
      questionText = questionData.question || questionData.content || '请思考这个问题';
      purposeText = questionData.purpose || questionData.hint || '';
    }
    
    questionDiv.innerHTML = `
      <div class="socratic-question">
        <div class="question-icon">🤔</div>
        <div class="question-content">
          <div class="question-text">${questionText}</div>
          ${purposeText ? `<div class="question-purpose">💡 ${purposeText}</div>` : ''}
        </div>
      </div>
    `;
    
    messageContainer.appendChild(questionDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  formatMessageContent(content) {
    // 处理Markdown格式
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    content = content.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // 处理换行
    content = content.replace(/\n/g, '<br>');
    
    return content;
  }

  updateWorkflowSteps(completedSteps) {
    const steps = document.querySelectorAll('.workflow-step');
    steps.forEach(step => {
      const stepName = step.dataset.step;
      if (completedSteps.includes(stepName)) {
        step.classList.add('completed');
      } else {
        step.classList.remove('completed');
      }
    });
  }

  updateProfileDisplay(profile) {
    const entityCountElement = document.getElementById('profileEntityCount');
    const relationCountElement = document.getElementById('profileRelationCount');
    const summaryElement = document.getElementById('profileSummary');
    
    if (entityCountElement) {
      entityCountElement.textContent = profile.graph_statistics.entity_count;
    }
    
    if (relationCountElement) {
      relationCountElement.textContent = profile.graph_statistics.relation_count;
    }
    
    if (summaryElement) {
      summaryElement.innerHTML = `
        <div class="profile-summary-content">
          ${profile.user_context.user_summary || '暂无用户画像信息'}
        </div>
      `;
    }
  }

  updateProcessingStatus(processing) {
    const statusElement = document.getElementById('processingStatus');
    const sendButton = document.getElementById('sendButton');
    
    if (statusElement) {
      statusElement.textContent = processing ? '处理中...' : '空闲';
    }
    
    if (sendButton) {
      sendButton.disabled = processing;
      sendButton.textContent = processing ? '处理中...' : '发送';
    }
  }

  updateSessionDisplay() {
    const sessionElement = document.getElementById('sessionId');
    if (sessionElement && this.currentSession) {
      sessionElement.textContent = this.currentSession.substring(0, 8) + '...';
    }
  }

  getCurrentUserContext() {
    // 返回当前用户上下文信息
    return {
      user_summary: '当前用户',
      user_entities: [],
      entity_count: 0,
      relation_count: 0
    };
  }

  startHealthCheck() {
    setInterval(async () => {
      try {
        const health = await this.systemMonitor.checkHealth();
        this.updateConnectionStatus(health.status === 'healthy' ? '在线' : '异常');
      } catch (error) {
        this.updateConnectionStatus('离线');
      }
    }, 30000); // 每30秒检查一次
  }

  updateConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
      const type = status === '在线' ? 'online' : 'offline';
      statusElement.innerHTML = `${status} <span class="status-indicator ${type}"></span>`;
    }
  }

  showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;
    
    container.appendChild(notification);
    
    // 自动移除通知
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 5000);
  }

  showError(message) {
    this.showNotification(message, 'error');
  }

  showWarning(message) {
    this.showNotification(message, 'warning');
  }

  showSuccess(message) {
    this.showNotification(message, 'success');
  }
}
```

### 22. 使用示例

```javascript
// 初始化应用
const app = new MultiAgentLearningApp('http://localhost:8000');

// 发送消息
async function sendMessage() {
  const input = document.getElementById('messageInput');
  const message = input.value.trim();
  
  if (!message) return;
  
  // 清空输入框
  input.value = '';
  
  // 显示用户消息
  app.displayMessage(message, 'user');
  
  // 发送到后端
  await app.sendMessage(message, {
    config: {
      max_iterations: 5,
      enable_socratic: true
    }
  });
}

// 绑定发送按钮
document.getElementById('sendButton').addEventListener('click', sendMessage);

// 绑定回车键
document.getElementById('messageInput').addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// 清空对话
document.getElementById('clearChatBtn').addEventListener('click', () => {
  const container = document.getElementById('chatMessages');
  container.innerHTML = `
    <div class="message system">
      🎓 对话已清空，请输入您的问题开始新的学习之旅。
    </div>
  `;
});

// 查看用户画像
document.getElementById('viewProfileBtn').addEventListener('click', async () => {
  try {
    const profile = await app.profileManager.getUserProfile();
    app.showUserProfileModal(profile);
  } catch (error) {
    app.showError('获取用户画像失败');
  }
});

// 清空用户画像
document.getElementById('clearProfileBtn').addEventListener('click', async () => {
  if (confirm('确定要清空用户画像吗？这将删除所有学习记录。')) {
    try {
      await app.profileManager.clearUserProfile();
      app.showSuccess('用户画像已清空');
      await app.loadUserProfile();
    } catch (error) {
      app.showError('清空用户画像失败');
    }
  }
});
```

## 错误处理和最佳实践

### 23. 错误处理策略

```javascript
class ErrorHandler {
  static handleAPIError(error, context = '') {
    console.error(`API错误 [${context}]:`, error);
    
    let userMessage = '操作失败，请稍后重试';
    
    if (error.message.includes('NetworkError')) {
      userMessage = '网络连接失败，请检查网络设置';
    } else if (error.message.includes('404')) {
      userMessage = '请求的资源不存在';
    } else if (error.message.includes('500')) {
      userMessage = '服务器内部错误，请联系管理员';
    } else if (error.message.includes('timeout')) {
      userMessage = '请求超时，请稍后重试';
    }
    
    return {
      error: error,
      userMessage: userMessage,
      context: context
    };
  }

  static async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        if (i === maxRetries - 1) {
          throw error;
        }
        
        console.warn(`请求失败，${delay}ms后重试 (${i + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2; // 指数退避
      }
    }
  }
}
```

### 24. 数据验证

```javascript
class DataValidator {
  static validateQueryRequest(data) {
    const errors = [];
    
    if (!data.query || typeof data.query !== 'string') {
      errors.push('查询内容不能为空且必须是字符串');
    }
    
    if (data.query && data.query.length > 500) {
      errors.push('查询内容不能超过500个字符');
    }
    
    if (data.session_id && typeof data.session_id !== 'string') {
      errors.push('会话ID必须是字符串');
    }
    
    if (data.user_id && typeof data.user_id !== 'string') {
      errors.push('用户ID必须是字符串');
    }
    
    if (data.config && typeof data.config !== 'object') {
      errors.push('配置必须是对象');
    }
    
    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }

  static validateUserProfile(profile) {
    const errors = [];
    
    if (!profile || typeof profile !== 'object') {
      errors.push('用户画像必须是对象');
      return { isValid: false, errors };
    }
    
    if (!profile.user_id || typeof profile.user_id !== 'string') {
      errors.push('用户ID不能为空且必须是字符串');
    }
    
    if (profile.graph_statistics) {
      const stats = profile.graph_statistics;
             if (typeof stats.entity_count !== 'number' || stats.entity_count < 0) {
         errors.push('实体数量必须是非负整数');
       }
       
       if (typeof stats.relation_count !== 'number' || stats.relation_count < 0) {
         errors.push('关系数量必须是非负整数');
       }
     }
     
     return {
       isValid: errors.length === 0,
       errors: errors
     };
   }
 }
```

### 25. 性能优化

```javascript
class PerformanceOptimizer {
  constructor() {
    this.requestCache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
  }

  async cachedRequest(key, requestFn) {
    const cached = this.requestCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    const data = await requestFn();
    this.requestCache.set(key, {
      data: data,
      timestamp: Date.now()
    });

    return data;
  }

  clearCache() {
    this.requestCache.clear();
  }

  // 防抖函数
  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // 节流函数
  static throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
}
```

### 26. 状态管理

```javascript
class AppStateManager {
  constructor() {
    this.state = {
      user: {
        id: 'anonymous',
        profile: null,
        preferences: {}
      },
      session: {
        id: null,
        isActive: false,
        startTime: null
      },
      system: {
        isOnline: false,
        health: 'unknown',
        stats: null
      },
      ui: {
        isLoading: false,
        currentView: 'chat',
        notifications: []
      }
    };
    
    this.listeners = new Map();
  }

  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    this.listeners.get(key).add(callback);
    
    // 返回取消订阅函数
    return () => {
      const callbacks = this.listeners.get(key);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  setState(path, value) {
    const keys = path.split('.');
    let current = this.state;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in current)) {
        current[keys[i]] = {};
      }
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    
    // 通知监听器
    this.notifyListeners(path, value);
  }

  getState(path) {
    const keys = path.split('.');
    let current = this.state;
    
    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return undefined;
      }
    }
    
    return current;
  }

  notifyListeners(path, value) {
    const callbacks = this.listeners.get(path);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(value, path);
        } catch (error) {
          console.error('状态监听器错误:', error);
        }
      });
    }
  }
}
```

## 数据模型和类型定义

### 27. TypeScript 类型定义

```typescript
// 基础类型定义
interface APIResponse<T = any> {
  success: boolean;
  timestamp: string;
  error?: string;
  data?: T;
}

// 查询相关类型
interface QueryRequest {
  query: string;
  session_id?: string;
  user_id?: string;
  user_context?: UserContext;
  config?: QueryConfig;
  force_mode?: 'normal' | 'socratic';
}

interface QueryResponse {
  success: boolean;
  session_id: string;
  final_response: string;
  query_classification: QueryClassification;
  execution_summary: ExecutionSummary;
  user_profile_context?: UserContext;
  conversation_saved: boolean;
  timestamp: string;
  error?: string;
}

interface QueryClassification {
  query_mode: string;
  confidence: number;
  detected_topics: string[];
  complexity_level: string;
}

interface ExecutionSummary {
  steps_completed: string[];
  total_steps: number;
  execution_time: number;
  agents_used: string[];
}

interface QueryConfig {
  max_iterations?: number;
  timeout_seconds?: number;
  enable_learning?: boolean;
  enable_socratic?: boolean;
  auto_continue?: boolean;
}

// 用户相关类型
interface UserContext {
  user_summary?: string;
  user_entities?: string[];
  entity_count?: number;
  relation_count?: number;
  triples?: Triple[];
}

interface UserProfile {
  user_id: string;
  graph_statistics: GraphStatistics;
  user_context: UserContext;
  profile_completeness: number;
}

interface GraphStatistics {
  entity_count: number;
  relation_count: number;
}

interface Triple {
  subject: string;
  predicate: string;
  object: string;
}

// 会话相关类型
interface Session {
  session_id: string;
  user_id: string;
  start_time: string;
  end_time?: string;
  total_turns: number;
  topics: string[];
}

interface SessionTurn {
  turn_id: string;
  timestamp: string;
  user_input: string;
  system_response: string;
  metadata: {
    query_classification: QueryClassification;
    execution_summary: ExecutionSummary;
  };
}

// 系统状态类型
interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    mongodb: 'connected' | 'disconnected';
    multi_agent_system: 'available' | 'unavailable';
  };
  timestamp: string;
  service: string;
}

interface SystemStats {
  success_rate: number;
  total_queries: number;
  active_sessions: number;
  system_uptime: number;
  timestamp: string;
}

// 存储相关类型
interface StorageStats {
  total_sessions: number;
  total_conversations: number;
  total_users: number;
  storage_size: string;
  last_backup: string;
}

interface ExportData {
  profile: UserProfile;
  sessions: Session[];
  conversations: SessionTurn[];
}
```

### 28. 数据验证模式

```javascript
// 使用 Joi 进行数据验证
const Joi = require('joi');

const schemas = {
  queryRequest: Joi.object({
    query: Joi.string().min(1).max(500).required(),
    session_id: Joi.string().optional(),
    user_id: Joi.string().optional(),
    user_context: Joi.object({
      user_summary: Joi.string().optional(),
      user_entities: Joi.array().items(Joi.string()).optional(),
      entity_count: Joi.number().integer().min(0).optional(),
      relation_count: Joi.number().integer().min(0).optional(),
      triples: Joi.array().items(Joi.object({
        subject: Joi.string().required(),
        predicate: Joi.string().required(),
        object: Joi.string().required()
      })).optional()
    }).optional(),
    config: Joi.object({
      max_iterations: Joi.number().integer().min(1).max(10).optional(),
      timeout_seconds: Joi.number().integer().min(30).max(600).optional(),
      enable_learning: Joi.boolean().optional(),
      enable_socratic: Joi.boolean().optional(),
      auto_continue: Joi.boolean().optional()
    }).optional(),
    force_mode: Joi.string().valid('normal', 'socratic').optional()
  }),

  userProfile: Joi.object({
    user_id: Joi.string().required(),
    graph_statistics: Joi.object({
      entity_count: Joi.number().integer().min(0).required(),
      relation_count: Joi.number().integer().min(0).required()
    }).required(),
    user_context: Joi.object({
      user_summary: Joi.string().optional(),
      user_entities: Joi.array().items(Joi.string()).optional(),
      entity_count: Joi.number().integer().min(0).optional(),
      relation_count: Joi.number().integer().min(0).optional(),
      triples: Joi.array().items(Joi.object({
        subject: Joi.string().required(),
        predicate: Joi.string().required(),
        object: Joi.string().required()
      })).optional()
    }).required(),
    profile_completeness: Joi.number().min(0).max(1).required()
  })
};

class SchemaValidator {
  static validate(data, schemaName) {
    const schema = schemas[schemaName];
    if (!schema) {
      throw new Error(`Schema '${schemaName}' not found`);
    }
    
    const { error, value } = schema.validate(data, {
      abortEarly: false,
      stripUnknown: true
    });
    
    if (error) {
      throw new Error(`Validation failed: ${error.details.map(d => d.message).join(', ')}`);
    }
    
    return value;
  }
}
```

## 部署和配置指南

### 29. 环境配置

```javascript
// config.js
const config = {
  development: {
    api: {
      baseURL: 'http://localhost:8000',
      timeout: 30000,
      retries: 3
    },
    features: {
      enableCaching: true,
      enableLogging: true,
      enableDebug: true
    }
  },
  
  production: {
    api: {
      baseURL: 'https://api.yourdomain.com',
      timeout: 60000,
      retries: 5
    },
    features: {
      enableCaching: true,
      enableLogging: false,
      enableDebug: false
    }
  }
};

const environment = process.env.NODE_ENV || 'development';
export default config[environment];
```

### 30. Docker 部署

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# 更改文件所有权
RUN chown -R nextjs:nodejs /app
USER nextjs

# 暴露端口
EXPOSE 3000

# 启动应用
CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
    networks:
      - app-network

  backend:
    image: your-backend-image
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/hw_agent
    depends_on:
      - mongo
    networks:
      - app-network

  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - app-network

volumes:
  mongo_data:

networks:
  app-network:
    driver: bridge
```

### 31. Nginx 配置

```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    
    # 前端静态文件
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket 支持（如果需要）
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 测试指南

### 32. 单元测试

```javascript
// tests/api.test.js
import { MultiAgentAPI } from '../src/api';

describe('MultiAgentAPI', () => {
  let api;
  
  beforeEach(() => {
    api = new MultiAgentAPI('http://localhost:8000');
  });
  
  describe('makeRequest', () => {
    it('should make successful API request', async () => {
      const mockResponse = { success: true, data: 'test' };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });
      
      const result = await api.makeRequest('/test');
      
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/multi-agent/test',
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });
    
    it('should handle API errors', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500
      });
      
      await expect(api.makeRequest('/test')).rejects.toThrow('HTTP error! status: 500');
    });
  });
});

// tests/query-handler.test.js
import { QueryHandler } from '../src/query-handler';

describe('QueryHandler', () => {
  let queryHandler;
  let mockApi;
  
  beforeEach(() => {
    mockApi = {
      makeRequest: jest.fn()
    };
    queryHandler = new QueryHandler(mockApi);
  });
  
  describe('sendQuery', () => {
    it('should send query successfully', async () => {
      const mockResponse = {
        success: true,
        session_id: 'session_123',
        final_response: 'Test response'
      };
      
      mockApi.makeRequest.mockResolvedValue(mockResponse);
      
      const result = await queryHandler.sendQuery('test query', {
        userId: 'user123',
        config: { max_iterations: 5 }
      });
      
      expect(result).toEqual(mockResponse);
      expect(queryHandler.currentSessionId).toBe('session_123');
      expect(mockApi.makeRequest).toHaveBeenCalledWith('/enhanced-query', {
        method: 'POST',
        body: JSON.stringify({
          query: 'test query',
          session_id: null,
          user_id: 'user123',
          user_context: {},
          config: { max_iterations: 5 },
          force_mode: null
        })
      });
    });
  });
});
```

### 33. 集成测试

```javascript
// tests/integration.test.js
import { MultiAgentLearningApp } from '../src/app';

describe('MultiAgentLearningApp Integration', () => {
  let app;
  
  beforeAll(async () => {
    app = new MultiAgentLearningApp('http://localhost:8000');
    await app.init();
  });
  
  afterAll(async () => {
    // 清理测试数据
  });
  
  describe('Complete Workflow', () => {
    it('should handle complete query workflow', async () => {
      // 1. 检查系统健康状态
      const health = await app.systemMonitor.checkHealth();
      expect(health.status).toBe('healthy');
      
      // 2. 加载用户画像
      const profile = await app.profileManager.getUserProfile();
      expect(profile).toBeDefined();
      
      // 3. 发送查询
      const response = await app.sendMessage('什么是古代日本文化？');
      expect(response.success).toBe(true);
      expect(response.final_response).toBeDefined();
      
      // 4. 验证会话创建
      expect(app.currentSession).toBeDefined();
      
      // 5. 验证用户画像更新
      const updatedProfile = await app.profileManager.getUserProfile();
      expect(updatedProfile.graph_statistics.entity_count).toBeGreaterThanOrEqual(
        profile.graph_statistics.entity_count
      );
    }, 30000); // 30秒超时
  });
});
```

### 34. 性能测试

```javascript
// tests/performance.test.js
import { MultiAgentAPI } from '../src/api';

describe('Performance Tests', () => {
  let api;
  
  beforeEach(() => {
    api = new MultiAgentAPI('http://localhost:8000');
  });
  
  it('should handle concurrent requests', async () => {
    const concurrentRequests = 10;
    const startTime = Date.now();
    
    const promises = Array(concurrentRequests).fill().map(() =>
      api.makeRequest('/health')
    );
    
    const results = await Promise.all(promises);
    const endTime = Date.now();
    
    expect(results).toHaveLength(concurrentRequests);
    expect(results.every(r => r.status === 'healthy')).toBe(true);
    
    const totalTime = endTime - startTime;
    const avgTime = totalTime / concurrentRequests;
    
    console.log(`Average response time: ${avgTime}ms`);
    expect(avgTime).toBeLessThan(1000); // 平均响应时间应小于1秒
  });
  
  it('should handle large payloads', async () => {
    const largeQuery = 'a'.repeat(1000); // 1000字符的查询
    
    const startTime = Date.now();
    const response = await api.makeRequest('/enhanced-query', {
      method: 'POST',
      body: JSON.stringify({
        query: largeQuery,
        user_context: {
          user_entities: Array(100).fill('test_entity'),
          triples: Array(50).fill({
            subject: 'test_subject',
            predicate: 'test_predicate',
            object: 'test_object'
          })
        }
      })
    });
    const endTime = Date.now();
    
    expect(response.success).toBe(true);
    expect(endTime - startTime).toBeLessThan(10000); // 应小于10秒
  });
});
```

## 故障排除和常见问题

### 35. 常见错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| 400 | 请求参数错误 | 检查请求格式和参数类型 |
| 401 | 未授权访问 | 检查认证信息（当前版本不需要） |
| 403 | 禁止访问 | 检查权限设置 |
| 404 | 资源不存在 | 检查API端点路径 |
| 500 | 服务器内部错误 | 检查后端日志，联系管理员 |
| 502 | 网关错误 | 检查后端服务状态 |
| 503 | 服务不可用 | 等待服务恢复或联系管理员 |
| 504 | 网关超时 | 检查网络连接和后端响应时间 |

### 36. 调试技巧

```javascript
// 启用调试模式
class DebugHelper {
  static enableDebugMode() {
    // 启用详细日志
    localStorage.setItem('debug', 'true');
    
    // 拦截所有API请求
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      console.log('🔍 API Request:', args);
      const startTime = Date.now();
      
      try {
        const response = await originalFetch(...args);
        const endTime = Date.now();
        console.log('✅ API Response:', {
          url: args[0],
          status: response.status,
          time: endTime - startTime
        });
        return response;
      } catch (error) {
        console.error('❌ API Error:', error);
        throw error;
      }
    };
    
    // 监听状态变化
    if (window.app && window.app.stateManager) {
      window.app.stateManager.subscribe('*', (value, path) => {
        console.log('🔄 State Change:', path, value);
      });
    }
  }
  
  static disableDebugMode() {
    localStorage.removeItem('debug');
    // 恢复原始fetch
    if (window._originalFetch) {
      window.fetch = window._originalFetch;
    }
  }
}

// 使用示例
if (process.env.NODE_ENV === 'development') {
  DebugHelper.enableDebugMode();
}
```

### 37. 性能监控

```javascript
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      apiCalls: 0,
      apiErrors: 0,
      avgResponseTime: 0,
      totalResponseTime: 0
    };
    
    this.startMonitoring();
  }
  
  startMonitoring() {
    // 监控API调用
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      this.metrics.apiCalls++;
      const startTime = performance.now();
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const responseTime = endTime - startTime;
        
        this.metrics.totalResponseTime += responseTime;
        this.metrics.avgResponseTime = this.metrics.totalResponseTime / this.metrics.apiCalls;
        
        return response;
      } catch (error) {
        this.metrics.apiErrors++;
        throw error;
      }
    };
  }
  
  getMetrics() {
    return {
      ...this.metrics,
      errorRate: this.metrics.apiCalls > 0 ? 
        (this.metrics.apiErrors / this.metrics.apiCalls) * 100 : 0
    };
  }
  
  generateReport() {
    const metrics = this.getMetrics();
    return `
性能监控报告:
- API调用次数: ${metrics.apiCalls}
- API错误次数: ${metrics.apiErrors}
- 错误率: ${metrics.errorRate.toFixed(2)}%
- 平均响应时间: ${metrics.avgResponseTime.toFixed(2)}ms
    `;
  }
}
```

