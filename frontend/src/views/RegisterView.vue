<template>
  <div class="register-container">
    <div class="register-left">
      <div class="register-left-content">
        <div class="logo-icon">📚</div>
        <h1 class="register-left-title">AI 科研文献分析平台</h1>
        <p class="register-left-desc">开始你的智能科研之旅</p>
        <div class="register-features">
          <div class="feature-item">
            <span class="feature-icon">✅</span>
            <span>免费使用所有核心功能</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📄</span>
            <span>无限制文献管理</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <span>AI 驱动的智能分析</span>
          </div>
        </div>
      </div>
    </div>

    <div class="register-right">
      <div class="register-card">
        <div class="register-welcome">
          <h2>创建账号</h2>
          <p>免费注册，开始使用 AI 科研助手</p>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          label-width="0"
          class="register-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名（3-20个字符）"
              size="large"
              prefix-icon="User"
              class="register-input"
            />
          </el-form-item>

          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱"
              size="large"
              prefix-icon="Message"
              class="register-input"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码（6-20个字符）"
              size="large"
              prefix-icon="Lock"
              show-password
              class="register-input"
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              prefix-icon="Lock"
              show-password
              class="register-input"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              style="width: 100%; height: 48px; font-size: 16px; border-radius: 10px;"
              :loading="loading"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '注 册' }}
            </el-button>
          </el-form-item>

          <div class="register-footer">
            <span>已有账号？</span>
            <el-link type="primary" @click="$router.push('/login')" underline="never">
              立即登录
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
const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const res = await axios.post('/api/auth/register', {
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password
      })

      if (res.data.code === 200 || res.data.code === 0) {
        ElMessage.success('注册成功！请登录')
        router.push('/login')
      } else {
        ElMessage.error(res.data.message || '注册失败')
      }
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '注册失败，请重试')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-container {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

.register-left {
  flex: 1.2;
  background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  position: relative;
  overflow: hidden;
}

.register-left::before {
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

.register-left-content {
  position: relative;
  z-index: 1;
  color: #fff;
  max-width: 460px;
}

.logo-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.register-left-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.register-left-desc {
  font-size: 18px;
  opacity: 0.85;
  margin-bottom: 40px;
  font-weight: 300;
}

.register-features {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  font-size: 15px;
  font-weight: 400;
  transition: background 0.3s;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.2);
}

.feature-icon {
  font-size: 20px;
}

.register-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.register-card {
  width: 100%;
  max-width: 420px;
  padding: 20px 0;
}

.register-welcome {
  margin-bottom: 36px;
}

.register-welcome h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a2332;
  margin-bottom: 8px;
}

.register-welcome p {
  color: #8c8f9c;
  font-size: 15px;
}

.register-form .register-input {
  border-radius: 10px;
}

.register-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 4px 16px;
  height: 48px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s;
}

.register-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 1px 6px rgba(102, 126, 234, 0.15);
}

.register-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15), 0 1px 6px rgba(102, 126, 234, 0.1);
}

.register-footer {
  text-align: center;
  font-size: 14px;
  color: #8c8f9c;
  margin-top: 4px;
}

.register-footer .el-link {
  font-weight: 500;
}

@media (max-width: 900px) {
  .register-left {
    display: none;
  }
  .register-right {
    flex: 1;
    background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
  }
  .register-card {
    background: #fff;
    padding: 40px 32px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  }
  .register-welcome h2 {
    color: #1a2332;
  }
  .register-welcome p {
    color: #8c8f9c;
  }
}

@media (max-width: 480px) {
  .register-card {
    padding: 24px 20px;
  }
  .register-welcome h2 {
    font-size: 22px;
  }
}
</style>
