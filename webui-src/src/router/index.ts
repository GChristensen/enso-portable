import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// Views are imported statically so they all land in the single app bundle.
// The one thing kept out of it is the code editor, which drags in ace (by far
// the largest dependency) and is loaded on demand from the views that use it.
import AboutView from '@/views/AboutView.vue'
import ApiRefView from '@/views/ApiRefView.vue'
import CommandsView from '@/views/CommandsView.vue'
import EditorView from '@/views/EditorView.vue'
import SettingsView from '@/views/SettingsView.vue'
import TasksView from '@/views/TasksView.vue'
import TutorialView from '@/views/TutorialView.vue'

/**
 * Route paths are also the nav order.
 *
 * The API-reference page is at /api-ref rather than /api on purpose: /api
 * would sit directly on top of the /api/... endpoint namespace, and a typo'd
 * endpoint could then be answered with the SPA shell instead of a 404.
 */
const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/settings' },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: { title: 'Settings' },
  },
  {
    path: '/commands',
    name: 'commands',
    component: CommandsView,
    meta: { title: 'Your Commands' },
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: TasksView,
    meta: { title: 'Tasks' },
  },
  {
    path: '/editor',
    name: 'editor',
    component: EditorView,
    meta: { title: 'Command Editor' },
  },
  {
    path: '/api-ref',
    name: 'api-ref',
    component: ApiRefView,
    meta: { title: 'API Reference' },
  },
  {
    path: '/tutorial',
    name: 'tutorial',
    component: TutorialView,
    meta: { title: 'Tutorial' },
  },
  {
    path: '/about',
    name: 'about',
    component: AboutView,
    meta: { title: 'About' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/settings' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  // Hash targets are handled by StaticDoc, which has to wait for its v-html
  // content to exist before the element can be scrolled to.
  scrollBehavior: (to) => (to.hash ? false : { top: 0 }),
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `Enso: ${title}` : 'Enso'
})
