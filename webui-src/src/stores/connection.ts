import { reactive } from 'vue'

/**
 * Whether the Enso HTTP server is currently reachable.
 *
 * Enso restarts as a genuinely new process, so there are a few seconds where
 * nothing is listening on the port. The API client reports that here and the
 * ConnectionBanner surfaces it, rather than letting requests fail silently.
 */
export const connection = reactive({
  online: true,
  /** How many consecutive failures the current outage has seen. */
  attempts: 0,

  /**
   * Set when this tab can no longer load its own code and only a reload will
   * fix it -- the assets were rebuilt underneath it, so the hashed filenames
   * this page was served with are gone from disk. Unlike an outage, waiting
   * does not help, so the user has to be told rather than quietly retried.
   */
  reloadRequired: false,

  requireReload() {
    this.reloadRequired = true
  },

  lost(attempt: number) {
    this.attempts = attempt + 1
    // One transient failure is not worth a banner -- a restart reliably
    // produces several, so wait for the second before saying anything.
    if (this.attempts > 1) this.online = false
  },

  restored() {
    this.attempts = 0
    this.online = true
  },
})
