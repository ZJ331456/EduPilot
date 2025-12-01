<template>
  <div class="summary-board">
    <div class="summary-section">
      <h4>学习进度</h4>
      <el-progress
        :percentage="progressPercentage"
        :color="progressColor"
      />
      <div class="progress-details">
        <span>理解水平：{{ understandingLevel }}</span>
        <span>对话轮次：{{ conversationRound }}</span>
      </div>
    </div>

    <div class="summary-section">
      <h4>已覆盖概念</h4>
      <div class="concepts-list">
        <el-tag
          v-for="concept in keyConcepts"
          :key="concept"
          size="small"
          style="margin: 4px"
        >
          {{ concept }}
        </el-tag>
      </div>
    </div>

    <div class="summary-section">
      <h4>学习目标</h4>
      <el-steps direction="vertical" :active="achievedObjectives.length">
        <el-step
          v-for="objective in learningObjectives"
          :key="objective"
          :title="objective"
          :status="achievedObjectives.includes(objective) ? 'success' : 'wait'"
        />
      </el-steps>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  workflowState: {
    type: Object,
    default: null
  }
})

const understandingLevel = computed(() => {
  return props.workflowState?.understanding_level || '未知'
})

const conversationRound = computed(() => {
  return props.workflowState?.conversation_round || 0
})

const keyConcepts = computed(() => {
  return props.workflowState?.key_concepts_covered || []
})

const learningObjectives = computed(() => {
  return props.workflowState?.learning_objectives || []
})

const achievedObjectives = computed(() => {
  return props.workflowState?.achieved_objectives || []
})

const progressPercentage = computed(() => {
  if (learningObjectives.value.length === 0) return 0
  return Math.round((achievedObjectives.value.length / learningObjectives.value.length) * 100)
})

const progressColor = computed(() => {
  if (progressPercentage.value < 30) return '#e6a23c'
  if (progressPercentage.value < 70) return '#409eff'
  return '#67c23a'
})
</script>

<style scoped>
.summary-board {
  padding: 16px;
}

.summary-section {
  margin-bottom: 24px;
}

.summary-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.progress-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.concepts-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>

