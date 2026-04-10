<template>
  <div class="context-canvas">
    <div class="canvas-header">
      <h3>知识画布</h3>
      <el-button-group>
        <el-button size="small" @click="viewMode = 'graph'">
          <el-icon><Share /></el-icon>
          图谱
        </el-button>
        <el-button size="small" @click="viewMode = 'note'">
          <el-icon><Document /></el-icon>
          笔记
        </el-button>
        <el-button size="small" @click="viewMode = 'summary'">
          <el-icon><List /></el-icon>
          总结
        </el-button>
      </el-button-group>
    </div>

    <div class="canvas-content">
      <!-- 知识图谱视图 -->
      <KnowledgeGraph
        v-if="viewMode === 'graph' && knowledgeGraph"
        :graph-data="knowledgeGraph"
        @node-click="handleNodeClick"
      />

      <!-- 概念笔记视图 -->
      <ConceptNote
        v-else-if="viewMode === 'note' && conceptNote"
        :content="conceptNote"
        @pin="handlePin"
      />

      <!-- 学习总结视图 -->
      <SummaryBoard
        v-else-if="viewMode === 'summary'"
        :workflow-state="workflowState"
      />

      <!-- 空状态 -->
      <div v-else class="empty-canvas">
        <el-empty description="暂无内容">
          <template #image>
            <el-icon :size="80" color="#667eea"><Document /></el-icon>
          </template>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Share, Document, List } from '@element-plus/icons-vue'
import KnowledgeGraph from './KnowledgeGraph.vue'
import ConceptNote from './ConceptNote.vue'
import SummaryBoard from './SummaryBoard.vue'

const props = defineProps({
  intent: {
    type: String,
    default: null
  },
  knowledgeGraph: {
    type: Array,
    default: null
  },
  conceptNote: {
    type: String,
    default: null
  },
  workflowState: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['pin-content'])

const viewMode = ref('graph')

// 根据意图自动切换视图
const autoViewMode = computed(() => {
  if (!props.intent) return 'graph'
  
  const intentMap = {
    'concept_explanation': 'graph',
    'guided_learning': 'note',
    'problem_solving': 'note',
    'direct_answer': 'summary'
  }
  
  return intentMap[props.intent] || 'graph'
})

// 监听意图变化，自动切换视图
watch(() => props.intent, (newIntent) => {
  if (newIntent) {
    viewMode.value = autoViewMode.value
  }
}, { immediate: true })

const handleNodeClick = (node) => {
  console.log('点击节点:', node)
  // TODO: 处理节点点击，可能触发新的查询
}

const handlePin = (content) => {
  emit('pin-content', content)
}
</script>

<style scoped>
.context-canvas {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}

.canvas-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.canvas-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.canvas-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-canvas {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

