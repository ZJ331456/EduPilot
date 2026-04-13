<template>
  <div class="chat-view">
    <div class="chat-layout">
      <!-- 左侧主对话区 -->
      <div class="chat-main">
        <div class="chat-card">
          <!-- 头部 -->
          <div class="chat-header">
            <div class="header-left">
              <div class="header-icon">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="header-info">
                <h2 class="header-title">智能学习对话</h2>
                <span class="header-status" v-if="sessionId">
                  <span class="status-dot"></span>
                  会话进行中
                </span>
              </div>
            </div>
            <div class="header-actions">
              <el-button
                v-if="sessionId"
                size="small"
                @click="endSession"
                type="danger"
                plain
              >
                结束会话
              </el-button>
            </div>
          </div>

          <!-- 模式切换 -->
          <div class="mode-tabs">
            <button
              class="mode-tab"
              :class="{ active: currentMode === 'direct' }"
              @click="currentMode = 'direct'"
            >
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              直接对话
            </button>
            <button
              class="mode-tab"
              :class="{ active: currentMode === 'socratic' }"
              @click="currentMode = 'socratic'"
            >
              <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.40912C11.0108 7.05014 11.7289 6.91894 12.4272 7.03871C13.1255 7.15849 13.7588 7.52152 14.2151 8.06353C14.6713 8.60553 14.9211 9.29152 14.92 10C14.92 12 11.92 13 11.92 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M12 17H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              苏格拉底式
            </button>
          </div>

          <!-- 消息列表 -->
          <div class="messages-container" ref="messagesContainer">
            <!-- 空状态 -->
            <div v-if="messages.length === 0" class="empty-state">
              <div class="empty-illustration">
                <svg viewBox="0 0 120 120" fill="none">
                  <circle cx="60" cy="60" r="50" fill="url(#emptyGrad)" opacity="0.1"/>
                  <path d="M60 30C41.879 30 27 44.879 27 63C27 81.121 41.879 96 60 96C78.121 96 93 81.121 93 63C93 44.879 78.121 30 60 30ZM60 86C47.85 86 38 76.15 38 64C38 51.85 47.85 42 60 42C72.15 42 82 51.85 82 64C82 76.15 72.15 86 60 86Z" fill="url(#emptyGrad)"/>
                  <circle cx="60" cy="64" r="8" fill="url(#emptyGrad)"/>
                  <defs>
                    <linearGradient id="emptyGrad" x1="27" y1="30" x2="93" y2="96">
                      <stop offset="0%" stop-color="#FFFFFF"/>
                      <stop offset="100%" stop-color="#CCCCCC"/>
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <h3 class="empty-title">开始你的学习之旅</h3>
              <p class="empty-desc">输入问题，我会为你提供智能解答或引导式学习</p>
              <div class="quick-actions">
                <button
                  v-for="q in quickQuestions"
                  :key="q"
                  class="quick-btn"
                  @click="useQuickQuestion(q)"
                >
                  {{ q }}
                </button>
              </div>
            </div>

            <!-- 消息列表 -->
            <div
              v-for="(message, index) in messages"
              :key="index"
              :class="['message-item', message.role]"
            >
              <div class="message-avatar">
                <div v-if="message.role === 'user'" class="avatar user">
                  <span>{{ userNameChar }}</span>
                </div>
                <div v-else class="avatar assistant">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M12 3L2 12H5V21H19V12H22L12 3Z" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="14" r="3" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
              </div>
              <div class="message-content">
                <div class="message-meta">
                  <span class="message-role">{{ message.role === 'user' ? '你' : 'EduPilot' }}</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-text markdown-content" v-html="formatMessage(message.content)"></div>

                <!-- 工作流步骤 -->
                <div v-if="message.workflow_steps && message.workflow_steps.length > 0" class="message-extra">
                  <el-collapse>
                    <el-collapse-item title="执行过程" name="workflow">
                      <el-timeline>
                        <el-timeline-item
                          v-for="(step, idx) in message.workflow_steps"
                          :key="idx"
                          :type="step.status === 'success' ? 'success' : 'danger'"
                          :timestamp="`${step.duration_ms.toFixed(0)}ms`"
                          placement="top"
                        >
                          <div class="workflow-step">
                            <span class="step-name">{{ step.step_name }}</span>
                            <el-tag size="small" type="success" effect="dark">{{ step.agent_name }}</el-tag>
                          </div>
                        </el-timeline-item>
                      </el-timeline>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>

            <!-- 加载状态 -->
            <div v-if="isLoading" class="message-item assistant loading">
              <div class="message-avatar">
                <div class="avatar assistant">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M12 3L2 12H5V21H19V12H22L12 3Z" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="14" r="3" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="input-container">
            <div class="input-wrapper">
              <textarea
                v-model="userInput"
                class="chat-input"
                :rows="3"
                :placeholder="currentMode === 'socratic' ? '输入问题，我将通过提问引导你思考...' : '输入你的问题...'"
                @keydown.ctrl.enter="sendMessage"
                :disabled="isLoading"
              ></textarea>
              <button
                class="send-btn"
                :class="{ disabled: !userInput.trim() || isLoading }"
                :disabled="!userInput.trim() || isLoading"
                @click="sendMessage"
              >
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <div class="input-hint">
              <span class="hint-icon">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 16V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <circle cx="12" cy="8" r="1" fill="currentColor"/>
                </svg>
              </span>
              按 Ctrl + Enter 快速发送
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧边栏 -->
      <div class="chat-sidebar">
        <!-- 会话信息 -->
        <div class="sidebar-card" v-if="sessionId">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 16V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <circle cx="12" cy="8" r="1" fill="currentColor"/>
            </svg>
            会话信息
          </h3>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">会话ID</span>
              <span class="info-value truncate">{{ sessionId }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">消息数</span>
              <span class="info-value">{{ messages.length }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">当前模式</span>
              <span class="info-value mode-badge" :class="currentMode">
                {{ currentMode === 'direct' ? '直接对话' : '苏格拉底式' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 下一步建议 -->
        <div class="sidebar-card" v-if="nextSuggestions.length > 0">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            下一步建议
          </h3>
          <div class="suggestion-list">
            <div
              v-for="(suggestion, idx) in nextSuggestions"
              :key="idx"
              class="suggestion-item"
            >
              <span class="suggestion-num">{{ idx + 1 }}</span>
              <span class="suggestion-text">{{ suggestion }}</span>
            </div>
          </div>
        </div>

        <!-- 快捷问题 -->
        <div class="sidebar-card">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.40912C11.0108 7.05014 11.7289 6.91894 12.4272 7.03871C13.1255 7.15849 13.7588 7.52152 14.2151 8.06353C14.6713 8.60553 14.9211 9.29152 14.92 10C14.92 12 11.92 13 11.92 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M12 17H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ currentMode === 'socratic' ? '苏格拉底引导问题' : '快捷问题' }}
          </h3>
          <div class="quick-questions">
            <button
              v-for="q in (currentMode === 'socratic' ? socraticQuestions : quickQuestions)"
              :key="q"
              class="quick-question-btn"
              @click="useQuickQuestion(q)"
            >
              {{ q }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'
import * as edupilot from '../api/edupilot'
import MarkdownIt from 'markdown-it'

// Markdown 配置
const md = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: true,
  typographer: true
})

// Store
const userStore = useUserStore()
const chatStore = useChatStore()

// 状态
const userInput = ref('')
const messagesContainer = ref(null)
const currentMode = ref('direct')

// 计算属性
const userId = computed(() => userStore.userId)
const sessionId = computed(() => userStore.sessionId)
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)
const nextSuggestions = computed(() => chatStore.nextSuggestions)

const userNameChar = computed(() => {
  const name = userStore.userName || '游'
  return name.charAt(0).toUpperCase()
})

// 快捷问题
const quickQuestions = [
  '解释一下机器学习中的梯度下降',
  '帮我总结一下链表和数组的区别',
  '什么是操作系统中的死锁？'
]

const socraticQuestions = [
  '为什么学习算法很重要？',
  '什么是递归？它和循环有什么联系？',
  '为什么我们需要数据结构？'
]

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 格式化消息
function formatMessage(content) {
  try {
    return md.render(content || '')
  } catch (error) {
    return `<p>${(content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>`
  }
}

// 使用快捷问题
function useQuickQuestion(question) {
  if (isLoading.value) return
  userInput.value = question
  nextTick(() => sendMessage())
}

// 发送消息
async function sendMessage() {
  const message = userInput.value.trim()
  if (!message || isLoading.value) return

  chatStore.addMessage({
    role: 'user',
    content: message
  })

  userInput.value = ''
  chatStore.setLoading(true)

  try {
    const response = await edupilot.chat({
      userId: userId.value,
      sessionId: sessionId.value,
      message,
      mode: currentMode.value,
      updateGraph: true
    })

    userStore.setSessionId(response.session_id)
    chatStore.setSessionId(response.session_id)

    chatStore.addMessage({
      role: 'assistant',
      content: response.reply
    })

    await nextTick()
    scrollToBottom()

  } catch (error) {
    console.error('发送消息失败:', error)
    chatStore.addMessage({
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后重试。'
    })
  } finally {
    chatStore.setLoading(false)
  }
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

// 结束会话
async function endSession() {
  try {
    await ElMessageBox.confirm(
      '确定要结束当前会话吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (sessionId.value) {
      await edupilot.endSession(sessionId.value, userId.value)
    }

    userStore.clearSession()
    chatStore.clearMessages()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('结束会话失败:', error)
    }
  }
}

// 监听消息变化
watch(messages, () => {
  nextTick(() => scrollToBottom())
}, { deep: true })

watch(isLoading, (newVal) => {
  if (newVal) {
    nextTick(() => scrollToBottom())
  }
})
</script>

<style scoped>
.chat-view {
  height: 100%;
}

.chat-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  height: 100%;
}

/* 主聊天区 */
.chat-main {
  display: flex;
  flex-direction: column;
}

.chat-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* 头部 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--border-color);
  background: transparent;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 38px;
  height: 38px;
  background: var(--text-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--bg-base);
}

.header-icon svg {
  width: 18px;
  height: 18px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.header-status .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
}

/* 模式切换 */
.mode-tabs {
  display: flex;
  gap: 8px;
  padding: 14px 24px;
  background: transparent;
  border-bottom: 1px solid var(--border-color);
}

.mode-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-tab svg {
  width: 16px;
  height: 16px;
}

.mode-tab:hover {
  border-color: var(--text-secondary);
  color: var(--text-primary);
}

.mode-tab.active {
  background: var(--text-primary);
  border-color: var(--text-primary);
  color: var(--bg-base);
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: transparent;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 40px;
}

.empty-illustration {
  width: 140px;
  height: 140px;
  margin-bottom: 24px;
}

.empty-illustration svg {
  width: 100%;
  height: 100%;
}

.empty-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 24px;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-btn {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-btn:hover {
  border-color: var(--text-secondary);
  color: var(--text-primary);
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.loading .message-content {
  background: var(--bg-card);
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.avatar.user {
  background: var(--text-primary);
  color: var(--bg-base);
}

.avatar.assistant {
  background: var(--bg-card);
  color: var(--text-primary);
}

.avatar svg {
  width: 18px;
  height: 18px;
}

.message-content {
  flex: 1;
  max-width: 72%;
  background: var(--bg-card);
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.message-item.user .message-content {
  background: var(--text-primary);
  color: var(--bg-base);
  border: none;
  border-radius: var(--radius-lg) var(--radius-lg) 4px var(--radius-lg);
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
}

.message-item.user .message-meta {
  border-bottom-color: rgba(0, 0, 0, 0.1);
}

.message-role {
  font-weight: 600;
  color: var(--text-primary);
}

.message-item.user .message-role {
  color: var(--bg-base);
}

.message-time {
  color: var(--text-muted);
}

.message-item.user .message-time {
  color: rgba(0, 0, 0, 0.4);
}

.message-text {
  line-height: 1.6;
  font-size: 14px;
}

.message-extra {
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

/* 加载动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.2s infinite;
  opacity: 0.5;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

/* 输入框 */
.input-container {
  padding: 18px 24px;
  background: transparent;
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  transition: all var(--transition-fast);
  color: var(--text-primary);
}

.chat-input:focus {
  outline: none;
  border-color: var(--text-secondary);
  background: var(--bg-card);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--text-primary);
  color: var(--bg-base);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-normal);
}

.send-btn svg {
  width: 18px;
  height: 18px;
}

.send-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
}

.send-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

.hint-icon {
  width: 14px;
  height: 14px;
}

.hint-icon svg {
  width: 100%;
  height: 100%;
}

/* 右侧边栏 */
.chat-sidebar {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sidebar-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  padding: 18px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 14px;
}

.card-title svg {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.truncate {
  max-width: 110px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mode-badge {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
}

.mode-badge.direct {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.mode-badge.socratic {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.suggestion-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--text-secondary);
  color: var(--bg-base);
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.suggestion-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quick-question-btn {
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-question-btn:hover {
  border-color: var(--text-secondary);
  color: var(--text-primary);
}

/* 响应式 */
@media (max-width: 1200px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .chat-sidebar {
    display: none;
  }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 14px 16px;
  }

  .messages-container {
    padding: 16px;
  }

  .input-container {
    padding: 14px 16px;
  }
}

/* 动画 */
@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-6px);
  }
}
</style>
