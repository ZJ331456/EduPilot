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
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="3"
        placeholder="输入你的问题，开始学习之旅..."
        @keydown.ctrl.enter="handleSend"
        :disabled="isLoading"
      />
      <div class="input-actions">
        <el-button
          type="primary"
          @click="handleSend"
          :loading="isLoading"
          :disabled="!userInput.trim()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Reading, Loading } from '@element-plus/icons-vue'
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

.input-area {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.input-actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}
</style>

