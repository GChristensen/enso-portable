# Enso Web UI

Vue 3 + Vite SPA for the Enso settings/commands/editor pages.

## Important: the build output is committed

`npm run build` writes to **`../enso/enso/webui/`**, and that directory is
checked into git. This is deliberate — the Windows installer (`setup.nsi`) and
`make_dist_unix.cmd` both copy the `enso\enso` tree verbatim, so end users get a
working UI without ever installing Node.

**After changing anything in here, run `npm run build` and commit the result
alongside your source changes.** A source change without a rebuild ships nothing.

`../enso/enso/webui/` is fully generated. Do not hand-edit files there; they are
erased on every build (`emptyOutDir`).

## Why this lives at the repo root

`setup.nsi` does `File /r ... enso\enso` and `make_dist_unix.cmd` does
`robocopy enso\enso ... /e`. Neither excludes `node_modules`. If this project
sat under `enso\enso\`, the installer would ship tens of thousands of dependency
files. Keeping it at the repo root means both packaging scripts stay correct
with no exclusions to remember.

## Development

```sh
npm install
npm run dev        # http://localhost:5173, proxies /api -> http://localhost:31750
```

Run Enso in another terminal so the API is live:

```sh
cd ../enso && debug.bat        # Windows
```

The dev server proxies `/api` to the running Enso, so the UI talks to real
commands, real config and a real editor backend.

```sh
npm run build      # typecheck + build into ../enso/enso/webui
npm run typecheck  # vue-tsc only
```

## Layout

```
src/api/          HTTP client (token cache, 401 replay, restart backoff) + typed endpoints
src/components/   AppHeader, CodeEditor, CommandsTable, StaticDoc, ...
src/composables/  useAutosave, useToc, useFileIO
src/content/      static doc fragments (tutorial, API reference, changelog)
src/stores/       reactive connection state
src/views/        one per route
public/           images/ and icons/, copied verbatim to the output root
```

## Auth

The client fetches `GET /api/enso/token` and sends it as HTTP Basic on every
request. Enso restarts as a brand new process with a brand new token, so the
client transparently re-fetches on `401` and replays the request, and backs off
while the socket is down. That is why an open tab survives `enso restart`
without a reload — see `src/api/client.ts`.
