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

      <!-- 带侧边栏的布局模式 -->
      <el-container v-else class="layout-container">
        <!-- 侧边栏 -->
        <el-aside width="260px" class="app-sidebar">
          <!-- Logo 区域 -->
          <div class="sidebar-header">
            <div class="logo-wrapper">
              <div class="logo-icon">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 12H5V21H19V12H22L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="14" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
            <div class="logo-text">
              <span class="title">EduPilot</span>
              <span class="subtitle">智能学习助理</span>
            </div>
          </div>

          <!-- 导航菜单 -->
          <nav class="sidebar-nav">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="nav-item"
              :class="{ active: currentRoute === item.path }"
            >
              <span class="nav-icon" v-html="item.icon"></span>
              <span class="nav-label">{{ item.label }}</span>
              <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
            </router-link>
          </nav>

          <!-- 底部用户卡片 -->
          <div class="sidebar-footer">
            <div class="user-card">
              <div class="user-avatar">
                <span>{{ userNameChar }}</span>
              </div>
              <div class="user-info">
                <span class="user-name">{{ userName || '访客用户' }}</span>
                <span class="user-status">
                  <span class="status-dot"></span>
                  在线
                </span>
              </div>
            </div>
          </div>
        </el-aside>

        <el-container>
          <!-- 顶部栏 -->
          <el-header class="app-header">
            <div class="header-left">
              <h1 class="page-title">{{ currentPageTitle }}</h1>
            </div>

            <div class="header-right">
              <!-- 系统状态 -->
              <div class="status-indicator">
                <span class="status-dot" :class="{ active: systemOnline }"></span>
                <span class="status-text">{{ systemOnline ? '系统正常' : '系统离线' }}</span>
              </div>

              <!-- 延迟指标 -->
              <div class="metric-badge">
                <svg class="metric-icon" viewBox="0 0 24 24" fill="none">
                  <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="metric-value">{{ averageLatency }}ms</span>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import { usePerformanceStore } from './stores/performance'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const route = useRoute()
const userStore = useUserStore()
const performanceStore = usePerformanceStore()

const currentRoute = computed(() => route.path)
const isHomePage = computed(() => route.path === '/')
const userName = computed(() => userStore.userName)
const averageLatency = computed(() => Math.round(performanceStore.averageApiTime || 0))
const systemOnline = ref(true)

const userNameChar = computed(() => {
  const name = userStore.userName || '游'
  return name.charAt(0).toUpperCase()
})

// 导航菜单项
const navItems = [
  {
    path: '/',
    label: '首页概览',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  },
  {
    path: '/chat',
    label: '学习对话',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" stroke-width="2"/></svg>'
  },
  {
    path: '/knowledge',
    label: '知识检索',
    icon: '<svg viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/><path d="M21 21L16.65 16.65" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
  },
  {
    path: '/graph',
    label: '图谱可视化',
    icon: '<svg viewBox="0 0 24 24" fill="none"><circle cx="5" cy="12" r="3" stroke="currentColor" stroke-width="2"/><circle cx="19" cy="12" r="3" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="5" r="3" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="19" r="3" stroke="currentColor" stroke-width="2"/><path d="M8.5 10L11 11.5M15.5 10L13 11.5M8.5 14L11 12.5M15.5 14L13 12.5" stroke="currentColor" stroke-width="2"/></svg>'
  },
  {
    path: '/workbench',
    label: '学习工作台',
    icon: '<svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/><path d="M3 9H21M9 21V9" stroke="currentColor" stroke-width="2"/></svg>'
  },
  {
    path: '/profile',
    label: '我的画像',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/></svg>'
  },
  {
    path: '/performance',
    label: '系统监控',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M22 12H18L15 21L9 3L6 12H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  }
]

const currentPageTitle = computed(() => {
  const map = {
    '/': '首页概览',
    '/chat': '智能对话',
    '/knowledge': '知识检索',
    '/graph': '图谱可视化',
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
/* 主容器 */
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-base);
  position: relative;
}

.layout-container {
  height: 100%;
  position: relative;
  z-index: 1;
}

/* ==================== 侧边栏 ==================== */
.app-sidebar {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 20;
  position: relative;
  overflow: hidden;
}

/* Logo 区域 */
.sidebar-header {
  height: 68px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 14px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
  z-index: 1;
}

.logo-wrapper {
  flex-shrink: 0;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: var(--text-primary);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--bg-base);
  transition: transform var(--transition-normal);
}

.logo-icon:hover {
  transform: scale(1.05);
}

.logo-icon svg {
  width: 20px;
  height: 20px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-text .title {
  font-weight: 700;
  font-size: 16px;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.3px;
}

.logo-text .subtitle {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  margin-top: 2px;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  position: relative;
  font-weight: 500;
  font-size: 14px;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--bg-card);
  color: var(--text-primary);
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 50%;
  background: var(--text-primary);
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity var(--transition-fast);
}

.nav-item:hover .nav-icon,
.nav-item.active .nav-icon {
  opacity: 1;
}

.nav-icon svg {
  width: 100%;
  height: 100%;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  background: var(--text-muted);
  color: var(--bg-base);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--radius-full);
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.user-card:hover {
  border-color: var(--border-hover);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--bg-base);
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-status {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-dot.active {
  background: var(--success-color);
}

/* ==================== 顶部栏 ==================== */
.app-header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  height: 60px !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 10;
  position: sticky;
  top: 0;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.2px;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 6px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
}

.status-indicator .status-dot {
  width: 5px;
  height: 5px;
}

.status-indicator .status-dot.active {
  background: var(--success-color);
}

.metric-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-icon {
  width: 14px;
  height: 14px;
}

.metric-value {
  font-weight: 600;
  color: var(--text-primary);
}

/* ==================== 主内容区 ==================== */
.app-main {
  background: var(--bg-base);
  padding: 24px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

/* ==================== 动画 ==================== */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ==================== 响应式 ==================== */
@media (max-width: 992px) {
  .app-sidebar {
    width: 72px !important;
  }

  .logo-text,
  .nav-label,
  .nav-badge,
  .user-info {
    display: none;
  }

  .sidebar-header {
    justify-content: center;
    padding: 0;
  }

  .nav-item {
    justify-content: center;
    padding: 10px;
  }

  .user-card {
    justify-content: center;
    padding: 8px;
  }
}
</style>
