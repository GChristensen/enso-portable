<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import StaticDoc from '@/components/StaticDoc.vue'
import html from '@/content/api.html?raw'
</script>

<template>
  <AppHeader title="API" />
  <StaticDoc :html="html" />
</template>
