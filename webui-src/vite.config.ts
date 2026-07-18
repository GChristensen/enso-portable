import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Build output goes straight into the directory Flask serves, and that
// directory is committed — end users install Enso without a Node toolchain.
// Keep `sourcemap` off: every UI change already churns hashed bundles in git.
export default defineConfig({
  plugins: [vue()],
  base: '/',
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  build: {
    outDir: '../enso/enso/webui',
    emptyOutDir: true, // required: outDir lies outside the Vite root
    target: 'es2020',
    sourcemap: false,
    assetsDir: 'assets',
    // One stylesheet rather than one per view.
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        // No manualChunks on purpose. ace-builds is imported only by
        // CodeEditor.vue, which is only ever imported dynamically, so Rollup
        // already isolates the pair into one lazy chunk. Naming it explicitly
        // here made things worse: forcing CodeEditor.vue into a manual chunk
        // pulled Vue in after it and turned the chunk into a *static* import
        // of the entry, so every page downloaded all of ace.
      },
    },
  },
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:31750' },
  },
})
