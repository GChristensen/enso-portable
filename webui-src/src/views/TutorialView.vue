<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import StaticDoc from '@/components/StaticDoc.vue'
import html from '@/content/tutorial.html?raw'
</script>

<template>
  <AppHeader title="Tutorial" />
  <StaticDoc :html="html" />
</template>

<style>
#toc h2 {
  border-top: none;
  margin-bottom: 0;
}

[data-toc] {
  list-style: none;
  padding-left: 0;
  margin-top: 0;
}

[data-toc] ul {
  list-style: none;
  padding-left: 20px;
}

[data-toc] li {
  padding: 2px 0;
}
</style>
