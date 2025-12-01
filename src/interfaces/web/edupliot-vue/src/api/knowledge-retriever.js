/**
 * 知识检索器 API
 * 对应后端: /api/agent/v1/knowledge-manager/
 * Core 模块: core.agents.knowledge_manager
 * 
 * ⚠️ 注意：后端路由为 knowledge-manager，不是 knowledge-retriever
 */

import apiClient from './client'

export default {
  /**
   * 检索知识
   * POST /knowledge-manager/retrieve
   */
  retrieve(data) {
    return apiClient.post('/knowledge-manager/retrieve', data)
  },

  /**
   * 获取概念详情
   * GET /knowledge-manager/concept/:conceptName
   */
  getConcept(conceptName) {
    return apiClient.get(`/knowledge-manager/concept/${encodeURIComponent(conceptName)}`)
  },

  /**
   * 获取知识库列表
   * GET /knowledge-manager/bases
   */
  listBases() {
    return apiClient.get('/knowledge-manager/bases')
  },

  /**
   * 获取知识库详情
   * GET /knowledge-manager/bases/:name
   */
  getBase(name) {
    return apiClient.get(`/knowledge-manager/bases/${encodeURIComponent(name)}`)
  },

  /**
   * 获取相关概念
   * GET /knowledge-manager/related/:conceptName
   */
  getRelated(conceptName, params = {}) {
    return apiClient.get(`/knowledge-manager/related/${encodeURIComponent(conceptName)}`, { params })
  },

  /**
   * 获取搜索建议
   * GET /knowledge-manager/suggestions
   */
  getSuggestions(params) {
    return apiClient.get('/knowledge-manager/suggestions', { params })
  }
}

