# EduPilot Vue 前端启动指南

## 📋 概述

已完成一个完整的、简洁优美的 Vue 3 前端界面，完美对接后端 API！

### ✅ 已完成的工作

1. **技术栈升级**
   - Vue 3 Composition API
   - Element Plus UI 组件库
   - Pinia 状态管理
   - Vue Router 路由
   - Axios HTTP 客户端
   - Vite 构建工具

2. **完整的 API 集成**
   - 所有 API 调用已封装在 `src/api/index.js`
   - 对接 `/api/agent/v1/*` 所有接口
   - 自动代理配置

3. **4 个核心页面**
   - 首页 (HomePage.vue) - 系统介绍和状态
   - 学习对话 (ChatView.vue) - 智能对话界面★
   - 知识检索 (KnowledgeView.vue) - 语义搜索
   - 用户画像 (ProfileView.vue) - 学习数据分析

4. **状态管理**
   - 用户状态 (stores/user.js)
   - 对话状态 (stores/chat.js)

5. **现代化 UI 设计**
   - 简洁优美的界面
   - 响应式布局
   - 流畅的动画过渡
   - 渐变背景色

## 🚀 快速启动

### 步骤 1: 安装依赖

```bash
cd src/interfaces/web/edupliot-vue
npm install
```

### 步骤 2: 启动后端 API

在**另一个终端**，在项目根目录运行：

```bash
# 确保在项目根目录 D:\Project\STUAgent\EduPilot
python -m src.interfaces.api
```

后端将运行在 `http://localhost:8000`

### 步骤 3: 启动 Vue 开发服务器

```bash
# 在 edupliot-vue 目录
npm run dev
```

前端将运行在 `http://localhost:5173`

### 步骤 4: 访问应用

打开浏览器访问：**http://localhost:5173**

## 📁 项目文件结构

```
src/interfaces/web/edupliot-vue/
├── src/
│   ├── api/
│   │   └── index.js          # ★ API客户端（对接后端）
│   ├── router/
│   │   └── index.js          # 路由配置
│   ├── stores/
│   │   ├── user.js           # 用户状态
│   │   └── chat.js           # 对话状态
│   ├── views/
│   │   ├── HomePage.vue      # 首页
│   │   ├── ChatView.vue      # ★ 学习对话（核心）
│   │   ├── KnowledgeView.vue # 知识检索
│   │   └── ProfileView.vue   # 用户画像
│   ├── App.vue               # 根组件
│   └── main.js               # 入口文件
├── package.json              # 依赖配置
├── vite.config.js            # ★ Vite配置（含API代理）
└── README.md                 # 项目文档
```

## 🎯 核心功能展示

### 1. 首页 (/)

<details>
<summary>功能特性</summary>

- 🏠 欢迎页面
- 📊 系统状态实时显示
- 🎨 核心功能卡片展示
- 📈 系统统计信息
- 🚀 快速开始引导

**API 调用：**
- `GET /api/agent/v1/health` - 健康检查
- `GET /api/agent/v1/stats` - 系统统计

</details>

### 2. 学习对话 (/chat) ⭐

<details>
<summary>功能特性</summary>

- 💬 实时对话界面
- 🤖 智能问答
- 📊 查询分析展示
- 📝 学习计划展示
- 💡 快速问题示例
- 🔄 会话管理
- ⏱️ 消息时间戳
- 🎨 Markdown 渲染

**API 调用：**
- `POST /api/agent/v1/workflow/session/start` - 启动会话
- `POST /api/agent/v1/workflow/session/continue` - 继续会话
- `DELETE /api/agent/v1/workflow/session/{id}` - 结束会话

**交互流程：**
1. 用户输入问题
2. 调用 API 启动/继续会话
3. 展示 AI 回复
4. 显示查询分析结果
5. 显示学习计划
6. 提供下一步建议

</details>

### 3. 知识检索 (/knowledge)

<details>
<summary>功能特性</summary>

- 🔍 语义搜索
- 📚 知识库浏览
- 🔗 相关概念推荐
- 📖 概念详情查看
- 🎯 搜索策略选择
- 🌟 热门搜索

**API 调用：**
- `POST /api/agent/v1/knowledge/retrieve` - 检索知识
- `GET /api/agent/v1/knowledge/concept/{name}` - 概念详情
- `GET /api/agent/v1/knowledge/related/{name}` - 相关概念
- `GET /api/agent/v1/knowledge/bases` - 知识库列表

**搜索选项：**
- 混合检索（推荐）
- 语义检索
- 关键词检索
- 结果数量：5/10/15

</details>

### 4. 用户画像 (/profile)

<details>
<summary>功能特性</summary>

- 👤 用户信息展示
- 📊 学习统计
- 📝 学习记录时间线
- 🕸️ 知识图谱
- 📈 学习模式分析

**API 调用：**
- `GET /api/agent/v1/memory/profile/{userId}` - 用户画像
- `GET /api/agent/v1/memory/learning-records/{userId}` - 学习记录
- `GET /api/agent/v1/memory/knowledge-graph/{userId}` - 知识图谱

**展示数据：**
- 总交互次数
- 平均质量分数
- 连续学习天数
- 知识图谱节点数
- 学习模式类型

</details>

## 🔧 配置说明

### Vite 代理配置

在 `vite.config.js` 中已配置 API 代理：

```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

这意味着所有 `/api/*` 请求会自动转发到后端 `http://localhost:8000/api/*`

### API 基础配置

在 `src/api/index.js` 中：

```javascript
const apiClient = axios.create({
  baseURL: '/api/agent/v1',
  timeout: 30000
})
```

## 💡 使用示例

### 示例 1: 启动学习会话

1. 访问 http://localhost:5173/chat
2. 输入问题：「什么是大化改新？」
3. 点击发送或按 Ctrl+Enter
4. 查看 AI 回复和分析结果

### 示例 2: 检索知识

1. 访问 http://localhost:5173/knowledge
2. 输入关键词：「奈良时代」
3. 选择检索策略：混合检索
4. 点击搜索
5. 查看检索结果

### 示例 3: 查看画像

1. 访问 http://localhost:5173/profile
2. 查看学习统计
3. 浏览学习记录
4. 查看知识图谱

## 🎨 UI 设计特点

1. **配色方案**
   - 主色：#667eea（紫蓝）
   - 辅色：#764ba2（深紫）
   - 渐变背景

2. **布局**
   - 响应式设计
   - 卡片式布局
   - 清晰的视觉层次

3. **交互**
   - 流畅的动画
   - 即时反馈
   - 友好的提示

4. **组件**
   - Element Plus 组件
   - 自定义样式
   - 一致的设计语言

## 📦 依赖说明

### 主要依赖

```json
{
  "vue": "^3.5.22",           // Vue 3 框架
  "vue-router": "^4.2.5",     // 路由管理
  "axios": "^1.6.0",          // HTTP 客户端
  "element-plus": "^2.5.0",   // UI 组件库
  "pinia": "^2.1.7",          // 状态管理
  "markdown-it": "^14.0.0"    // Markdown 渲染
}
```

### 开发依赖

```json
{
  "vite": "^7.1.7",                         // 构建工具
  "@vitejs/plugin-vue": "^6.0.1",          // Vue 插件
  "unplugin-auto-import": "^0.17.0",       // 自动导入
  "unplugin-vue-components": "^0.26.0"     // 组件自动导入
}
```

## 🔍 调试技巧

### 1. 查看 API 请求

打开浏览器开发者工具：
- Network 标签页
- 筛选 XHR/Fetch
- 查看请求/响应详情

### 2. Vue DevTools

安装 Vue DevTools 浏览器扩展：
- 查看组件树
- 监控状态变化
- 调试路由

### 3. 控制台日志

代码中有详细的 console.log：
```javascript
console.error('API Error:', error)
```

## ⚠️ 常见问题

### Q1: 前端启动后无法连接后端？

**解决方案：**
1. 确保后端已启动：`python -m src.interfaces.api`
2. 检查后端运行在 `http://localhost:8000`
3. 查看浏览器控制台错误信息

### Q2: npm install 失败？

**解决方案：**
```bash
# 清除缓存
npm cache clean --force

# 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 重新安装
npm install
```

### Q3: 页面空白？

**解决方案：**
1. 查看浏览器控制台错误
2. 确认所有依赖已安装
3. 检查 Node.js 版本 >= 20.19.0

### Q4: API 请求 404？

**解决方案：**
1. 检查后端 API 是否正常运行
2. 访问 http://localhost:8000/api/agent/v1/health
3. 查看 Vite 代理配置

## 🚀 生产部署

### 1. 构建

```bash
npm run build
```

### 2. 预览

```bash
npm run preview
```

### 3. 部署

将 `dist/` 目录部署到静态服务器（Nginx、Apache 等）

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

## 📝 下一步建议

1. **完善功能**
   - 添加用户认证
   - 实现深色模式
   - 添加更多图表

2. **优化性能**
   - 实现虚拟滚动
   - 添加请求缓存
   - 优化打包体积

3. **增强体验**
   - 添加快捷键
   - 实现拖拽功能
   - 添加语音输入

## 🎉 开始使用

```bash
# 1. 安装依赖
cd src/interfaces/web/edupliot-vue
npm install

# 2. 启动后端（新终端）
cd ../../..
python -m src.interfaces.api

# 3. 启动前端
cd src/interfaces/web/edupliot-vue
npm run dev

# 4. 访问应用
# http://localhost:5173
```

---

**版本**: 3.0.0  
**创建日期**: 2025-10-09  
**技术栈**: Vue 3 + Element Plus + Vite

