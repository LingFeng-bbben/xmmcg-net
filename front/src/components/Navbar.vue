<template>
  <el-menu
    :default-active="activeIndex"
    mode="horizontal"
    :ellipsis="false"
    @select="handleSelect"
    class="navbar"
  >
    <div class="logo">
      <el-icon size="24"><Trophy /></el-icon>
      <span class="logo-text">XMMCG</span>
    </div>
    
    <div class="flex-grow" />
    
    <el-menu-item index="/">首页</el-menu-item>
    
    <!-- 根据阶段权限动态显示菜单项 -->
    <el-menu-item 
      index="/songs"
      :disabled="!pageAccess.songs"
      :class="{ 'disabled-menu-item': !pageAccess.songs }"
    >
      歌曲
      <el-tooltip v-if="!pageAccess.songs" content="此功能在竞标期开放" placement="bottom">
        <el-icon size="16" style="margin-left: 4px;"><Warning /></el-icon>
      </el-tooltip>
    </el-menu-item>
    
    <el-menu-item 
      index="/charts"
      :disabled="!pageAccess.charts"
      :class="{ 'disabled-menu-item': !pageAccess.charts }"
    >
      谱面
      <el-tooltip v-if="!pageAccess.charts" content="此功能在制谱期开放" placement="bottom">
        <el-icon size="16" style="margin-left: 4px;"><Warning /></el-icon>
      </el-tooltip>
    </el-menu-item>
    
    <el-menu-item 
      index="/eval"
      :disabled="!pageAccess.eval"
      :class="{ 'disabled-menu-item': !pageAccess.eval }"
    >
      评分
      <el-tooltip v-if="!pageAccess.eval" content="此功能在互评期开放" placement="bottom">
        <el-icon size="16" style="margin-left: 4px;"><Warning /></el-icon>
      </el-tooltip>
    </el-menu-item>
    
    <div class="flex-grow" />
    
    <div v-if="!isLoggedIn" class="auth-buttons">
      <el-button type="primary" size="small" @click="$router.push('/login')">
        登录
      </el-button>
      <el-button type="success" size="small" @click="$router.push('/register')">
        注册
      </el-button>
    </div>
    
    <el-sub-menu v-else index="user" class="user-menu">
      <template #title>
        <el-icon><UserFilled /></el-icon>
        <span>{{ username }}</span>
      </template>
      <el-menu-item index="/profile">
        <el-icon><User /></el-icon>
        个人中心
      </el-menu-item>
      <el-menu-item @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出登录
      </el-menu-item>
    </el-sub-menu>
  </el-menu>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Trophy, UserFilled, User, SwitchButton, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useCurrentPhase } from '../router/index.js'

const router = useRouter()
const route = useRoute()

const activeIndex = ref('/')
const username = ref(localStorage.getItem('username') || '')
const isLoggedIn = computed(() => !!localStorage.getItem('token'))

const pageAccess = ref({
  home: true,
  songs: true,
  charts: true,
  eval: true,
  profile: true
})

// 监听路由变化，更新激活菜单项
watch(() => route.path, (newPath) => {
  activeIndex.value = newPath
}, { immediate: true })

const loadPhasePermissions = async () => {
  try {
    const phase = await useCurrentPhase()
    if (phase?.page_access) {
      pageAccess.value = phase.page_access
    }
  } catch (error) {
    console.error('加载阶段权限失败:', error)
  }
}

const handleSelect = (key) => {
  if (key !== 'user') {
    // 检查权限
    const routePermissions = {
      '/songs': pageAccess.value.songs,
      '/charts': pageAccess.value.charts,
      '/eval': pageAccess.value.eval,
      '/profile': pageAccess.value.profile
    }
    
    if (routePermissions[key] === false) {
      ElMessage.warning('此功能在当前阶段不可用')
      return
    }
    
    router.push(key)
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  username.value = ''
  ElMessage.success('已退出登录')
  router.push('/')
}

onMounted(() => {
  loadPhasePermissions()
  // 每 30 秒刷新权限
  setInterval(() => {
    loadPhasePermissions()
  }, 30000)
})
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
  cursor: pointer;
}

.logo-text {
  margin-left: 5px;
}

.flex-grow {
  flex-grow: 1;
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
}

.user-menu {
  margin-left: auto;
}

.disabled-menu-item {
  opacity: 0.6;
  cursor: not-allowed;
}

.disabled-menu-item:hover {
  background-color: transparent !important;
}

@media (max-width: 768px) {
  .logo-text {
    display: none;
  }
  
  .auth-buttons {
    gap: 5px;
    padding: 0 10px;
  }
}
</style>
