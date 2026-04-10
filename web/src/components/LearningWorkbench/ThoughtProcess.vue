<template>
  <div class="thought-process">
    <div class="process-header">
      <el-icon class="pulse-icon"><Cpu /></el-icon>
      <span>AI 思考链路</span>
      <span v-if="process.isActive" class="status-tag processing">Processing</span>
      <span v-else class="status-tag completed">Completed</span>
    </div>
    
    <div class="process-timeline">
      <div
        v-for="(step, index) in process.steps"
        :key="index"
        :class="['timeline-item', step.status]"
      >
        <div class="timeline-left">
          <div class="timeline-dot">
            <el-icon v-if="step.status === 'completed'"><Check /></el-icon>
            <el-icon v-else-if="step.status === 'active'" class="is-loading"><Loading /></el-icon>
            <div v-else class="dot-placeholder"></div>
          </div>
          <div v-if="index !== process.steps.length - 1" class="timeline-line"></div>
        </div>
        
        <div class="timeline-content">
          <div class="step-header">
            <span class="step-title">{{ step.title }}</span>
            <span v-if="step.message" class="step-time">{{ step.message }}</span>
          </div>
          <div v-if="step.details" class="step-details">
            <!-- 预留：未来可以展示具体的 JSON 结果或参数 -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Cpu, Check, Loading } from '@element-plus/icons-vue'

defineProps({
  process: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.thought-process {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.process-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 15px;
}

.pulse-icon {
  color: var(--primary-color);
  font-size: 18px;
}

.status-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
  text-transform: uppercase;
}

.status-tag.processing {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.status-tag.completed {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.process-timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
  padding-bottom: 20px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
}

.timeline-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.timeline-item.active .timeline-dot {
  border-color: var(--primary-color);
  color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.timeline-item.completed .timeline-dot {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.timeline-line {
  flex: 1;
  width: 2px;
  background: var(--border-color);
  margin-top: 4px;
  margin-bottom: 4px;
}

.timeline-content {
  flex: 1;
  padding-top: 2px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.step-title {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.step-time {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: monospace;
}
</style>

