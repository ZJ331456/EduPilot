<template>
  <div class="chat-stream">
    <!-- 消息列表 -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <el-empty description="开始你的学习之旅吧！">
          <template #image>
            <el-icon :size="100" color="#667eea"><Reading /></el-icon>
          </template>
        </el-empty>
      </div>

      <!-- 消息项 -->
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message-item', message.role]"
      >
        <MessageBubble :message="message" />
      </div>

      <!-- 思考过程可视化 -->
      <ThoughtProcess
        v-if="thoughtProcess && thoughtProcess.isActive"
        :process="thoughtProcess"
      />

      <!-- 苏格拉底交互卡片 -->
      <SocraticCard
        v-if="socraticDialogue && socraticDialogue.is_socratic_mode"
        :dialogue="socraticDialogue"
        @quick-reply="handleQuickReply"
      />

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-indicator">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在思考...</span>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="输入你的问题，开始学习之旅..."
          @keydown.enter.exact.prevent="handleSend"
          @keydown.shift.enter="handleShiftEnter"
          :disabled="isLoading"
          class="message-input"
          resize="none"
        />
        <div class="input-actions">
          <el-button
            type="primary"
            size="small"
            @click="handleSend"
            :loading="isLoading"
            :disabled="!userInput.trim()"
            class="send-btn"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Reading, Loading, Promotion } from '@element-plus/icons-vue'
import MessageBubble from './MessageBubble.vue'
import ThoughtProcess from './ThoughtProcess.vue'
import SocraticCard from './SocraticCard.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  workflowState: {
    type: Object,
    default: null
  },
  thoughtProcess: {
    type: Object,
    default: null
  },
  socraticDialogue: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['send-message', 'continue-session'])

const userInput = ref('')
const messagesContainer = ref(null)

const handleSend = () => {
  if (!userInput.value.trim() || props.isLoading) return
  
  const message = userInput.value.trim()
  userInput.value = ''
  
  emit('send-message', message)
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

// 处理 Shift+Enter 换行（默认行为，无需特殊处理）
const handleShiftEnter = () => {
  // textarea 的默认行为就是换行，无需额外处理
}

const handleQuickReply = (reply) => {
  emit('continue-session', reply)
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(() => props.messages.length, () => {
  nextTick(() => {
    scrollToBottom()
  })
})
</script>

<style scoped>
.chat-stream {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-item {
  display: flex;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 输入区域 - 优化样式 */
.input-area {
  padding: 16px 24px 20px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 8px 12px;
  transition: all var(--transition-fast);
}

.input-wrapper:focus-within {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-sm);
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  padding: 8px 0;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  resize: none;
}

.message-input :deep(.el-textarea__inner::placeholder) {
  color: var(--text-ghost);
}

.message-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.input-actions {
  display: flex;
  align-items: center;
  padding-bottom: 4px;
}

.send-btn {
  border-radius: var(--radius-md);
  font-weight: 500;
  background: var(--text-primary);
  border-color: var(--text-primary);
  color: var(--bg-base);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 4px;
}

.send-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--bg-hover);
  transform: translateY(-1px);
}

.send-btn:disabled {
  background: var(--text-ghost);
  border-color: var(--text-ghost);
  color: var(--text-muted);
}
</style>

