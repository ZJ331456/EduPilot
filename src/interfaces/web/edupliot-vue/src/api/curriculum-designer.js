/**
 * 课程设计器 API
 * 对应后端: /api/agent/v1/curriculum-designer/
 * Core 模块: core.agents.curriculum_designer
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 设计课程
   * POST /curriculum-designer/design
   */
  design(data) {
    return apiClient.post('/curriculum-designer/design', data)
  }
}

