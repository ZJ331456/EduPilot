/**
 * EduPilot 新后端 /api/v1 客户端（与 FastAPI 对齐）
 */
import axios from 'axios'

const edupilot = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

export async function healthCheck() {
  const { data } = await edupilot.get('/health')
  return data
}

export async function chat({ userId, sessionId, message, mode = 'direct', updateGraph = true }) {
  const body = {
    user_id: userId,
    session_id: sessionId || null,
    message,
    mode,
    update_graph: updateGraph
  }
  const { data } = await edupilot.post('/chat', body)
  return data
}

export async function endSession(sessionId, userId) {
  const { data } = await edupilot.post(`/chat/sessions/${sessionId}/end`, { user_id: userId })
  return data
}

export async function getKnowledgeGraph(kbId) {
  const { data } = await edupilot.get(`/graph/knowledge/${kbId}`)
  return data
}

export async function queryKnowledgeGraph(kbId, q, mode = 'local') {
  const { data } = await edupilot.get(`/graph/knowledge/${kbId}/query`, {
    params: { q, mode }
  })
  return data
}

export async function indexKnowledge(kbId, sourcePath = null, useSample = false) {
  const { data } = await edupilot.post(`/graph/knowledge/${kbId}/index`, {
    source_path: sourcePath,
    use_sample: useSample
  })
  return data
}

export async function getDialogueGraph(sessionId) {
  const { data } = await edupilot.get(`/graph/session/${sessionId}`)
  return data
}

export async function getUserLongGraph(userId) {
  const { data } = await edupilot.get(`/graph/user/${userId}/long_term`)
  return data
}

export async function analyzeProfile(payload) {
  const { data } = await edupilot.post('/profile/analyze', payload)
  return data
}

export async function getProfile(userId) {
  const { data } = await edupilot.get(`/profile/${userId}`)
  return data
}

export async function generatePlan(userId, goalHint = '') {
  const { data } = await edupilot.post('/plan/generate', {
    user_id: userId,
    goal_hint: goalHint
  })
  return data
}

export async function getPlan(userId) {
  const { data } = await edupilot.get(`/plan/${userId}`)
  return data
}

export async function runEvaluation(payload) {
  const { data } = await edupilot.post('/evaluation/run', payload)
  return data
}

export default edupilot
