<template>
  <div class="lazy-image" ref="containerRef">
    <img
      v-if="isLoaded"
      :src="src"
      :alt="alt"
      @load="onLoad"
      @error="onError"
      :class="{ 'fade-in': loaded }"
    />
    <div v-else class="placeholder">
      <el-icon class="is-loading"><Loading /></el-icon>
    </div>
    <div v-if="error" class="error-placeholder">
      <el-icon><WarnTriangleFilled /></el-icon>
      <span>加载失败</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Loading, WarnTriangleFilled } from '@element-plus/icons-vue'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  alt: {
    type: String,
    default: ''
  },
  threshold: {
    type: Number,
    default: 0.1
  }
})

const containerRef = ref(null)
const isLoaded = ref(false)
const loaded = ref(false)
const error = ref(false)

let observer = null

const onLoad = () => {
  loaded.value = true
}

const onError = () => {
  error.value = true
}

const startObserving = () => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !isLoaded.value) {
          isLoaded.value = true
          observer.disconnect()
        }
      })
    },
    { threshold: props.threshold }
  )

  if (containerRef.value) {
    observer.observe(containerRef.value)
  }
}

onMounted(() => {
  startObserving()
})

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.lazy-image {
  position: relative;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.lazy-image img {
  width: 100%;
  height: auto;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.lazy-image img.fade-in {
  opacity: 1;
}

.placeholder,
.error-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #999;
}

.error-placeholder {
  color: #f56c6c;
}
</style>

