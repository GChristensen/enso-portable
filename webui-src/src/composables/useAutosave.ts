import { onBeforeUnmount } from 'vue'

/**
 * Debounced save, matching the original editor behaviour: write a second
 * after typing stops, and again immediately on blur.
 */
export function useAutosave(save: () => unknown, delay = 1000) {
  let timer: ReturnType<typeof setTimeout> | null = null

  function cancel() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  /** Call on every change. */
  function schedule() {
    cancel()
    timer = setTimeout(() => {
      timer = null
      void save()
    }, delay)
  }

  /** Call on blur: save now, and drop any pending debounce. */
  function flush() {
    cancel()
    void save()
  }

  onBeforeUnmount(cancel)

  return { schedule, flush, cancel }
}
