import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref([])
  const isLoading = ref(false)
  const sessionId = ref(null)
  const userId = ref('anonymous')
  const workflowState = ref({
    complete: false,
    waiting_for_user: false,
    conversation_stage: null,
    understanding_level: null,
    analysis: null,
    plan: null,
    execution_summary: null,
    performance_data: null
  })
  const socraticDialogue = ref(null)
  const nextSuggestions = ref([])
  const thoughtProcess = ref(null)

  // Getters
  const hasMessages = computed(() => messages.value.length > 0)
  const isWaitingForUser = computed(() => workflowState.value.waiting_for_user)

  // Actions
  function addMessage(message) {
    messages.value.push({
      ...message,
      id: message.id || `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: message.timestamp || new Date()
    })
  }

  function clearMessages() {
    messages.value = []
  }

  function setLoading(loading) {
    isLoading.value = loading
  }

  function setSessionId(id) {
    sessionId.value = id
  }

  function setUserId(id) {
    userId.value = id
  }

  function updateWorkflowState(state) {
    workflowState.value = {
      ...workflowState.value,
      ...state
    }
  }

  function setSocraticDialogue(dialogue) {
    socraticDialogue.value = dialogue
  }

  function setNextSuggestions(suggestions) {
    nextSuggestions.value = suggestions || []
  }

  function setThoughtProcess(process) {
    thoughtProcess.value = process
  }

  function clearSession() {
    messages.value = []
    sessionId.value = null
    workflowState.value = {
      complete: false,
      waiting_for_user: false,
      conversation_stage: null,
      understanding_level: null,
      analysis: null,
      plan: null,
      execution_summary: null,
      performance_data: null
    }
    socraticDialogue.value = null
    nextSuggestions.value = []
    thoughtProcess.value = null
  }

  return {
    // State
    messages,
    isLoading,
    sessionId,
    userId,
    workflowState,
    socraticDialogue,
    nextSuggestions,
    thoughtProcess,
    // Getters
    hasMessages,
    isWaitingForUser,
    // Actions
    addMessage,
    clearMessages,
    setLoading,
    setSessionId,
    setUserId,
    updateWorkflowState,
    setSocraticDialogue,
    setNextSuggestions,
    setThoughtProcess,
    clearSession
  }
}, {
  persist: {
    key: 'edupilot-chat',
    storage: localStorage,
    paths: ['messages', 'sessionId', 'workflowState', 'socraticDialogue'],
    // 只持久化最近50条消息，避免localStorage过大
    beforeRestore: (ctx) => {
      if (ctx.store.messages && ctx.store.messages.length > 50) {
        ctx.store.messages = ctx.store.messages.slice(-50)
      }
    }
  }
})
