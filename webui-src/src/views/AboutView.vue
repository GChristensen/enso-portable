<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import StaticDoc from '@/components/StaticDoc.vue'
import { getEnsoVersion } from '@/api/enso'
// The changelog used to be fetched over HTTP as a standalone page and injected
// with .html(). It is a build-time import now: one fewer request, and it stops
// being reachable as a bare URL.
import changes from '@/content/changes.html?raw'

const version = ref('')

onMounted(async () => {
  version.value = await getEnsoVersion()
})
</script>

<template>
  <div id="about-container">
    <AppHeader title="About" />

    <div id="about-version-panel">
      <img id="enso-logo" src="/images/logo.png" height="145" alt="Enso" />
      <h1>Enso Launcher (Open-Source)</h1>
      <h2 id="about-version">Version: {{ version }}</h2>
      <div class="about-links">
        <img class="favicon" src="/images/enso-16.png" alt="" />
        <a
          class="about-link"
          href="https://gchristensen.github.io/enso-portable/"
          target="_blank"
          rel="noopener"
          >Homepage</a
        >
        |
        <img class="favicon" src="/icons/github.ico" alt="" />
        <a
          class="about-link"
          href="https://github.com/GChristensen/enso-portable/"
          target="_blank"
          rel="noopener"
          >GitHub</a
        >
      </div>
    </div>

    <div id="about-changes-header"><h2>Changes</h2></div>
    <StaticDoc id="about-changes" :html="changes" />
  </div>
</template>

<style scoped>
#about-container {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
}

#about-version-panel {
  margin-top: 15px;
  text-align: center;
}

#about-version-panel h1 {
  color: var(--enso-green);
  border-top: none;
  font-size: 24pt;
  margin: 10px;
}

#about-version-panel h2 {
  font-size: 18px;
  border-top: none;
  margin-top: 0;
}

.about-link {
  font-size: 12pt;
}

#about-changes-header {
  flex: 0 0 auto;
  margin-top: 20px;
  text-align: center;
}

#about-changes-header h2 {
  margin-bottom: 0;
}

#about-changes {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  font-size: 12pt;
}
</style>

<style>
#about-changes * {
  font-size: 12pt;
}

.change-date {
  display: inline-block;
  margin-left: 10px;
}

.change-info {
  padding-left: 20px;
}
</style>
