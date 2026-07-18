<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import EditorToolbar from '@/components/EditorToolbar.vue'
import { useAutosave } from '@/composables/useAutosave'
import { downloadText } from '@/composables/useFileIO'
import { deleteCategory, getCategories, readCategory, writeCategory } from '@/api/enso'
import '@/assets/editor.css'

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
const editor = ref<InstanceType<typeof CodeEditor> | null>(null)

async function save() {
  await writeCategory(category.value, code.value)
}

const autosave = useAutosave(save)

async function load(name: string) {
  let text = ''
  try {
    text = await readCategory(name)
  } catch {
    // A category with no file yet (just created) 404s; start empty.
    text = ''
  }
  editor.value?.reset(text)
}

async function selectCategory(name: string) {
  autosave.cancel()
  await save() // don't lose edits when switching away
  category.value = name
  localStorage.setItem(LAST_CATEGORY_KEY, name)
  await load(name)
}

async function createCategory() {
  const name = prompt('Create category: ')?.trim()
  if (!name) return

  if (!categories.value.includes(name)) categories.value.push(name)
  category.value = name
  localStorage.setItem(LAST_CATEGORY_KEY, name)
  // Write immediately so the category exists server-side even if left empty.
  editor.value?.reset('')
  await save()
}

async function removeCategory() {
  if (category.value === DEFAULT_CATEGORY) return
  if (!confirm(`Do you really want to delete "${category.value}"?`)) return

  const removed = category.value
  await deleteCategory(removed)
  categories.value = categories.value.filter((c) => c !== removed)
  await selectCategory(categories.value[0] ?? DEFAULT_CATEGORY)
}

function onUpload(text: string) {
  editor.value?.reset(text)
  autosave.flush()
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
