<template>
  <div class="chat-view">
    <el-row :gutter="24">
      <!-- 主对话区 -->
      <el-col :xs="24" :lg="16">
        <el-card class="chat-card">
          <template #header>
            <div class="chat-header">
              <div class="header-left">
                <el-icon><ChatDotRound /></el-icon>
                <span>智能学习对话</span>
                <el-tag v-if="sessionId" type="success" size="small" effect="plain">
                  会话中
                </el-tag>
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
          </template>

          <!-- 消息列表 -->
          <div class="messages-container" ref="messagesContainer">
            <div v-if="messages.length === 0" class="empty-state">
              <el-empty description="开始你的学习之旅吧！">
                <template #image>
                  <el-icon :size="80" color="#e5e7eb"><Reading /></el-icon>
                </template>
              </el-empty>
            </div>

            <div 
              v-for="(message, index) in messages" 
              :key="index"
              :class="['message-item', message.role]"
            >
              <div class="message-avatar">
                <!-- 用户头像 -->
                <el-avatar 
                  v-if="message.role === 'user'"
                  :size="40" 
                  class="user-avatar"
                >
                  <el-icon :size="20"><UserFilled /></el-icon>
                </el-avatar>
                <!-- 系统头像 -->
                <el-avatar 
                  v-else 
                  :size="40" 
                  class="assistant-avatar"
                >
                  <el-icon :size="20"><ChatDotSquare /></el-icon>
                </el-avatar>
              </div>
              <div class="message-content">
                <div class="message-meta">
                  <span class="message-role">
                    {{ message.role === 'user' ? '你' : 'EduPilot' }}
                  </span>
                  <span class="message-time">
                    {{ formatTime(message.timestamp) }}
                  </span>
                </div>
                <div class="message-text" v-html="formatMessage(message.content)"></div>
                
                <!-- 显示苏格拉底式对话信息 -->
                <SocraticDialogue 
                  v-if="message.socratic_dialogue" 
                  :dialogue="message.socratic_dialogue" 
                />
                
                <!-- 显示工作流步骤 (新版) -->
                <div v-if="message.workflow_steps && message.workflow_steps.length > 0" class="message-extra">
                  <el-collapse>
                    <el-collapse-item title="工作流执行过程" name="workflow">
                       <el-timeline>
                        <el-timeline-item
                          v-for="(step, idx) in message.workflow_steps"
                          :key="idx"
                          :type="step.status === 'success' ? 'success' : 'danger'"
                          :timestamp="`${step.duration_ms.toFixed(0)}ms`"
                          placement="top"
                        >
                          <el-card class="workflow-step-card" shadow="hover">
                            <template #header>
                              <div class="step-header">
                                <span class="step-name">{{ step.step_name }}</span>
                                <el-tag size="small" effect="dark">{{ step.agent_name }}</el-tag>
                              </div>
                            </template>
                            
                            <!-- 步骤结果展示 -->
                            <div class="step-content">
                                <!-- Analysis -->
                                <div v-if="step.agent_name === 'QueryAnalyzer'">
                                    <p><strong>Intent:</strong> {{ step.result.intent }}</p>
                                </div>
                                
                                <!-- Orchestrator -->
                                <div v-if="step.agent_name === 'Orchestrator' && step.result.next_workers">
                                    <p><strong>Next Workers:</strong> {{ step.result.next_workers }}</p>
                                </div>

                                <!-- DraftWriter -->
                                <div v-if="step.agent_name === 'DraftWriter'">
                                    <p>初稿已生成</p>
                                </div>

                                <!-- Reviewer -->
                                <div v-if="step.agent_name === 'Reviewer'">
                                    <p>审核完成</p>
                                </div>
                                
                                <!-- ToolSpecialist -->
                                <div v-if="step.agent_name === 'ToolSpecialist' && step.result.outputs">
                                     <div v-for="(output, tool_name) in step.result.outputs" :key="tool_name">
                                        <p><strong>{{ tool_name }}:</strong> {{ output }}</p>
                                     </div>
                                </div>

                                 <!-- CurriculumDesigner -->
                                <div v-if="step.agent_name === 'CurriculumDesigner' && step.result.topic">
                                    <p><strong>Topic:</strong> {{ step.result.topic }}</p>
                                </div>
                            </div>
                          </el-card>
                        </el-timeline-item>
                      </el-timeline>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <!-- 显示分析结果 (旧版兼容) -->
                <div v-else-if="message.analysis" class="message-extra">
                  <el-collapse>
                    <el-collapse-item title="查询分析" name="analysis">
                      <el-descriptions :column="2" size="small" border>
                        <el-descriptions-item label="意图">
                          <el-tag size="small" effect="plain">{{ message.analysis.intent }}</el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="查询类型">
                          <el-tag size="small" type="success" effect="plain">
                            {{ message.analysis.query_type }}
                          </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="置信度">
                          <el-progress 
                            :percentage="message.analysis.confidence * 100" 
                            :format="() => (message.analysis.confidence * 100).toFixed(1) + '%'"
                          />
                        </el-descriptions-item>
                      </el-descriptions>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <!-- 显示学习计划 -->
                <div v-if="message.plan" class="message-extra">
                  <el-collapse>
                    <el-collapse-item title="学习计划" name="plan">
                      <div class="plan-content">
                        <!-- 计划类型 -->
                        <div v-if="message.plan.plan_type" style="margin-bottom: 12px">
                          <el-tag type="info" size="small" effect="plain">
                            {{ message.plan.plan_type }}
                          </el-tag>
                        </div>
                        
                        <!-- 推理说明 -->
                        <div v-if="message.plan.reasoning" class="plan-reasoning">
                          <div class="reasoning-title">
                            💡 规划思路
                          </div>
                          <div class="reasoning-text">
                            {{ message.plan.reasoning }}
                          </div>
                        </div>
                        
                        <!-- 行动项 -->
                        <div v-if="message.plan.action_items && message.plan.action_items.length > 0">
                          <div class="steps-title">
                            📋 执行步骤
                          </div>
                          <el-steps 
                            direction="vertical" 
                            :active="message.plan.action_items.length"
                          >
                            <el-step 
                              v-for="(action, idx) in message.plan.action_items" 
                              :key="idx"
                              :title="`步骤${idx + 1}: ${action.action_type || '执行动作'}`"
                              :description="action.description || '暂无描述'"
                              status="success"
                            />
                          </el-steps>
                        </div>
                        
                        <!-- 空状态提示 -->
                        <el-empty 
                          v-if="!message.plan.plan_type && !message.plan.action_items?.length && !message.plan.reasoning" 
                          description="学习计划生成中..."
                          :image-size="60"
                        />
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>

            <!-- 加载状态 -->
            <div v-if="isLoading" class="message-item assistant">
              <div class="message-avatar">
                <el-avatar :size="40" class="assistant-avatar loading-avatar">
                  <el-icon :size="20"><ChatDotSquare /></el-icon>
                </el-avatar>
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
            <el-input
              v-model="userInput"
              type="textarea"
              :rows="3"
              placeholder="输入你的问题，开始学习之旅..."
              @keydown.ctrl.enter="sendMessage"
              :disabled="isLoading"
              class="chat-input"
            />
            <div class="input-actions">
              <div class="input-hint">
                <el-icon><InfoFilled /></el-icon>
                按 Ctrl+Enter 快速发送
              </div>
              <el-button 
                type="primary" 
                size="large"
                @click="sendMessage"
                :loading="isLoading"
                :disabled="!userInput.trim()"
                class="send-button"
              >
                <el-icon><Promotion /></el-icon>
                <span>发送消息</span>
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 侧边栏 -->
      <el-col :xs="24" :lg="8">
        <!-- 快速提示 -->
        <el-card class="sidebar-card">
          <template #header>
            <div class="card-header">
              <el-icon><QuestionFilled /></el-icon>
              <span>{{ currentQuestionType === 'socratic' ? '苏格拉底式引导' : '快速示例' }}</span>
              <el-button 
                size="small" 
                text 
                @click="toggleQuestionType"
                class="toggle-btn"
              >
                <el-icon>
                  <QuestionFilled v-if="currentQuestionType === 'normal'" />
                  <ChatLineRound v-else />
                </el-icon>
                {{ currentQuestionType === 'normal' ? '苏格拉底模式' : '普通模式' }}
              </el-button>
            </div>
          </template>
          <div class="quick-questions">
            <el-button 
              v-for="q in currentQuestions" 
              :key="q"
              text
              size="small"
              @click="useQuickQuestion(q)"
              :class="['quick-question-btn', currentQuestionType === 'socratic' ? 'socratic-btn' : '']"
            >
              <el-icon>
                <ChatLineRound v-if="currentQuestionType === 'socratic'" />
                <QuestionFilled v-else />
              </el-icon>
              {{ q }}
            </el-button>
          </div>
          
          <!-- 苏格拉底式对话说明 -->
          <div v-if="currentQuestionType === 'socratic'" class="socratic-hint">
            <el-alert
              title="苏格拉底式引导"
              type="info"
              :closable="false"
              show-icon
              size="small"
            >
              <template #default>
                <div style="font-size: 12px; line-height: 1.4;">
                  通过提问的方式引导你深入思考，帮助你建立对知识的全面理解。
                  选择下方问题开始苏格拉底式学习体验！
                </div>
              </template>
            </el-alert>
          </div>
        </el-card>

        <!-- 工作流状态 -->
        <WorkflowStatus 
          v-if="workflowState" 
          :workflow-state="workflowState"
          :socratic-dialogue="socraticDialogue"
        />

        <!-- 会话信息 -->
        <el-card class="sidebar-card" v-if="sessionId">
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>会话信息</span>
            </div>
          </template>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="会话ID">
              <el-text size="small" truncated style="width: 150px">{{ sessionId }}</el-text>
            </el-descriptions-item>
            <el-descriptions-item label="消息数">
              {{ messages.length }}
            </el-descriptions-item>
            <el-descriptions-item label="用户ID">
              <el-text size="small" truncated style="width: 150px">{{ userId }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 下一步建议 -->
        <el-card class="sidebar-card" v-if="nextSuggestions.length > 0">
          <template #header>
            <div class="card-header">
              <el-icon><Guide /></el-icon>
              <span>下一步建议</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item 
              v-for="(suggestion, idx) in nextSuggestions" 
              :key="idx"
              size="small"
              type="primary"
              hollow
            >
              {{ suggestion }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  UserFilled,
  ChatDotSquare,
  Reading,
  QuestionFilled,
  ChatLineRound,
  InfoFilled,
  Guide,
  Promotion
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'
import { useThrottleFn } from '../composables/useThrottle'
import api from '../api'
import MarkdownIt from 'markdown-it'
import SocraticDialogue from '../components/SocraticDialogue.vue'
import WorkflowStatus from '../components/WorkflowStatus.vue'
import {
  formatDate,
  showError,
  showSuccess,
  showWarning,
  DEFAULT_QUICK_QUESTIONS,
  SOCRATIC_TRIGGER_QUESTIONS,
  DEBOUNCE_DELAYS
} from '../utils'

// 配置 markdown-it
const md = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: true,
  typographer: true
})

const userStore = useUserStore()
const chatStore = useChatStore()

const userId = computed(() => userStore.userId)
const sessionId = computed(() => userStore.sessionId)
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

const workflowState = computed(() => chatStore.workflowState)
const socraticDialogue = computed(() => chatStore.socraticDialogue)
const nextSuggestions = computed(() => chatStore.nextSuggestions)

const userInput = ref('')
const messagesContainer = ref(null)

const quickQuestions = DEFAULT_QUICK_QUESTIONS
const socraticQuestions = SOCRATIC_TRIGGER_QUESTIONS
const currentQuestionType = ref('normal')

function formatTime(timestamp) {
  return formatDate(timestamp, 'time')
}

function formatMessage(content) {
  try {
    return md.render(content || '')
  } catch (error) {
    console.warn('Markdown 解析失败:', error)
    return `<p>${(content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>`
  }
}

function useQuickQuestion(question) {
  if (isLoading.value) {
    showWarning('请等待当前消息发送完成')
    return
  }
  userInput.value = question
  nextTick(() => {
    sendMessage()
  })
}

function toggleQuestionType() {
  currentQuestionType.value = currentQuestionType.value === 'normal' ? 'socratic' : 'normal'
}

const currentQuestions = computed(() => {
  return currentQuestionType.value === 'socratic' ? socraticQuestions : quickQuestions
})

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
    let response

    if (sessionId.value) {
      response = await api.workflow.continueSession({
        session_id: sessionId.value,
        user_id: userId.value,
        user_response: message
      })
    } else {
      response = await api.workflow.startSession({
        user_id: userId.value,
        query: message,
        workflow_config: {
          enable_socratic: true,
          enable_learning: true
        }
      })
      userStore.setSessionId(response.session_id)
    }

    chatStore.addMessage({
      role: 'assistant',
      content: response.response,
      analysis: response.analysis,
      plan: response.plan,
      execution_summary: response.execution_summary,
      socratic_dialogue: response.socratic_dialogue
    })

    if (response.workflow_complete !== undefined) {
      chatStore.updateWorkflowState({
        complete: response.workflow_complete,
        waitingForUser: response.waiting_for_user,
        conversationStage: response.conversation_stage,
        understandingLevel: response.understanding_level,
        conversationRound: response.conversation_round
      })
    }

    if (response.socratic_dialogue) {
      chatStore.setSocraticDialogue(response.socratic_dialogue)
    }

    if (response.next_suggestions) {
      chatStore.setNextSuggestions(response.next_suggestions)
    }

    await nextTick()
    scrollToBottom()

  } catch (error) {
    console.error('发送消息失败:', error)
    showError(error, '发送失败，请重试')
  } finally {
    chatStore.setLoading(false)
  }
}

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
      await api.workflow.endSession(sessionId.value)
    }

    userStore.clearSession()
    chatStore.clearMessages()
    
    showSuccess('会话已结束')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('结束会话失败:', error)
      showError(error, '结束会话失败')
    }
  }
}

const scrollToBottom = useThrottleFn((smooth = true) => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    })
  }
}, DEBOUNCE_DELAYS.SCROLL)

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
  max-width: 1400px;
  margin: 0 auto;
}

.chat-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
  border-radius: 12px;
}

.chat-card :deep(.el-card__header) {
  padding: 16px 24px;
  border-bottom: 1px solid #f3f4f6;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #1f2937;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f9fafb;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.message-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-item.user {
  flex-direction: row-reverse;
}

/* 修正用户消息气泡颜色 */
.message-item.user .message-content {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  color: white;
  border: none;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
}

/* 修正用户消息中的文本颜色 */
.message-item.user .message-text,
.message-item.user .message-text :deep(p) {
  color: white;
}

.message-avatar {
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2);
  border: 2px solid #fff;
}

.assistant-avatar {
  background: #ffffff !important;
  color: #4f46e5;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.loading-avatar {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(79, 70, 229, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(79, 70, 229, 0); }
}

/* 助手消息气泡 */
.message-content {
  flex: 1;
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 12px;
  max-width: 80%;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: #374151;
}

.message-item.user .message-content .message-meta {
  border-bottom-color: rgba(255,255,255,0.2);
}

.message-item.user .message-role,
.message-item.user .message-time {
  color: rgba(255,255,255,0.9);
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}

.message-role {
  font-weight: 600;
  color: #111827;
}

.message-time {
  color: #9ca3af;
  font-size: 12px;
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
  font-size: 15px;
}

.message-text :deep(p) {
  margin: 8px 0;
}

/* 代码块样式修复 */
.message-text :deep(pre) {
  background: #1f2937;
  color: #f9fafb;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-text :deep(code) {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

.message-item:not(.user) .message-text :deep(code) {
  background: #f3f4f6;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 4px;
}

.message-extra {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.workflow-step-card {
  margin-bottom: 8px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-name {
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.step-content {
  font-size: 13px;
  color: #6b7280;
}

.step-content p {
  margin: 4px 0;
}

.plan-reasoning {
  background: #f9fafb;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
}

.reasoning-title, .steps-title {
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  margin-bottom: 6px;
}

.reasoning-text {
  color: #4b5563;
  font-size: 14px;
  line-height: 1.5;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.input-container {
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  background: #ffffff;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  border-color: #d1d5db;
  padding: 12px;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.chat-input :deep(.el-textarea__inner):focus {
  background: #ffffff;
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.input-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #9ca3af;
}

.send-button {
  border-radius: 20px;
  padding: 8px 24px;
  background: #4f46e5;
  border-color: #4f46e5;
  font-weight: 600;
}

.send-button:hover {
  background: #4338ca;
  border-color: #4338ca;
  transform: translateY(-1px);
}

.sidebar-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  margin-bottom: 16px;
}

.sidebar-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.toggle-btn {
  margin-left: auto;
  color: #4f46e5;
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-question-btn {
  justify-content: flex-start;
  text-align: left;
  white-space: normal;
  height: auto;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  color: #4b5563;
}

.quick-question-btn:hover {
  background: #f5f3ff;
  color: #4f46e5;
  border-color: #c7d2fe;
}

.socratic-btn {
  border-left: 3px solid #10b981 !important;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .chat-card {
    height: calc(100vh - 120px);
    margin-bottom: 20px;
  }
}
</style>
