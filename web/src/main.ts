import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { permissionDirectivePlugin } from './hooks'
import './styles/global.css'
import VXETable from 'vxe-table'
import VxeUIBase from 'vxe-pc-ui'
import 'vxe-table/lib/style.css'
import 'vxe-pc-ui/lib/style.css'

createApp(App).use(router).use(permissionDirectivePlugin).use(VXETable).use(VxeUIBase).mount('#app')