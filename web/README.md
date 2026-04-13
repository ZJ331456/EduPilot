# 前端模块 (web/)

## 概述

Vue 3 前端，采用 Composition API 和 Element Plus UI 组件库，柠檬绿配色主题。

## 目录结构

```
web/
├── src/
│   ├── main.js              # 应用入口
│   ├── App.vue              # 根组件
│   ├── assets/
│   │   ├── base.css        # 全局基础样式
│   │   ├── variables.css    # CSS 变量定义
│   │   └── main.css         # 全局工具类
│   ├── views/              # 页面视图
│   │   ├── HomePage.vue    # 首页
│   │   ├── ChatView.vue    # 对话页
│   │   ├── KnowledgeView.vue # 知识库页
│   │   ├── GraphExplorer.vue # 图谱页
│   │   ├── ProfileView.vue  # 画像页
│   │   ├── PerformanceView.vue # 监控页
│   │   └── LearningWorkbench.vue # 工作台
│   ├── components/          # 公共组件
│   ├── api/                # API 客户端
│   │   └── edupilot.js    # 后端接口封装
│   ├── stores/             # Pinia 状态管理
│   │   ├── user.js        # 用户状态
│   │   ├── chat.js        # 对话状态
│   │   └── performance.js  # 性能监控
│   ├── router/             # 路由配置
│   │   └── index.js
│   ├── composables/         # 组合式函数
│   └── utils/              # 工具函数
│       ├── index.js
│       ├── constants.js     # 常量定义
│       ├── format.js        # 格式化函数
│       └── validators.js    # 验证器
└── package.json
```

## 柠檬绿主题配色

```css
:root {
  /* 主色调 */
  --primary-color: #69DB7C;      /* 柠檬绿 */
  --primary-light: #B2F2BB;     /* 浅绿 */
  --primary-dark: #40C057;      /* 深绿 */
  --primary-hover: #51D067;
  --primary-active: #37B24D;

  /* 背景色 */
  --bg-primary: #FAFFFE;
  --bg-secondary: #F8FDF9;
  --bg-card: #FFFFFF;

  /* 文字色 */
  --text-primary: #1A1C20;
  --text-secondary: #5C5F66;
  --text-muted: #9CA3AF;
}
```

## 主要页面

### 1. HomePage 首页

展示系统概览、核心功能和系统状态。

```vue
<script setup>
import { onMounted, ref } from 'vue'
import { healthCheck } from '@/api/edupilot'

const health = ref({ status: 'healthy' })

onMounted(async () => {
  const data = await healthCheck()
  health.value = data
})
</script>
```

### 2. ChatView 对话页

支持直接对话和苏格拉底式对话两种模式。

```vue
<script setup>
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import * as edupilot from '@/api/edupilot'

const chatStore = useChatStore()
const userInput = ref('')
const currentMode = ref('direct')

async function sendMessage() {
  const message = userInput.value.trim()
  if (!message) return

  chatStore.addMessage({ role: 'user', content: message })
  userInput.value = ''

  const response = await edupilot.chat({
    userId: 'user_123',
    message,
    mode: currentMode.value
  })

  chatStore.addMessage({ role: 'assistant', content: response.reply })
}
</script>
```

### 3. GraphExplorer 图谱页

ECharts 力导向图可视化，展示知识库/会话/用户三种图谱。

## API 客户端

```javascript
// 发送对话消息
const response = await edupilot.chat({
  userId: 'user_123',
  sessionId: null,
  message: '你好',
  mode: 'direct'
})

// 获取会话图谱
const graph = await edupilot.getDialogueGraph(sessionId)

// 获取用户长期图谱
const longGraph = await edupilot.getUserLongGraph(userId)
```

## 状态管理

### userStore 用户状态

```javascript
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
console.log(userStore.userId)
console.log(userStore.sessionId)
```

### chatStore 对话状态

```javascript
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
chatStore.addMessage({ role: 'user', content: '你好' })
chatStore.setLoading(true)
chatStore.clearMessages()
```

## 启动开发服务器

```bash
cd web
npm install
npm run dev
```

访问 `http://localhost:5173`
