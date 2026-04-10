<template>
  <div class="graph-page">
    <el-card>
      <template #header>
        <div class="hdr">
          <span>知识图谱与对话图谱</span>
          <el-radio-group v-model="view" size="small">
            <el-radio-button label="knowledge">知识库图谱</el-radio-button>
            <el-radio-button label="dialogue">本会话对话图谱</el-radio-button>
            <el-radio-button label="user">用户长期图谱</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div v-if="view === 'knowledge'" class="toolbar">
        <el-input v-model="kbId" placeholder="知识库 ID，默认 sanguo" style="max-width: 220px" />
        <el-button type="primary" @click="loadKnowledge" :loading="loading">加载</el-button>
        <el-button @click="runIndex" :loading="indexing">用 metadata 样本文本建索引</el-button>
        <span class="hint">使用 data/metadata/sanguo_sample.txt 写入知识库并构建 GraphRAG（耗时较长）</span>
      </div>
      <div ref="chartRef" class="chart" />
      <p v-if="error" class="err">{{ error }}</p>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { getKnowledgeGraph, getDialogueGraph, getUserLongGraph, indexKnowledge } from '@/api/edupilot'

const chartRef = ref(null)
const view = ref('knowledge')
const kbId = ref('sanguo')
const loading = ref(false)
const indexing = ref(false)
const error = ref('')
let chart

const userStore = useUserStore()
const chatStore = useChatStore()

function toGraphOption(payload) {
  const nodes = (payload.nodes || []).map((n, i) => ({
    id: n.id || n.name,
    name: n.name || n.id,
    symbolSize: 18,
    category: i % 3
  }))
  const links = (payload.links || []).map((l) => ({
    source: l.source,
    target: l.target,
    label: { show: false }
  }))
  return {
    tooltip: {},
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        force: { repulsion: 120, edgeLength: 80 },
        label: { show: true, position: 'right' },
        data: nodes,
        links,
        lineStyle: { color: '#aaa', curveness: 0.1 }
      }
    ]
  }
}

async function render(payload) {
  error.value = ''
  await nextTick()
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const opt = toGraphOption(payload)
  if (!(payload.nodes || []).length) {
    error.value = payload.error || '暂无节点，请先建立索引或对话'
  }
  chart.setOption(opt, true)
}

async function loadKnowledge() {
  loading.value = true
  try {
    const data = await getKnowledgeGraph(kbId.value || 'sanguo')
    await render(data)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function runIndex() {
  indexing.value = true
  try {
    await indexKnowledge(kbId.value || 'sanguo', null, true)
    await loadKnowledge()
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    indexing.value = false
  }
}

async function loadDialogue() {
  const sid = userStore.sessionId
  if (!sid) {
    error.value = '请先在对话页发起会话'
    await render({ nodes: [], links: [] })
    return
  }
  loading.value = true
  try {
    const data = await getDialogueGraph(sid)
    await render({ nodes: data.nodes || [], links: data.links || [], error: data.error })
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function loadUser() {
  loading.value = true
  try {
    const data = await getUserLongGraph(userStore.userId)
    await render({ nodes: data.nodes || [], links: data.links || [] })
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

watch(view, (v) => {
  if (v === 'knowledge') loadKnowledge()
  if (v === 'dialogue') loadDialogue()
  if (v === 'user') loadUser()
})

onMounted(() => {
  loadKnowledge()
})
</script>

<style scoped>
.graph-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}
.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.hint {
  font-size: 12px;
  color: #888;
}
.chart {
  width: 100%;
  height: 560px;
}
.err {
  color: #c00;
  margin-top: 8px;
}
</style>
