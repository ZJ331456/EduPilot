<template>
  <div class="profile-view">
    <!-- 个人信息顶部横幅 -->
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

    <!-- 统计概览（对齐后端画像 JSON + 长期图谱） -->
    <el-row :gutter="20" class="stats-overview">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon blue"><el-icon><DataLine /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ (profile?.strengths && profile.strengths.length) || 0 }}</div>
            <div class="stat-label">优势项数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon green"><el-icon><TrendCharts /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ (profile?.gaps && profile.gaps.length) || 0 }}</div>
            <div class="stat-label">待补项数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon orange"><el-icon><Calendar /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value text-ellipsis">{{ profile?.learning_style || '—' }}</div>
            <div class="stat-label">学习风格</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon purple"><el-icon><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ knowledgeGraph?.total_nodes || 0 }}</div>
            <div class="stat-label">图谱节点</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="toolbar-row">
      <el-col :span="24">
        <el-space wrap>
          <el-button type="primary" :loading="analyzing" @click="refreshProfileAnalysis">
            重新分析画像
          </el-button>
          <el-button :loading="loadingPlan" @click="loadLearningPlan">加载学习计划</el-button>
          <el-input
            v-model="planGoalHint"
            placeholder="生成计划时的目标说明（可选）"
            style="max-width: 320px"
            clearable
          />
          <el-button type="success" :loading="generatingPlan" @click="generateLearningPlanAction">
            生成学习计划
          </el-button>
        </el-space>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="learningPlan && Object.keys(learningPlan).length" style="margin-bottom: 20px">
      <el-col :span="24">
        <el-card class="clean-card">
          <template #header><span class="title">学习计划（后端 /api/v1/plan）</span></template>
          <pre class="json-block">{{ JSON.stringify(learningPlan, null, 2) }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <!-- 画像详情（LLM 结构化输出） -->
    <div class="content-section" v-if="profile && hasStructuredProfile">
      <el-card class="clean-card">
        <template #header>
          <span class="title">画像详情</span>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学习风格" v-if="profile.learning_style">
            {{ profile.learning_style }}
          </el-descriptions-item>
          <el-descriptions-item label="优势" v-if="profile.strengths?.length">
            <el-tag v-for="(s, i) in profile.strengths" :key="i" size="small" class="tag-gap">{{ s }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="短板" v-if="profile.gaps?.length">
            <el-tag v-for="(g, i) in profile.gaps" :key="i" type="warning" size="small" class="tag-gap">{{ g }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="兴趣" v-if="profile.interests?.length">
            <el-tag v-for="(x, i) in profile.interests" :key="i" type="success" size="small" class="tag-gap">{{ x }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="推荐侧重" v-if="profile.recommended_focus">
            {{ profile.recommended_focus }}
          </el-descriptions-item>
          <el-descriptions-item label="风险与注意" v-if="profile.risk_notes">
            {{ profile.risk_notes }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <!-- 学习轨迹（旧版记忆服务已移除，占位提示） -->
    <div class="content-section">
      <el-card class="clean-card">
        <template #header>
          <div class="card-header">
            <span class="title">学习轨迹</span>
          </div>
        </template>
        <el-empty description="当前后端未单独提供学习轨迹列表，对话内容见「学习对话」页与 data/sessions" />
      </el-card>
    </div>

    <!-- 知识图谱与洞察 -->
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
              <span class="title">画像洞察</span>
            </div>
          </template>
          <div v-if="profile?.recommended_focus || profile?.risk_notes" class="insight-panel">
            <p v-if="profile.recommended_focus" class="insight-block">
              <strong>推荐侧重</strong><br />
              {{ profile.recommended_focus }}
            </p>
            <p v-if="profile.risk_notes" class="insight-block">
              <strong>注意</strong><br />
              {{ profile.risk_notes }}
            </p>
          </div>
          <el-empty v-else description="请先点击「重新分析画像」生成结构化数据" />
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
import {
  getProfile,
  getUserLongGraph,
  analyzeProfile,
  getPlan,
  generatePlan
} from '../api/edupilot'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent } from 'echarts/components'
import {
  formatDate,
  formatPercentage,
  normalizeProfile,
  mapGraphNodes,
  mapGraphEdges
} from '../utils'

use([CanvasRenderer, GraphChart, TitleComponent, TooltipComponent])

const userStore = useUserStore()
const userId = computed(() => userStore.userId)
const userName = computed(() => userStore.userName)

const profile = ref(null)
const knowledgeGraph = ref(null)
const loadingGraph = ref(false)
const learningPlan = ref(null)
const planGoalHint = ref('')
const analyzing = ref(false)
const loadingPlan = ref(false)
const generatingPlan = ref(false)

const hasStructuredProfile = computed(() => {
  const p = profile.value
  if (!p) return false
  return !!(p.learning_style || p.strengths?.length || p.recommended_focus)
})

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
    let p = await getProfile(userId.value)
    if (!p || Object.keys(p).length === 0) {
      await analyzeProfile({ user_id: userId.value, session_id: null, extra_summary: '' })
      p = await getProfile(userId.value)
    }
    profile.value = normalizeProfile(p)

    loadingGraph.value = true
    const g = await getUserLongGraph(userId.value)
    const edges = (g.links || []).map((l) => ({
      source: l.source,
      target: l.target,
      relation: l.value
    }))
    knowledgeGraph.value = {
      nodes: g.nodes || [],
      edges,
      total_nodes: (g.nodes || []).length
    }
    loadingGraph.value = false

    const plan = await getPlan(userId.value)
    learningPlan.value = plan && Object.keys(plan).length ? plan : null
  } catch (e) {
    console.error(e)
  }
}

async function refreshProfileAnalysis() {
  analyzing.value = true
  try {
    await analyzeProfile({ user_id: userId.value, session_id: null, extra_summary: '' })
    profile.value = normalizeProfile(await getProfile(userId.value))
  } finally {
    analyzing.value = false
  }
}

async function loadLearningPlan() {
  loadingPlan.value = true
  try {
    const plan = await getPlan(userId.value)
    learningPlan.value = plan && Object.keys(plan).length ? plan : null
  } finally {
    loadingPlan.value = false
  }
}

async function generateLearningPlanAction() {
  generatingPlan.value = true
  try {
    await generatePlan(userId.value, planGoalHint.value || '')
    await loadLearningPlan()
  } finally {
    generatingPlan.value = false
  }
}

function loadKnowledgeGraph() {
  loadData()
}

onMounted(() => loadData())
</script>

<style scoped>
/* 全局容器 - 深色极简 */
.profile-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* 顶部 Banner - 深色卡片风格 */
.profile-banner {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 36px 40px;
  margin-bottom: 28px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 28px;
}

.user-avatar-large {
  background: var(--text-primary) !important;
  color: var(--bg-base);
  border: 4px solid var(--border-color);
}

.user-name {
  margin: 0 0 8px 0;
  color: var(--text-primary);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 统计卡片 - 深色灰阶 */
.stats-overview {
  margin-bottom: 28px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-2px);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.blue { 
  background: var(--bg-secondary); 
  color: var(--text-primary); 
}
.stat-icon.green { 
  background: var(--bg-secondary); 
  color: var(--text-primary); 
}
.stat-icon.orange { 
  background: var(--bg-secondary); 
  color: var(--text-primary); 
}
.stat-icon.purple { 
  background: var(--bg-secondary); 
  color: var(--text-primary); 
}

.stat-value { 
  font-size: 26px; 
  font-weight: 700; 
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.stat-label { 
  font-size: 13px; 
  color: var(--text-secondary);
  margin-top: 2px;
}

.text-ellipsis {
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.json-block {
  font-size: 12px;
  line-height: 1.5;
  max-height: 360px;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: var(--radius-md);
}

.tag-gap {
  margin-right: 6px;
  margin-bottom: 4px;
}

.insight-panel {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.insight-block {
  margin: 0 0 12px 0;
}

.insight-block strong {
  color: var(--text-primary);
}

/* 通用卡片 - 深色简洁边框 */
.clean-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  transition: all 0.2s ease;
}

.clean-card:hover {
  border-color: var(--border-hover);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title { 
  font-size: 15px; 
  font-weight: 600; 
  color: var(--text-primary);
}

/* 时间轴 - 深色线条 */
.timeline-container {
  padding: 14px 0;
}

.timeline-item {
  position: relative;
  padding-left: 28px;
  margin-bottom: 24px;
  border-left: 2px solid var(--border-color);
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
  background: var(--text-primary);
  border: 3px solid var(--bg-card);
  box-shadow: 0 0 0 2px var(--border-color);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.timeline-title { 
  font-weight: 600; 
  color: var(--text-primary);
  font-size: 14px;
}

.timeline-time { 
  font-size: 12px; 
  color: var(--text-muted);
}

.timeline-desc { 
  margin: 0 0 10px 0; 
  font-size: 14px; 
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 图表区域 - 深色背景 */
.graph-container {
  height: 400px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.knowledge-graph-chart {
  width: 100%;
  height: 100%;
}

/* 情感面板 - 深色灰阶 */
.emotion-panel {
  padding: 14px 0;
}

.current-emotion {
  text-align: center;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.confidence {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

.emotion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  font-size: 14px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.emotion-item:hover {
  background: var(--bg-hover);
}

.emotion-item .label { 
  width: 70px; 
  color: var(--text-secondary);
  font-weight: 500;
}

.emotion-item .count { 
  width: 36px; 
  text-align: right; 
  color: var(--text-primary);
  font-weight: 600;
}

.content-section {
  margin-bottom: 24px;
}
</style>
