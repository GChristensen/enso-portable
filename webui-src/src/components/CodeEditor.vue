<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
// Import from the package root, not src-noconflict/ace: it resolves to the
// same file but is the entry point that carries type declarations.
import ace from 'ace-builds'
// Left to itself, Ace fetches its mode and theme at runtime by injecting a
// <script> whose URL it guesses from its own location -- a guess that is
// wrong under a bundler. Importing them for side effects instead registers
// them into Ace's module registry at load time, so setMode/setTheme resolve
// synchronously and nothing is fetched. These must come after the core
// import above, which ES module evaluation order guarantees.
import 'ace-builds/src-noconflict/mode-python'
import 'ace-builds/src-noconflict/theme-monokai'

const props = withDefaults(
  defineProps<{
    modelValue: string
    showGutter?: boolean
    printMargin?: number
  }>(),
  { showGutter: true, printMargin: 120 },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
  focus: []
  save: []
}>()

const host = ref<HTMLElement | null>(null)
let editor: ace.Ace.Editor | null = null
let observer: ResizeObserver | null = null
/** Set while we are writing props into the editor, to suppress the echo. */
let applying = false

onMounted(() => {
  if (!host.value) return

  editor = ace.edit(host.value)
  editor.setTheme('ace/theme/monokai')
  const session = editor.getSession()
  session.setMode('ace/mode/python')
  // The python mode ships no worker; without this Ace probes for one and
  // logs a failure.
  session.setUseWorker(false)
  editor.setPrintMarginColumn(props.printMargin)
  editor.renderer.setShowGutter(props.showGutter)

  editor.setValue(props.modelValue, -1)
  session.setUndoManager(new ace.UndoManager())

  editor.commands.addCommand({
    name: 'Save',
    bindKey: { win: 'Ctrl-S', mac: 'Command-S' },
    exec: () => emit('save'),
  })

  session.on('change', () => {
    if (applying || !editor) return
    emit('update:modelValue', editor.getValue())
  })

  editor.on('blur', () => emit('blur'))
  editor.on('focus', () => emit('focus'))

  // Replaces the old `innerHeight() - header - footer - 20` arithmetic, which
  // had to be recomputed by hand and silently mis-sized whenever the chrome
  // around the editor changed height. Sizing is pure CSS now; Ace just needs
  // to be told when the box changed.
  observer = new ResizeObserver(() => editor?.resize())
  observer.observe(host.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  editor?.destroy()
  editor = null
})

watch(
  () => props.modelValue,
  (value) => {
    if (!editor || value === editor.getValue()) return
    applying = true
    // -1 parks the cursor at the start instead of selecting the whole buffer.
    editor.setValue(value, -1)
    applying = false
  },
)

watch(
  () => props.showGutter,
  (show) => editor?.renderer.setShowGutter(show),
)

defineExpose({
  focus: () => editor?.focus(),
  /** Insert text at the cursor, as the template-stub links do. */
  insert: (text: string) => {
    if (!editor) return
    editor.session.insert(editor.getCursorPosition(), text)
    editor.focus()
  },
  /** Replace the buffer and drop undo history, for load/upload. */
  reset: (text: string) => {
    if (!editor) return
    applying = true
    editor.setValue(text, -1)
    editor.getSession().setUndoManager(new ace.UndoManager())
    applying = false
    emit('update:modelValue', text)
  },
})
</script>

<template>
  <div ref="host" class="code-editor"></div>
</template>

<style scoped>
.code-editor {
  width: 100%;
  height: 100%;
  min-height: 0;
}
</style>
