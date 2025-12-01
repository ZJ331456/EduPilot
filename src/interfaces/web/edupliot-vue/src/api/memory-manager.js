/**
 * 记忆管理器 API
 * 对应后端: /api/agent/v1/memory-manager/
 * Core 模块: core.agents.memory_manager
 */

import apiClient from './client'

export default {
  /**
   * 获取用户画像
   * GET /memory-manager/profile/:userId
   */
  getProfile(userId, params = {}) {
    return apiClient.get(`/memory-manager/profile/${userId}`, { params })
  },

  /**
   * 更新用户画像
   * POST /memory-manager/profile/:userId/update
   */
  updateProfile(userId, data) {
    return apiClient.post(`/memory-manager/profile/${userId}/update`, data)
  },

  /**
   * 获取会话记忆
   * GET /memory-manager/session/:sessionId
   */
  getSession(sessionId, params = {}) {
    return apiClient.get(`/memory-manager/session/${sessionId}`, { params })
  },

  /**
   * 分析会话记忆
   * POST /memory-manager/session/analyze
   */
  analyzeSession(data) {
    return apiClient.post('/memory-manager/session/analyze', data)
  },

  /**
   * 获取学习记录
   * GET /memory-manager/learning-records/:userId
   */
  getLearningRecords(userId, params = {}) {
    return apiClient.get(`/memory-manager/learning-records/${userId}`, { params })
  },

  /**
   * 获取知识图谱
   * GET /memory-manager/knowledge-graph/:userId
   */
  getKnowledgeGraph(userId) {
    return apiClient.get(`/memory-manager/knowledge-graph/${userId}`)
  }
}

