<template>
  <div class="profile-view">
    <!-- 🎨 个人信息顶部横幅 -->
    <div class="profile-banner">
      <div class="banner-content">
        <div class="avatar-section">
          <el-avatar :size="80" class="user-avatar-large">
            <el-icon :size="40"><User /></el-icon>
          </el-avatar>
        </div>
        <div class="user-details">
          <h1 class="user-name">{{ userName }}</h1>
          <div class="user-meta">
            <span class="user-id">ID: {{ userId }}</span>
            <el-tag size="small" type="success" effect="light" round>活跃学习者</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 📊 统计概览 -->
    <el-row :gutter="20" class="stats-overview">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon blue"><el-icon><DataLine /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ profile?.total_interactions || 0 }}</div>
            <div class="stat-label">总交互</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon green"><el-icon><TrendCharts /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ formatPercentage(profile?.average_quality || 0) }}</div>
            <div class="stat-label">平均质量</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon orange"><el-icon><Calendar /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ profile?.learning_streak || 0 }}</div>
            <div class="stat-label">连续学习</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon purple"><el-icon><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ knowledgeGraph?.total_nodes || 0 }}</div>
            <div class="stat-label">知识节点</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 📝 学习记录 -->
    <div class="content-section">
      <el-card class="clean-card">
        <template #header>
          <div class="card-header">
            <span class="title">学习轨迹</span>
            <el-button link type="primary" @click="loadLearningRecords" :loading="loadingRecords">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </template>
        <div v-if="learningRecords.length > 0" class="timeline-container">
          <div 
            v-for="(record, index) in learningRecords.slice(0, 5)"
            :key="index"
            class="timeline-item"
          >
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="timeline-title">{{ record.title || '学习记录' }}</span>
                <span class="timeline-time">{{ formatDate(record.timestamp) }}</span>
              </div>
              <p class="timeline-desc">{{ record.summary || '暂无详情' }}</p>
              <div class="timeline-tags">
                <el-tag size="small" type="info" effect="plain" v-if="record.query_type">
                  {{ record.query_type }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无学习记录" />
      </el-card>
    </div>

    <!-- 🎯 情感与知识 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="16">
        <el-card class="clean-card">
          <template #header>
            <div class="card-header">
              <span class="title">知识图谱</span>
              <el-button link type="primary" @click="loadKnowledgeGraph" :loading="loadingGraph">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div v-if="knowledgeGraph && knowledgeGraph.total_nodes > 0" class="graph-container">
            <v-chart 
              class="knowledge-graph-chart" 
              :option="graphOption" 
              autoresize
            />
          </div>
          <el-empty v-else description="暂无知识图谱数据" />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="clean-card">
          <template #header>
            <div class="card-header">
              <span class="title">情感分析</span>
            </div>
          </template>
          <div v-if="emotionsData && emotionsData.current" class="emotion-panel">
            <div class="current-emotion">
              <el-tag size="large" :type="getEmotionTagType(emotionsData.current.primary_emotion)">
                {{ translateEmotion(emotionsData.current.primary_emotion) }}
              </el-tag>
              <span class="confidence">置信度: {{ formatPercentage(emotionsData.current.confidence, 0) }}</span>
            </div>
            
            <div class="emotion-list">
              <div 
                v-for="(count, emotion) in emotionsData.statistics.distribution" 
                :key="emotion"
                class="emotion-item"
              >
                <span class="label">{{ translateEmotion(emotion) }}</span>
                <el-progress 
                  :percentage="(count / emotionsData.statistics.total_count * 100)"
                  :show-text="false"
                  style="width: 100px"
                />
                <span class="count">{{ count }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  User, DataLine, TrendCharts, Calendar, Connection, Refresh
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import api from '../api'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent } from 'echarts/components'
import {
  formatDate, formatPercentage, translateEmotion, getEmotionTagType,
  normalizeProfile, normalizeLearningRecords, safeGet, mapGraphNodes, mapGraphEdges
} from '../utils'

use([CanvasRenderer, GraphChart, TitleComponent, TooltipComponent])

const userStore = useUserStore()
const userId = computed(() => userStore.userId)
const userName = computed(() => userStore.userName)

const profile = ref(null)
const learningRecords = ref([])
const knowledgeGraph = ref(null)
const emotionsData = ref(null)
const loadingRecords = ref(false)
const loadingGraph = ref(false)

// ECharts Option
const graphOption = computed(() => {
  if (!knowledgeGraph.value?.nodes) return {}
  const nodes = mapGraphNodes(knowledgeGraph.value.nodes)
  const links = mapGraphEdges(knowledgeGraph.value.edges)
  
  return {
    tooltip: {},
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      roam: true,
      label: { show: true, position: 'right', formatter: '{b}' },
      force: { repulsion: 100, edgeLength: 100 },
      itemStyle: { color: '#4f46e5' },
      lineStyle: { color: '#e5e7eb' }
    }]
  }
})

async function loadData() {
  try {
    // Load Profile
    const pData = await api.memoryManager.getProfile(userId.value, { include_emotions: true })
    profile.value = normalizeProfile(pData.profile)
    emotionsData.value = pData.emotions
    
    // Load Records
    loadingRecords.value = true
    const rData = await api.memoryManager.getLearningRecords(userId.value, { limit: 5 })
    learningRecords.value = normalizeLearningRecords(safeGet(rData, 'data.records', []))
    loadingRecords.value = false
    
    // Load Graph
    loadingGraph.value = true
    const gData = await api.memoryManager.getKnowledgeGraph(userId.value)
    const graph = safeGet(gData, 'data.graph', {})
    const stats = safeGet(gData, 'data.statistics', {})
    knowledgeGraph.value = {
      nodes: graph.nodes || [],
      edges: graph.edges || [],
      total_nodes: stats.total_nodes || 0
    }
    loadingGraph.value = false
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.profile-view {
  max-width: 1200px;
  margin: 0 auto;
}

/* 顶部 Banner */
.profile-banner {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-avatar-large {
  background: #4f46e5;
  color: white;
  border: 4px solid #eef2ff;
}

.user-name {
  margin: 0 0 8px 0;
  color: #111827;
  font-size: 24px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #6b7280;
  font-size: 14px;
}

/* 统计卡片 */
.stats-overview {
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.blue { background: #eff6ff; color: #3b82f6; }
.stat-icon.green { background: #ecfdf5; color: #10b981; }
.stat-icon.orange { background: #fff7ed; color: #f97316; }
.stat-icon.purple { background: #f5f3ff; color: #8b5cf6; }

.stat-value { font-size: 24px; font-weight: 700; color: #111827; }
.stat-label { font-size: 13px; color: #6b7280; }

/* 通用卡片 */
.clean-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title { font-size: 16px; font-weight: 600; color: #374151; }

/* 时间轴 */
.timeline-container {
  padding: 12px 0;
}

.timeline-item {
  position: relative;
  padding-left: 24px;
  margin-bottom: 20px;
  border-left: 2px solid #e5e7eb;
}

.timeline-dot {
  position: absolute;
  left: -6px;
  top: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #4f46e5;
  border: 2px solid #ffffff;
  box-shadow: 0 0 0 2px #eef2ff;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.timeline-title { font-weight: 600; color: #1f2937; }
.timeline-time { font-size: 12px; color: #9ca3af; }
.timeline-desc { margin: 0 0 8px 0; font-size: 14px; color: #4b5563; }

/* 图表 */
.graph-container {
  height: 400px;
  background: #f9fafb;
  border-radius: 8px;
}

.knowledge-graph-chart {
  width: 100%;
  height: 100%;
}

/* 情感面板 */
.emotion-panel {
  padding: 12px 0;
}

.current-emotion {
  text-align: center;
  margin-bottom: 20px;
}

.confidence {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.emotion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.emotion-item .label { width: 60px; color: #4b5563; }
.emotion-item .count { width: 30px; text-align: right; color: #6b7280; }
</style>
