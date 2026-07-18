<script setup lang="ts">
import { connection } from '@/stores/connection'

function reload() {
  window.location.reload()
}
</script>

<template>
  <Transition name="banner">
    <!-- Reload takes precedence: it is not a wait-and-see condition, so it
         must not be masked by the transient "reconnecting" message. -->
    <div v-if="connection.reloadRequired" class="connection-banner connection-banner--action" role="alert">
      Enso was updated — this page is out of date.
      <button type="button" class="connection-banner__button" @click="reload">Reload</button>
    </div>
    <div v-else-if="!connection.online" class="connection-banner" role="status">
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

.connection-banner--action {
  background: var(--enso-green);
}

.connection-banner__button {
  margin-left: 10px;
  font: inherit;
  font-variant-caps: small-caps;
  color: var(--enso-text);
  background: #fff;
  border: none;
  border-radius: 2px;
  padding: 1px 10px;
  cursor: pointer;
}

.connection-banner__button:focus-visible {
  outline: 2px solid var(--enso-text);
  outline-offset: 1px;
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