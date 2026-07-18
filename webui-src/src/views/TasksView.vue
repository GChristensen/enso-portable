<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import EditorToolbar from '@/components/EditorToolbar.vue'
import { useAutosave } from '@/composables/useAutosave'
import { downloadText } from '@/composables/useFileIO'
import { readTasks, writeTasks } from '@/api/enso'
import '@/assets/editor.css'

const PLACEHOLDER = '# Tasks is a block of code executed in a separate thread on Enso start.'

const code = ref('')
const expanded = ref(false)
const editor = ref<InstanceType<typeof CodeEditor> | null>(null)

/** True while the buffer holds the placeholder rather than real content. */
const showingPlaceholder = ref(false)

async function save() {
  // Never persist the placeholder as if the user had written it.
  if (showingPlaceholder.value) return
  await writeTasks(code.value)
}

const autosave = useAutosave(save)

function showPlaceholder() {
  showingPlaceholder.value = true
  editor.value?.reset(PLACEHOLDER)
}

function onFocus() {
  if (!showingPlaceholder.value) return
  showingPlaceholder.value = false
  editor.value?.reset('')
}

function onBlur() {
  autosave.flush()
  if (!showingPlaceholder.value && code.value.trim() === '') showPlaceholder()
}

function onUpload(text: string) {
  showingPlaceholder.value = false
  editor.value?.reset(text)
  autosave.flush()
}

onMounted(async () => {
  let text = ''
  try {
    text = (await readTasks()).trim()
  } catch {
    text = '' // no tasks.py yet
  }

  if (text) editor.value?.reset(text)
  else showPlaceholder()
})

watch(expanded, (on) => {
  document.getElementById('app')?.classList.toggle('app--expanded', on)
  editor.value?.focus()
})

onBeforeUnmount(() => {
  document.getElementById('app')?.classList.remove('app--expanded')
  autosave.flush()
})
</script>

<template>
  <div class="editor-page" :class="{ 'editor-page--expanded': expanded }">
    <div class="editor-page__header">
      <div class="editor-page__chrome">
        <AppHeader title="Tasks" />
      </div>

      <EditorToolbar
        v-model:expanded="expanded"
        @download="downloadText('tasks.py', showingPlaceholder ? '' : code)"
        @upload="onUpload"
      />
    </div>

    <div class="editor-page__panel">
      <CodeEditor
        ref="editor"
        v-model="code"
        @update:model-value="autosave.schedule()"
        @focus="onFocus"
        @blur="onBlur"
        @save="autosave.flush()"
      />
    </div>

    <div class="editor-page__footer">
      <div class="editor-page__info">Saving is done automatically.</div>
    </div>
  </div>
</template>
