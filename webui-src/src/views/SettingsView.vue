<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import { useAutosave } from '@/composables/useAutosave'
import {
  getColorThemes,
  getConfig,
  getConfigDir,
  getEnsoVersion,
  getEnsorc,
  getPythonVersion,
  getRetreatInstalled,
  openConfigDir,
  setConfig,
  setEnsorc,
} from '@/api/enso'

const ensoVersion = ref('')
const pythonVersion = ref('')

const themes = ref<string[]>([])
const theme = ref('')

const retreatInstalled = ref(false)
const retreatEnabled = ref(false)
const retreatShowIcon = ref(false)

const configDir = ref('')

const ensorc = ref('')
const ensorcReady = ref(false)
const autosave = useAutosave(() => setEnsorc(ensorc.value))

onMounted(async () => {
  // Independent reads; one failing should not blank the rest of the page.
  void getEnsoVersion().then((v) => (ensoVersion.value = v))
  void getPythonVersion().then((v) => (pythonVersion.value = v))
  void getConfigDir().then((v) => (configDir.value = v))

  void getColorThemes().then((data) => {
    const all = { ...data.all }
    delete all.default // internal alias, never offered as a choice
    themes.value = Object.keys(all)
    theme.value = data.current
  })

  retreatInstalled.value = await getRetreatInstalled()
  if (retreatInstalled.value) {
    retreatEnabled.value = (await getConfig('RETREAT_DISABLE')) !== 'True'
    retreatShowIcon.value = (await getConfig('RETREAT_SHOW_ICON')) !== 'False'
  }

  try {
    ensorc.value = (await getEnsorc()).trim()
  } catch {
    ensorc.value = '' // no ensorc.py yet
  }
  ensorcReady.value = true
})

function onThemeChange(value: string) {
  theme.value = value
  void setConfig('COLOR_THEME', value)
}

watch(retreatEnabled, (on) => void setConfig('RETREAT_DISABLE', on ? 'False' : 'True'))
watch(retreatShowIcon, (on) => void setConfig('RETREAT_SHOW_ICON', on ? 'True' : 'False'))
</script>

<template>
  <AppHeader title="Settings" />

  <div class="page-tip">
    <p>
      You can get to this page at any time using the “enso settings” command. Restart is required to
      apply changes.
    </p>
  </div>

  <div class="columns">
    <section class="col-wide">
      <h2 class="top">Custom Initialization</h2>
      <div id="ensorc-box">
        <CodeEditor
          v-if="ensorcReady"
          v-model="ensorc"
          :show-gutter="false"
          @update:model-value="autosave.schedule()"
          @blur="autosave.flush()"
          @save="autosave.flush()"
        />
      </div>
    </section>

    <section class="col-narrow">
      <h2 class="top">Version Information</h2>
      <div class="advanced">
        <p>
          You are using: <b>Enso Open-Source</b> <span class="version">{{ ensoVersion }}</span
          >, <b>Python</b> <span class="version">{{ pythonVersion }}</span>
        </p>
      </div>

      <h2>Color Theme</h2>
      <div class="advanced">
        <p>
          Enso color theme:
          <select
            :value="theme"
            @change="onThemeChange(($event.target as HTMLSelectElement).value)"
          >
            <option v-for="name in themes" :key="name" :value="name">{{ name }}</option>
          </select>
        </p>
      </div>

      <!-- Only rendered when Retreat is actually installed. The old page kept
           the block in the DOM and flipped visibility, so it reserved space. -->
      <template v-if="retreatInstalled">
        <h2>Enso Retreat</h2>
        <div class="advanced vertically-aligned">
          <input id="retreat-enable" v-model="retreatEnabled" type="checkbox" />
          <label for="retreat-enable">Enable Enso Retreat</label>
        </div>
        <div class="advanced vertically-aligned">
          <input
            id="retreat-show-icon"
            v-model="retreatShowIcon"
            type="checkbox"
            :disabled="!retreatEnabled"
          />
          <label for="retreat-show-icon">Show Enso Retreat icon</label>
        </div>
      </template>

      <h2>Backup/Restore</h2>
      <div class="advanced">
        Your Enso configuration is stored at:
        <div class="advanced">
          <input type="text" :value="configDir" readonly />
        </div>
        <div class="advanced">
          <a href="#" @click.prevent="openConfigDir()">Open in explorer</a>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
#ensorc-box {
  width: 100%;
  height: 410px;
}

.version {
  font-style: italic;
}

input[type='text'] {
  width: 100%;
  box-sizing: border-box;
}
</style>
