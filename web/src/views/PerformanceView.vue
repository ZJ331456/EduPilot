<template>
  <div class="performance-view">
    <!-- 🎨 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon><Monitor /></el-icon>
        </div>
        <div>
          <h1 class="page-title">性能监控</h1>
          <p class="page-subtitle">系统实时状态与资源监控</p>
        </div>
      </div>
      <el-button 
        type="primary" 
        plain
        @click="refreshData" 
        :loading="loading"
      >
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 学习评测（对齐后端 POST /api/v1/evaluation/run） -->
    <div class="section-container">
      <el-card class="clean-card">
        <template #header>
          <div class="card-header">
            <span class="title">学习评测</span>
          </div>
        </template>
        <p class="hint-text">结合当前用户与可选会话摘录，调用大模型生成评分与建议。</p>
        <el-form label-width="88px" class="eval-form">
          <el-form-item label="学习目标">
            <el-input v-model="evalGoals" type="textarea" :rows="2" placeholder="可选" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="evalLoading" @click="submitEvaluation">
              运行评测
            </el-button>
          </el-form-item>
        </el-form>
        <pre v-if="evalResult" class="eval-pre">{{ JSON.stringify(evalResult, null, 2) }}</pre>
      </el-card>
    </div>

    <!-- 核心指标卡片组 -->
    <el-row :gutter="20" class="metrics-overview">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card">
          <div class="metric-icon primary">
            <el-icon><DataLine /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ metrics.totalRequests }}</div>
            <div class="metric-label">总请求数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card">
          <div class="metric-icon success">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ metrics.successRate.toFixed(1) }}%</div>
            <div class="metric-label">成功率</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card">
          <div class="metric-icon warning">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ formatDuration(metrics.avgResponseTime) }}</div>
            <div class="metric-label">平均响应</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="metric-card">
          <div class="metric-icon danger">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-value">{{ metrics.slowRequestsCount }}</div>
            <div class="metric-label">慢请求数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 🎯 前端性能 -->
    <div class="section-container">
      <el-card class="clean-card">
        <template #header>
          <div class="card-header">
            <span class="title">前端性能指标</span>
          </div>
        </template>
        
        <div class="performance-grid">
          <div class="perf-item">
            <span class="perf-label">页面加载</span>
            <div class="perf-value">{{ frontendMetrics.pageLoadTime }}ms</div>
            <el-progress 
              :percentage="Math.min((frontendMetrics.pageLoadTime / 3000) * 100, 100)" 
              :color="getProgressColor(frontendMetrics.pageLoadTime, 3000)"
              :show-text="false"
              :stroke-width="4"
            />
          </div>
          
          <div class="perf-item">
            <span class="perf-label">首次绘制 (FCP)</span>
            <div class="perf-value">{{ frontendMetrics.firstContentfulPaint }}ms</div>
            <el-progress 
              :percentage="Math.min((frontendMetrics.firstContentfulPaint / 2000) * 100, 100)" 
              :color="getProgressColor(frontendMetrics.firstContentfulPaint, 2000)"
              :show-text="false"
              :stroke-width="4"
            />
          </div>
          
          <div class="perf-item">
            <span class="perf-label">平均 API 耗时</span>
            <div class="perf-value">{{ frontendMetrics.averageApiTime }}ms</div>
            <el-progress 
              :percentage="Math.min((frontendMetrics.averageApiTime / 1000) * 100, 100)" 
              :color="getProgressColor(frontendMetrics.averageApiTime, 1000)"
              :show-text="false"
              :stroke-width="4"
            />
          </div>

          <div class="perf-item stat-only">
            <div class="stat-row">
              <span class="label">资源总数</span>
              <span class="value">{{ frontendMetrics.resourceCount }}</span>
            </div>
            <div class="stat-row">
              <span class="label">错误计数</span>
              <span class="value" :class="{ 'text-danger': frontendMetrics.errorCount > 0 }">
                {{ frontendMetrics.errorCount }}
              </span>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 🔥 后端性能表格 -->
    <div class="section-container">
      <el-card class="clean-card">
        <template #header>
          <div class="card-header">
            <span class="title">后端 API 统计</span>
            <el-button type="danger" link @click="clearCache">清空缓存</el-button>
          </div>
        </template>
        
        <el-table :data="endpointStats" style="width: 100%">
          <el-table-column prop="endpoint" label="端点" min-width="200" />
          <el-table-column prop="avg" label="平均耗时" width="120">
            <template #default="{ row }">
              <span :class="getTimeClass(row.avg)">{{ formatDuration(row.avg) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="min" label="最小" width="100">
            <template #default="{ row }">{{ formatDuration(row.min) }}</template>
          </el-table-column>
          <el-table-column prop="max" label="最大" width="100">
            <template #default="{ row }">{{ formatDuration(row.max) }}</template>
          </el-table-column>
          <el-table-column prop="count" label="调用次数" width="100" align="center">
            <template #default="{ row }"><el-tag size="small" type="info">{{ row.count }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 💾 缓存统计 -->
    <div class="section-container">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="clean-card cache-card">
            <div class="cache-stat">
              <div class="cache-label">缓存条目数</div>
              <div class="cache-value">{{ cacheStats.cache_size }}</div>
            </div>
            <el-icon class="cache-icon"><Files /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="clean-card cache-card">
            <div class="cache-stat">
              <div class="cache-label">缓存 TTL</div>
              <div class="cache-value">{{ cacheStats.cache_ttl }}s</div>
            </div>
            <el-icon class="cache-icon"><Clock /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  Monitor, Refresh, DataLine, CircleCheck, Timer, Warning, 
  Files, Clock
} from '@element-plus/icons-vue'
import { usePerformanceStore } from '@/stores/performance'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { runEvaluation } from '../api/edupilot'
import { showError, showSuccess, showWarning, formatDate, formatDuration, safeGet } from '../utils'

const performanceStore = usePerformanceStore()
const userStore = useUserStore()
const chatStore = useChatStore()
const evalGoals = ref('')
const evalResult = ref(null)
const evalLoading = ref(false)

async function submitEvaluation() {
  evalLoading.value = true
  try {
    const res = await runEvaluation({
      user_id: userStore.userId,
      session_id: chatStore.sessionId,
      goals: evalGoals.value,
      extra_summary: ''
    })
    evalResult.value = res.evaluation || res
    showSuccess('评测完成')
  } catch (e) {
    console.error(e)
    showError(e, '评测失败')
  } finally {
    evalLoading.value = false
  }
}

const loading = ref(false)
const backendPerformance = ref({})
const cacheStats = ref({ cache_size: 0, cache_ttl: 0 })

const frontendMetrics = computed(() => performanceStore.getReport())

const metrics = computed(() => {
  const data = backendPerformance.value.data || {}
  return {
    totalRequests: data.endpoint_stats ? 
      Object.values(data.endpoint_stats).reduce((sum, stat) => sum + stat.count, 0) : 0,
    successRate: 100,
    avgResponseTime: data.endpoint_stats ?
      Object.values(data.endpoint_stats).reduce((sum, stat) => sum + stat.avg, 0) /
      Object.keys(data.endpoint_stats).length : 0,
    slowRequestsCount: data.slow_requests_count || 0
  }
})

const endpointStats = computed(() => {
  const stats = backendPerformance.value.data?.endpoint_stats || {}
  return Object.entries(stats).map(([endpoint, data]) => ({ endpoint, ...data }))
})

const getProgressColor = (value, max) => {
  const p = (value / max) * 100
  return p < 50 ? '#10b981' : p < 80 ? '#f59e0b' : '#ef4444'
}

const getTimeClass = (time) => {
  if (time < 500) return 'text-success'
  if (time < 1000) return 'text-warning'
  return 'text-danger'
}

const refreshData = async () => {
  loading.value = true
  try {
    backendPerformance.value = { data: {} }
    cacheStats.value = { cache_size: 0, cache_ttl: 0 }
    showSuccess('当前使用 EduPilot 后端（无旧版 endpoint 统计接口）')
  } catch (error) {
    console.error(error)
    showError(error, '获取数据失败')
  } finally {
    loading.value = false
  }
}

const clearCache = async () => {
  showWarning('EduPilot 未实现旧版缓存清理，可忽略此项')
}

onMounted(() => {
  performanceStore.startMonitoring()
  refreshData()
})
</script>

<style scoped>
.performance-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 36px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e5e5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.header-icon {
  width: 52px;
  height: 52px;
  background: #f5f5f5;
  color: #000000;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  color: #000000;
  margin: 0;
  letter-spacing: -0.5px;
}

.page-subtitle {
  color: #666666;
  font-size: 14px;
  margin: 4px 0 0 0;
}

.hint-text {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px 0;
}

.eval-form {
  max-width: 560px;
}

.eval-pre {
  margin-top: 12px;
  padding: 12px;
  background: #f8f8f8;
  border-radius: 8px;
  font-size: 12px;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 指标卡片 - 黑白灰 */
.metrics-overview {
  margin-bottom: 32px;
}

.metric-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 16px;
  transition: all 0.2s ease;
}

.metric-card:hover {
  border-color: #000000;
  transform: translateY(-2px);
}

.metric-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.metric-icon.primary { 
  background: #000000; 
  color: #ffffff; 
}
.metric-icon.success { 
  background: #f5f5f5; 
  color: #333333; 
}
.metric-icon.warning { 
  background: #f5f5f5; 
  color: #444444; 
}
.metric-icon.danger { 
  background: #f5f5f5; 
  color: #555555; 
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #000000;
  letter-spacing: -0.5px;
}

.metric-label {
  font-size: 13px;
  color: #888888;
  margin-top: 2px;
}

/* 通用卡片 - 简洁边框 */
.clean-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  transition: all 0.2s ease;
}

.clean-card:hover {
  border-color: #cccccc;
}

.section-container {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  font-size: 15px;
  font-weight: 600;
  color: #000000;
}

/* 前端性能网格 - 黑白极简 */
.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.perf-item {
  background: #f7f7f7;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid #e5e5e5;
  transition: all 0.2s ease;
}

.perf-item:hover {
  border-color: #000000;
  transform: translateY(-2px);
}

.perf-label {
  font-size: 13px;
  color: #666666;
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
}

.perf-value {
  font-size: 24px;
  font-weight: 700;
  color: #000000;
  margin-bottom: 12px;
  letter-spacing: -0.3px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 14px;
  font-size: 14px;
  padding: 10px 14px;
  background: #ffffff;
  border-radius: 8px;
}

.stat-row .label { color: #666666; }
.stat-row .value { font-weight: 600; color: #000000; }

/* 表格优化 */
.clean-card :deep(.el-table) {
  --el-table-border-color: #e5e5e5;
  --el-table-header-bg-color: #f7f7f7;
}

.clean-card :deep(.el-table th.el-table__cell) {
  font-weight: 600;
  color: #666666;
  font-size: 13px;
}

.clean-card :deep(.el-table td.el-table__cell) {
  font-size: 14px;
}

/* 缓存卡片 - 黑白简约 */
.cache-card :deep(.el-card__body) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px;
}

.cache-label { 
  color: #666666; 
  font-size: 14px; 
  margin-bottom: 6px;
  font-weight: 500;
}

.cache-value { 
  color: #000000; 
  font-size: 28px; 
  font-weight: 700;
  letter-spacing: -0.5px;
}

.cache-icon { 
  font-size: 40px; 
  color: #cccccc;
  opacity: 0.8;
}

/* 辅助类 */
.text-success { color: #333333; font-weight: 600; }
.text-warning { color: #555555; font-weight: 600; }
.text-danger { color: #000000; font-weight: 600; }
</style>
