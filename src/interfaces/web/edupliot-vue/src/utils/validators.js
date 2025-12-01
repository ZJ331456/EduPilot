/**
 * 数据验证工具函数
 */

/**
 * 验证是否为空值
 * @param {any} value - 待验证的值
 * @returns {boolean} 是否为空
 */
export function isEmpty(value) {
  if (value == null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * 验证是否为有效的数字
 * @param {any} value - 待验证的值
 * @returns {boolean} 是否为有效数字
 */
export function isValidNumber(value) {
  return typeof value === 'number' && !isNaN(value) && isFinite(value)
}

/**
 * 验证是否为有效的百分比值 (0-1)
 * @param {any} value - 待验证的值
 * @returns {boolean} 是否为有效百分比
 */
export function isValidPercentage(value) {
  return isValidNumber(value) && value >= 0 && value <= 1
}

/**
 * 验证是否为有效的日期
 * @param {any} value - 待验证的值
 * @returns {boolean} 是否为有效日期
 */
export function isValidDate(value) {
  if (!value) return false
  const date = new Date(value)
  return date instanceof Date && !isNaN(date.getTime())
}

/**
 * 验证是否为有效的对象
 * @param {any} value - 待验证的值
 * @returns {boolean} 是否为有效对象
 */
export function isValidObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

/**
 * 安全获取嵌套属性
 * @param {object} obj - 对象
 * @param {string} path - 属性路径，如 'a.b.c'
 * @param {any} defaultValue - 默认值
 * @returns {any} 属性值或默认值
 */
export function safeGet(obj, path, defaultValue = undefined) {
  if (!isValidObject(obj)) return defaultValue
  
  const keys = path.split('.')
  let result = obj
  
  for (const key of keys) {
    if (result == null || typeof result !== 'object') {
      return defaultValue
    }
    result = result[key]
  }
  
  return result !== undefined ? result : defaultValue
}

/**
 * 验证数组是否非空
 * @param {any} value - 待验证的值
 * @returns {boolean} 是否为非空数组
 */
export function isNonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0
}

/**
 * 清理对象中的空值
 * @param {object} obj - 原始对象
 * @returns {object} 清理后的对象
 */
export function cleanObject(obj) {
  if (!isValidObject(obj)) return {}
  
  return Object.entries(obj).reduce((acc, [key, value]) => {
    if (!isEmpty(value)) {
      acc[key] = value
    }
    return acc
  }, {})
}

