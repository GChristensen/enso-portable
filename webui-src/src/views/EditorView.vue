<script setup lang="ts">
import { defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
// Loaded on demand: this is what pulls in ace, and keeping it out of the
// main bundle means pages with no editor never download or parse it.
// The type import is erased at build time, so it costs nothing.
import type CodeEditorComponent from '@/components/CodeEditor.vue'
import EditorToolbar from '@/components/EditorToolbar.vue'
import { useAutosave } from '@/composables/useAutosave'
import { downloadText } from '@/composables/useFileIO'
import { deleteCategory, getCategories, readCategory, writeCategory } from '@/api/enso'
import '@/assets/editor.css'

const CodeEditor = defineAsyncComponent(
  () => import('@/components/CodeEditor.vue'),
)

const DEFAULT_CATEGORY = 'user'
const LAST_CATEGORY_KEY = 'lastNamespace'

const STUBS = {
  simple: `def cmd_my_command(ensoapi):
    """My command description"""
    ensoapi.display_message("Hello world!")`,

  varargs: `def cmd_my_command(ensoapi, argument):
    """My command description"""
    ensoapi.display_message(argument)`,

  boundargs: `def cmd_my_command(ensoapi, argument):
    """My command description"""
    ensoapi.display_message(argument)

cmd_my_command.valid_args = ["arg1", "arg2"]`,
}

const route = useRoute()
const router = useRouter()

const categories = ref<string[]>([DEFAULT_CATEGORY])
const category = ref(DEFAULT_CATEGORY)
const code = ref('')
const expanded = ref(false)
const editor = ref<InstanceType<typeof CodeEditorComponent> | null>(null)

async function save() {
  await writeCategory(category.value, code.value)
}

const autosave = useAutosave(save)

/** Put a document into the editor without it counting as an edit. */
function setCode(text: string) {
  code.value = text
  // No-op before the async editor mounts; it seeds itself from `code`.
  editor.value?.resetHistory()
  // The assignment above would otherwise schedule a save of what we just read.
  autosave.cancel()
}

async function load(name: string) {
  let text = ''
  try {
    text = await readCategory(name)
  } catch {
    // A category with no file yet (just created) 404s; start empty.
    text = ''
  }
  setCode(text)
}

/** Switch to `name` without writing the current buffer anywhere. */
async function openCategory(name: string) {
  autosave.cancel()
  category.value = name
  localStorage.setItem(LAST_CATEGORY_KEY, name)
  await load(name)
}

async function selectCategory(name: string) {
  autosave.cancel()
  await save() // don't lose edits when switching away
  await openCategory(name)
}

async function createCategory() {
  const name = prompt('Create category: ')?.trim()
  if (!name) return

  if (!categories.value.includes(name)) categories.value.push(name)
  category.value = name
  localStorage.setItem(LAST_CATEGORY_KEY, name)
  // Write immediately so the category exists server-side even if left empty.
  setCode('')
  await save()
}

async function removeCategory() {
  if (category.value === DEFAULT_CATEGORY) return

  const removed = category.value
  if (!confirm(`Do you really want to delete "${removed}"?`)) return

  // Drop any pending autosave, then wait for one already on the wire: both
  // target the category being deleted, and either would recreate the file
  // after the delete. Clicking Delete blurs the editor, which fires a save,
  // so this is the normal path rather than a corner case.
  autosave.cancel()
  await autosave.settled()

  await deleteCategory(removed)
  categories.value = categories.value.filter((c) => c !== removed)

  // openCategory, not selectCategory -- the latter saves the current buffer on
  // the way out, which would write it straight back into the file we just
  // deleted.
  await openCategory(categories.value[0] ?? DEFAULT_CATEGORY)
}

function onUpload(text: string) {
  setCode(text)
  void save()
}

onMounted(async () => {
  // ?category=<name> (from a legacy edit.html?<name> redirect) wins over the
  // remembered one.
  const requested = route.query.category
  category.value =
    (typeof requested === 'string' && requested) ||
    localStorage.getItem(LAST_CATEGORY_KEY) ||
    DEFAULT_CATEGORY

  try {
    const names = await getCategories()
    categories.value = [
      DEFAULT_CATEGORY,
      ...names.filter((n) => n !== DEFAULT_CATEGORY).sort(),
    ]
  } catch {
    categories.value = [DEFAULT_CATEGORY]
  }
  if (!categories.value.includes(category.value)) categories.value.push(category.value)

  await load(category.value)
  editor.value?.focus()
})

watch(expanded, (on) => {
  document.getElementById('app')?.classList.toggle('app--expanded', on)
  editor.value?.focus()
})

onBeforeUnmount(() => {
  document.getElementById('app')?.classList.remove('app--expanded')
  autosave.flush()
})

// Keep the URL honest when the category changes, so a refresh reopens it.
watch(category, (name) => {
  void router.replace({ query: { ...route.query, category: name } })
})
</script>

<template>
  <div class="editor-page" :class="{ 'editor-page--expanded': expanded }">
    <div class="editor-page__header">
      <div class="editor-page__chrome">
        <AppHeader title="Command Editor" />
      </div>

      <EditorToolbar
        v-model:expanded="expanded"
        @download="downloadText(`${category}.py`, code)"
        @upload="onUpload"
      >
        <label for="script-namespaces">Category:&nbsp;</label>
        <select
          id="script-namespaces"
          :value="category"
          @change="selectCategory(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="name in categories" :key="name" :value="name">
            {{ name === DEFAULT_CATEGORY ? '<user>' : name }}
          </option>
        </select>
        <button type="button" class="icon-button" title="Create category" @click="createCategory">
          <img src="/images/document_create.png" alt="Create category" />
        </button>
        <button
          type="button"
          class="icon-button"
          title="Delete category"
          :disabled="category === DEFAULT_CATEGORY"
          @click="removeCategory"
        >
          <img src="/images/document_delete.png" alt="Delete category" />
        </button>
      </EditorToolbar>
    </div>

    <div class="editor-page__panel">
      <CodeEditor
        ref="editor"
        v-model="code"
        @update:model-value="autosave.schedule()"
        @blur="autosave.flush()"
        @save="autosave.flush()"
      />
    </div>

    <div class="editor-page__footer">
      <div class="editor-page__info">Saving is done automatically.</div>
      <div class="editor-page__buttons">
        Insert template commands:
        <a href="#" class="action" @click.prevent="editor?.insert(STUBS.simple)">NO ARGS</a> |
        <a href="#" class="action" @click.prevent="editor?.insert(STUBS.varargs)">VAR ARG</a> |
        <a href="#" class="action" @click.prevent="editor?.insert(STUBS.boundargs)">BOUND ARG</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
#script-namespaces {
  margin-right: 2px;
}

.icon-button:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
