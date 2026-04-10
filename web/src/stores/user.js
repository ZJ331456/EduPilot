import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // State
  const userId = ref(localStorage.getItem('userId') || `user_${Date.now()}`)
  const sessionId = ref(null)
  const userName = ref(localStorage.getItem('userName') || '学习者')
  
  // Getters
  const isLoggedIn = computed(() => !!userId.value)
  
  // Actions
  function setUserId(id) {
    userId.value = id
    localStorage.setItem('userId', id)
  }
  
  function setUserName(name) {
    userName.value = name
    localStorage.setItem('userName', name)
  }
  
  function setSessionId(id) {
    sessionId.value = id
  }
  
  function clearSession() {
    sessionId.value = null
  }
  
  return {
    userId,
    sessionId,
    userName,
    isLoggedIn,
    setUserId,
    setUserName,
    setSessionId,
    clearSession
  }
})

