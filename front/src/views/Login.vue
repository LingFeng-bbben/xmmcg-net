<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>用户登录</h2>
        </div>
      </template>
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="rules" 
        label-width="80px"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading" 
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
        <el-form-item>
          <div class="login-footer">
            <span>还没有账号？</span>
            <el-link type="primary" @click="$router.push('/register')">
              立即注册
            </el-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { login } from '../api'

const router = useRouter()
const route = useRoute()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于 6 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const data = await login(loginForm.username, loginForm.password)

        // 调试：打印后端返回
        console.log('Login API response:', data)

        // 后端返回 {user: {...}}，无 token；用 session cookie 维持登录
        // 为了前端路由守卫简单，写入一个占位 token
        localStorage.setItem('token', 'session')
        localStorage.setItem('username', data.user?.username || loginForm.username)
        
        ElMessage.success('登录成功')
        //修改让重定向可以刷新页面。
        const redirectPath = route.query.redirect || '/profile'

        // 2. 为了兼容 Hash模式 (#/profile) 和 History模式 (/profile)
        // 使用 router.resolve 生成完整的 href (例如: http://localhost/#/profile)
        const { href } = router.resolve({ path: redirectPath })

        // 3. 使用原生 window.location 进行跳转，这会触发浏览器刷新
        window.location.href = href
        
        // // 跳转到之前的页面或个人中心
        // const redirect = route.query.redirect || '/profile'
        // router.push(redirect)
      } catch (error) {
        ElMessage.error(error.message || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
}

.card-header h2 {
  margin: 0;
  text-align: center;
  color: #303133;
}

.login-footer {
  width: 100%;
  text-align: center;
  font-size: 14px;
  color: #909399;
}

.login-footer span {
  margin-right: 5px;
}
</style>
