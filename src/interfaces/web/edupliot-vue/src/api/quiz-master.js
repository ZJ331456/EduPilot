/**
 * 测验大师 API
 * 对应后端: /api/agent/v1/quiz-master/
 * Core 模块: core.agents.quiz_master
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 生成测试题
   * POST /quiz-master/generate
   */
  generate(data) {
    return apiClient.post('/quiz-master/generate', data)
  }
}

