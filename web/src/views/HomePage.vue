<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
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
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" stroke-width="2"/>
            </svg>
            开始对话
          </button>
          <button class="btn-secondary" @click="exploreKnowledge">
            <svg viewBox="0 0 24 24" fill="none">
              <circle cx="5" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
              <circle cx="19" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
              <path d="M8 12H16" stroke="currentColor" stroke-width="2"/>
            </svg>
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
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2"/>
              </svg>
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
          :style="{ '--delay': index * 0.08 + 's' }"
        >
          <div class="feature-icon" v-html="feature.icon"></div>
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
          v-for="(step, index) in workflowSteps2"
          :key="index"
          class="workflow-step"
        >
          <div class="step-number">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="step-content">
            <h4>{{ step.title }}</h4>
            <p>{{ step.description }}</p>
          </div>
          <div class="step-connector" v-if="index < workflowSteps2.length - 1">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
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
import { healthCheck } from '../api/edupilot'
import { formatNumber, safeGet } from '../utils'

const router = useRouter()

const features = [
  {
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" stroke-width="2"/></svg>',
    title: '生成式对话',
    tag: 'Socratic',
    description: '用追问与澄清让学习者自己推导答案，而不是直接给结论。'
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none"><circle cx="5" cy="12" r="3" stroke="currentColor" stroke-width="2"/><circle cx="19" cy="12" r="3" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="5" r="3" stroke="currentColor" stroke-width="2"/><path d="M8.5 9.5L11 11.5M15.5 9.5L13 11.5M8.5 14.5L11 12.5M15.5 14.5L13 12.5" stroke="currentColor" stroke-width="2"/></svg>',
    title: '图谱检索',
    tag: 'GraphRAG',
    description: '基于知识图谱的关联搜索，确保回答有出处、有结构。'
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/></svg>',
    title: '个性画像',
    tag: 'Profile',
    description: '跟踪认知水平与偏好，实时调整学习难度与形式。'
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M4 19.5C4 18.837 4.26339 18.2011 4.73223 17.7322C5.20107 17.2634 5.83696 17 6.5 17H20" stroke="currentColor" stroke-width="2"/><path d="M6.5 2H20V22H6.5C5.83696 22 5.20107 21.7366 4.73223 21.2678C4.26339 20.7989 4 20.163 4 19.5V4.5C4 3.83696 4.26339 3.20107 4.73223 2.73223C5.20107 2.26339 5.83696 2 6.5 2Z" stroke="currentColor" stroke-width="2"/></svg>',
    title: '课程设计',
    tag: 'Curriculum',
    description: '把碎片问题组装为进阶路线，含练习与测验闭环。'
  },
  {
    icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M22 12H18L15 21L9 3L6 12H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    title: '性能观测',
    tag: 'Ops',
    description: 'API 级别监控、缓存与限流，确保低延迟稳定可用。'
  }
]

const workflowSteps = [
  { title: '意图理解', description: '快速分辨目标、上下文和需要的工具' },
  { title: '路径规划', description: '动态 fan-out/fan-in 安排知识检索与技能执行' },
  { title: '对话引导', description: 'Socratic 提问 + 记忆管理，锁定薄弱点' },
  { title: '产出与评审', description: 'Draft + Reviewer + Quiz 三段式输出与质检' }
]

const workflowSteps2 = [
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
const successRate = computed(() => {
  const total = safeGet(stats.value, 'total_requests', 0) || 1
  const success = safeGet(stats.value, 'successful_requests', 0)
  return Math.round((success / total) * 100)
})
const avgLatency = computed(() => Math.round(safeGet(stats.value, 'average_response_time', 0)))
const activeAgents = computed(() => Object.keys(safeGet(health.value, 'agents_status', {})).length || 10)

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
.home {
  max-width: 1280px;
  margin: 0 auto;
  padding: 48px 32px 80px;
}

/* ========== Hero Section ========== */
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
  min-height: 60vh;
  margin-bottom: 100px;
}

.hero-content {
  max-width: 480px;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -1.5px;
  margin: 0 0 20px;
  color: var(--text-primary);
}

.gradient-text {
  color: var(--text-primary);
}

.hero-desc {
  font-size: 16px;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0 0 32px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: var(--text-primary);
  color: var(--bg-base);
  border: none;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.15);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.btn-secondary svg {
  width: 18px;
  height: 18px;
}

.btn-secondary:hover {
  border-color: var(--border-hover);
  background: var(--bg-card);
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tech-tag {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

.tech-tag:hover {
  border-color: var(--border-hover);
  color: var(--text-secondary);
}

/* ========== Hero Visual ========== */
.hero-visual {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 10px;
}

.metric-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 18px;
  transition: all var(--transition-normal);
}

.metric-card:hover {
  border-color: var(--border-hover);
}

.metric-card.highlight {
  grid-row: span 2;
  background: var(--bg-card);
  border: 1px solid var(--border-hover);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.metric-card.highlight .metric-icon {
  width: 44px;
  height: 44px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
}

.metric-card.highlight .metric-icon svg {
  width: 22px;
  height: 22px;
}

.metric-card.highlight .metric-value {
  font-size: 40px;
  color: var(--text-primary);
}

.metric-card.highlight .metric-label {
  color: var(--text-secondary);
}

.metric-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.metric-value small {
  font-size: 13px;
  font-weight: 500;
  opacity: 0.7;
  margin-left: 2px;
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
}

/* ========== Workflow Preview ========== */
.workflow-preview {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.live-dot {
  width: 5px;
  height: 5px;
  background: var(--text-secondary);
  border-radius: 50%;
}

.workflow-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  opacity: 0.5;
  transition: opacity var(--transition-normal);
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
  width: 7px;
  height: 7px;
  background: var(--border-hover);
  border-radius: 50%;
  flex-shrink: 0;
}

.timeline-item.active .marker-dot {
  background: var(--text-primary);
}

.marker-line {
  width: 1px;
  flex: 1;
  min-height: 20px;
  background: var(--border-color);
}

.timeline-content h5 {
  margin: 0 0 2px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.timeline-content p {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

/* ========== Features Section ========== */
.features-section {
  margin-bottom: 100px;
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-tag {
  display: inline-block;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 34px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.5px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.feature-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 24px;
  transition: all var(--transition-normal);
  animation: fadeInUp 0.5s ease-out both;
  animation-delay: var(--delay);
}

.feature-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-3px);
}

.feature-icon {
  width: 44px;
  height: 44px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: var(--text-secondary);
  transition: all var(--transition-normal);
}

.feature-icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.feature-card:hover .feature-icon {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.feature-tag {
  display: inline-block;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.feature-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.feature-card p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

/* ========== Workflow Section ========== */
.workflow-section {
  margin-bottom: 64px;
}

.workflow-steps {
  display: flex;
  align-items: stretch;
  gap: 12px;
}

.workflow-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 28px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  position: relative;
  transition: all var(--transition-normal);
}

.workflow-step:hover {
  border-color: var(--border-hover);
}

.step-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-ghost);
  margin-bottom: 12px;
  font-family: var(--font-mono);
  transition: color var(--transition-normal);
}

.workflow-step:hover .step-number {
  color: var(--text-secondary);
}

.step-content h4 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.step-content p {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.step-connector {
  position: absolute;
  right: -18px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 50%;
}

.step-connector svg {
  width: 12px;
  height: 12px;
  color: var(--text-muted);
}

/* ========== Responsive ========== */
@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 48px;
    min-height: auto;
  }

  .hero-content {
    max-width: 100%;
    text-align: center;
  }

  .hero-title {
    font-size: 40px;
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
    padding: 32px 16px 60px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-desc {
    font-size: 15px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .btn-primary, .btn-secondary {
    width: 100%;
    justify-content: center;
  }

  .section-header h2 {
    font-size: 28px;
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
    gap: 16px;
    padding: 20px;
  }

  .step-number {
    margin-bottom: 0;
    font-size: 22px;
  }
}

/* ========== Animations ========== */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
