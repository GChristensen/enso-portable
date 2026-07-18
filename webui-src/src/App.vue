<script setup lang="ts">
import { watchEffect } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import ConnectionBanner from '@/components/ConnectionBanner.vue'

const route = useRoute()

// The editor routes fill the viewport and scroll internally; the content
// routes scroll the page. The distinction lives on #app because the flex
// column has to start at the root of the layout.
watchEffect(() => {
  const fullHeight = route.name === 'editor' || route.name === 'tasks'
  document.getElementById('app')?.classList.toggle('app--fullheight', fullHeight)
})
</script>

<template>
  <ConnectionBanner />
  <RouterView />
</template>
