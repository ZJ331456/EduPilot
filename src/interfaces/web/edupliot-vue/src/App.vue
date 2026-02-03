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

      <!-- 带侧边栏的布局模式（其他页面） -->
      <el-container v-else class="layout-container">
        <!-- 侧边导航栏 -->
        <el-aside width="260px" class="app-sidebar">
          <div class="sidebar-header">
            <div class="logo-wrapper">
              <el-icon class="logo-icon"><Reading /></el-icon>
            </div>
            <div class="logo-text">
              <span class="title">EduPilot</span>
              <span class="subtitle">智能学习助理</span>
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
          <!-- 顶部栏 Header -->
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
    '/workbench': '学习工作台'
  }
  return map[route.path] || 'EduPilot'
})

onMounted(() => {
  performanceStore.startMonitoring()
})
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: #f7f7f7;
  position: relative;
}

.layout-container {
  height: 100%;
  position: relative;
  z-index: 1;
}

/* 侧边栏样式 */
.app-sidebar {
  background: #ffffff;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.sidebar-header {
  height: 76px;
  display: flex;
  align-items: center;
  padding: 0 22px;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}

.logo-wrapper {
  width: 40px;
  height: 40px;
  background: #000000;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-text .title {
  font-weight: 800;
  font-size: 17px;
  color: #000000;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.logo-text .subtitle {
  font-size: 11px;
  color: #888888;
  font-weight: 500;
  margin-top: 2px;
}

.sidebar-menu {
  border-right: none !important;
  flex: 1;
  padding: 20px 14px;
  background-color: transparent !important;
}

.el-menu-item {
  border-radius: 10px;
  margin-bottom: 2px;
  height: 46px;
  color: #666666 !important;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

.el-menu-item:hover {
  background-color: #f5f5f5 !important;
  color: #000000 !important;
}

.el-menu-item.is-active {
  background: #000000 !important;
  color: #ffffff !important;
}

.el-menu-item .el-icon {
  font-size: 18px;
  margin-right: 12px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e5e5;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
  background: #f5f5f5;
  border: 1px solid transparent;
}

.user-card:hover {
  background: #eeeeee;
}

.user-avatar {
  background: #000000 !important;
  color: white;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #000000;
}

.user-status {
  font-size: 11px;
  color: #666666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.user-status::before {
  content: '';
  width: 6px;
  height: 6px;
  background: #000000;
  border-radius: 50%;
}

/* 顶部 Header 样式 */
.app-header {
  background: #ffffff;
  border-bottom: 1px solid #e5e5e5;
  height: 60px !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  z-index: 10;
  position: sticky;
  top: 0;
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: #000000;
  letter-spacing: -0.3px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666666;
  padding: 6px 14px;
  background: #f5f5f5;
  border-radius: 20px;
}

.status-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #cccccc;
}

.status-indicator .dot.active {
  background-color: #000000;
}

.metric-badge {
  background: #f5f5f5;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  color: #666666;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.metric-badge .label {
  color: #888888;
}

.metric-badge .value {
  font-weight: 600;
  color: #000000;
}

/* 主内容区 */
.app-main {
  background: #f7f7f7;
  padding: 28px 32px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

/* 页面切换动画 - 轻量版 */
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
  background: rgba(15, 23, 42, 0.16);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 23, 42, 0.28);
}
</style>
