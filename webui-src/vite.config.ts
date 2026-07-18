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
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
        // Ace is by far the largest dependency. Give it its own named chunk
        // so it is obvious in the output what the weight is, and so the
        // routes that have no editor (Commands, Tutorial, About) never
        // fetch it.
        manualChunks: (id) => (id.includes('node_modules/ace-builds') ? 'ace' : undefined),
      },
    },
  },
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:31750' },
  },
})
