<template>
  <el-config-provider :locale="zhCn">
    <div id="app">
      <!-- 全屏模式（首页） -->
      <template v-if="isHomePage">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </template>

      <!-- 带有侧边栏的布局模式（其他页面） -->
      <el-container v-else class="layout-container">
        <!-- 侧边导航栏 -->
        <el-aside width="260px" class="app-sidebar">
          <div class="sidebar-header">
            <div class="logo-wrapper">
              <el-icon class="logo-icon"><Reading /></el-icon>
            </div>
            <div class="logo-text">
              <span class="title">EduPilot</span>
              <span class="subtitle">智能学习伙伴</span>
            </div>
          </div>

          <el-menu
            :default-active="currentRoute"
            class="sidebar-menu"
            router
            :collapse="false"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页概览</span>
            </el-menu-item>
            <el-menu-item index="/chat">
              <el-icon><ChatDotRound /></el-icon>
              <span>学习对话</span>
            </el-menu-item>
            <el-menu-item index="/knowledge">
              <el-icon><DataAnalysis /></el-icon>
              <span>知识图谱</span>
            </el-menu-item>
            <el-menu-item index="/workbench">
              <el-icon><Monitor /></el-icon>
              <span>学习工作台</span>
            </el-menu-item>
            <el-menu-item index="/profile">
              <el-icon><User /></el-icon>
              <span>我的画像</span>
            </el-menu-item>
            <el-menu-item index="/performance">
              <el-icon><Odometer /></el-icon>
              <span>系统监控</span>
            </el-menu-item>
          </el-menu>

          <!-- 侧边栏底部用户区 -->
          <div class="sidebar-footer">
            <div class="user-card">
              <el-avatar :size="36" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-info">
                <span class="user-name">{{ userName || '访客用户' }}</span>
                <span class="user-status">在线</span>
              </div>
            </div>
          </div>
        </el-aside>

        <el-container>
          <!-- 顶部极简 Header -->
          <el-header class="app-header">
            <div class="header-left">
              <span class="page-title">{{ currentPageTitle }}</span>
            </div>
            
            <div class="header-right">
              <div class="status-indicator">
                <span class="dot" :class="{ active: true }"></span>
                <span class="label">System Normal</span>
              </div>
              <div class="metric-badge">
                <span class="label">延迟</span>
                <span class="value">{{ averageLatency }}ms</span>
              </div>
            </div>
          </el-header>

          <!-- 主内容区 -->
          <el-main class="app-main">
            <router-view v-slot="{ Component }">
              <transition name="fade-slide" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import { usePerformanceStore } from './stores/performance'
import { 
  Odometer, 
  HomeFilled, 
  ChatDotRound, 
  DataAnalysis, 
  User, 
  Reading,
  Monitor
} from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const route = useRoute()
const userStore = useUserStore()
const performanceStore = usePerformanceStore()

const currentRoute = computed(() => route.path)
const isHomePage = computed(() => route.path === '/')
const userName = computed(() => userStore.userName)
const averageLatency = computed(() => Math.round(performanceStore.averageApiTime || 0))

const currentPageTitle = computed(() => {
  const map = {
    '/': '概览',
    '/chat': '智能对话',
    '/knowledge': '知识检索',
    '/profile': '用户画像',
    '/performance': '性能监控',
    '/workbench': '沉浸式工作台'
  }
  return map[route.path] || 'EduPilot'
})

onMounted(() => {
  performanceStore.startMonitoring()
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  /* 简约白主题配色 */
  --primary-color: #4f46e5;      /* Indigo 600 - 专业、现代 */
  --primary-light: #818cf8;
  --primary-fade: #eef2ff;       /* 极浅的靛蓝背景 */
  
  --bg-body: #f9fafb;            /* 浅灰背景，保护视力 */
  --bg-white: #ffffff;
  
  --text-primary: #111827;       /* 深灰几近黑 */
  --text-secondary: #6b7280;     /* 中灰 */
  --text-tertiary: #9ca3af;      /* 浅灰 */
  
  --border-color: #e5e7eb;
  --border-hover: #d1d5db;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: var(--bg-body);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.layout-container {
  height: 100%;
}

/* 侧边栏样式 */
.app-sidebar {
  background-color: var(--bg-white);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  z-index: 20;
}

.sidebar-header {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 12px;
  border-bottom: 1px solid transparent;
}

.logo-wrapper {
  width: 36px;
  height: 36px;
  background: var(--primary-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: var(--shadow-md);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-text .title {
  font-weight: 700;
  font-size: 18px;
  color: var(--text-primary);
  line-height: 1.2;
}

.logo-text .subtitle {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.sidebar-menu {
  border-right: none !important;
  flex: 1;
  padding: 16px 12px;
  background-color: transparent !important;
}

.el-menu-item {
  border-radius: 8px;
  margin-bottom: 4px;
  height: 48px;
  color: var(--text-secondary) !important;
  font-weight: 500;
}

.el-menu-item:hover {
  background-color: var(--bg-body) !important;
  color: var(--text-primary) !important;
}

.el-menu-item.is-active {
  background-color: var(--primary-fade) !important;
  color: var(--primary-color) !important;
  font-weight: 600;
}

.el-menu-item .el-icon {
  font-size: 18px;
  margin-right: 10px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 10px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.user-card:hover {
  background-color: var(--bg-body);
}

.user-avatar {
  background-color: var(--primary-light);
  color: white;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-status {
  font-size: 12px;
  color: #10b981; /* Green */
}

/* 顶部 Header 样式 */
.app-header {
  background-color: var(--bg-white);
  border-bottom: 1px solid var(--border-color);
  height: 64px !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  z-index: 10;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.status-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #d1d5db;
}

.status-indicator .dot.active {
  background-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.metric-badge {
  background-color: var(--bg-body);
  padding: 4px 12px;
  border-radius: 99px;
  font-size: 12px;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.metric-badge .value {
  font-weight: 600;
  color: var(--text-primary);
  margin-left: 4px;
}

/* 主内容区 */
.app-main {
  background-color: var(--bg-body);
  padding: 32px;
  height: calc(100vh - 64px);
  overflow-y: auto;
}

/* 页面切换动画 - 简约版 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>