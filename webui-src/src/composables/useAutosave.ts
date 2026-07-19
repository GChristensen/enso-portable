import { onBeforeUnmount } from 'vue'

/**
 * Debounced save, matching the original editor behaviour: write a second
 * after typing stops, and again immediately on blur.
 *
 * `save` is told whether the call is deliberate -- the debounce firing
 * (which only ever follows a real edit) or an explicit Ctrl+S -- as opposed
 * to a blur, which can fire on a buffer the user never actually touched.
 * Callers use this to decide whether an empty buffer is safe to save as-is;
 * see _write_user_file's docstring in webui.py for the failure mode this
 * guards against.
 */
export function useAutosave(save: (intentional: boolean) => unknown, delay = 1000) {
  let timer: ReturnType<typeof setTimeout> | null = null
  let inFlight: Promise<unknown> | null = null

  function cancel() {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  function run(intentional: boolean) {
    inFlight = Promise.resolve(save(intentional)).finally(() => {
      inFlight = null
    })
    return inFlight
  }

  /** Call on every change. Always follows a real edit, so this is deliberate. */
  function schedule() {
    cancel()
    timer = setTimeout(() => {
      timer = null
      void run(true)
    }, delay)
  }

  /**
   * Save now. `intentional` defaults to false for blur; pass true for the
   * other caller of this function, an explicit Ctrl+S.
   */
  function flush(intentional = false) {
    cancel()
    return run(intentional)
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
