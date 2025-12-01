/**
 * 交叉观察器 Hook（用于懒加载、无限滚动等）
 */

import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

export function useIntersectionObserver(
  target,
  callback,
  options = {}
) {
  const isIntersecting = ref(false)
  let observer = null

  const defaultOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1,
    ...options
  }

  const startObserving = () => {
    const element = typeof target === 'function' ? target() : target.value

    if (!element) return

    observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        isIntersecting.value = entry.isIntersecting
        if (callback) {
          callback(entry)
        }
      })
    }, defaultOptions)

    observer.observe(element)
  }

  const stopObserving = () => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  onMounted(() => {
    startObserving()
  })

  onBeforeUnmount(() => {
    stopObserving()
  })

  // 监听 target 变化
  if (target.value) {
    watch(target, () => {
      stopObserving()
      startObserving()
    })
  }

  return {
    isIntersecting,
    startObserving,
    stopObserving
  }
}

