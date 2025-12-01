/**
 * 内容审核器 API
 * 对应后端: /api/agent/v1/reviewer/
 * Core 模块: core.agents.reviewer
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 审核内容草稿
   * POST /reviewer/review
   */
  review(data) {
    return apiClient.post('/reviewer/review', data)
  }
}

