# EduPilot Vue 前端

基于 Vue 3 + Element Plus 的现代化智能学习助手前端界面。

## ✨ 特性

- 🎨 **简洁优美** - 基于 Element Plus 的现代化 UI 设计
- 🚀 **高性能** - Vue 3 Composition API + Vite 构建
- 📱 **响应式** - 完美适配桌面和移动端
- 🔌 **API 集成** - 完整对接后端 FastAPI 服务
- 🎯 **功能完整** - 学习对话、知识检索、用户画像

## 🏗️ 项目结构

```
src/
├── api/              # API 客户端
│   └── index.js      # API 方法封装
├── assets/           # 静态资源
├── components/       # 公共组件
├── router/           # 路由配置
├── stores/           # Pinia 状态管理
│   ├── user.js       # 用户状态
│   └── chat.js       # 对话状态
├── views/            # 页面组件
│   ├── HomePage.vue      # 首页
│   ├── ChatView.vue      # 学习对话
│   ├── KnowledgeView.vue # 知识检索
│   └── ProfileView.vue   # 用户画像
├── App.vue           # 根组件
└── main.js           # 入口文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

服务将运行在 `http://localhost:5173`

### 3. 确保后端 API 已启动

```bash
# 在项目根目录
python -m src.interfaces.api
```

后端 API 应运行在 `http://localhost:8000`

## 📦 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

## 🎯 功能页面

### 首页 (/)
- 系统状态展示
- 核心功能介绍
- 快速开始引导

### 学习对话 (/chat)
- 智能对话界面
- 实时消息展示
- 查询分析结果
- 学习计划展示
- 会话管理

### 知识检索 (/knowledge)
- 语义搜索
- 知识库浏览
- 概念详情查看
- 相关概念推荐

### 用户画像 (/profile)
- 学习统计
- 学习记录
- 知识图谱
- 学习模式分析

## 🔧 配置说明

### API 代理配置

在 `vite.config.js` 中配置：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

### 环境变量

创建 `.env.local` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 🎨 UI 组件库

使用 [Element Plus](https://element-plus.org/) 作为 UI 组件库。

主要组件：
- `el-card` - 卡片容器
- `el-button` - 按钮
- `el-input` - 输入框
- `el-message` - 消息提示
- `el-timeline` - 时间线
- `el-collapse` - 折叠面板

## 📡 API 调用示例

```javascript
import api from '@/api'

// 启动学习会话
const response = await api.workflow.startSession({
  user_id: 'user123',
  query: '什么是大化改新？'
})

// 检索知识
const results = await api.knowledge.retrieve({
  query: '大化改新',
  top_k: 5,
  retrieval_strategy: 'hybrid'
})

// 获取用户画像
const profile = await api.memory.getUserProfile('user123')
```

## 🌐 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 📝 开发规范

### 代码风格
- 使用 Composition API
- 使用 `<script setup>` 语法
- 组件名使用 PascalCase
- 文件名使用 PascalCase

### 提交规范
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `perf:` 性能优化

## 🐛 常见问题

### Q: 无法连接到后端 API？

**A:** 确保：
1. 后端 API 服务已启动
2. API 运行在 `http://localhost:8000`
3. Vite 代理配置正确

### Q: 页面空白？

**A:** 检查浏览器控制台是否有错误信息，确保所有依赖已正确安装。

### Q: 组件样式不生效？

**A:** 确保 Element Plus 已正确导入：
```javascript
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
```

## 📄 许可证

与主项目相同

## 🙏 致谢

- [Vue 3](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [Vite](https://vitejs.dev/)
- [Pinia](https://pinia.vuejs.org/)

---

**版本**: 3.0.0  
**更新日期**: 2025-10-09
