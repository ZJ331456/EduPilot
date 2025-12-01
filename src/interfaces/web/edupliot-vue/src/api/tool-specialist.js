/**
 * 工具专家 API
 * 对应后端: /api/agent/v1/tool-specialist/
 * Core 模块: core.agents.tool_specialist
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 执行工具调用
   * POST /tool-specialist/execute
   */
  execute(data) {
    return apiClient.post('/tool-specialist/execute', data)
  }
}

