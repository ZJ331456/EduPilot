/**
 * 格式化工具函数
 * 统一处理日期、文本等格式化需求
 */

/**
 * 格式化日期时间
 * @param {string|Date} timestamp - 时间戳或日期对象
 * @param {string} format - 格式类型: 'full' | 'date' | 'time' | 'relative'
 * @returns {string} 格式化后的字符串
 */
export function formatDate(timestamp, format = 'full') {
  if (!timestamp) return ''
  
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  
  if (isNaN(date.getTime())) {
    return ''
  }

  switch (format) {
    case 'time':
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    
    case 'date':
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    
    case 'relative':
      return getRelativeTime(date)
    
    case 'full':
    default:
      return date.toLocaleString('zh-CN')
  }
}

/**
 * 获取相对时间
 * @param {Date} date - 日期对象
 * @returns {string} 相对时间描述
 */
function getRelativeTime(date) {
  const now = new Date()
  const diff = now - date
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return formatDate(date, 'date')
}

/**
 * 格式化百分比
 * @param {number} value - 数值 (0-1)
 * @param {number} decimals - 小数位数
 * @returns {string} 百分比字符串
 */
export function formatPercentage(value, decimals = 1) {
  if (typeof value !== 'number' || isNaN(value)) return '0%'
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 格式化数字，添加千分位分隔符
 * @param {number} num - 数字
 * @returns {string} 格式化后的字符串
 */
export function formatNumber(num) {
  if (typeof num !== 'number' || isNaN(num)) return '0'
  return num.toLocaleString('zh-CN')
}

/**
 * 截断文本
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @param {string} ellipsis - 省略符号
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 100, ellipsis = '...') {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + ellipsis
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`
}

/**
 * 格式化持续时间
 * @param {number} ms - 毫秒数
 * @returns {string} 格式化后的持续时间
 */
export function formatDuration(ms) {
  if (!ms || ms < 0) return '0ms'
  
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  if (ms < 3600000) return `${Math.floor(ms / 60000)}分${Math.floor((ms % 60000) / 1000)}秒`
  
  const hours = Math.floor(ms / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  return `${hours}小时${minutes}分钟`
}

/**
 * 格式化时间（快捷方法，用于消息时间戳等）
 * @param {string|Date} timestamp - 时间戳或日期对象
 * @returns {string} 格式化后的时间字符串（相对时间或完整时间）
 */
export function formatTime(timestamp) {
  if (!timestamp) return ''
  return formatDate(timestamp, 'relative')
}

