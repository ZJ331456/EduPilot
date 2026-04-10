<template>
  <div
    class="virtual-scroll-container"
    ref="containerRef"
    @scroll="handleScroll"
    :style="{ height: containerHeight + 'px' }"
  >
    <!-- 占位空间 -->
    <div :style="{ height: totalHeight + 'px', position: 'relative' }">
      <!-- 可见项 -->
      <div
        v-for="item in visibleItems"
        :key="item.index"
        class="virtual-scroll-item"
        :style="{
          position: 'absolute',
          top: item.top + 'px',
          width: '100%'
        }"
      >
        <slot :item="item.data" :index="item.index"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    required: true
  },
  itemHeight: {
    type: Number,
    default: 80
  },
  containerHeight: {
    type: Number,
    default: 600
  },
  buffer: {
    type: Number,
    default: 5 // 缓冲区项数
  }
})

const containerRef = ref(null)
const scrollTop = ref(0)

// 总高度
const totalHeight = computed(() => props.items.length * props.itemHeight)

// 可见范围
const visibleRange = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight)
  const end = Math.ceil((scrollTop.value + props.containerHeight) / props.itemHeight)
  
  return {
    start: Math.max(0, start - props.buffer),
    end: Math.min(props.items.length, end + props.buffer)
  }
})

// 可见项
const visibleItems = computed(() => {
  const { start, end } = visibleRange.value
  const items = []
  
  for (let i = start; i < end; i++) {
    items.push({
      index: i,
      data: props.items[i],
      top: i * props.itemHeight
    })
  }
  
  return items
})

// 处理滚动
const handleScroll = () => {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop
  }
}

// 滚动到指定位置
const scrollToIndex = (index) => {
  if (containerRef.value) {
    containerRef.value.scrollTop = index * props.itemHeight
  }
}

defineExpose({
  scrollToIndex
})
</script>

<style scoped>
.virtual-scroll-container {
  overflow-y: auto;
  position: relative;
}

.virtual-scroll-item {
  box-sizing: border-box;
}
</style>

