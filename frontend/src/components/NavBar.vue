<template>
  <header class="navbar">
    <div class="navbar-left">
      <span class="navbar-logo" @click="$router.push('/papers')">
        📚 AI 科研助手
      </span>
    </div>
    <div class="navbar-center">
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        router
        class="navbar-menu"
      >
        <el-menu-item index="/papers" :route="{ path: '/papers' }">
          <el-icon><Document /></el-icon> 文献库
        </el-menu-item>
        <el-menu-item index="/graph" :route="{ path: '/graph' }">
          <el-icon><Share /></el-icon> 关系图
        </el-menu-item>
        <el-menu-item index="/agent" :route="{ path: '/agent' }">
          <el-icon><Edit /></el-icon> Agent 规划
        </el-menu-item>
        <el-menu-item index="/review" :route="{ path: '/review' }">
          <el-icon><Edit /></el-icon> 综述辅助
        </el-menu-item>
      </el-menu>
    </div>
    <div class="navbar-right">
      <span class="navbar-user">
        <el-avatar :size="32" icon="UserFilled" />
        <span class="username">{{ username || '用户' }}</span>
      </span>
      <el-button type="text" @click="handleLogout" class="logout-btn">
        退出
      </el-button>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Share, Edit } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const username = ref('')

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  username.value = localStorage.getItem('username') || '用户'
})
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 40px;
  background: #ffffff;
  border-bottom: 1px solid #e8ecf1;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}
.navbar-left {
  display: flex;
  align-items: center;
}
.navbar-logo {
  font-size: 20px;
  font-weight: 700;
  color: #667eea;
  cursor: pointer;
  user-select: none;
  letter-spacing: -0.5px;
}
.navbar-logo:hover {
  color: #764ba2;
}
.navbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}
.navbar-menu {
  border-bottom: none !important;
}
.navbar-menu :deep(.el-menu-item) {
  font-weight: 500;
  color: #555;
  border-bottom: 2px solid transparent;
  transition: all 0.25s;
}
.navbar-menu :deep(.el-menu-item:hover) {
  color: #667eea;
}
.navbar-menu :deep(.el-menu-item.is-active) {
  color: #667eea;
  border-bottom-color: #667eea;
}
.navbar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 6px;
}
.navbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.navbar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: default;
}
.navbar-user .username {
  font-size: 14px;
  color: #333;
}
.logout-btn {
  color: #8c8f9c !important;
  font-weight: 500 !important;
  padding: 6px 12px !important;
}
.logout-btn:hover {
  color: #f56c6c !important;
}

@media (max-width: 768px) {
  .navbar { padding: 0 16px; }
  .navbar-center { display: none; }
  .navbar-logo { font-size: 16px; }
  .navbar-user .username { display: none; }
}
</style>