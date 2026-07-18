import { getJSON, getText, post } from './client'
import { COMMAND_FLAGS, type ColorThemes, type Command, type CommandFlag } from './types'

// Command names contain spaces ("enso settings") and category names are
// user-chosen, so every interpolated path segment gets encoded. The old UI
// interpolated them raw, which Werkzeug tolerated but which broke for any
// name containing a character with URL meaning.
const enc = encodeURIComponent

/* ---------------------------------------------------------------- versions */

export const getEnsoVersion = () => getText('/api/enso/version')
export const getPythonVersion = () => getText('/api/python/version')

/* ------------------------------------------------------------------ config */

export const getConfig = (key: string) => getText(`/api/enso/get/config/${enc(key)}`)

// `value` travels in the body, not the path: a config value containing "/"
// would otherwise change which route matched.
export const setConfig = (key: string, value: string) =>
  post(`/api/enso/set/config/${enc(key)}`, { value })

export const getColorThemes = () => getJSON<ColorThemes>('/api/enso/color_themes')

export const getConfigDir = () => getText('/api/enso/get/config_dir')
export const openConfigDir = () => post('/api/enso/open/config_dir')

export const getEnsorc = () => getText('/api/enso/get/ensorc')
export const setEnsorc = (ensorc: string) => post('/api/enso/set/ensorc', { ensorc })

/* ----------------------------------------------------------------- retreat */

export const getRetreatInstalled = async () => Boolean(await getText('/api/retreat/installed'))
export const showRetreatOptions = () => post('/api/retreat/show_options')

/* ---------------------------------------------------------------- commands */

export const getCommands = () => getJSON<Command[]>('/api/enso/get/commands')
export const getVoiceAvailable = () => getJSON<boolean>('/api/enso/voice/available')

export const setCommandFlag = (flag: CommandFlag, name: string, on: boolean) =>
  post(`/api/enso/${COMMAND_FLAGS[flag]}/${on ? 'enable' : 'disable'}/${enc(name)}`)

/* -------------------------------------------------------------- categories */

export const getCategories = () => getJSON<string[]>('/api/enso/get/user_command_categories')

export const readCategory = (category: string) =>
  getText(`/api/enso/commands/read_category/${enc(category)}`)

export const writeCategory = (category: string, code: string) =>
  post(`/api/enso/commands/write_category/${enc(category)}`, { code })

export const deleteCategory = (category: string) =>
  post(`/api/enso/commands/delete_category/${enc(category)}`)

/* ------------------------------------------------------------------- tasks */

export const readTasks = () => getText('/api/enso/read_tasks')
export const writeTasks = (code: string) => post('/api/enso/write_tasks', { code })
