<script setup lang="ts">
import { computed, reactive } from 'vue'
import { RouterLink } from 'vue-router'
import { setCommandFlag } from '@/api/enso'
import type { Command, CommandFlag } from '@/api/types'

const props = defineProps<{
  commands: Command[]
  voiceAvailable: boolean
}>()

/**
 * Local mutable flag state, keyed by command name.
 *
 * The server sends these as the string "true" or omits them entirely, so they
 * are normalised to booleans once here rather than being re-tested for
 * truthiness at every use.
 */
const flags = reactive(
  new Map<string, Record<CommandFlag, boolean>>(
    props.commands.map((c) => [
      c.name,
      {
        // The server sends `disabled`; flip it here, once, so that everything
        // downstream reads positively and `true` always means "enable".
        enabled: !c.disabled,
        voice: Boolean(c.voice),
        voiceOnly: Boolean(c.voiceOnly),
        voiceConfirm: Boolean(c.voiceConfirm),
      },
    ]),
  ),
)

const categories = computed(() => {
  const byName = new Map<string, Command[]>()
  for (const cmd of props.commands) {
    const list = byName.get(cmd.category)
    if (list) list.push(cmd)
    else byName.set(cmd.category, [cmd])
  }
  return [...byName.entries()]
    .map(([name, commands]) => ({
      name,
      label: name === 'other' ? 'other commands' : name,
      commands: [...commands].sort((a, b) => a.name.localeCompare(b.name)),
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

function setFlag(name: string, flag: CommandFlag, on: boolean) {
  const state = flags.get(name)
  if (!state) return
  state[flag] = on
  void setCommandFlag(flag, name, on)
}

/**
 * Voice-only and confirm both qualify *how* a voice command behaves, so
 * either one implies the command is a voice command at all.
 */
function setDependent(name: string, flag: 'voiceOnly' | 'voiceConfirm', on: boolean) {
  setFlag(name, flag, on)
  if (on && !flags.get(name)?.voice) setFlag(name, 'voice', true)
}
</script>

<template>
  <table class="commands-table">
    <thead>
      <tr>
        <th class="col-category">Categories</th>
        <th class="command-check" title="Enabled">⏻</th>
        <template v-if="voiceAvailable">
          <th class="command-check" title="Voice Command">🎙️</th>
          <th class="command-check" title="Voice-Only Command">👂🏻</th>
          <th class="command-check" title="Confirm Before Running">
            🆗<sup>
              <RouterLink
                class="voice-help"
                to="/tutorial#voice-recognition"
                title="About voice recognition"
                >?</RouterLink
              >
            </sup>
          </th>
        </template>
        <th class="col-commands">Commands</th>
      </tr>
    </thead>

    <!-- One tbody per category: the rowspan cell that names the category is a
         single binding, and the per-category rule comes from the tbody border
         instead of a hand-managed "topcell" class. -->
    <tbody v-for="category in categories" :key="category.name">
      <tr v-for="(cmd, index) in category.commands" :key="cmd.name">
        <td v-if="index === 0" class="command-feed" :rowspan="category.commands.length">
          {{ category.label }}
          <div class="meta">
            <RouterLink :to="{ path: '/editor', query: { category: category.name } }">
              Open in editor
            </RouterLink>
          </div>
        </td>

        <td class="command-check">
          <input
            type="checkbox"
            title="Enabled"
            :checked="flags.get(cmd.name)?.enabled"
            @change="setFlag(cmd.name, 'enabled', ($event.target as HTMLInputElement).checked)"
          />
        </td>

        <template v-if="voiceAvailable">
          <td class="command-check">
            <input
              type="checkbox"
              title="Voice Command"
              :checked="flags.get(cmd.name)?.voice"
              @change="setFlag(cmd.name, 'voice', ($event.target as HTMLInputElement).checked)"
            />
          </td>
          <td class="command-check">
            <input
              type="checkbox"
              title="Voice-Only Command"
              :checked="flags.get(cmd.name)?.voiceOnly"
              @change="
                setDependent(cmd.name, 'voiceOnly', ($event.target as HTMLInputElement).checked)
              "
            />
          </td>
          <td class="command-check">
            <input
              type="checkbox"
              title="Confirm Before Running"
              :checked="flags.get(cmd.name)?.voiceConfirm"
              @change="
                setDependent(cmd.name, 'voiceConfirm', ($event.target as HTMLInputElement).checked)
              "
            />
          </td>
        </template>

        <td class="command">
          <span class="name">{{ cmd.name }}</span>
          <!-- Server-supplied HTML, as in the original UI. It comes from the
               user's own local command files. -->
          <span class="description" v-html="cmd.description"></span>
          <div class="help" v-html="cmd.help"></div>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.commands-table {
  width: 100%;

  /* Line box of the command name. Named because the checkbox cells centre
     themselves against it -- see .command-check below. */
  --command-line: 16px;
  --checkbox-size: 14px;
  --row-padding-top: 4px;
}

.col-category {
  width: 25%;
}

/* Takes whatever the category and checkbox columns leave. Previously this was
   a hardcoded 55%, which left 20% of the table with no column claiming it --
   the browser handed that slack to the checkbox columns and blew them out to
   45px each for a 14px checkbox. */
.col-commands {
  width: auto;
}

.commands-table td {
  vertical-align: top;
}

/* The hairline that used to be painted per-cell via a "topcell" class: it
   separates categories, so it goes on the first row of each tbody only, and
   runs unbroken across every column including the checkboxes. */
.commands-table tbody > tr:first-child > td {
  border-top: 1px solid var(--enso-rule);
}

.command-feed {
  font-size: 18px;
}

.command-feed .meta {
  font-size: 76%;
}

.command {
  padding: var(--row-padding-top) 6px 4px 6px;
}

.command .name,
.command .description {
  line-height: var(--command-line);
}

.command-feed {
  padding: 6px 12px;
}

.command .name {
  font-size: 15pt;
}

.command .description {
  display: inline;
  font-size: 12pt;
  margin-left: 10px;
  color: #a7a7a7;
}

.command .help {
  margin-top: 5px;
  color: var(--enso-muted-dim);
}

/* width:1% makes the column shrink to its minimum content width, so each of
   these is just the checkbox plus a little breathing room. */
.command-check {
  width: 1%;
  white-space: nowrap;
  padding: var(--row-padding-top) 2px 0 2px;
  text-align: center;
}

/* Centre the checkbox on the command name's line box rather than hanging it
   from the top of the cell, so it sits on the same line as the text. */
td.command-check input[type='checkbox'] {
  display: block;
  margin: calc((var(--command-line) - var(--checkbox-size)) / 2) auto 0 auto;
}

th.command-check {
  font-size: 15px;
  font-weight: normal;
  font-variant-caps: normal;
  vertical-align: middle;
  padding: 0 2px;
  /* The help link is absolutely positioned against this so it cannot widen
     the 22px column or push the emoji off centre. */
  position: relative;
}

.voice-help {
  position: absolute;
  top: -2px;
  font-size: 10px;
  line-height: 1;
  text-decoration: none;
  color: var(--enso-green);
}

.voice-help:hover {
  text-decoration: underline;
}
</style>
