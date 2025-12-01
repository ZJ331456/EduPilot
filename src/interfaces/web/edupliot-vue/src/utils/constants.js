/**
 * 全局常量配置
 */

// 情感类型映射
export const EMOTION_MAP = {
  positive: '积极',
  negative: '消极',
  curious: '好奇',
  confused: '困惑',
  neutral: '中性'
}

// 情感颜色映射
export const EMOTION_COLORS = {
  positive: '#67C23A',
  negative: '#F56C6C',
  curious: '#409EFF',
  confused: '#E6A23C',
  neutral: '#909399'
}

// 情感标签类型
export const EMOTION_TAG_TYPES = {
  positive: 'success',
  negative: 'danger',
  curious: 'primary',
  confused: 'warning',
  neutral: 'info'
}

// 趋势类型映射
export const TREND_MAP = {
  improving: '上升趋势',
  declining: '下降趋势',
  stable: '稳定',
  unknown: '未知'
}

// 趋势标签类型
export const TREND_TAG_TYPES = {
  improving: 'success',
  declining: 'warning',
  stable: 'info',
  unknown: 'info'
}

// 学习模式映射
export const LEARNING_PATTERN_MAP = {
  visual: '视觉学习',
  auditory: '听觉学习',
  kinesthetic: '动觉学习',
  reading: '阅读学习'
}

// API 配置
export const API_CONFIG = {
  TIMEOUT: 60000,  // 增加到 60 秒，因为 LLM 调用可能较慢
  RETRY_TIMES: 3,
  RETRY_DELAY: 1000
}

// 消息配置
export const MESSAGE_CONFIG = {
  SUCCESS_DURATION: 2000,
  ERROR_DURATION: 3000,
  WARNING_DURATION: 2500,
  INFO_DURATION: 2000
}

// 分页配置
export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZES: [5, 10, 20, 50],
  MAX_PAGE_SIZE: 100
}

// 图表配置
export const CHART_CONFIG = {
  COLORS: {
    PRIMARY: '#667eea',
    SECONDARY: '#764ba2',
    SUCCESS: '#67c23a',
    WARNING: '#e6a23c',
    DANGER: '#f56c6c',
    INFO: '#909399'
  },
  GRADIENTS: {
    PRIMARY: ['#667eea', '#764ba2'],
    SECONDARY: ['#f093fb', '#f5576c'],
    SUCCESS: ['#67c23a', '#4caf50']
  }
}

// 动画配置
export const ANIMATION_CONFIG = {
  DURATION: {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500
  },
  EASING: 'cubic-bezier(0.4, 0, 0.2, 1)'
}

// 本地存储键名
export const STORAGE_KEYS = {
  USER_ID: 'userId',
  USER_NAME: 'userName',
  THEME: 'theme',
  LANGUAGE: 'language'
}

// 查询类型
export const QUERY_TYPES = {
  KNOWLEDGE: 'knowledge',
  SOCRATIC: 'socratic',
  LEARNING: 'learning',
  MIXED: 'mixed'
}

// 响应式断点
export const BREAKPOINTS = {
  XS: 480,
  SM: 768,
  MD: 992,
  LG: 1200,
  XL: 1920
}

// 默认快速问题
export const DEFAULT_QUICK_QUESTIONS = [
  '什么是大化改新？',
  '请解释古坟时代的特征',
  '德川幕府的政治制度是怎样的？',
  '请比较奈良时代和平安时代'
]

// 苏格拉底式对话触发问题（更容易触发苏格拉底式引导）
export const SOCRATIC_TRIGGER_QUESTIONS = [
  '我不太理解这个概念，能帮我分析一下吗？',
  '这个问题很复杂，我需要更深入的思考',
  '请引导我一步步理解这个历史事件',
  '我想从多个角度来理解这个问题',
  '能通过提问的方式帮助我学习吗？',
  '请用苏格拉底式的方法来引导我思考',
  '我想通过对话来深入理解这个概念',
  '请帮助我建立对这个问题的全面认识'
]

// 节流/防抖延迟
export const DEBOUNCE_DELAYS = {
  SEARCH: 500,
  INPUT: 300,
  SCROLL: 100,
  RESIZE: 200
}

