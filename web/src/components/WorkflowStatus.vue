<template>
  <el-card v-if="workflowState" class="workflow-status">
    <template #header>
      <div class="card-header">
        <el-icon><Setting /></el-icon>
        <span>工作流状态</span>
        <el-tag 
          :type="getStatusTagType()" 
          size="small" 
          class="status-tag"
        >
          {{ getStatusText() }}
        </el-tag>
      </div>
    </template>
    
    <el-descriptions :column="2" size="small" border>
      <el-descriptions-item label="完成状态">
        <el-tag :type="workflowState.complete ? 'success' : 'warning'">
          {{ workflowState.complete ? '已完成' : '进行中' }}
        </el-tag>
      </el-descriptions-item>
      
      <el-descriptions-item label="等待用户">
        <el-tag :type="workflowState.waitingForUser ? 'info' : 'success'">
          <el-icon v-if="workflowState.waitingForUser"><Clock /></el-icon>
          {{ workflowState.waitingForUser ? '等待中' : '正常' }}
        </el-tag>
      </el-descriptions-item>
      
      <el-descriptions-item label="对话阶段">
        <el-tag :type="getStageTagType()" size="small">
          {{ translateStage(workflowState.conversationStage) }}
        </el-tag>
      </el-descriptions-item>
      
      <el-descriptions-item label="理解水平">
        <el-tag :type="getUnderstandingLevelTag()" size="small">
          {{ translateUnderstandingLevel(workflowState.understandingLevel) }}
        </el-tag>
      </el-descriptions-item>
      
      <el-descriptions-item label="对话轮次">
        <el-progress 
          :percentage="getConversationProgress()" 
          :format="() => `${workflowState.conversationRound} 轮`"
          :stroke-width="6"
        />
      </el-descriptions-item>
      
      <el-descriptions-item label="学习进度">
        <el-progress 
          :percentage="getLearningProgress()" 
          :format="() => getLearningProgressText()"
          :stroke-width="6"
          :color="getProgressColor()"
        />
      </el-descriptions-item>
    </el-descriptions>
    
    <!-- 状态指示器 -->
    <div class="status-indicators">
      <div class="indicator-item">
        <el-icon :class="['indicator-icon', workflowState.complete ? 'active' : '']">
          <CircleCheck />
        </el-icon>
        <span>工作流完成</span>
      </div>
      
      <div class="indicator-item">
        <el-icon :class="['indicator-icon', workflowState.waitingForUser ? 'active' : '']">
          <User />
        </el-icon>
        <span>等待用户</span>
      </div>
      
      <div class="indicator-item">
        <el-icon :class="['indicator-icon', isSocraticMode ? 'active' : '']">
          <QuestionFilled />
        </el-icon>
        <span>苏格拉底模式</span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { 
  Setting, 
  Clock, 
  CircleCheck, 
  User, 
  QuestionFilled 
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  workflowState: {
    type: Object,
    default: null
  },
  socraticDialogue: {
    type: Object,
    default: null
  }
})

// Computed
const isSocraticMode = computed(() => {
  return props.socraticDialogue?.is_socratic_mode || false
})

// 翻译对话阶段
function translateStage(stage) {
  const stageMap = {
    'initialization': '初始化',
    'query_analysis': '查询分析',
    'planning': '规划阶段',
    'execution': '执行阶段',
    'socratic_guidance': '苏格拉底引导',
    'conclusion': '总结阶段',
    'waiting_for_user': '等待用户',
    'completed': '已完成'
  }
  return stageMap[stage] || stage || '未知'
}

// 翻译理解水平
function translateUnderstandingLevel(level) {
  const levelMap = {
    'beginner': '初学者',
    'intermediate': '中级',
    'advanced': '高级',
    'low': '较低',
    'medium': '中等',
    'high': '较高',
    'unknown': '未知'
  }
  return levelMap[level] || level || '未知'
}

// 获取状态标签类型
function getStatusTagType() {
  if (props.workflowState.complete) return 'success'
  if (props.workflowState.waitingForUser) return 'info'
  return 'warning'
}

// 获取状态文本
function getStatusText() {
  if (props.workflowState.complete) return '已完成'
  if (props.workflowState.waitingForUser) return '等待用户'
  return '进行中'
}

// 获取阶段标签类型
function getStageTagType() {
  const stage = props.workflowState.conversationStage
  const tagMap = {
    'initialization': 'info',
    'query_analysis': 'primary',
    'planning': 'warning',
    'execution': 'success',
    'socratic_guidance': 'primary',
    'conclusion': 'success',
    'waiting_for_user': 'info',
    'completed': 'success'
  }
  return tagMap[stage] || 'info'
}

// 获取理解水平标签类型
function getUnderstandingLevelTag() {
  const level = props.workflowState.understandingLevel
  const tagMap = {
    'beginner': 'warning',
    'intermediate': 'primary',
    'advanced': 'success',
    'low': 'warning',
    'medium': 'primary',
    'high': 'success',
    'unknown': 'info'
  }
  return tagMap[level] || 'info'
}

// 获取对话进度
function getConversationProgress() {
  const round = props.workflowState.conversationRound || 0
  return Math.min((round / 5) * 100, 100) // 假设5轮为满分
}

// 获取学习进度
function getLearningProgress() {
  if (props.workflowState.complete) return 100
  
  const stage = props.workflowState.conversationStage
  const progressMap = {
    'initialization': 10,
    'query_analysis': 25,
    'planning': 40,
    'execution': 70,
    'socratic_guidance': 85,
    'conclusion': 95,
    'completed': 100
  }
  
  return progressMap[stage] || 0
}

// 获取学习进度文本
function getLearningProgressText() {
  const progress = getLearningProgress()
  if (progress >= 100) return '已完成'
  if (progress >= 70) return '接近完成'
  if (progress >= 40) return '进行中'
  return '刚开始'
}

// 获取进度条颜色
function getProgressColor() {
  const progress = getLearningProgress()
  if (progress >= 100) return '#67c23a'
  if (progress >= 70) return '#409eff'
  if (progress >= 40) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.workflow-status {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  margin-left: auto;
}

.status-indicators {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: space-around;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.indicator-icon {
  font-size: 20px;
  color: #c0c4cc;
  transition: color 0.3s;
}

.indicator-icon.active {
  color: #67c23a;
}

.indicator-item span {
  font-size: 11px;
}
</style>
