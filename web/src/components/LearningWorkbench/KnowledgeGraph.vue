<template>
  <div class="knowledge-graph">
    <div ref="graphContainer" class="graph-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  graphData: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['node-click'])

const graphContainer = ref(null)
let chartInstance = null

const initGraph = () => {
  if (!graphContainer.value) return
  
  chartInstance = echarts.init(graphContainer.value)
  
  // 构建图谱数据
  const nodes = []
  const links = []
  
  // 从graphData构建节点和边
  props.graphData.forEach((item, index) => {
    nodes.push({
      id: `node_${index}`,
      name: item,
      symbolSize: 30,
      category: 0
    })
  })
  
  // 示例：添加一些连接
  if (nodes.length > 1) {
    for (let i = 0; i < nodes.length - 1; i++) {
      links.push({
        source: nodes[i].id,
        target: nodes[i + 1].id
      })
    }
  }
  
  const option = {
    tooltip: {},
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      roam: true,
      label: {
        show: true,
        position: 'right',
        formatter: '{b}'
      },
      lineStyle: {
        color: 'source',
        curveness: 0.3
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      force: {
        repulsion: 100,
        gravity: 0.1,
        edgeLength: 100
      }
    }]
  }
  
  chartInstance.setOption(option)
  
  // 监听节点点击
  chartInstance.on('click', (params) => {
    if (params.dataType === 'node') {
      emit('node-click', params.data)
    }
  })
}

onMounted(() => {
  initGraph()
})

watch(() => props.graphData, () => {
  if (chartInstance) {
    initGraph()
  }
}, { deep: true })
</script>

<style scoped>
.knowledge-graph {
  width: 100%;
  height: 100%;
}

.graph-container {
  width: 100%;
  height: 600px;
  min-height: 400px;
}
</style>

