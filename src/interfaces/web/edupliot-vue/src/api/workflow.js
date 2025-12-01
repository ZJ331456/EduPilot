/**
 * 工作流 API
 * 对应后端: /api/agent/v1/workflow/
 * Core 模块: core.workflow
 */

import { workflowClient } from './client'

export default {
  /**
   * 启动学习会话
   * POST /workflow/session/start
   */
  startSession(data) {
    return workflowClient.post('/workflow/session/start', data)
  },

  /**
   * 继续学习会话
   * POST /workflow/session/continue
   */
  continueSession(data) {
    return workflowClient.post('/workflow/session/continue', data)
  },

  /**
   * 获取会话信息
   * GET /workflow/session/:sessionId
   */
  getSession(sessionId, params = {}) {
    return workflowClient.get(`/workflow/session/${sessionId}`, { params })
  },

  /**
   * 结束会话
   * DELETE /workflow/session/:sessionId
   */
  endSession(sessionId) {
    return workflowClient.delete(`/workflow/session/${sessionId}`)
  },

  /**
   * 获取活跃会话列表
   * GET /workflow/sessions/active
   */
  getActiveSessions() {
    return workflowClient.get('/workflow/sessions/active')
  },

  /**
   * 获取苏格拉底式对话详情
   * GET /workflow/session/:sessionId/socratic
   */
  getSocraticDialogue(sessionId) {
    return workflowClient.get(`/workflow/session/${sessionId}/socratic`)
  },

  /**
   * 获取苏格拉底式问题类型
   * GET /workflow/socratic/question-types
   */
  getSocraticQuestionTypes() {
    return workflowClient.get('/workflow/socratic/question-types')
  },

  /**
   * 获取苏格拉底式引导策略
   * GET /workflow/socratic/strategies
   */
  getSocraticStrategies() {
    return workflowClient.get('/workflow/socratic/strategies')
  }
}

