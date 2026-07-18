<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { buildToc } from '@/composables/useToc'

const props = defineProps<{ html: string }>()

const root = ref<HTMLElement | null>(null)
const route = useRoute()
const router = useRouter()

/**
 * Scroll to the routed hash.
 *
 * This has to be done by hand: the content arrives via v-html, so at the
 * moment the browser would natively scroll, the target element does not exist
 * yet. /tutorial#voice-recognition is linked from the Commands page and the
 * changelog, so this path matters.
 */
async function scrollToHash() {
  if (!route.hash) return
  await nextTick()
  const id = decodeURIComponent(route.hash.slice(1))
  document.getElementById(id)?.scrollIntoView()
}

/** Route in-app for internal links inside the rendered HTML. */
function onClick(event: MouseEvent) {
  if (event.defaultPrevented || event.button !== 0) return
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return

  const anchor = (event.target as HTMLElement).closest('a')
  if (!anchor || anchor.target === '_blank') return

  const href = anchor.getAttribute('href')
  if (!href) return

  // In-page anchors: scroll without pushing a navigation.
  if (href.startsWith('#')) {
    event.preventDefault()
    document.getElementById(decodeURIComponent(href.slice(1)))?.scrollIntoView()
    return
  }

  // Same-origin app links become client-side navigations; anything else
  // (github.com, external docs) is left to the browser.
  if (href.startsWith('/')) {
    event.preventDefault()
    router.push(href)
  }
}

onMounted(async () => {
  if (root.value) buildToc(root.value)
  await scrollToHash()
})

watch(() => route.hash, scrollToHash)
watch(
  () => props.html,
  async () => {
    await nextTick()
    if (root.value) buildToc(root.value)
  },
)
</script>

<template>
  <div ref="root" v-html="html" @click="onClick"></div>
</template>
