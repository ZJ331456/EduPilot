<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <div class="status-pill">
          <span class="pulse"></span>
          <span class="status-text">{{ healthStatus.text }}</span>
        </div>
        
        <h1 class="hero-title">
          <span class="gradient-text">智能学习</span>
          <br />精准决策
        </h1>
        
        <p class="hero-desc">
          多智能体编排 · 图谱检索 · 提问式引导<br/>
          为每个问题给出可追溯、可验证的学习路径
        </p>

        <div class="hero-actions">
          <button class="btn-primary" @click="startLearning">
            <el-icon><ChatDotRound /></el-icon>
            开始对话
          </button>
          <button class="btn-secondary" @click="exploreKnowledge">
            <el-icon><Search /></el-icon>
            知识图谱
          </button>
        </div>

        <div class="tech-stack">
          <span v-for="tag in heroTags" :key="tag" class="tech-tag">{{ tag }}</span>
        </div>
      </div>

      <div class="hero-visual">
        <div class="metrics-grid">
          <div class="metric-card highlight">
            <div class="metric-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="metric-info">
              <span class="metric-value">{{ avgLatency }}<small>ms</small></span>
              <span class="metric-label">平均响应</span>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-info">
              <span class="metric-value">{{ successRate }}<small>%</small></span>
              <span class="metric-label">成功率</span>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-info">
              <span class="metric-value">{{ totalRequests }}</span>
              <span class="metric-label">总请求</span>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-info">
              <span class="metric-value">{{ activeAgents }}</span>
              <span class="metric-label">活跃 Agents</span>
            </div>
          </div>
        </div>

        <div class="workflow-preview">
          <div class="preview-header">
            <span class="preview-title">工作流实况</span>
            <span class="live-badge">
              <span class="live-dot"></span>
              Live
            </span>
          </div>
          <div class="workflow-timeline">
            <div 
              v-for="(step, index) in workflowSteps" 
              :key="index" 
              class="timeline-item"
              :class="{ 'active': index === 0 }"
            >
              <div class="timeline-marker">
                <span class="marker-dot"></span>
                <span class="marker-line" v-if="index < workflowSteps.length - 1"></span>
              </div>
              <div class="timeline-content">
                <h5>{{ step.title }}</h5>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <span class="section-tag">核心能力</span>
        <h2>为学习而设计的多智能体协作</h2>
      </div>
      
      <div class="features-grid">
        <article 
          v-for="(feature, index) in features" 
          :key="feature.title" 
          class="feature-card"
          :style="{ '--delay': index * 0.1 + 's' }"
        >
          <div class="feature-icon">
            <component :is="feature.icon" />
          </div>
          <span class="feature-tag">{{ feature.tag }}</span>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </article>
      </div>
    </section>

    <!-- Workflow Section -->
    <section class="workflow-section">
      <div class="section-header">
        <span class="section-tag">工作流程</span>
        <h2>从意图解析到测验闭环</h2>
      </div>
      
      <div class="workflow-steps">
        <div 
          v-for="(step, index) in workflowSteps" 
          :key="index" 
          class="workflow-step"
        >
          <div class="step-number">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="step-content">
            <h4>{{ step.title }}</h4>
            <p>{{ step.description }}</p>
          </div>
          <div class="step-connector" v-if="index < workflowSteps.length - 1">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M5 12h14M12 5l7 7-7 7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
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
import { healthCheck } from '../api/edupilot'
import { formatNumber, safeGet } from '../utils'

const router = useRouter()

const features = [
  { icon: ChatDotRound, title: '生成式对话', tag: 'Socratic', description: '用追问与澄清让学习者自己推导答案，而不是直接给结论。' },
  { icon: DataAnalysis, title: '图谱检索', tag: 'GraphRAG', description: '基于知识图谱的关联搜索，确保回答有出处、有结构。' },
  { icon: TrendCharts, title: '个性画像', tag: 'Profile', description: '跟踪认知水平与偏好，实时调整学习难度与形式。' },
  { icon: Reading, title: '课程设计', tag: 'Curriculum', description: '把碎片问题组装为进阶路线，含练习与测验闭环。' },
  { icon: Monitor, title: '性能观测', tag: 'Ops', description: 'API 级别监控、缓存与限流，确保低延迟稳定可用。' }
]

const workflowSteps = [
  { title: '意图理解', description: '快速分辨目标、上下文和需要的工具' },
  { title: '路径规划', description: '动态 fan-out/fan-in 安排知识检索与技能执行' },
  { title: '对话引导', description: 'Socratic 提问 + 记忆管理，锁定薄弱点' },
  { title: '产出与评审', description: 'Draft + Reviewer + Quiz 三段式输出与质检' }
]

const heroTags = ['多智能体', 'GraphRAG', 'Socratic', '可视化']

const stats = ref(null)
const health = ref({ status: 'healthy' })

const healthStatus = computed(() => ({
  text: health.value?.status === 'healthy' ? '运行正常' : '需要检查'
}))

const totalRequests = computed(() => formatNumber(safeGet(stats.value, 'total_requests', 0)))
const failedRequests = computed(() => safeGet(stats.value, 'failed_requests', 0))
const successRate = computed(() => {
  const total = safeGet(stats.value, 'total_requests', 0) || 1
  const success = safeGet(stats.value, 'successful_requests', 0)
  return Math.round((success / total) * 100)
})
const avgLatency = computed(() => Math.round(safeGet(stats.value, 'average_response_time', 0)))
const activeAgents = computed(() => Object.keys(safeGet(health.value, 'agents_status', {})).length || 10)
const uptimeText = computed(() => {
  const seconds = safeGet(health.value, 'uptime_seconds', 0)
  if (!seconds) return '刚刚启动'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  return hours ? `${hours}h ${mins}m` : `${mins}m`
})

function startLearning() { router.push('/chat') }
function exploreKnowledge() { router.push('/graph') }

onMounted(async () => {
  try {
    const healthData = await healthCheck()
    health.value = { status: healthData.status === 'ok' ? 'healthy' : 'degraded' }
    stats.value = { total_requests: 0, successful_requests: 0, average_response_time: 0 }
  } catch (e) {
    console.error(e)
    health.value = { status: 'unknown' }
  }
})
</script>

<style scoped>
/* ========== 基础样式 - 黑白极简 ========== */
.home {
  max-width: 1280px;
  margin: 0 auto;
  padding: 48px 32px 100px;
}

/* ========== Hero Section ========== */
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  align-items: center;
  min-height: 65vh;
  margin-bottom: 120px;
}

.hero-content {
  max-width: 520px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #e5e5e5;
  border-radius: 100px;
  font-size: 13px;
  font-weight: 500;
  color: #666666;
  margin-bottom: 28px;
}

.pulse {
  width: 8px;
  height: 8px;
  background: #000000;
  border-radius: 50%;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -2px;
  margin: 0 0 24px;
  color: #000000;
}

.gradient-text {
  background: linear-gradient(135deg, #000000 0%, #333333 50%, #666666 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 18px;
  line-height: 1.7;
  color: #666666;
  margin: 0 0 36px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  margin-bottom: 32px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 32px;
  background: #000000;
  color: white;
  border: none;
  border-radius: 100px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #1a1a1a;
  transform: translateY(-2px);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 28px;
  background: #ffffff;
  color: #000000;
  border: 2px solid #e5e5e5;
  border-radius: 100px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  border-color: #000000;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tech-tag {
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #e5e5e5;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 500;
  color: #666666;
  transition: all 0.2s ease;
}

.tech-tag:hover {
  background: #000000;
  border-color: #000000;
  color: #ffffff;
}

/* ========== Hero Visual ========== */
.hero-visual {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
}

.metric-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 24px;
  transition: all 0.25s ease;
}

.metric-card:hover {
  border-color: #000000;
}

.metric-card.highlight {
  grid-row: span 2;
  background: #000000;
  border: none;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
}

.metric-card.highlight .metric-icon {
  width: 52px;
  height: 52px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.metric-card.highlight .metric-value {
  font-size: 48px;
  color: white;
}

.metric-card.highlight .metric-label {
  color: rgba(255, 255, 255, 0.7);
}

.metric-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-value {
  font-size: 32px;
  font-weight: 800;
  color: #000000;
  letter-spacing: -1px;
}

.metric-value small {
  font-size: 14px;
  font-weight: 500;
  opacity: 0.6;
  margin-left: 2px;
}

.metric-label {
  font-size: 13px;
  color: #888888;
}

/* ========== Workflow Preview ========== */
.workflow-preview {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 20px;
  padding: 28px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.preview-title {
  font-size: 14px;
  font-weight: 700;
  color: #000000;
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: #f5f5f5;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  color: #666666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: #000000;
  border-radius: 50%;
}

.workflow-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: 16px;
  padding: 14px 0;
  opacity: 0.5;
  transition: all 0.25s ease;
}

.timeline-item.active {
  opacity: 1;
}

.timeline-item:hover {
  opacity: 1;
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.marker-dot {
  width: 10px;
  height: 10px;
  background: #e5e5e5;
  border-radius: 50%;
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.timeline-item.active .marker-dot {
  background: #000000;
}

.marker-line {
  width: 2px;
  flex: 1;
  min-height: 32px;
  background: #e5e5e5;
}

.timeline-content h5 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #000000;
}

.timeline-content p {
  margin: 0;
  font-size: 13px;
  color: #888888;
}

/* ========== Features Section ========== */
.features-section {
  margin-bottom: 120px;
}

.section-header {
  text-align: center;
  margin-bottom: 56px;
}

.section-tag {
  display: inline-block;
  padding: 8px 18px;
  background: #f5f5f5;
  border: 1px solid #e5e5e5;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  color: #666666;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 42px;
  font-weight: 800;
  color: #000000;
  margin: 0;
  letter-spacing: -1px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.feature-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 20px;
  padding: 32px;
  transition: all 0.3s ease;
}

.feature-card:hover {
  border-color: #000000;
  transform: translateY(-4px);
}

.feature-icon {
  width: 56px;
  height: 56px;
  background: #f5f5f5;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #333333;
  margin-bottom: 24px;
  transition: all 0.25s ease;
}

.feature-card:hover .feature-icon {
  background: #000000;
  color: white;
}

.feature-tag {
  display: inline-block;
  padding: 5px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #888888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 20px;
  font-weight: 700;
  color: #000000;
  margin: 0 0 12px;
}

.feature-card p {
  font-size: 14px;
  line-height: 1.7;
  color: #666666;
  margin: 0;
}

/* ========== Workflow Section ========== */
.workflow-section {
  margin-bottom: 80px;
}

.workflow-steps {
  display: flex;
  align-items: stretch;
  gap: 16px;
}

.workflow-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 36px 28px;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 20px;
  position: relative;
  transition: all 0.25s ease;
}

.workflow-step:hover {
  border-color: #000000;
  transform: translateY(-4px);
}

.step-number {
  font-size: 36px;
  font-weight: 800;
  color: #e5e5e5;
  margin-bottom: 16px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  transition: all 0.25s ease;
}

.workflow-step:hover .step-number {
  color: #000000;
}

.step-content h4 {
  font-size: 17px;
  font-weight: 700;
  color: #000000;
  margin: 0 0 8px;
}

.step-content p {
  font-size: 14px;
  color: #888888;
  margin: 0;
  line-height: 1.6;
}

.step-connector {
  position: absolute;
  right: -24px;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.step-connector svg {
  width: 20px;
  height: 20px;
  color: #cccccc;
}

/* ========== Responsive ========== */
@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 56px;
    min-height: auto;
  }
  
  .hero-content {
    max-width: 100%;
    text-align: center;
  }
  
  .hero-title {
    font-size: 48px;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .tech-stack {
    justify-content: center;
  }
  
  .hero-visual {
    order: -1;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .metric-card.highlight {
    grid-row: auto;
  }
}

@media (max-width: 768px) {
  .home {
    padding: 24px 16px 60px;
  }
  
  .hero-title {
    font-size: 36px;
  }
  
  .hero-desc {
    font-size: 16px;
  }
  
  .hero-actions {
    flex-direction: column;
  }
  
  .btn-primary, .btn-secondary {
    width: 100%;
    justify-content: center;
  }
  
  .section-header h2 {
    font-size: 32px;
  }
  
  .workflow-steps {
    flex-direction: column;
  }
  
  .step-connector {
    display: none;
  }
  
  .workflow-step {
    flex-direction: row;
    text-align: left;
    gap: 20px;
    padding: 24px;
  }
  
  .step-number {
    margin-bottom: 0;
    font-size: 28px;
  }
}
</style>
