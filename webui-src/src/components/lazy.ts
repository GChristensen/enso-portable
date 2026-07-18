import { defineAsyncComponent, type AsyncComponentLoader } from 'vue'
import { connection } from '@/stores/connection'

/**
 * Asynchronous components that survive an Enso restart.
 *
 * The API client already replays requests across a restart, but a lazily
 * loaded chunk is fetched by the module loader, not by our client -- so
 * navigating to an editor during the seconds Enso is down left the component
 * permanently unrendered, with no error anywhere.
 *
 * Two failure modes have to be told apart, because only one of them is worth
 * retrying:
 *
 *   - The server is down (restarting). Transient; retry and it will come back.
 *   - The server is up but the chunk 404s. The assets were rebuilt and this
 *     tab is holding filenames that no longer exist. Retrying is futile; the
 *     page has to be reloaded to pick up the new index.html.
 *
 * Reachability is the discriminator: if the API answers but the chunk still
 * will not load, it is the second case.
 */

const RETRY_DELAYS_MS = [300, 800, 1500, 2500, 4000]

async function serverIsReachable(): Promise<boolean> {
  try {
    // Deliberately a bare fetch, not the API client: that one retries
    // internally, and here the whole point is a single immediate answer.
    await fetch('/api/enso/token', { credentials: 'omit', cache: 'no-store' })
    // Any response at all -- including 403 or 404 -- means something answered,
    // which is the only question being asked here. Checking res.ok instead
    // would read an auth rejection as "server down" and retry forever.
    return true
  } catch {
    // fetch rejects only when nothing answered: Enso is mid-restart.
    return false
  }
}

export function lazyComponent(loader: AsyncComponentLoader) {
  return defineAsyncComponent({
    loader,
    // Long enough that a normal fast load shows no spinner at all.
    delay: 250,
    onError: (error, retry, fail, attempts) => {
      void (async () => {
        // From the second failure on, check whether the server is actually
        // there. If it is, more retries cannot help -- our filenames are stale.
        if (attempts >= 2 && (await serverIsReachable())) {
          console.error('Chunk failed to load while the server is up:', error)
          connection.requireReload()
          fail()
          return
        }

        if (attempts > RETRY_DELAYS_MS.length) {
          console.error('Chunk failed to load, giving up:', error)
          connection.requireReload()
          fail()
          return
        }

        setTimeout(retry, RETRY_DELAYS_MS[attempts - 1])
      })()
    },
  })
}

/**
 * The code editor, and behind it ace -- by far the largest dependency, and the
 * only thing kept out of the main bundle. Shared by the editor, tasks and
 * settings views so the retry behaviour above is defined once.
 */
export const CodeEditorAsync = lazyComponent(() => import('@/components/CodeEditor.vue'))