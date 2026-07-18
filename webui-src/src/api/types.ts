/** A command as returned by /api/enso/get/commands. */
export interface Command {
  name: string
  /** Server-supplied HTML. Rendered with v-html, as the old UI did. */
  description: string
  /** Server-supplied HTML. */
  help: string
  category: string
  file: string
  // The server omits these keys when false and sends the *string* "true"
  // when set, so they must be read for truthiness, never compared to `true`.
  disabled?: string
  voice?: string
  voiceOnly?: string
  voiceConfirm?: string
}

export interface ColorThemes {
  current: string
  all: Record<string, unknown>
}

/** The four independent per-command flags, and the API path segment for each. */
export const COMMAND_FLAGS = {
  disabled: 'commands',
  voice: 'commands/voice',
  voiceOnly: 'commands/voice_only',
  voiceConfirm: 'commands/voice_confirm',
} as const

export type CommandFlag = keyof typeof COMMAND_FLAGS
