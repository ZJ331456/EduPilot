<template>
  <div class="concept-note">
    <div class="note-toolbar">
      <el-button size="small" @click="handlePin">
        <el-icon><Star /></el-icon>
        固定到画布
      </el-button>
      <el-button size="small" @click="handleCopy">
        <el-icon><DocumentCopy /></el-icon>
        复制
      </el-button>
    </div>
    
    <div class="note-content" v-html="formattedContent"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Star, DocumentCopy } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'

const props = defineProps({
  content: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['pin'])

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true
})

const formattedContent = computed(() => {
  return md.render(props.content)
})

const handlePin = () => {
  emit('pin', props.content)
  ElMessage.success('已固定到画布')
}

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(props.content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.concept-note {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.note-toolbar {
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  gap: 8px;
}

.note-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  line-height: 1.8;
  color: var(--text-primary);
}

.note-content :deep(h1),
.note-content :deep(h2),
.note-content :deep(h3) {
  margin-top: 24px;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.note-content :deep(p) {
  margin-bottom: 12px;
}

.note-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.note-content :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}
</style>

