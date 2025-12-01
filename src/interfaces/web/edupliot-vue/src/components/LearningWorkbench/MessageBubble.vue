<template>
  <div :class="['message-bubble', message.role]">
    <div class="message-avatar">
      <el-avatar :size="40">
        <el-icon v-if="message.role === 'user'"><UserFilled /></el-icon>
        <el-icon v-else><ChatDotSquare /></el-icon>
      </el-avatar>
    </div>
    <div class="message-content">
      <div class="message-text" v-html="formatMessage(message.content)"></div>
      <div v-if="message.timestamp" class="message-time">
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { UserFilled, ChatDotSquare } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { formatTime } from '../../utils/format'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true
})

const formatMessage = (content) => {
  if (!content) return ''
  return md.render(content)
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-bubble.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-bubble.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-bubble.assistant .message-text {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  backdrop-filter: blur(10px);
}

.message-time {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 4px;
  padding: 0 4px;
}
</style>

