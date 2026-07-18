<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import CommandsTable from '@/components/CommandsTable.vue'
import { getCommands, getVoiceAvailable } from '@/api/enso'
import type { Command } from '@/api/types'

const commands = ref<Command[]>([])
const voiceAvailable = ref(false)
const showHelp = ref(false)
const loaded = ref(false)

const categoryCount = computed(() => new Set(commands.value.map((c) => c.category)).size)

onMounted(async () => {
  // Probe voice support before rendering, but never let the probe failing
  // block the table -- it just means the voice columns stay hidden.
  try {
    voiceAvailable.value = (await getVoiceAvailable()) === true
  } catch {
    voiceAvailable.value = false
  }

  commands.value = await getCommands()
  loaded.value = true
})
</script>

<template>
  <AppHeader title="Wherein are listed the commands at your disposal." />

  <div class="page-tip">
    <p>You can get to this page at any time using the “help” command.</p>
    <p>
      You have <span>{{ commands.length }}</span> commands in
      <span>{{ categoryCount }}</span> categories. |
      <a href="#" @click.prevent="showHelp = !showHelp">{{
        showHelp ? 'Hide help' : 'Show help'
      }}</a>
    </p>
  </div>

  <div v-show="showHelp" class="ubiq-tutorial" style="font-size: 100%">
    <ul>
      <li>
        All the commands that Enso recognizes are listed in the right column. The black text is the
        command's name (what you type into Enso to use it). The grey text explains what the command
        does.
      </li>
      <li>The left column shows all the command categories available.</li>
      <li>
        If there's a command you don't want, uncheck the box next to it. You can get the command
        back by re-checking the box.
      </li>
    </ul>
  </div>

  <CommandsTable
    v-if="loaded"
    :commands="commands"
    :voice-available="voiceAvailable"
  />
</template>
