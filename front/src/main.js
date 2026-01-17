import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/main.css'

const app = createApp(App)

// 配置 API 基础 URL（用于图片加载）
// 开发环境：http://localhost:8000
// 生产环境：同域名和协议
if (window.location.hostname === 'localhost' && window.location.port === '5173') {
  window.API_BASE_URL = 'http://localhost:8000'
} else {
  // 生产环境：使用相同的协议和域名
  window.API_BASE_URL = `${window.location.protocol}//${window.location.host}`
}

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
