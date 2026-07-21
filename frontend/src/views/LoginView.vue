<template>
  <div class="login-container">
    <!-- 左侧品牌区 -->
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-icon">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1 class="brand-title">AI 科研助手</h1>
        <p class="brand-desc">智能阅读 · 文献管理 · 科研规划</p>
        <div class="brand-features">
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>AI 自动总结论文</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>基于论文内容问答</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>文献关系图谱</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>Agent 科研规划</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="login-form-wrapper">
      <div class="login-card">
        <div class="login-welcome">
          <h2>欢迎回来</h2>
          <p>登录以继续使用 AI 科研助手</p>
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
            <span class="forgot-link">忘记密码？</span>
          </div>

          <el-form-item>
            <button
              class="login-btn"
              :disabled="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </button>
          </el-form-item>

          <div class="login-footer">
            <span>还没有账号？</span>
            <span class="register-link" @click="$router.push('/register')">立即注册</span>
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
    { min: 3, max: 20, message: '用户名长度 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const res = await axios.post('/api/auth/login', {
      username: loginForm.username,
      password: loginForm.password
    })

    if (res.data.code === 200 || res.data.code === 0) {
      ElMessage.success('登录成功')
      localStorage.setItem('token', res.data.data.access_token || res.data.data.token)
      if (rememberMe.value) {
        localStorage.setItem('remember_me', 'true')
      }
      router.replace('/papers')
    } else {
      ElMessage.error(res.data.message || '登录失败')
    }
  } catch (error) {
    console.error('登录错误:', error)
    ElMessage.error(error.response?.data?.message || '登录失败，请检查网络')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ============================================================
   ===== 容器 =====
   ============================================================ */
.login-container {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.06) 0%, transparent 50%),
                    radial-gradient(ellipse at 90% 80%, rgba(123, 200, 164, 0.06) 0%, transparent 50%);
}

/* ============================================================
   ===== 左侧品牌区 =====
   ============================================================ */
.login-brand {
  flex: 1.2;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  background: var(--primary-gradient);
  position: relative;
  overflow: hidden;
}

.login-brand::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -20%;
  width: 80%;
  height: 80%;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 50%;
}

.login-brand::after {
  content: '';
  position: absolute;
  bottom: -20%;
  left: -10%;
  width: 60%;
  height: 60%;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 50%;
}

.brand-content {
  position: relative;
  z-index: 1;
  color: #fff;
  max-width: 420px;
}

.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  margin-bottom: 24px;
}

.brand-icon svg {
  stroke: #fff;
}

.brand-title {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.brand-desc {
  font-size: 18px;
  opacity: 0.8;
  font-weight: 300;
  margin-bottom: 40px;
}

.brand-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  backdrop-filter: blur(4px);
  font-size: 14px;
  font-weight: 400;
  transition: background 0.3s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.14);
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-icon svg {
  stroke: rgba(255, 255, 255, 0.7);
}

/* ============================================================
   ===== 右侧登录表单 =====
   ============================================================ */
.login-form-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 20px 0;
}

.login-welcome {
  margin-bottom: 32px;
  text-align: center;
}

.login-welcome h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.login-welcome p {
  color: var(--text-muted);
  font-size: 15px;
}

/* ===== 表单 ===== */
.login-form .login-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.7);
  border: 2px solid transparent;
  transition: all 0.3s ease;
  height: 48px;
  padding: 0 16px;
}

.login-form .login-input :deep(.el-input__wrapper:hover) {
  background: #ffffff;
  border-color: rgba(95, 195, 228, 0.2);
}

.login-form .login-input :deep(.el-input__wrapper.is-focus) {
  background: #ffffff;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 4px rgba(95, 195, 228, 0.08);
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.login-options :deep(.el-checkbox__label) {
  font-size: 14px;
  color: var(--text-secondary);
}

.forgot-link {
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s ease;
}

.forgot-link:hover {
  color: var(--primary-500);
}

/* ===== 登录按钮 ===== */
.login-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 20px rgba(95, 195, 228, 0.25);
  height: 48px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 32px rgba(95, 195, 228, 0.35);
}

.login-btn:active:not(:disabled) {
  transform: scale(0.97);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* ===== 底部 ===== */
.login-footer {
  text-align: center;
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}

.register-link {
  color: var(--primary-500);
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease;
}

.register-link:hover {
  color: var(--primary-600);
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 900px) {
  .login-brand {
    display: none;
  }

  .login-form-wrapper {
    flex: 1;
    background: var(--bg-primary);
    padding: 24px;
  }

  .login-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    padding: 32px 24px;
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-md);
    border: 1px solid rgba(255, 255, 255, 0.6);
  }

  .login-welcome h2 {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .login-form-wrapper {
    padding: 16px;
  }

  .login-card {
    padding: 24px 16px;
  }

  .login-welcome h2 {
    font-size: 22px;
  }

  .login-btn {
    height: 44px;
    font-size: 15px;
  }
}
</style>