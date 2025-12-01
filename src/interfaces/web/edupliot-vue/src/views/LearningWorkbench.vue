<template>
  <div class="learning-workbench">
    <!-- 三栏布局容器 -->
    <div class="workbench-layout">
      <!-- 左侧导航栏 -->
      <div class="navigation-panel">
        <NavigationPanel
          :sessions="sessions"
          :current-session-id="sessionId"
          @select-session="handleSelectSession"
          @new-session="handleNewSession"
        />
      </div>

      <!-- 中控区：对话流 -->
      <div class="dialogue-panel">
        <ChatStream
          :messages="messages"
          :is-loading="isLoading"
          :workflow-state="workflowState"
          :thought-process="thoughtProcess"
          :socratic-dialogue="socraticDialogue"
          @send-message="handleSendMessage"
          @continue-session="handleContinueSession"
        />
      </div>

      <!-- 右侧画布：动态上下文 -->
      <div class="context-panel">
        <ContextCanvas
          :intent="currentIntent"
          :knowledge-graph="knowledgeGraph"
          :concept-note="conceptNote"
          :workflow-state="workflowState"
          @pin-content="handlePinContent"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import NavigationPanel from '../components/LearningWorkbench/NavigationPanel.vue'
import ChatStream from '../components/LearningWorkbench/ChatStream.vue'
import ContextCanvas from '../components/LearningWorkbench/ContextCanvas.vue'
import api from '../api'

// Stores
const chatStore = useChatStore()
const userStore = useUserStore()

// 状态
const sessions = ref([])
const thoughtProcess = ref(null)

// 计算属性
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)
const sessionId = computed(() => chatStore.sessionId)
const workflowState = computed(() => chatStore.workflowState)
const socraticDialogue = computed(() => chatStore.socraticDialogue)

// 从工作流状态提取意图和知识图谱
const currentIntent = computed(() => {
  if (!workflowState.value) return null
  return workflowState.value.analysis?.intent || workflowState.value.query_type
})

const knowledgeGraph = computed(() => {
  if (!workflowState.value) return null
  return workflowState.value.knowledge_sources || []
})

const conceptNote = computed(() => {
  if (!workflowState.value) return null
  return workflowState.value.plan?.reasoning || workflowState.value.response
})

// 转换工作流步骤为思考过程
const convertWorkflowSteps = (steps = []) => {
  return {
    isActive: steps.length > 0,
    steps: steps.map(step => ({
      title: `${getAgentLabel(step.agent_name)} (${step.step_name})`,
      message: step.status === 'success' ? `耗时 ${step.duration_ms.toFixed(0)}ms` : step.error,
      status: step.status === 'success' ? 'completed' : 'active' // 简化的状态映射
    }))
  }
}

const getAgentLabel = (name) => {
  const labels = {
    'QueryAnalyzer': '意图分析',
    'Orchestrator': '学习规划',
    'DraftWriter': '内容生成',
    'Reviewer': '内容审核',
    'CurriculumDesigner': '课程设计',
    'QuizMaster': '测验生成',
    'ToolSpecialist': '工具调用',
    'SocraticGuide': '苏格拉底引导',
    'KnowledgeManager': '知识检索'
  }
  return labels[name] || name
}

// 方法
const handleSendMessage = async (message) => {
  chatStore.setLoading(true)
  // 重置思考过程
  thoughtProcess.value = { isActive: true, steps: [] }
  
  try {
    const response = await api.workflow.startSession({
      user_id: userStore.userId,
      query: message,
      workflow_config: {
        enable_socratic: true,
        enable_learning: true
      }
    })
    
    // 更新思考过程
    if (response.workflow_steps) {
      thoughtProcess.value = convertWorkflowSteps(response.workflow_steps)
    }

    chatStore.addMessage({
      role: 'assistant',
      content: response.response,
      timestamp: new Date(),
      analysis: response.analysis,
      plan: response.plan,
      socratic_dialogue: response.socratic_dialogue
    })
    
    chatStore.setSessionId(response.session_id)
    chatStore.updateWorkflowState({
      complete: response.workflow_complete,
      waiting_for_user: response.waiting_for_user,
      conversation_stage: response.conversation_stage,
      understanding_level: response.understanding_level,
      analysis: response.analysis,
      knowledge_sources: response.analysis?.retrieval_plan?.query_strategy?.sources // 提取知识源
    })
    
    if (response.socratic_dialogue) {
      chatStore.setSocraticDialogue(response.socratic_dialogue)
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    chatStore.addMessage({
      role: 'system',
      content: '抱歉，系统遇到了一些问题。请稍后再试。',
      timestamp: new Date()
    })
  } finally {
    chatStore.setLoading(false)
  }
}

const handleContinueSession = async (userResponse) => {
  if (!sessionId.value) return
  
  chatStore.setLoading(true)
  thoughtProcess.value = { isActive: true, steps: [] }
  
  try {
    const response = await api.workflow.continueSession({
      session_id: sessionId.value,
      user_id: userStore.userId,
      user_response: userResponse
    })

    // 更新思考过程
    if (response.workflow_steps) {
      thoughtProcess.value = convertWorkflowSteps(response.workflow_steps)
    }
    
    chatStore.addMessage({
      role: 'assistant',
      content: response.response,
      timestamp: new Date(),
      socratic_dialogue: response.socratic_dialogue
    })
    
    chatStore.updateWorkflowState({
      complete: response.workflow_complete,
      waiting_for_user: response.waiting_for_user,
      conversation_stage: response.conversation_stage,
      understanding_level: response.understanding_level
    })

    if (response.socratic_dialogue) {
      chatStore.setSocraticDialogue(response.socratic_dialogue)
    }
  } catch (error) {
    console.error('继续会话失败:', error)
  } finally {
    chatStore.setLoading(false)
  }
}

const handleSelectSession = (session) => {
  // 加载历史会话
  chatStore.setSessionId(session.id)
  // TODO: 从API加载会话历史
}

const handleNewSession = () => {
  chatStore.clearMessages()
  chatStore.setSessionId(null)
}

const handlePinContent = (content) => {
  // 将内容固定到画布
  console.log('Pin content:', content)
}

// 生命周期
onMounted(() => {
  // 加载会话列表
  // TODO: 从API加载
})
</script>

<style scoped>
.learning-workbench {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}

.workbench-layout {
  display: grid;
  grid-template-columns: 240px 1fr 45%;
  height: 100%;
  gap: 0;
}

.navigation-panel {
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.dialogue-panel {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.context-panel {
  background: var(--bg-secondary);
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .workbench-layout {
    grid-template-columns: 200px 1fr 40%;
  }
}

@media (max-width: 1024px) {
  .workbench-layout {
    grid-template-columns: 1fr;
  }
  
  .navigation-panel,
  .context-panel {
    display: none;
  }
}
</style>

