/**
 * 数据映射工具函数
 * 用于转换和映射各种数据类型
 */

import {
  EMOTION_MAP,
  EMOTION_COLORS,
  EMOTION_TAG_TYPES,
  TREND_MAP,
  TREND_TAG_TYPES,
  LEARNING_PATTERN_MAP
} from './constants'

import {
  Sunny,
  CircleClose,
  QuestionFilled,
  MostlyCloudy,
  Cloudy,
  Top,
  Bottom,
  Minus
} from '@element-plus/icons-vue'

/**
 * 翻译情感类型
 * @param {string} emotion - 情感类型英文
 * @returns {string} 情感类型中文
 */
export function translateEmotion(emotion) {
  return EMOTION_MAP[emotion] || emotion
}

/**
 * 获取情感图标
 * @param {string} emotion - 情感类型
 * @returns {Component} Vue 图标组件
 */
export function getEmotionIcon(emotion) {
  const iconMap = {
    positive: Sunny,
    negative: CircleClose,
    curious: QuestionFilled,
    confused: MostlyCloudy,
    neutral: Cloudy
  }
  return iconMap[emotion] || Cloudy
}

/**
 * 获取情感颜色
 * @param {string} emotion - 情感类型
 * @returns {string} 颜色代码
 */
export function getEmotionColor(emotion) {
  return EMOTION_COLORS[emotion] || EMOTION_COLORS.neutral
}

/**
 * 获取情感标签类型
 * @param {string} emotion - 情感类型
 * @returns {string} Element Plus 标签类型
 */
export function getEmotionTagType(emotion) {
  return EMOTION_TAG_TYPES[emotion] || EMOTION_TAG_TYPES.neutral
}

/**
 * 翻译趋势类型
 * @param {string} trend - 趋势类型英文
 * @returns {string} 趋势类型中文
 */
export function translateTrend(trend) {
  return TREND_MAP[trend] || trend
}

/**
 * 获取趋势图标
 * @param {string} trend - 趋势类型
 * @returns {Component} Vue 图标组件
 */
export function getTrendIcon(trend) {
  const iconMap = {
    improving: Top,
    declining: Bottom,
    stable: Minus,
    unknown: Minus
  }
  return iconMap[trend] || Minus
}

/**
 * 获取趋势标签类型
 * @param {string} trend - 趋势类型
 * @returns {string} Element Plus 标签类型
 */
export function getTrendTagType(trend) {
  return TREND_TAG_TYPES[trend] || TREND_TAG_TYPES.unknown
}

/**
 * 翻译学习模式
 * @param {string} pattern - 学习模式英文
 * @returns {string} 学习模式中文
 */
export function translatePattern(pattern) {
  return LEARNING_PATTERN_MAP[pattern] || pattern
}

/**
 * 转换 ECharts 图表节点数据
 * @param {Array} nodes - 原始节点数组
 * @returns {Array} 转换后的节点数组
 */
export function mapGraphNodes(nodes) {
  if (!Array.isArray(nodes)) return []
  
  return nodes.map((node, index) => ({
    id: node.id || index,
    name: node.label || node.name || `节点${index}`,
    symbolSize: 30 + (node.weight || Math.random()) * 20,
    value: node.weight || 1,
    category: index % 3,
    itemStyle: {
      borderWidth: 2,
      borderColor: '#fff',
      shadowBlur: 10,
      shadowColor: 'rgba(102, 126, 234, 0.5)'
    },
    label: {
      show: true,
      fontSize: 12,
      color: '#fff',
      fontWeight: 'bold'
    }
  }))
}

/**
 * 转换 ECharts 图表边数据
 * @param {Array} edges - 原始边数组
 * @returns {Array} 转换后的边数组
 */
export function mapGraphEdges(edges) {
  if (!Array.isArray(edges)) return []
  
  return edges.map(edge => ({
    source: edge.source || edge.from,
    target: edge.target || edge.to,
    label: {
      show: true,
      formatter: edge.label || edge.relation || '',
      fontSize: 10,
      color: 'rgba(255, 255, 255, 0.6)'
    },
    lineStyle: {
      color: 'rgba(102, 126, 234, 0.3)',
      curveness: 0.2,
      width: 2
    }
  }))
}

/**
 * 规范化用户画像数据
 * @param {object} profile - 原始画像数据
 * @returns {object} 规范化后的画像数据
 */
export function normalizeProfile(profile) {
  if (!profile) return null
  
  return {
    totalInteractions: profile.total_interactions || 0,
    averageQuality: profile.average_quality || 0,
    learningStreak: profile.learning_streak || 0,
    ...profile
  }
}

/**
 * 规范化学习记录数据
 * @param {Array} records - 原始记录数组
 * @returns {Array} 规范化后的记录数组
 */
export function normalizeLearningRecords(records) {
  if (!Array.isArray(records)) return []
  
  return records.map(record => ({
    id: record.id || record.timestamp,
    title: record.title || '学习记录',
    summary: record.summary || '暂无详情',
    timestamp: record.timestamp || new Date().toISOString(),
    queryType: record.query_type || record.type,
    qualityScore: record.quality_score || 0,
    ...record
  }))
}

