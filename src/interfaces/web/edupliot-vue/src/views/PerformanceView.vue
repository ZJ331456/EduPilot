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

    <!-- 📊 核心指标卡片组 -->
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
import { ElMessageBox } from 'element-plus'
import {
  Monitor, Refresh, DataLine, CircleCheck, Timer, Warning, 
  Files, Clock
} from '@element-plus/icons-vue'
import api from '@/api'
import { usePerformanceStore } from '@/stores/performance'
import { showError, showSuccess, showWarning, formatDate, formatDuration, safeGet } from '../utils'

const performanceStore = usePerformanceStore()
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
    backendPerformance.value = await api.system.performanceStats() || {}
    const cacheData = await api.system.cacheStats()
    cacheStats.value = safeGet(cacheData, 'data', { cache_size: 0, cache_ttl: 0 })
    showSuccess('数据已更新')
  } catch (error) {
    console.error(error)
    showError(error, '获取数据失败')
  } finally {
    loading.value = false
  }
}

const clearCache = async () => {
  try {
    await ElMessageBox.confirm('确定清空缓存？', '警告', { type: 'warning' })
    await api.system.clearCache()
    showSuccess('缓存已清空')
    refreshData()
  } catch (e) { /* cancel */ }
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
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 14px;
  margin: 4px 0 0 0;
}

/* 指标卡片 */
.metrics-overview {
  margin-bottom: 32px;
}

.metric-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transform: translateY(-2px);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.metric-icon.primary { background: #eff6ff; color: #3b82f6; }
.metric-icon.success { background: #ecfdf5; color: #10b981; }
.metric-icon.warning { background: #fffbeb; color: #f59e0b; }
.metric-icon.danger { background: #fef2f2; color: #ef4444; }

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.metric-label {
  font-size: 13px;
  color: #6b7280;
}

/* 通用卡片 */
.clean-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

/* 前端性能网格 */
.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.perf-item {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}

.perf-label {
  font-size: 13px;
  color: #6b7280;
  display: block;
  margin-bottom: 8px;
}

.perf-value {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}

.stat-row .label { color: #6b7280; }
.stat-row .value { font-weight: 600; color: #1f2937; }

/* 缓存卡片 */
.cache-card :deep(.el-card__body) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
}

.cache-label { color: #6b7280; font-size: 14px; margin-bottom: 4px; }
.cache-value { color: #111827; font-size: 24px; font-weight: 700; }
.cache-icon { font-size: 32px; color: #e5e7eb; }

/* 辅助类 */
.text-success { color: #10b981; }
.text-warning { color: #f59e0b; }
.text-danger { color: #ef4444; }
</style>
