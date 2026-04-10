<template>
  <div class="navigation-panel">
    <div class="panel-header">
      <h3>学习导航</h3>
      <el-button
        type="primary"
        size="small"
        @click="$emit('new-session')"
        :icon="Plus"
      >
        新会话
      </el-button>
    </div>

    <div class="sessions-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        :class="['session-item', { active: session.id === currentSessionId }]"
        @click="$emit('select-session', session)"
      >
        <div class="session-header">
          <el-icon><ChatDotRound /></el-icon>
          <span class="session-title">{{ session.title || '未命名会话' }}</span>
        </div>
        <div class="session-meta">
          <span class="session-time">{{ formatTime(session.updatedAt) }}</span>
          <el-tag v-if="session.unread" type="danger" size="small">
            {{ session.unread }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="panel-footer">
      <el-button text @click="showSettings = true">
        <el-icon><Setting /></el-icon>
        设置
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ChatDotRound, Plus, Setting } from '@element-plus/icons-vue'
import { formatTime } from '../../utils/format'

defineProps({
  sessions: {
    type: Array,
    default: () => []
  },
  currentSessionId: {
    type: String,
    default: null
  }
})

defineEmits(['select-session', 'new-session'])

const showSettings = ref(false)
</script>

<style scoped>
.navigation-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--border-color-hover);
}

.session-item.active {
  background: rgba(102, 126, 234, 0.15);
  border-color: var(--primary-color);
}

.session-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.session-title {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
}

.panel-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}
</style>

