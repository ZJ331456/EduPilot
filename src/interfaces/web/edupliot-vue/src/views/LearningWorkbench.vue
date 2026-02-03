<template>
  <div class="learning-workbench">
    <!-- 左侧导航栏 -->
    <aside class="side-panel left-panel" :class="{ 'is-collapsed': !isLeftPanelOpen }">
      <div class="panel-header">
        <span class="panel-title">历史会话</span>
        <el-button link class="close-btn" @click="toggleLeftPanel">
          <el-icon><Fold /></el-icon>
        </el-button>
      </div>
      <div class="panel-content custom-scrollbar">
        <NavigationPanel
          :sessions="sessions"
          :current-session-id="sessionId"
          @select-session="handleSelectSession"
          @new-session="handleNewSession"
        />
      </div>
    </aside>

    <!-- 中控区：对话流 -->
    <main class="main-panel">
      <!-- 顶部工具栏 -->
      <header class="workspace-header">
        <div class="header-left">
          <el-tooltip content="展开会话列表" placement="bottom" v-if="!isLeftPanelOpen">
            <el-button link @click="toggleLeftPanel" class="toggle-btn">
              <el-icon><Expand /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
        
        <div class="header-center">
          <h2 class="workspace-title">EduPilot 智能学习助手</h2>
        </div>

        <div class="header-right">
          <el-tooltip content="展开知识面板" placement="bottom" v-if="!isRightPanelOpen">
            <el-button link @click="toggleRightPanel" class="toggle-btn">
              <el-icon><Operation /></el-icon>
              <span class="btn-text">知识面板</span>
            </el-button>
          </el-tooltip>
        </div>
      </header>

      <!-- 对话区域 -->
      <div class="chat-container">
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
    </main>

    <!-- 右侧画布：动态上下文 -->
    <aside class="side-panel right-panel" :class="{ 'is-collapsed': !isRightPanelOpen }">
      <div class="panel-header">
        <span class="panel-title">知识上下文</span>
        <div class="header-actions">
           <el-tooltip content="固定面板" placement="top">
             <el-icon class="action-icon"><Pushpin /></el-icon>
           </el-tooltip>
           <el-button link class="close-btn" @click="toggleRightPanel">
            <el-icon><DArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="panel-content custom-scrollbar">
        <ContextCanvas
          :intent="currentIntent"
          :knowledge-graph="knowledgeGraph"
          :concept-note="conceptNote"
          :workflow-state="workflowState"
          @pin-content="handlePinContent"
        />
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { useUserStore } from '../stores/user'
import NavigationPanel from '../components/LearningWorkbench/NavigationPanel.vue'
import ChatStream from '../components/LearningWorkbench/ChatStream.vue'
import ContextCanvas from '../components/LearningWorkbench/ContextCanvas.vue'
import api from '../api'
import { 
  Expand, Fold, Operation, DArrowRight, Pushpin
} from '@element-plus/icons-vue'

// Stores
const chatStore = useChatStore()
const userStore = useUserStore()

// UI 状态
const isLeftPanelOpen = ref(true)
const isRightPanelOpen = ref(true)

// 数据状态
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

// UI 方法
const toggleLeftPanel = () => {
  isLeftPanelOpen.value = !isLeftPanelOpen.value
}

const toggleRightPanel = () => {
  isRightPanelOpen.value = !isRightPanelOpen.value
}

// 转换工作流步骤为思考过程
const convertWorkflowSteps = (steps = []) => {
  return {
    isActive: steps.length > 0,
    steps: steps.map(step => ({
      title: `${getAgentLabel(step.agent_name)} (${step.step_name})`,
      message: step.status === 'success' ? `耗时 ${step.duration_ms.toFixed(0)}ms` : step.error,
      status: step.status === 'success' ? 'completed' : 'active'
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

// 业务方法
const handleSendMessage = async (message) => {
  chatStore.setLoading(true)
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
      knowledge_sources: response.analysis?.retrieval_plan?.query_strategy?.sources
    })
    
    if (response.socratic_dialogue) {
      chatStore.setSocraticDialogue(response.socratic_dialogue)
    }
    
    // 自动展开右侧面板如果有丰富内容
    if (response.analysis || response.knowledge_sources?.length > 0) {
      if (!isRightPanelOpen.value && window.innerWidth > 1400) {
        isRightPanelOpen.value = true
      }
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
  chatStore.setSessionId(session.id)
  // TODO: Load history
}

const handleNewSession = () => {
  chatStore.clearMessages()
  chatStore.setSessionId(null)
}

const handlePinContent = (content) => {
  console.log('Pin content:', content)
}

onMounted(() => {
  // TODO: Load session list
  // 响应式初始状态
  if (window.innerWidth < 1200) {
    isRightPanelOpen.value = false
  }
  if (window.innerWidth < 768) {
    isLeftPanelOpen.value = false
  }
})
</script>

<style scoped>
.learning-workbench {
  height: 100vh;
  width: 100vw;
  display: flex;
  background: #f5f7fa;
  overflow: hidden;
  position: relative;
}

/* 侧边栏通用样式 */
.side-panel {
  height: 100%;
  background: #ffffff;
  border-right: 1px solid #eef0f2;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 10;
  box-shadow: 2px 0 8px rgba(0,0,0,0.02);
}

.left-panel {
  width: 260px;
  flex-shrink: 0;
}

.right-panel {
  width: 420px;
  flex-shrink: 0;
  border-left: 1px solid #eef0f2;
  border-right: none;
  box-shadow: -2px 0 8px rgba(0,0,0,0.02);
}

/* 折叠状态 */
.side-panel.is-collapsed {
  width: 0;
  overflow: hidden;
  border: none;
  opacity: 0;
}

/* 面板头部 */
.panel-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f2f5;
  background: #ffffff;
  flex-shrink: 0;
}

.panel-title {
  font-weight: 600;
  font-size: 14px;
  color: #1a1a1a;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
}

/* 中间主区域 */
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 防止 flex 子项溢出 */
  background: #f5f7fa;
  position: relative;
}

/* 顶部工具栏 */
.workspace-header {
  height: 56px;
  padding: 0 20px;
  background: #ffffff;
  border-bottom: 1px solid #eef0f2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  z-index: 5;
}

.workspace-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  letter-spacing: 0.5px;
}

.header-left, .header-right {
  width: 100px; /* 占位平衡 */
  display: flex;
  align-items: center;
}

.header-right {
  justify-content: flex-end;
}

.toggle-btn {
  font-size: 18px;
  color: #606266;
  padding: 8px;
}

.toggle-btn:hover {
  color: #409eff;
  background-color: #ecf5ff;
}

.btn-text {
  font-size: 14px;
  margin-left: 4px;
}

/* 聊天区域 */
.chat-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* 辅助样式 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-icon {
  font-size: 16px;
  color: #909399;
  cursor: pointer;
  transition: color 0.2s;
}

.action-icon:hover {
  color: #409eff;
}

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e0e3e9;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

/* 响应式调整 */
@media (max-width: 1280px) {
  .right-panel {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .learning-workbench {
    flex-direction: column;
  }
  
  .side-panel {
    position: absolute;
    height: 100%;
    z-index: 100;
  }
  
  .right-panel {
    right: 0;
    width: 85%;
    transform: translateX(100%);
  }
  
  .right-panel:not(.is-collapsed) {
    transform: translateX(0);
  }
  
  .left-panel {
    left: 0;
    width: 80%;
    transform: translateX(-100%);
  }
  
  .left-panel:not(.is-collapsed) {
    transform: translateX(0);
  }
  
  /* 在移动端覆盖默认的 width: 0 隐藏方式，改用 transform */
  .side-panel.is-collapsed {
    width: auto; /* 恢复宽度以便 transform 生效 */
    /* pointer-events: none; */
  }
}
</style>

