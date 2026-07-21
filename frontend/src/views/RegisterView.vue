<template>
  <div class="register-container">
    <!-- ===== 左侧品牌区 ===== -->
    <div class="register-brand">
      <div class="brand-content">
        <div class="brand-icon">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1 class="brand-title">AI 科研助手</h1>
        <p class="brand-desc">开始你的智能科研之旅</p>
        <div class="brand-features">
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>免费使用所有核心功能</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>无限制文献管理</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>AI 驱动的智能分析</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 右侧注册表单 ===== -->
    <div class="register-form-wrapper">
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
            <button
              class="register-btn"
              :disabled="loading"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '注 册' }}
            </button>
          </el-form-item>

          <div class="register-footer">
            <span>已有账号？</span>
            <span class="login-link" @click="$router.push('/login')">立即登录</span>
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

  try {
    await registerFormRef.value.validate()
  } catch {
    return
  }

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
    console.error('注册错误:', error)
    ElMessage.error(error.response?.data?.message || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ============================================================
   ===== 容器 =====
   ============================================================ */
.register-container {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.06) 0%, transparent 50%),
                    radial-gradient(ellipse at 90% 80%, rgba(123, 200, 164, 0.06) 0%, transparent 50%);
}

/* ============================================================
   ===== 左侧品牌区 =====
   ============================================================ */
.register-brand {
  flex: 1.2;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  background: var(--primary-gradient);
  position: relative;
  overflow: hidden;
}

.register-brand::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -20%;
  width: 80%;
  height: 80%;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 50%;
}

.register-brand::after {
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
  display: flex;
  flex-direction: column;
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
   ===== 右侧注册表单 =====
   ============================================================ */
.register-form-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
}

.register-card {
  width: 100%;
  max-width: 400px;
  padding: 20px 0;
}

.register-welcome {
  margin-bottom: 32px;
  text-align: center;
}

.register-welcome h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.register-welcome p {
  color: var(--text-muted);
  font-size: 15px;
}

/* ===== 表单 ===== */
.register-form .register-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.7);
  border: 2px solid transparent;
  transition: all 0.3s ease;
  height: 48px;
  padding: 0 16px;
}

.register-form .register-input :deep(.el-input__wrapper:hover) {
  background: #ffffff;
  border-color: rgba(95, 195, 228, 0.2);
}

.register-form .register-input :deep(.el-input__wrapper.is-focus) {
  background: #ffffff;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 4px rgba(95, 195, 228, 0.08);
}

/* ===== 注册按钮 ===== */
.register-btn {
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

.register-btn:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 32px rgba(95, 195, 228, 0.35);
}

.register-btn:active:not(:disabled) {
  transform: scale(0.97);
}

.register-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* ===== 底部 ===== */
.register-footer {
  text-align: center;
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}

.login-link {
  color: var(--primary-500);
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease;
}

.login-link:hover {
  color: var(--primary-600);
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 900px) {
  .register-brand {
    display: none;
  }

  .register-form-wrapper {
    flex: 1;
    background: var(--bg-primary);
    padding: 24px;
  }

  .register-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    padding: 32px 24px;
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-md);
    border: 1px solid rgba(255, 255, 255, 0.6);
  }

  .register-welcome h2 {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .register-form-wrapper {
    padding: 16px;
  }

  .register-card {
    padding: 24px 16px;
  }

  .register-welcome h2 {
    font-size: 22px;
  }

  .register-btn {
    height: 44px;
    font-size: 15px;
  }
}
</style>