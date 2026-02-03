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

/* 顶部 Banner - 黑白极简 */
.profile-banner {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 20px;
  padding: 36px 40px;
  margin-bottom: 28px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 28px;
}

.user-avatar-large {
  background: #000000 !important;
  color: white;
  border: 4px solid #f5f5f5;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.user-name {
  margin: 0 0 8px 0;
  color: #000000;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #666666;
  font-size: 14px;
}

/* 统计卡片 - 黑白灰 */
.stats-overview {
  margin-bottom: 28px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #000000;
  transform: translateY(-2px);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.blue { background: #f5f5f5; color: #000000; }
.stat-icon.green { background: #f5f5f5; color: #333333; }
.stat-icon.orange { background: #f5f5f5; color: #444444; }
.stat-icon.purple { background: #f5f5f5; color: #555555; }

.stat-value { 
  font-size: 26px; 
  font-weight: 700; 
  color: #000000;
  letter-spacing: -0.5px;
}

.stat-label { 
  font-size: 13px; 
  color: #888888;
  margin-top: 2px;
}

/* 通用卡片 - 简洁边框 */
.clean-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  margin-bottom: 24px;
  transition: all 0.2s ease;
}

.clean-card:hover {
  border-color: #cccccc;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title { 
  font-size: 15px; 
  font-weight: 600; 
  color: #000000;
}

/* 时间轴 - 黑白 */
.timeline-container {
  padding: 14px 0;
}

.timeline-item {
  position: relative;
  padding-left: 28px;
  margin-bottom: 24px;
  border-left: 2px solid #e5e5e5;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -7px;
  top: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #000000;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 2px #e5e5e5;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.timeline-title { 
  font-weight: 600; 
  color: #000000;
  font-size: 14px;
}

.timeline-time { 
  font-size: 12px; 
  color: #888888;
}

.timeline-desc { 
  margin: 0 0 10px 0; 
  font-size: 14px; 
  color: #666666;
  line-height: 1.6;
}

/* 图表区域 */
.graph-container {
  height: 400px;
  background: #f7f7f7;
  border-radius: 14px;
  border: 1px solid #e5e5e5;
}

.knowledge-graph-chart {
  width: 100%;
  height: 100%;
}

/* 情感面板 - 黑白灰 */
.emotion-panel {
  padding: 14px 0;
}

.current-emotion {
  text-align: center;
  margin-bottom: 24px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 14px;
}

.confidence {
  display: block;
  font-size: 12px;
  color: #888888;
  margin-top: 8px;
}

.emotion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  font-size: 14px;
  padding: 10px 14px;
  background: #f7f7f7;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.emotion-item:hover {
  background: #f0f0f0;
}

.emotion-item .label { 
  width: 70px; 
  color: #666666;
  font-weight: 500;
}

.emotion-item .count { 
  width: 36px; 
  text-align: right; 
  color: #000000;
  font-weight: 600;
}

.content-section {
  margin-bottom: 24px;
}
</style>
