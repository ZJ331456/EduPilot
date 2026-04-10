<template>
  <div class="socratic-card">
    <div class="card-header">
      <div class="header-left">
        <el-icon><ChatLineRound /></el-icon>
        <span>苏格拉底式引导</span>
        <el-tag size="small" :type="getQuestionTypeTag(dialogue.question_type)">
          {{ getQuestionTypeLabel(dialogue.question_type) }}
        </el-tag>
        <!-- 新增：引导策略标签 -->
        <el-tag v-if="dialogue.guidance_strategy" size="small" effect="plain" type="info">
          {{ dialogue.guidance_strategy }}
        </el-tag>
      </div>
      <div class="understanding-level">
        <span>理解水平：</span>
        <el-progress
          :percentage="getUnderstandingPercentage(dialogue.understanding_level)"
          :format="() => getUnderstandingLabel(dialogue.understanding_level)"
          :color="getUnderstandingColor(dialogue.understanding_level)"
        />
      </div>
    </div>

    <div class="card-question">
      <div class="question-text">{{ dialogue.current_question }}</div>
      <div v-if="dialogue.question_purpose" class="question-purpose">
        💡 {{ dialogue.question_purpose }}
      </div>
    </div>

    <div class="card-actions">
      <div class="quick-replies">
        <el-button
          v-for="reply in quickReplies"
          :key="reply"
          size="small"
          @click="handleQuickReply(reply)"
          :type="reply === '我不知道' ? 'warning' : 'default'"
        >
          {{ reply }}
        </el-button>
      </div>
    </div>

    <div v-if="dialogue.next_steps && dialogue.next_steps.length > 0" class="card-next-steps">
      <div class="next-steps-title">下一步建议：</div>
      <ul class="next-steps-list">
        <li v-for="(step, index) in dialogue.next_steps" :key="index">
          {{ step }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChatLineRound } from '@element-plus/icons-vue'

const props = defineProps({
  dialogue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['quick-reply'])

const quickReplies = computed(() => {
  const defaults = ['我不知道', '举个例子', '换个角度', '继续深入']
  return props.dialogue.quick_replies || defaults
})

const getQuestionTypeLabel = (type) => {
  const labels = {
    'clarifying': '澄清',
    'assumption': '假设', // 更新：hypothesis -> assumption
    'implication': '含义',
    'evidence': '证据',
    'perspective': '视角',
    'meta': '元认知', // 新增
    'application': '应用', // 新增
    'synthesis': '综合'
  }
  return labels[type] || type
}

const getQuestionTypeTag = (type) => {
  const tags = {
    'clarifying': 'info',
    'assumption': 'warning', // 更新
    'implication': 'success',
    'evidence': 'danger',
    'perspective': '',
    'meta': 'warning', // 新增
    'application': 'success', // 新增
    'synthesis': 'warning'
  }
  return tags[type] || ''
}

const getUnderstandingPercentage = (level) => {
  const levels = {
    'no_understanding': 0, // 对应后端 UnderstandingLevel 枚举
    'basic_understanding': 25,
    'partial_understanding': 50,
    'good_understanding': 75,
    'full_understanding': 100,
    // 兼容旧值
    'unknown': 0,
    'beginner': 25,
    'intermediate': 50,
    'advanced': 80
  }
  return levels[level] || 0
}

const getUnderstandingLabel = (level) => {
  const labels = {
    'no_understanding': '未理解',
    'basic_understanding': '基础',
    'partial_understanding': '部分',
    'good_understanding': '良好',
    'full_understanding': '透彻',
    // 兼容旧值
    'unknown': '未知',
    'beginner': '初级',
    'intermediate': '中级',
    'advanced': '高级'
  }
  return labels[level] || level
}

const getUnderstandingColor = (level) => {
  // 简化映射逻辑
  const percentage = getUnderstandingPercentage(level)
  if (percentage < 30) return '#909399'
  if (percentage < 60) return '#e6a23c'
  if (percentage < 80) return '#409eff'
  return '#67c23a'
}

const handleQuickReply = (reply) => {
  emit('quick-reply', reply)
}
</script>

<style scoped>
.socratic-card {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  padding: 20px;
  margin: 16px 0;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--text-primary);
}

.understanding-level {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 200px;
}

.card-question {
  margin-bottom: 20px;
}

.question-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: 8px;
}

.question-purpose {
  font-size: 13px;
  color: var(--text-secondary);
  font-style: italic;
}

.card-actions {
  margin-bottom: 16px;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.card-next-steps {
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.next-steps-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.next-steps-list {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.8;
}
</style>

