<script setup lang="ts">
import { ref } from 'vue'
import { readFileAsText } from '@/composables/useFileIO'

defineProps<{ expanded: boolean }>()

const emit = defineEmits<{
  download: []
  upload: [text: string]
  'update:expanded': [value: boolean]
}>()

const picker = ref<HTMLInputElement | null>(null)

async function onPicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  emit('upload', await readFileAsText(file))
  // Reset so picking the same file twice fires change again.
  input.value = ''
}
</script>

<template>
  <div class="editor-toolbar">
    <button type="button" class="icon-button" title="Download" @click="emit('download')">
      <img src="/images/download.png" alt="Download" />
    </button>
    <button type="button" class="icon-button" title="Upload" @click="picker?.click()">
      <img src="/images/upload.png" alt="Upload" />
    </button>
    <input ref="picker" type="file" accept=".py,text/x-python" hidden @change="onPicked" />

    <div class="editor-toolbar__spacer"></div>

    <slot />

    <button
      type="button"
      class="icon-button"
      :title="expanded ? 'Collapse editor' : 'Expand editor'"
      @click="emit('update:expanded', !expanded)"
    >
      <!-- State drives the image. The old code did the reverse: it read the
           img src back out of the DOM and string-matched it to decide what
           the current state was. -->
      <img :src="expanded ? '/images/collapse.png' : '/images/expand.png'" alt="" />
    </button>
  </div>
</template>

<style scoped>
.editor-toolbar {
  margin: 5px 0;
  display: flex;
  align-items: center;
  gap: 2px;
}

.editor-toolbar__spacer {
  flex: 1 0;
}

.icon-button {
  background: none;
  border: none;
  padding: 0 2px;
  cursor: pointer;
  line-height: 0;
}

.icon-button:focus-visible {
  outline: 2px solid var(--enso-green);
}
</style>
