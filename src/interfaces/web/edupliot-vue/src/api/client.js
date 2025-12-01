/**
 * API 客户端基础配置
 * 提供统一的 axios 实例和拦截器
 */

import axios from 'axios'
import { API_CONFIG } from '../utils/constants'
import { handleApiError } from '../utils/errorHandler'

// 创建默认 axios 实例
const apiClient = axios.create({
  baseURL: '/api/agent/v1',
  timeout: 30000, // 30秒，适合大多数API调用
  headers: {
    'Content-Type': 'application/json'
  }
})

// 创建工作流专用 axios 实例（更长的超时时间）
const workflowClient = axios.create({
  baseURL: '/api/agent/v1',
  timeout: 120000, // 2分钟，因为工作流可能包含LLM调用
  headers: {
    'Content-Type': 'application/json'
  }
})

// 通用请求拦截器
const requestInterceptor = (config) => {
  // 添加 token 或其他请求头
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // 添加请求 ID
  config.headers['X-Request-ID'] = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  
  return config
}

const requestErrorInterceptor = (error) => {
  console.error('Request Error:', error)
  return Promise.reject(error)
}

// 通用响应拦截器
const responseInterceptor = (response) => {
  // 统一返回 data 字段
  return response.data
}

const responseErrorInterceptor = (error) => {
  // 统一错误处理
  handleApiError(error, {
    defaultMessage: '请求失败，请稍后重试',
    showMessage: false, // 由调用方决定是否显示消息
    logError: true
  })
  return Promise.reject(error)
}

// 为两个客户端添加相同的拦截器
apiClient.interceptors.request.use(requestInterceptor, requestErrorInterceptor)
apiClient.interceptors.response.use(responseInterceptor, responseErrorInterceptor)

workflowClient.interceptors.request.use(requestInterceptor, requestErrorInterceptor)
workflowClient.interceptors.response.use(responseInterceptor, responseErrorInterceptor)

// 导出两个客户端
export { workflowClient }
export default apiClient

