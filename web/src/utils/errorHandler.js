/**
 * 统一错误处理工具
 */

import { ElMessage } from 'element-plus'
import { MESSAGE_CONFIG } from './constants'

/**
 * 错误类型枚举
 */
export const ErrorType = {
  NETWORK: 'NETWORK',
  API: 'API',
  VALIDATION: 'VALIDATION',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
}

/**
 * 解析错误类型
 * @param {Error} error - 错误对象
 * @returns {string} 错误类型
 */
function parseErrorType(error) {
  if (!error) return ErrorType.UNKNOWN
  
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return ErrorType.TIMEOUT
  }
  
  if (error.response) {
    return ErrorType.API
  }
  
  if (error.request) {
    return ErrorType.NETWORK
  }
  
  return ErrorType.UNKNOWN
}

/**
 * 获取友好的错误消息
 * @param {Error} error - 错误对象
 * @param {string} defaultMessage - 默认消息
 * @returns {string} 友好的错误消息
 */
export function getErrorMessage(error, defaultMessage = '操作失败') {
  if (!error) return defaultMessage
  
  const errorType = parseErrorType(error)
  
  switch (errorType) {
    case ErrorType.TIMEOUT:
      return '请求超时，请检查网络连接'
    
    case ErrorType.NETWORK:
      return '网络连接失败，请检查网络设置'
    
    case ErrorType.API:
      // 尝试从响应中获取详细错误信息
      const response = error.response
      if (response?.data?.detail) {
        return typeof response.data.detail === 'string' 
          ? response.data.detail 
          : response.data.message || defaultMessage
      }
      
      // 根据 HTTP 状态码返回友好消息
      switch (response?.status) {
        case 400:
          return '请求参数有误'
        case 401:
          return '未授权，请重新登录'
        case 403:
          return '没有权限执行此操作'
        case 404:
          return '请求的资源不存在'
        case 500:
          return '服务器内部错误'
        case 503:
          return '服务暂时不可用'
        default:
          return defaultMessage
      }
    
    case ErrorType.VALIDATION:
      return error.message || '数据验证失败'
    
    default:
      return error.message || defaultMessage
  }
}

/**
 * 显示错误消息
 * @param {Error|string} error - 错误对象或消息
 * @param {string} defaultMessage - 默认消息
 */
export function showError(error, defaultMessage = '操作失败') {
  const message = typeof error === 'string' 
    ? error 
    : getErrorMessage(error, defaultMessage)
  
  ElMessage.error({
    message,
    duration: MESSAGE_CONFIG.ERROR_DURATION,
    showClose: true
  })
}

/**
 * 显示成功消息
 * @param {string} message - 消息内容
 */
export function showSuccess(message) {
  ElMessage.success({
    message,
    duration: MESSAGE_CONFIG.SUCCESS_DURATION
  })
}

/**
 * 显示警告消息
 * @param {string} message - 消息内容
 */
export function showWarning(message) {
  ElMessage.warning({
    message,
    duration: MESSAGE_CONFIG.WARNING_DURATION
  })
}

/**
 * 显示信息消息
 * @param {string} message - 消息内容
 */
export function showInfo(message) {
  ElMessage.info({
    message,
    duration: MESSAGE_CONFIG.INFO_DURATION
  })
}

/**
 * 统一的 API 错误处理函数
 * @param {Error} error - 错误对象
 * @param {object} options - 配置选项
 * @returns {void}
 */
export function handleApiError(error, options = {}) {
  const {
    defaultMessage = '操作失败',
    showMessage = true,
    logError = true,
    throwError = false
  } = options
  
  if (logError) {
    console.error('API Error:', error)
  }
  
  if (showMessage) {
    showError(error, defaultMessage)
  }
  
  if (throwError) {
    throw error
  }
}

/**
 * 创建一个带错误处理的异步函数包装器
 * @param {Function} fn - 原始异步函数
 * @param {object} options - 错误处理选项
 * @returns {Function} 包装后的函数
 */
export function withErrorHandler(fn, options = {}) {
  return async function (...args) {
    try {
      return await fn.apply(this, args)
    } catch (error) {
      handleApiError(error, options)
      return null
    }
  }
}

/**
 * 重试机制包装器
 * @param {Function} fn - 要重试的函数
 * @param {number} maxRetries - 最大重试次数
 * @param {number} delay - 重试延迟（毫秒）
 * @returns {Function} 带重试机制的函数
 */
export function withRetry(fn, maxRetries = 3, delay = 1000) {
  return async function (...args) {
    let lastError
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn.apply(this, args)
      } catch (error) {
        lastError = error
        
        // 如果不是网络错误或超时，不重试
        const errorType = parseErrorType(error)
        if (errorType !== ErrorType.NETWORK && errorType !== ErrorType.TIMEOUT) {
          throw error
        }
        
        // 最后一次重试失败后不再等待
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
        }
      }
    }
    
    throw lastError
  }
}

