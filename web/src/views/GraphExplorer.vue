<template>
  <div class="graph-explorer">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h2 class="toolbar-title">
          <svg class="title-icon" viewBox="0 0 24 24" fill="none">
            <circle cx="5" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
            <circle cx="19" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="5" r="3" stroke="currentColor" stroke-width="2"/>
            <path d="M8 10L11 11.5M16 10L13 11.5M8 14L11 12.5M16 14L13 12.5" stroke="currentColor" stroke-width="2"/>
          </svg>
          知识图谱
        </h2>
      </div>

      <div class="toolbar-center">
        <!-- 模式切换 -->
        <div class="mode-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            class="mode-tab"
            :class="{ active: currentView === tab.value }"
            @click="switchView(tab.value)"
          >
            <span class="tab-icon" v-html="tab.icon"></span>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>
      </div>

      <div class="toolbar-right">
        <el-button
          v-if="currentView === 'knowledge'"
          :loading="loading"
          @click="loadData"
          size="default"
          class="refresh-btn"
        >
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none">
            <path d="M4 4V9H4.58152M19.9381 11C19.446 7.05369 16.0796 4 12 4C8.64262 4 5.76829 6.06817 4.58152 9M4.58152 9H9M20 20V15H19.4185M19.4185 15C18.2317 17.9318 15.3574 20 12 20C7.64262 20 4 16.4183 4 12C4 7.58172 7.64262 4 12 4C15.3574 4 18.2317 6.06817 19.4185 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 知识库工具栏 -->
    <div v-if="currentView === 'knowledge'" class="kb-toolbar">
      <el-input
        v-model="kbId"
        placeholder="知识库 ID"
        size="default"
        class="kb-input"
      />
      <el-button @click="loadData" :loading="loading" class="load-btn">加载</el-button>
      <el-button @click="runIndex" :loading="indexing" class="index-btn">构建索引</el-button>
      <!-- 显示模式切换 -->
      <div class="display-mode">
        <span class="mode-label">显示模式：</span>
        <el-select v-model="displayMode" size="small" style="width: 120px">
          <el-option label="概览（500节点）" value="overview" />
          <el-option label="完整（全部）" value="full" />
          <el-option label="精简（200节点）" value="compact" />
        </el-select>
      </div>
    </div>

    <!-- 图谱容器 -->
    <div class="graph-container" ref="containerRef">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner">
          <svg viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="80 40" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="loading-text">正在加载图谱...</span>
        <span v-if="totalNodeCount > 0" class="loading-count">共 {{ totalNodeCount }} 节点</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!nodeCount" class="empty-state">
        <div class="empty-illustration">
          <svg viewBox="0 0 120 120" fill="none">
            <circle cx="60" cy="60" r="50" stroke="currentColor" stroke-width="2" stroke-dasharray="8 4" opacity="0.3"/>
            <circle cx="40" cy="50" r="12" stroke="currentColor" stroke-width="2" opacity="0.5"/>
            <circle cx="80" cy="50" r="8" stroke="currentColor" stroke-width="2" opacity="0.5"/>
            <circle cx="60" cy="80" r="10" stroke="currentColor" stroke-width="2" opacity="0.5"/>
            <path d="M48 55L72 52M45 58L55 72M65 72L78 58" stroke="currentColor" stroke-width="2" opacity="0.3"/>
          </svg>
        </div>
        <h3 class="empty-title">暂无图谱数据</h3>
        <p class="empty-desc">{{ getEmptyMessage() }}</p>
        <el-button v-if="currentView === 'knowledge'" @click="runIndex" :loading="indexing" type="primary">
          构建索引
        </el-button>
        <el-button v-else-if="currentView === 'dialogue'" @click="goToChat" type="primary">
          去对话
        </el-button>
      </div>

      <!-- 图谱图表 -->
      <div ref="chartRef" class="chart" :class="{ hidden: !nodeCount || loading }"></div>

      <!-- 图例 -->
      <div v-if="nodeCount > 0" class="graph-legend">
        <div class="legend-item">
          <span class="legend-dot node"></span>
          <span class="legend-label">实体节点</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot edge"></span>
          <span class="legend-label">关系连接</span>
        </div>
        <div class="legend-item">
          <span class="legend-count">{{ nodeCount }}</span>
          <span class="legend-label">/ {{ totalNodeCount }} 节点</span>
        </div>
        <div class="legend-item">
          <span class="legend-count">{{ edgeCount }}</span>
          <span class="legend-label">边</span>
        </div>
      </div>

      <!-- 控制面板 -->
      <div v-if="nodeCount > 0" class="control-panel">
        <button class="control-btn" @click="zoomIn" title="放大">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
        <button class="control-btn" @click="zoomOut" title="缩小">
          <svg viewBox="0 0 24 24" fill="none"><path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
        <button class="control-btn" @click="resetZoom" title="重置">
          <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>
        </button>
        <button class="control-btn" @click="toggleAnimation" :class="{ active: isAnimating }" title="动画">
          <svg viewBox="0 0 24 24" fill="none"><polygon points="5,3 19,12 5,21" fill="currentColor"/></svg>
        </button>
      </div>

      <!-- 提示信息 -->
      <div v-if="nodeCount > 0 && nodeCount < totalNodeCount" class="expand-hint">
        <span>显示前 {{ nodeCount }} 个节点（共 {{ totalNodeCount }} 个）</span>
        <button class="expand-btn" @click="loadMore">加载更多</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-toast">
      <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 8V12M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span>{{ error }}</span>
      <button @click="error = ''">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { getKnowledgeGraph, getDialogueGraph, getUserLongGraph, indexKnowledge } from '@/api/edupilot'

// Refs
const chartRef = ref(null)
const containerRef = ref(null)
const currentView = ref('knowledge')
const kbId = ref('sanguo')
const loading = ref(false)
const indexing = ref(false)
const error = ref('')
const nodeCount = ref(0)
const edgeCount = ref(0)
const totalNodeCount = ref(0)
const displayMode = ref('overview')
const isAnimating = ref(false)

// 图表实例
let chart = null

// 原始数据缓存
let rawData = { nodes: [], links: [] }

// Store
const userStore = useUserStore()
const chatStore = useChatStore()

// Tab 配置
const tabs = [
  {
    value: 'knowledge',
    label: '知识库',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M4 19.5C4 18.837 4.26339 18.2011 4.73223 17.7322C5.20107 17.2634 5.83696 17 6.5 17H20" stroke="currentColor" stroke-width="2"/><path d="M6.5 2H20V22H6.5C5.83696 22 5.20107 21.7366 4.73223 21.2678C4.26339 20.7989 4 20.163 4 19.5V4.5C4 3.83696 4.26339 3.20107 4.73223 2.73223C5.20107 2.26339 5.83696 2 6.5 2Z" stroke="currentColor" stroke-width="2"/></svg>'
  },
  {
    value: 'dialogue',
    label: '会话图',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" stroke-width="2"/></svg>'
  },
  {
    value: 'user',
    label: '用户图',
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/></svg>'
  }
]

// 根据显示模式获取最大节点数
function getMaxNodes() {
  switch (displayMode.value) {
    case 'full': return Infinity  // 全部显示
    case 'compact': return 200
    case 'overview':
    default: return 500
  }
}

// 计算节点度数（连接数）
function calculateDegrees(nodes, links) {
  const degrees = new Map()
  nodes.forEach(n => degrees.set(n.id || n.name, 0))
  links.forEach(l => {
    const src = l.source
    const tgt = l.target
    degrees.set(src, (degrees.get(src) || 0) + 1)
    degrees.set(tgt, (degrees.get(tgt) || 0) + 1)
  })
  return degrees
}

// 智能采样：优先选择高度数节点
function smartSample(nodes, links, maxNodes) {
  if (nodes.length <= maxNodes) {
    return { nodes, links }
  }

  const degrees = calculateDegrees(nodes, links)

  // 按度数排序，优先选择连接数多的节点
  const sortedNodes = [...nodes].sort((a, b) => {
    const degA = degrees.get(a.id || a.name) || 0
    const degB = degrees.get(b.id || b.name) || 0
    return degB - degA
  })

  // 选择前 maxNodes 个节点
  const selectedNodes = sortedNodes.slice(0, maxNodes)
  const selectedIds = new Set(selectedNodes.map(n => n.id || n.name))

  // 只保留与选中节点相关的边
  const selectedLinks = links.filter(l =>
    selectedIds.has(l.source) && selectedIds.has(l.target)
  )

  return { nodes: selectedNodes, links: selectedLinks }
}

// 转换图谱数据 - 智能版
function toGraphOption(data) {
  const rawNodes = data.nodes || []
  const rawLinks = data.links || []

  if (rawNodes.length === 0) {
    return null
  }

  const degrees = calculateDegrees(rawNodes, rawLinks)

  // 根据度数设置节点大小
  const maxDegree = Math.max(...Array.from(degrees.values()), 1)
  const nodes = rawNodes.map((n, i) => {
    const id = n.id || n.name || String(i)
    const name = n.name || n.id || `节点${i}`
    const degree = degrees.get(id) || 0
    // 节点大小根据度数计算：基础大小 + 度数权重
    const baseSize = 20
    const degreeBonus = (degree / maxDegree) * 30
    const symbolSize = Math.min(60, baseSize + degreeBonus)

    return {
      id,
      name,
      symbolSize,
      degree,
      itemStyle: {
        opacity: 0.8 + (degree / maxDegree) * 0.2
      }
    }
  })

  // 边优化
  const links = rawLinks.map(l => ({
    source: l.source,
    target: l.target,
    lineStyle: {
      width: 0.5,
      opacity: 0.3,
      curveness: 0.05
    }
  }))

  const maxNodes = getMaxNodes()

  return {
    backgroundColor: '#0A0A0A',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 30, 30, 0.95)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      textStyle: { color: '#FFFFFF', fontSize: 13 },
      formatter: (params) => {
        if (params.dataType === 'node') {
          const degree = params.data.degree || 0
          return `<div style="padding:6px"><strong>${params.name}</strong><br/><span style="color:#A0A0A0">连接数: ${degree}</span></div>`
        }
        return `<div style="padding:4px"><span style="color:#A0A0A0">关系</span></div>`
      }
    },
    animation: isAnimating.value,
    animationDuration: 800,
    animationDurationUpdate: 500,
    series: [{
      type: 'graph',
      layout: 'force',
      // 力导向布局参数
      force: {
        repulsion: 80,
        edgeLength: 60,
        layoutAnimation: true,
        gravity: 0.1,
        alpha: 0.3,
        alphaDecay: 0.02,
        alphaMin: 0.001
      },
      // 漫游和拖拽
      roam: true,
      draggable: true,
      // 标签配置
      label: {
        show: true,
        position: 'right',
        fontSize: 11,
        color: '#A0A0A0',
        formatter: '{b}'
      },
      // 节点样式 - 黑白灰度
      itemStyle: {
        color: {
          type: 'radial',
          x: 0.3, y: 0.3, r: 0.8,
          colorStops: [
            { offset: 0, color: '#FFFFFF' },
            { offset: 0.5, color: '#CCCCCC' },
            { offset: 1, color: '#888888' }
          ]
        },
        borderColor: '#444444',
        borderWidth: 1
      },
      // 边样式
      lineStyle: {
        color: '#666666',
        width: 1,
        opacity: 0.4,
        curveness: 0.05
      },
      // 高亮效果
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 2, color: '#FFFFFF' },
        itemStyle: {
          borderColor: '#FFFFFF',
          borderWidth: 2,
          shadowBlur: 15
        },
        label: {
          show: true,
          fontWeight: 'bold'
        }
      },
      data: nodes,
      links: links
    }]
  }
}

// 渲染图谱
async function render(data) {
  error.value = ''
  await nextTick()

  if (!chartRef.value) return

  const rawNodes = data.nodes || []
  const rawLinks = data.links || []

  totalNodeCount.value = rawNodes.length

  // 数据为空时清除图表
  if (!rawNodes.length) {
    nodeCount.value = 0
    edgeCount.value = 0
    if (chart) {
      chart.clear()
    }
    return
  }

  // 初始化图表
  if (!chart) {
    const echarts = await import('echarts')
    chart = echarts.init(chartRef.value)
    window.addEventListener('resize', handleResize)
  }

  // 保存原始数据
  rawData = { nodes: rawNodes, links: rawLinks }

  // 智能采样
  const maxNodes = getMaxNodes()
  const { nodes: sampledNodes, links: sampledLinks } = smartSample(rawNodes, rawLinks, maxNodes)

  nodeCount.value = sampledNodes.length
  edgeCount.value = sampledLinks.length

  const opt = toGraphOption({ nodes: sampledNodes, links: sampledLinks })
  if (!opt) return

  chart.setOption(opt, true)

  // 节点点击事件 - 可以在这里添加展开功能
  chart.off('click')
  chart.on('click', (params) => {
    if (params.dataType === 'node') {
      console.log('节点点击:', params.name, '度数:', params.data.degree)
    }
  })
}

// 加载更多节点
function loadMore() {
  displayMode.value = 'overview'
  const { nodes, links } = smartSample(rawData.nodes, rawData.links, 800)
  nodeCount.value = nodes.length
  edgeCount.value = links.length

  const opt = toGraphOption({ nodes, links })
  if (opt && chart) {
    chart.setOption(opt, true)
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  error.value = ''
  try {
    let data
    switch (currentView.value) {
      case 'knowledge':
        data = await getKnowledgeGraph(kbId.value || 'sanguo')
        break
      case 'dialogue':
        const sid = userStore.sessionId
        if (!sid) {
          error.value = '请先在对话页发起会话'
          data = { nodes: [], links: [] }
        } else {
          data = await getDialogueGraph(sid)
        }
        break
      case 'user':
        data = await getUserLongGraph(userStore.userId)
        break
    }
    await render(data)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

// 构建索引
async function runIndex() {
  indexing.value = true
  error.value = ''
  try {
    await indexKnowledge(kbId.value || 'sanguo', null, true)
    await loadData()
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    indexing.value = false
  }
}

// 切换视图
function switchView(view) {
  currentView.value = view
  error.value = ''
  nodeCount.value = 0
  edgeCount.value = 0
  totalNodeCount.value = 0
  rawData = { nodes: [], links: [] }
  if (chart) {
    chart.clear()
  }
  loadData()
}

// 获取空状态消息
function getEmptyMessage() {
  switch (currentView.value) {
    case 'knowledge':
      return '请先加载知识库或构建索引'
    case 'dialogue':
      return '请先在对话页发起会话'
    case 'user':
      return '暂无用户图谱数据'
    default:
      return '暂无数据'
  }
}

// 跳转到对话页
function goToChat() {
  window.location.href = '/chat'
}

// 控制函数
function zoomIn() {
  if (chart) chart.dispatchAction({ type: 'zoomIn' })
}

function zoomOut() {
  if (chart) chart.dispatchAction({ type: 'zoomOut' })
}

function resetZoom() {
  if (chart) {
    chart.dispatchAction({ type: 'resetZoom' })
    chart.dispatchAction({ type: 'focusNodeAdjacency' })
  }
}

function toggleAnimation() {
  isAnimating.value = !isAnimating.value
  if (chart) {
    chart.setOption({ animation: isAnimating.value })
  }
}

function handleResize() {
  if (chart) chart.resize()
}

// 监听显示模式变化
watch(displayMode, () => {
  if (rawData.nodes.length > 0) {
    const { nodes, links } = smartSample(rawData.nodes, rawData.links, getMaxNodes())
    nodeCount.value = nodes.length
    edgeCount.value = links.length
    const opt = toGraphOption({ nodes, links })
    if (opt && chart) {
      chart.setOption(opt, true)
    }
  }
})

// 生命周期
onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
    chart = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.graph-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.title-icon {
  width: 24px;
  height: 24px;
  color: var(--primary-color);
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

/* 模式切换 */
.mode-tabs {
  display: flex;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  padding: 4px;
  gap: 4px;
}

.mode-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-tab:hover {
  color: var(--text-primary);
}

.mode-tab.active {
  background: var(--bg-card);
  color: var(--primary-dark);
  box-shadow: var(--shadow-sm);
}

.tab-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

/* 知识库工具栏 */
.kb-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.kb-input {
  width: 200px;
}

.display-mode {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.mode-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 图谱容器 */
.graph-container {
  flex: 1;
  position: relative;
  min-height: 400px;
  background: #0A0A0A;
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.chart.hidden {
  opacity: 0;
  position: absolute;
}

/* 加载状态 */
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 10, 0.95);
  z-index: 10;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  color: var(--primary-color);
  animation: spin 1s linear infinite;
}

.loading-spinner svg {
  width: 100%;
  height: 100%;
}

.loading-text {
  margin-top: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.loading-count {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-muted);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}

.empty-illustration {
  width: 140px;
  height: 140px;
  color: var(--primary-light);
  margin-bottom: 24px;
}

.empty-illustration svg {
  width: 100%;
  height: 100%;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 20px;
}

/* 图例 */
.graph-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  background: rgba(10, 10, 10, 0.9);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.node {
  background: linear-gradient(135deg, #FFFFFF, #888888);
}

.legend-dot.edge {
  width: 20px;
  height: 2px;
  border-radius: 1px;
  background: #666666;
}

.legend-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.legend-label {
  font-size: 12px;
  color: var(--text-muted);
}

/* 控制面板 */
.control-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  background: rgba(10, 10, 10, 0.9);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.control-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.control-btn svg {
  width: 18px;
  height: 18px;
}

.control-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.control-btn.active {
  background: var(--primary-light);
  color: var(--bg-primary);
}

/* 展开提示 */
.expand-hint {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(10, 10, 10, 0.9);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  font-size: 13px;
  color: var(--text-secondary);
}

.expand-btn {
  padding: 6px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.expand-btn:hover {
  background: var(--primary-color);
  color: var(--bg-primary);
  border-color: var(--primary-color);
}

/* 错误提示 */
.error-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: var(--bg-card);
  border: 1px solid var(--danger-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  color: var(--danger-color);
  font-size: 14px;
  z-index: 1000;
}

.error-toast svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.error-toast button {
  padding: 4px 12px;
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  font-size: 12px;
  cursor: pointer;
}

/* 响应式 */
@media (max-width: 768px) {
  .toolbar {
    flex-wrap: wrap;
    gap: 16px;
  }

  .toolbar-center {
    order: 3;
    width: 100%;
    justify-content: flex-start;
  }

  .display-mode {
    display: none;
  }

  .graph-legend {
    flex-wrap: wrap;
  }

  .expand-hint {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
