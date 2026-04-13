/**
 * 性能监控 Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePerformanceStore = defineStore('performance', () => {
  // 状态
  const metrics = ref({
    pageLoadTime: 0,
    firstContentfulPaint: 0,
    timeToInteractive: 0,
    resourceTimings: [],
    apiCalls: [],
    errors: []
  })

  const isMonitoring = ref(false)

  // 计算属性
  const averageApiTime = computed(() => {
    if (metrics.value.apiCalls.length === 0) return 0
    const total = metrics.value.apiCalls.reduce((sum, call) => sum + call.duration, 0)
    return total / metrics.value.apiCalls.length
  })

  const errorCount = computed(() => metrics.value.errors.length)

  const slowApiCalls = computed(() => {
    return metrics.value.apiCalls.filter(call => call.duration > 2000)
  })

  // 方法
  const startMonitoring = () => {
    if (isMonitoring.value) return

    // 监控页面加载性能
    if (window.performance) {
      const perfData = window.performance.timing
      
      // 使用更可靠的加载时间计算
      // 如果 loadEventEnd 为 0，使用 navigationStart 作为后备基准
      const navigationStart = perfData.navigationStart || 0
      const loadEventEnd = perfData.loadEventEnd || 0
      
      // 计算页面加载时间
      if (loadEventEnd > 0) {
        metrics.value.pageLoadTime = loadEventEnd - navigationStart
      } else {
        // 使用 fetchStart 或 domContentLoadedEventEnd 作为后备
        metrics.value.pageLoadTime = (perfData.domContentLoadedEventEnd || perfData.fetchStart) - navigationStart
      }

      // 获取 FCP
      const paint = window.performance.getEntriesByType('paint')
      const fcp = paint.find(entry => entry.name === 'first-contentful-paint')
      if (fcp) {
        metrics.value.firstContentfulPaint = Math.round(fcp.startTime)
      } else {
        // 如果没有 FCP 数据，使用 DOMContentLoaded 时间作为后备
        metrics.value.firstContentfulPaint = (perfData.domContentLoadedEventEnd || perfData.domContentLoadedEventStart || 0) - navigationStart
      }
    }

    // 监控资源加载
    if (window.PerformanceObserver) {
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          metrics.value.resourceTimings.push({
            name: entry.name,
            duration: entry.duration,
            size: entry.transferSize,
            type: entry.initiatorType
          })
        }
      })
      resourceObserver.observe({ entryTypes: ['resource'] })
    }

    // 监控错误
    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    isMonitoring.value = true
  }

  const stopMonitoring = () => {
    window.removeEventListener('error', handleError)
    window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    isMonitoring.value = false
  }

  const handleError = (event) => {
    metrics.value.errors.push({
      type: 'error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      timestamp: Date.now()
    })
  }

  const handleUnhandledRejection = (event) => {
    metrics.value.errors.push({
      type: 'unhandledrejection',
      message: event.reason?.message || String(event.reason),
      timestamp: Date.now()
    })
  }

  const recordApiCall = (url, duration, success) => {
    metrics.value.apiCalls.push({
      url,
      duration,
      success,
      timestamp: Date.now()
    })

    // 只保留最近100次调用
    if (metrics.value.apiCalls.length > 100) {
      metrics.value.apiCalls.shift()
    }
  }

  const getReport = () => {
    return {
      pageLoadTime: metrics.value.pageLoadTime,
      firstContentfulPaint: metrics.value.firstContentfulPaint,
      averageApiTime: averageApiTime.value,
      totalApiCalls: metrics.value.apiCalls.length,
      slowApiCallsCount: slowApiCalls.value.length,
      errorCount: errorCount.value,
      resourceCount: metrics.value.resourceTimings.length
    }
  }

  const reset = () => {
    metrics.value = {
      pageLoadTime: 0,
      firstContentfulPaint: 0,
      timeToInteractive: 0,
      resourceTimings: [],
      apiCalls: [],
      errors: []
    }
  }

  return {
    // 状态
    metrics,
    isMonitoring,

    // 计算属性
    averageApiTime,
    errorCount,
    slowApiCalls,

    // 方法
    startMonitoring,
    stopMonitoring,
    recordApiCall,
    getReport,
    reset
  }
})

