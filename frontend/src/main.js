import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import { ElMessage } from 'element-plus'
import { SuccessFilled, CircleCloseFilled, WarningFilled, InfoFilled } from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 配置 ElMessage 图标
ElMessage.success = (message, options = {}) => {
  return ElMessage({
    message,
    type: 'success',
    icon: SuccessFilled,
    ...options
  })
}

ElMessage.error = (message, options = {}) => {
  return ElMessage({
    message,
    type: 'error',
    icon: CircleCloseFilled,
    ...options
  })
}

ElMessage.warning = (message, options = {}) => {
  return ElMessage({
    message,
    type: 'warning',
    icon: WarningFilled,
    ...options
  })
}

ElMessage.info = (message, options = {}) => {
  return ElMessage({
    message,
    type: 'info',
    icon: InfoFilled,
    ...options
  })
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')