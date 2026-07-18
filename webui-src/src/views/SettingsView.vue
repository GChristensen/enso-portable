<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { useAutosave } from '@/composables/useAutosave'
import {
  getColorThemes,
  getConfig,
  getConfigDir,
  getEnsoVersion,
  getEnsorc,
  getPythonVersion,
  getRetreatInstalled,
  getVoiceAvailable,
  openConfigDir,
  setConfig,
  setEnsorc,
} from '@/api/enso'

// Loaded on demand: this is what pulls in ace, and keeping it out of the
// main bundle means pages with no editor never download or parse it.
const CodeEditor = defineAsyncComponent(
  () => import('@/components/CodeEditor.vue'),
)

const ensoVersion = ref('')
const pythonVersion = ref('')

const themes = ref<string[]>([])
const theme = ref('')

// Optional features. Each is shown only when its native module is present:
// retreatlib.pyd for Retreat, voicecmdlib.pyd for voice recognition.
const retreatInstalled = ref(false)
const retreatEnabled = ref(false)
const retreatShowIcon = ref(false)

const voiceAvailable = ref(false)
const voiceEnabled = ref(false)

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
    voiceAvailable.value = (await getVoiceAvailable()) === true
  } catch {
    voiceAvailable.value = false
  }
  if (voiceAvailable.value) {
    voiceEnabled.value = (await getConfig('VOICE_ENABLED')) !== 'False'
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

// Explicit handlers rather than v-model + watch: a watch also fires when the
// initial value is read in onMounted, which would POST the setting straight
// back to the server on every page load.
function onRetreatEnabledChange(on: boolean) {
  retreatEnabled.value = on
  void setConfig('RETREAT_DISABLE', on ? 'False' : 'True')
}

function onRetreatShowIconChange(on: boolean) {
  retreatShowIcon.value = on
  void setConfig('RETREAT_SHOW_ICON', on ? 'True' : 'False')
}

function onVoiceEnabledChange(on: boolean) {
  voiceEnabled.value = on
  void setConfig('VOICE_ENABLED', on ? 'True' : 'False')
}
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

      <!-- Optional features, side by side. Each is rendered only when its
           native module is present; the old page kept Retreat in the DOM and
           flipped visibility, so it reserved space even when absent. -->
      <div v-if="retreatInstalled || voiceAvailable" class="feature-columns">
        <section v-if="retreatInstalled" class="feature-column">
          <h2>Enso Retreat</h2>
          <div class="advanced vertically-aligned">
            <input
              id="retreat-enable"
              type="checkbox"
              :checked="retreatEnabled"
              @change="onRetreatEnabledChange(($event.target as HTMLInputElement).checked)"
            />
            <label for="retreat-enable">Enable Enso Retreat</label>
          </div>
          <div class="advanced vertically-aligned">
            <input
              id="retreat-show-icon"
              type="checkbox"
              :checked="retreatShowIcon"
              :disabled="!retreatEnabled"
              @change="onRetreatShowIconChange(($event.target as HTMLInputElement).checked)"
            />
            <label for="retreat-show-icon">Show Enso Retreat icon</label>
          </div>
        </section>

        <section v-if="voiceAvailable" class="feature-column feature-column--right">
          <h2>Voice Recognition</h2>
          <div class="advanced vertically-aligned">
            <input
              id="voice-enable"
              type="checkbox"
              :checked="voiceEnabled"
              @change="onVoiceEnabledChange(($event.target as HTMLInputElement).checked)"
            />
            <label for="voice-enable">Enable voice recognition</label>
          </div>
        </section>
      </div>

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
.feature-columns {
  display: flex;
  gap: var(--enso-gap);
  align-items: flex-start;
}

.feature-column {
  flex: 1 1 0;
  min-width: 0;
}

/* margin-left:auto rather than relying on being the second flex item, so it
   stays right-aligned even when Retreat is not installed and this is the
   only column present. */
.feature-column--right {
  margin-left: auto;
  text-align: right;
}

/* The label sits left of the checkbox on the right-hand column so the two
   read as a mirrored pair rather than drifting away from the heading. */
.feature-column--right .vertically-aligned {
  justify-content: flex-end;
}

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
