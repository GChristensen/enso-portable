import { createApp } from 'vue'

import '@/assets/theme.css'
import '@/assets/base.css'

import App from './App.vue'
import { router } from './router'

createApp(App).use(router).mount('#app')
