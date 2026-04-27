import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { permissionDirectivePlugin } from './hooks'
import './styles/global.css'

createApp(App).use(router).use(permissionDirectivePlugin).mount('#app')