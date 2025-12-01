/**
 * 防抖 Hook
 */

import { ref, watch, unref } from 'vue'

export function useDebounce(value, delay = 300) {
  const debouncedValue = ref(unref(value))
  let timer = null

  watch(
    () => unref(value),
    (newValue) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        debouncedValue.value = newValue
      }, delay)
    }
  )

  return debouncedValue
}

export function useDebounceFn(fn, delay = 300) {
  let timer = null

  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

