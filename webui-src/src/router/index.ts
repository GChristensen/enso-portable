import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

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
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: 'Settings' },
  },
  {
    path: '/commands',
    name: 'commands',
    component: () => import('@/views/CommandsView.vue'),
    meta: { title: 'Your Commands' },
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('@/views/TasksView.vue'),
    meta: { title: 'Tasks' },
  },
  {
    path: '/editor',
    name: 'editor',
    component: () => import('@/views/EditorView.vue'),
    meta: { title: 'Command Editor' },
  },
  {
    path: '/api-ref',
    name: 'api-ref',
    component: () => import('@/views/ApiRefView.vue'),
    meta: { title: 'API Reference' },
  },
  {
    path: '/tutorial',
    name: 'tutorial',
    component: () => import('@/views/TutorialView.vue'),
    meta: { title: 'Tutorial' },
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('@/views/AboutView.vue'),
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
