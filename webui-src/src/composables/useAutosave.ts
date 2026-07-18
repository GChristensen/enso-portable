import { onBeforeUnmount } from 'vue'

/**
 * Debounced save, matching the original editor behaviour: write a second
 * after typing stops, and again immediately on blur.
 */
export function useAutosave(save: () => unknown, delay = 1000) {
  let timer: ReturnType<typeof setTimeout> | null = null
  let inFlight: Promise<unknown> | null = null

  function cancel() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function run() {
    inFlight = Promise.resolve(save()).finally(() => {
      inFlight = null
    })
    return inFlight
  }

  /** Call on every change. */
  function schedule() {
    cancel()
    timer = setTimeout(() => {
      timer = null
      void run()
    }, delay)
  }

  /** Call on blur: save now, and drop any pending debounce. */
  function flush() {
    cancel()
    return run()
  }

  /**
   * Resolves once no save is in flight.
   *
   * Callers that are about to do something destructive -- deleting the file
   * being edited, say -- need this. Cancelling only stops a *pending* save;
   * a request already on the wire could still land after the delete and
   * recreate the file.
   */
  function settled() {
    return inFlight ?? Promise.resolve()
  }

  onBeforeUnmount(cancel)

  return { schedule, flush, cancel, settled }
}
