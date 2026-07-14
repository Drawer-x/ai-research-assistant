<template>
  <div class="login-container">
    <!-- 左侧装饰区域 -->
    <div class="login-left">
      <div class="login-left-content">
        <div class="logo-icon">📚</div>
        <h1 class="login-left-title">AI 科研文献分析平台</h1>
        <p class="login-left-desc">智能阅读 · 文献管理 · 科研规划</p>
        <div class="login-features">
          <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span>AI 自动总结论文</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">💬</span>
            <span>基于论文内容问答</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🔗</span>
            <span>文献关系图谱</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🎯</span>
            <span>Agent 科研规划</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="login-right">
      <div class="login-card">
        <div class="login-welcome">
          <h2>欢迎回来</h2>
          <p>登录以继续使用科研文献分析平台</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-width="0"
          @keyup.enter="handleLogin"
          class="login-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              prefix-icon="User"
              class="login-input"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              prefix-icon="Lock"
              show-password
              class="login-input"
            />
          </el-form-item>

          <div class="login-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" :underline="'never'">忘记密码？</el-link>
          </div>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              style="width: 100%; height: 48px; font-size: 16px; border-radius: 10px;"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>

          <div class="login-footer">
            <span>还没有账号？</span>
            <el-link type="primary" @click="$router.push('/register')" :underline="'never'">
              立即注册
            </el-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  console.log('1. 开始登录流程')
  
  if (!loginFormRef.value) {
    console.error('loginFormRef 不存在')
    return
  }

  try {
    console.log('2. 开始表单验证')
    await loginFormRef.value.validate()
    console.log('3. 表单验证通过')
  } catch (error) {
    console.log('3. 表单验证失败', error)
    return
  }

  loading.value = true
  console.log('4. 发送登录请求，用户名:', loginForm.username)
  
  try {
    // 尝试 POST 请求
    const response = await axios.post('/api/auth/login', {
      username: loginForm.username,
      password: loginForm.password
    })

    console.log('5. 收到登录响应:', response.data)

    if (response.data.code === 200) {
      console.log('6. 登录成功，保存 token')
      ElMessage.success('登录成功！')
      localStorage.setItem('token', response.data.data.access_token)
      if (rememberMe.value) {
        localStorage.setItem('remember_me', 'true')
      }
      console.log('7. 准备跳转到 /papers')
      router.replace('/papers')
      console.log('8. 跳转命令已执行')
    } else {
      console.log('6. 登录失败:', response.data.message)
      ElMessage.error(response.data.message || '登录失败')
    }
  } catch (error) {
    console.error('登录错误:', error)
    ElMessage.error(error.response?.data?.message || '登录失败，请检查网络或账号密码')
  } finally {
    loading.value = false
    console.log('9. 登录流程结束')
  }
}
</script>

<style scoped>
/* ===== 整体布局 ===== */
.login-container {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

/* ===== 左侧装饰区 ===== */
.login-left {
  flex: 1.2;
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  position: relative;
  overflow: hidden;
}

.login-left::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -20%;
  width: 80%;
  height: 80%;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  pointer-events: none;
}

.login-left::after {
  content: '';
  position: absolute;
  bottom: -20%;
  left: -10%;
  width: 60%;
  height: 60%;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 50%;
  pointer-events: none;
}

.login-left-content {
  position: relative;
  z-index: 1;
  color: #fff;
  max-width: 460px;
}

.logo-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.login-left-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.login-left-desc {
  font-size: 18px;
  opacity: 0.85;
  margin-bottom: 40px;
  font-weight: 300;
}

.login-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  font-size: 14px;
  font-weight: 400;
  transition: background 0.3s;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.2);
}

.feature-icon {
  font-size: 20px;
}

/* ===== 右侧登录区 ===== */
.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 20px 0;
}

.login-welcome {
  margin-bottom: 36px;
}

.login-welcome h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a2332;
  margin-bottom: 8px;
}

.login-welcome p {
  color: #8c8f9c;
  font-size: 15px;
}

.login-form .login-input {
  border-radius: 10px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 4px 16px;
  height: 48px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 1px 6px rgba(102, 126, 234, 0.15);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15), 0 1px 6px rgba(102, 126, 234, 0.1);
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.login-options :deep(.el-checkbox__label) {
  font-size: 14px;
  color: #666;
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: #8c8f9c;
  margin-top: 4px;
}

.login-footer .el-link {
  font-weight: 500;
}

/* ===== 响应式适配 ===== */
@media (max-width: 900px) {
  .login-left {
    display: none;
  }
  .login-right {
    flex: 1;
    background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
  }
  .login-card {
    background: #fff;
    padding: 40px 32px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  }
  .login-welcome h2 {
    color: #1a2332;
  }
  .login-welcome p {
    color: #8c8f9c;
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 24px 20px;
  }
  .login-welcome h2 {
    font-size: 22px;
  }
  .login-features {
    grid-template-columns: 1fr;
  }
}
</style>