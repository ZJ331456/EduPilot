/**
 * 节流 Hook
 */

import { ref, watch, unref } from 'vue'

export function useThrottle(value, delay = 300) {
  const throttledValue = ref(unref(value))
  let last = 0

  watch(
    () => unref(value),
    (newValue) => {
      const now = Date.now()
      if (now - last >= delay) {
        throttledValue.value = newValue
        last = now
      }
    }
  )

  return throttledValue
}

export function useThrottleFn(fn, delay = 300) {
  let last = 0

  return function (...args) {
    const now = Date.now()
    if (now - last >= delay) {
      fn.apply(this, args)
      last = now
    }
  }
}

