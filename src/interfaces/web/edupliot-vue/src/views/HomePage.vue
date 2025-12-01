<template>
  <div class="home-container">
    <!-- 欢迎区域 -->
    <section class="hero-section">
      <div class="hero-badge">
        <span class="badge-dot"></span>
        AI 驱动的个性化学习引擎
      </div>
      <h1 class="hero-title">
        学习，从此 <span class="highlight">清晰可见</span>
      </h1>
      <p class="hero-desc">
        EduPilot 结合多智能体协作与苏格拉底式引导，为你构建专属知识图谱。<br>
        不仅仅是回答问题，更是培养深度思考能力。
      </p>
      
      <div class="hero-actions">
        <el-button type="primary" size="large" class="main-btn" @click="startLearning" round>
          <el-icon class="el-icon--left"><ChatDotRound /></el-icon>
          开始对话
        </el-button>
        <el-button size="large" class="secondary-btn" @click="exploreKnowledge" round>
          <el-icon class="el-icon--left"><Search /></el-icon>
          检索知识
        </el-button>
      </div>

      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-val">{{ formatNumber(stats?.total_queries || 1204) }}</span>
          <span class="stat-key">次智能交互</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-val">{{ healthStatus.text }}</span>
          <span class="stat-key">系统状态</span>
        </div>
      </div>
    </section>

    <!-- 功能卡片区 -->
    <section class="features-section">
      <h2 class="section-header">核心能力</h2>
      <div class="features-grid">
        <div v-for="feature in features" :key="feature.title" class="feature-card">
          <div class="icon-box">
            <component :is="feature.icon" />
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- 流程图区 (简约线条风格) -->
    <section class="workflow-section">
      <h2 class="section-header">学习闭环</h2>
      <div class="steps-container">
        <div class="step" v-for="(step, index) in workflowSteps" :key="index">
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <h4>{{ step.title }}</h4>
            <p>{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Search, DataAnalysis, Reading, TrendCharts, Monitor } from '@element-plus/icons-vue'
import api from '../api'
import { formatNumber, safeGet } from '../utils'

const router = useRouter()

const features = [
  { icon: ChatDotRound, title: '深度对话', description: '不只是给出答案，更通过追问引导你探索知识的本质。' },
  { icon: DataAnalysis, title: '知识图谱', description: '可视化展示知识点关联，构建系统化的知识结构。' },
  { icon: TrendCharts, title: '学习画像', description: '根据你的交互习惯，实时生成个性化的能力维度分析。' },
  { icon: Reading, title: '苏格拉底引导', description: '采用经典的产婆术教学法，激发批判性思维。' }
]

const workflowSteps = [
  { title: '意图识别', description: '精准分析学习需求与当前上下文' },
  { title: '路径规划', description: '动态生成个性化学习与探索路径' },
  { title: '引导交互', description: '多轮对话与实时反馈修正' },
  { title: '知识沉淀', description: '自动归纳总结并更新知识库' }
]

const stats = ref(null)
const health = ref({ status: 'healthy' })

const healthStatus = computed(() => ({
  text: health.value?.status === 'healthy' ? '运行正常' : '维护中'
}))

function startLearning() { router.push('/chat') }
function exploreKnowledge() { router.push('/knowledge') }

onMounted(async () => {
  try {
    const [healthData, statsData] = await Promise.all([api.health(), api.stats()])
    health.value = healthData
    stats.value = safeGet(statsData, 'data', null)
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.home-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* Hero Section */
.hero-section {
  text-align: center;
  margin-bottom: 100px;
  padding-top: 40px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  padding: 6px 16px;
  border-radius: 99px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 24px;
  letter-spacing: -1px;
}

.hero-title .highlight {
  color: var(--primary-color);
  position: relative;
}

.hero-desc {
  font-size: 18px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto 40px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 60px;
}

.main-btn {
  padding: 12px 32px;
  height: auto;
  font-size: 16px;
  box-shadow: var(--shadow-md);
  transition: transform 0.2s;
}

.main-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.secondary-btn {
  padding: 12px 32px;
  height: auto;
  font-size: 16px;
  background: var(--bg-white);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.secondary-btn:hover {
  background: #f3f4f6;
  color: var(--primary-color);
  border-color: var(--border-color);
}

.stats-row {
  display: inline-flex;
  align-items: center;
  background: var(--bg-white);
  padding: 16px 32px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-key {
  font-size: 12px;
  color: var(--text-tertiary);
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--border-color);
}

/* Features Section */
.section-header {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 40px;
  text-align: center;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
  margin-bottom: 100px;
}

.feature-card {
  background: var(--bg-white);
  padding: 32px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.icon-box {
  width: 48px;
  height: 48px;
  background: var(--primary-fade);
  color: var(--primary-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 20px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.feature-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Workflow Section */
.steps-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.step {
  position: relative;
  padding: 24px;
  background: var(--bg-white);
  border-radius: 12px;
  border: 1px dashed var(--border-color);
}

.step-number {
  font-size: 40px;
  font-weight: 900;
  color: var(--primary-fade);
  position: absolute;
  top: 10px;
  right: 20px;
  pointer-events: none;
}

.step-content {
  position: relative;
  z-index: 1;
}

.step-content h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.step-content p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>