<template>
  <div v-if="dialogue && dialogue.is_socratic_mode" class="socratic-dialogue">
    <el-alert
      title="苏格拉底式引导"
      type="info"
      :closable="false"
      show-icon
      class="socratic-alert"
    >
      <template #default>
        <div class="socratic-content">
          <!-- 当前问题 -->
          <div v-if="dialogue.current_question" class="current-question">
            <h4>
              <el-icon><QuestionFilled /></el-icon>
              当前问题
            </h4>
            <p class="question-text">{{ dialogue.current_question }}</p>
          </div>
          
          <!-- 对话信息 -->
          <el-row :gutter="16" class="dialogue-info">
            <el-col :span="12">
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="问题类型">
                  <el-tag :type="getQuestionTypeTag(dialogue.question_type)" size="small">
                    {{ translateQuestionType(dialogue.question_type) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="理解水平">
                  <el-tag :type="getUnderstandingLevelTag(dialogue.understanding_level)" size="small">
                    {{ translateUnderstandingLevel(dialogue.understanding_level) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="引导策略">
                  {{ dialogue.guidance_strategy || '自适应引导' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
            
            <el-col :span="12">
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="已提问次数">
                  {{ dialogue.questions_asked }}/{{ dialogue.max_questions }}
                </el-descriptions-item>
                <el-descriptions-item label="问题目的">
                  {{ dialogue.question_purpose || '引导思考' }}
                </el-descriptions-item>
                <el-descriptions-item label="对话状态">
                  <el-tag type="success" size="small">进行中</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
          </el-row>
          
          <!-- 下一步建议 -->
          <div v-if="dialogue.next_steps && dialogue.next_steps.length > 0" class="next-steps">
            <h4>
              <el-icon><Guide /></el-icon>
              下一步建议
            </h4>
            <el-timeline>
              <el-timeline-item 
                v-for="(step, index) in dialogue.next_steps" 
                :key="index"
                size="small"
              >
                {{ step }}
              </el-timeline-item>
            </el-timeline>
          </div>
          
          <!-- 对话历史 -->
          <div v-if="dialogue.dialogue_history && dialogue.dialogue_history.length > 0" class="dialogue-history">
            <h4>
              <el-icon><ChatLineRound /></el-icon>
              对话历史
            </h4>
            <el-collapse>
              <el-collapse-item title="查看对话历史" name="history">
                <div class="history-messages">
                  <div 
                    v-for="(msg, index) in dialogue.dialogue_history" 
                    :key="index"
                    :class="['history-message', msg.role]"
                  >
                    <div class="message-role">
                      {{ msg.role === 'user' ? '你' : 'EduPilot' }}
                    </div>
                    <div class="message-content">{{ msg.content }}</div>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { QuestionFilled, Guide, ChatLineRound } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  dialogue: {
    type: Object,
    default: null
  }
})

// 翻译问题类型
function translateQuestionType(type) {
  const typeMap = {
    'clarification': '澄清类',
    'assumption': '假设类',
    'evidence': '证据类',
    'perspective': '视角类',
    'implication': '含义类',
    'meta': '元认知类',
    'synthesis': '综合类',
    'application': '应用类',
    'clarifying': '澄清类'
  }
  return typeMap[type] || type
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
  return levelMap[level] || level
}

// 获取问题类型标签样式
function getQuestionTypeTag(type) {
  const tagMap = {
    'clarification': 'primary',
    'assumption': 'warning',
    'evidence': 'success',
    'perspective': 'info',
    'implication': 'danger',
    'meta': 'primary',
    'synthesis': 'success',
    'application': 'warning',
    'clarifying': 'primary'
  }
  return tagMap[type] || 'info'
}

// 获取理解水平标签样式
function getUnderstandingLevelTag(level) {
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
</script>

<style scoped>
.socratic-dialogue {
  margin: 16px 0;
}

.socratic-alert {
  border-radius: 8px;
}

.socratic-content {
  padding: 8px 0;
}

.current-question {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.current-question h4 {
  margin: 0 0 8px 0;
  color: #409eff;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.question-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
}

.dialogue-info {
  margin: 16px 0;
}

.next-steps {
  margin: 16px 0;
}

.next-steps h4 {
  margin: 0 0 12px 0;
  color: #67c23a;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dialogue-history {
  margin: 16px 0;
}

.dialogue-history h4 {
  margin: 0 0 12px 0;
  color: #e6a23c;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.history-messages {
  max-height: 200px;
  overflow-y: auto;
}

.history-message {
  margin-bottom: 8px;
  padding: 8px;
  border-radius: 4px;
}

.history-message.user {
  background: rgba(64, 158, 255, 0.1);
  border-left: 3px solid #409eff;
}

.history-message.assistant {
  background: rgba(103, 194, 58, 0.1);
  border-left: 3px solid #67c23a;
}

.message-role {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #606266;
}

.message-content {
  font-size: 13px;
  line-height: 1.4;
  color: #303133;
}
</style>
