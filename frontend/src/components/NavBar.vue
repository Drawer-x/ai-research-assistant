<template>
  <header class="navbar">
    <div class="navbar-left">
      <span class="navbar-logo" @click="$router.push('/papers')">
        <span class="logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </span>
        <span class="logo-text">AI 科研助手</span>
      </span>
    </div>

    <div class="navbar-center">
      <nav class="nav-menu">
        <a
          v-for="item in menuItems"
          :key="item.path"
          class="nav-link"
          :class="{ active: activeMenu === item.path }"
          @click.prevent="$router.push(item.path)"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          {{ item.name }}
        </a>
      </nav>
    </div>

    <div class="navbar-right">
      <div class="user-avatar-wrapper" @click="toggleDropdown">
        <span class="user-avatar">{{ userInitial }}</span>
        <span class="username">{{ username || '用户' }}</span>
        <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </div>

      <transition name="dropdown">
        <div v-if="showDropdown" class="dropdown-menu">
          <div class="dropdown-item" @click="goToPlans">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            我的计划
          </div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item text-danger" @click="handleLogout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            退出登录
          </div>
        </div>
      </transition>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const username = ref('')
const showDropdown = ref(false)

// ===== 导航菜单项 =====
const menuItems = [
  { name: '文献库', path: '/papers', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>' },
  { name: '关系图', path: '/graph', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4" r="2"/><circle cx="4" cy="16" r="2"/><circle cx="20" cy="16" r="2"/><line x1="12" y1="6" x2="12" y2="10"/><line x1="6" y1="17" x2="10" y2="14"/><line x1="18" y1="17" x2="14" y2="14"/><line x1="12" y1="10" x2="10" y2="14"/><line x1="12" y1="10" x2="14" y2="14"/></svg>' },
  { name: 'Agent 规划', path: '/agent', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>' },
  { name: '综述辅助', path: '/review', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>' },
  { name: '计划列表', path: '/plans', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>' },
  { name: '论文发现', path: '/discovery', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>' },
  { name: '智能推荐', path: '/recommendations', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>' }
]

const activeMenu = computed(() => route.path)

const userInitial = computed(() => {
  return username.value ? username.value.charAt(0).toUpperCase() : 'U'
})

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

const goToPlans = () => {
  showDropdown.value = false
  router.push('/plans')
}

const handleLogout = () => {
  showDropdown.value = false
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  ElMessage.success('已退出登录')
  router.push('/login')
}

const handleClickOutside = (e) => {
  if (showDropdown.value && !e.target.closest('.navbar-right')) {
    showDropdown.value = false
  }
}

onMounted(() => {
  username.value = localStorage.getItem('username') || '用户'
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ============================================================
   ===== 导航栏 =====
   ============================================================ */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 72px;
  padding: 0 40px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 16px rgba(95, 195, 228, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}

/* ===== Logo ===== */
.navbar-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.navbar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  padding: 6px 14px;
  border-radius: var(--radius-lg);
  transition: all 0.2s ease;
}

.navbar-logo:hover {
  background: rgba(95, 195, 228, 0.06);
  transform: scale(1.02);
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(95, 195, 228, 0.25);
}

.logo-icon svg {
  stroke: #fff;
}

.logo-text {
  font-size: 20px;
  font-weight: 800;
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

/* ===== 导航菜单 ===== */
.navbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 2px;
  background: rgba(255, 255, 255, 0.4);
  padding: 4px;
  border-radius: var(--radius-xl);
  backdrop-filter: blur(8px);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  text-decoration: none;
  white-space: nowrap;
}

.nav-link .nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
}

.nav-link .nav-icon svg {
  stroke: currentColor;
}

.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.6);
  transform: translateY(-1px);
}

.nav-link.active {
  color: #5fc3e4;
  background: #ffffff;
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.10);
}

.nav-link.active .nav-icon {
  opacity: 1;
}

/* ===== 用户区域 ===== */
.navbar-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  position: relative;
}

.user-avatar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 16px 6px 6px;
  border-radius: var(--radius-full);
  transition: all 0.2s ease;
}

.user-avatar-wrapper:hover {
  background: rgba(255, 255, 255, 0.6);
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(95, 195, 228, 0.2);
}

.username {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
}

.dropdown-arrow {
  width: 18px;
  height: 18px;
  color: var(--text-muted);
  transition: transform 0.25s ease;
}

.user-avatar-wrapper:hover .dropdown-arrow {
  transform: rotate(180deg);
}

/* ===== 下拉菜单 ===== */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  min-width: 170px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  border-radius: var(--radius-lg);
  padding: 8px 0;
  box-shadow: 0 16px 48px rgba(95, 195, 228, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.dropdown-item:hover {
  background: rgba(95, 195, 228, 0.06);
  color: #5fc3e4;
}

.dropdown-item.text-danger {
  color: #f5a0a0;
}
.dropdown-item.text-danger:hover {
  background: rgba(245, 160, 160, 0.08);
  color: #c47a7a;
}

.dropdown-item svg {
  stroke: currentColor;
  flex-shrink: 0;
}

.dropdown-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.04);
  margin: 4px 12px;
}

/* ===== 过渡 ===== */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 900px) {
  .navbar {
    padding: 0 16px;
    height: 64px;
  }

  .navbar-center {
    display: none;
  }

  .logo-text {
    font-size: 16px;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
  }

  .logo-icon svg {
    width: 16px;
    height: 16px;
  }

  .username {
    display: none;
  }

  .dropdown-arrow {
    display: none;
  }

  .user-avatar-wrapper {
    padding: 4px;
  }
}
</style>
