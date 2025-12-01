/**
 * 内容撰写器 API
 * 对应后端: /api/agent/v1/draft-writer/
 * Core 模块: core.agents.draft_writer
 * 
 * ⚠️ 这是调试接口，生产环境建议使用 workflow API
 */

import apiClient from './client'

export default {
  /**
   * 撰写内容草稿
   * POST /draft-writer/write
   */
  write(data) {
    return apiClient.post('/draft-writer/write', data)
  },

  /**
   * 修改内容草稿
   * POST /draft-writer/revise
   */
  revise(data) {
    return apiClient.post('/draft-writer/revise', data)
  }
}

