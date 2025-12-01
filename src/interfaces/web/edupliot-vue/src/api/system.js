/**
 * 系统管理 API
 * 系统级别的接口
 */

import apiClient from './client'

export default {
  /**
   * 健康检查
   * GET /health
   */
  health() {
    return apiClient.get('/health')
  },

  /**
   * 获取系统统计
   * GET /stats
   */
  stats() {
    return apiClient.get('/stats')
  },

  /**
   * 获取性能统计
   * GET /stats/performance
   */
  performanceStats() {
    return apiClient.get('/stats/performance')
  },

  /**
   * 获取缓存统计
   * GET /stats/cache
   */
  cacheStats() {
    return apiClient.get('/stats/cache')
  },

  /**
   * 清空缓存
   * POST /cache/clear
   */
  clearCache() {
    return apiClient.post('/cache/clear')
  }
}

