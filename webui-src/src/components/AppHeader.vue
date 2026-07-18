<script setup lang="ts">
import { RouterLink } from 'vue-router'

/**
 * The single nav.
 *
 * This markup used to be copy-pasted into seven pages with a hardcoded
 * class="selected", and had already drifted: about.html's copy was missing
 * the Tasks link and pointed at a cmenu.html that does not exist. RouterLink
 * supplies the active class, so that class of bug is gone by construction.
 */
const links = [
  { to: '/settings', label: 'Settings' },
  { to: '/commands', label: 'Your Commands' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/editor', label: 'Command Editor' },
  { to: '/api-ref', label: 'API Reference' },
  { to: '/tutorial', label: 'Tutorial' },
  { to: '/about', label: 'About' },
]

defineProps<{
  /** The text after "Enso: " in the page heading. */
  title: string
}>()
</script>

<template>
  <header class="app-header">
    <div class="head"><span class="large">Enso: </span>{{ title }}</div>
    <nav id="nav-container">
      <ul id="nav">
        <li v-for="link in links" :key="link.to">
          <RouterLink :to="link.to">{{ link.label }}</RouterLink>
        </li>
      </ul>
    </nav>
  </header>
</template>

<style>
/* Not scoped: RouterLink's active class lands on the <a>, and the nav is
   styled as a unit. */
#nav-container {
  /* Was margin-left: -40px + float, purely to cancel the default <ul>
     padding. Zeroing the padding says what was meant. */
  margin: 0;
}

#nav {
  display: flex;
  margin: 0;
  padding: 0;
  list-style: none;
}

#nav li {
  flex: 1;
  min-width: 0;
  background-color: var(--enso-nav-bg);
  border-left: 1px solid var(--enso-nav-border);
  margin: 0;
  padding: 0;
  height: 45px;
  text-align: left;
}

#nav a {
  padding: 5px;
  color: #fff;
  display: block;
  height: 100%;
  text-decoration: none;
  box-sizing: border-box;
}

#nav li:hover,
#nav li:has(> a.router-link-active) {
  background-color: var(--enso-green);
}

#nav a:focus-visible {
  outline: 2px solid var(--enso-text);
  outline-offset: -2px;
}
</style>
