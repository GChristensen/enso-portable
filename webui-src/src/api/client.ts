import { connection } from '@/stores/connection'

/**
 * HTTP client for the Enso API.
 *
 * The whole point of this module is surviving an Enso restart without a page
 * reload. A restart replaces the process, which means:
 *
 *   - a brand new AUTH_TOKEN, so the cached one starts returning 401, and
 *   - a brand new listening socket, so for a few seconds nothing answers.
 *
 * So every request refetches the token on 401 and replays itself, and backs
 * off through the window where the socket is down. Both orderings converge:
 * if the new server is already up we see the 401 first, otherwise we see a
 * network error and retry until it is.
 */

let tokenPromise: Promise<string> | null = null

async function fetchToken(): Promise<string> {
  const res = await fetch('/api/enso/token', { credentials: 'omit' })
  if (!res.ok) throw new Error(`token request failed: ${res.status}`)
  const body = (await res.json()) as { token: string }
  return body.token
}

/** Cached, and deduped so a burst of calls on page load shares one request. */
function getToken(): Promise<string> {
  return (tokenPromise ??= fetchToken().catch((e) => {
    tokenPromise = null // don't cache a rejection
    throw e
  }))
}

const BACKOFF_MS = [250, 500, 1000, 2000, 2000, 3000]
const MAX_UNAUTHORIZED = 2

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** One attempt. Throws the Response on HTTP error, TypeError on network error. */
async function attempt(path: string, init: RequestInit, token: string) {
  const headers = new Headers(init.headers)
  headers.set('Authorization', 'Basic ' + btoa('default:' + token))
  const res = await fetch(path, { ...init, headers, credentials: 'omit' })
  if (!res.ok) throw res
  return res
}

export async function request(path: string, init: RequestInit = {}): Promise<Response> {
  let unauthorized = 0

  for (let n = 0; ; n++) {
    try {
      const res = await attempt(path, init, await getToken())
      if (connection.attempts > 0) connection.restored()
      return res
    } catch (e) {
      if (e instanceof Response) {
        // 401: our token is stale because Enso restarted. Drop it, refetch,
        // and replay this same request. Bounded so a server that always 401s
        // surfaces the error instead of spinning forever.
        if (e.status === 401 && ++unauthorized <= MAX_UNAUTHORIZED) {
          tokenPromise = null
          continue
        }
        throw e // a real server error, or we've given up on auth
      }

      // Not a Response => fetch itself rejected: connection refused, i.e.
      // Enso is mid-restart. Ride it out.
      connection.lost(n)
      await sleep(BACKOFF_MS[Math.min(n, BACKOFF_MS.length - 1)])
    }
  }
}

export async function getText(path: string): Promise<string> {
  return (await request(path)).text()
}

export async function getJSON<T>(path: string): Promise<T> {
  return (await request(path)).json() as Promise<T>
}

/** Mutating call. Form-encoded, because the Flask handlers read request.form. */
export async function post(path: string, fields?: Record<string, string>): Promise<Response> {
  const init: RequestInit = { method: 'POST' }
  if (fields) {
    init.body = new URLSearchParams(fields)
    init.headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
  }
  return request(path, init)
}
