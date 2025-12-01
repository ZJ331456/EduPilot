/**
 * 编排器 API
 * 对应后端: /api/agent/v1/orchestrator/
 * Core 模块: core.agents.orchestrator
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 制定学习计划
   * POST /orchestrator/plan
   */
  plan(data) {
    return apiClient.post('/orchestrator/plan', data)
  }
}

