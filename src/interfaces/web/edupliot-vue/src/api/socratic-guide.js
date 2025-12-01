/**
 * 苏格拉底引导 API
 * 对应后端: /api/agent/v1/socratic-guide/
 * Core 模块: core.agents.socratic_guide
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 获取苏格拉底引导
   * POST /socratic-guide/guide
   */
  guide(data) {
    return apiClient.post('/socratic-guide/guide', data)
  }
}

