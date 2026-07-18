<script setup lang="ts">
import { connection } from '@/stores/connection'
</script>

<template>
  <Transition name="banner">
    <div v-if="!connection.online" class="connection-banner" role="status">
      Enso is restarting — reconnecting…
    </div>
  </Transition>
</template>

<style scoped>
.connection-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 6px 10px;
  text-align: center;
  font-variant-caps: small-caps;
  font-size: 14px;
  color: #fff;
  background: var(--enso-nav-bg);
}

.banner-enter-active,
.banner-leave-active {
  transition: transform 0.15s ease;
}

.banner-enter-from,
.banner-leave-to {
  transform: translateY(-100%);
}
</style>
