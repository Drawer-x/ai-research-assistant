<template>
  <div id="app">
    <NavBar v-if="showNavbar" />
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'

const route = useRoute()
const showNavbar = computed(() => {
  return !['/login', '/register'].includes(route.path)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f4f9;
  color: #1a2332;
  -webkit-font-smoothing: antialiased;
}
#app {
  min-height: 100vh;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: #f0f2f5;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb {
  background: #c1c7d0;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #a0a7b0;
}

.el-button {
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.25s ease !important;
}
.el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
}
.el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.35);
}

.el-input__wrapper {
  border-radius: 10px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
  transition: box-shadow 0.3s ease !important;
}
.el-input__wrapper:hover {
  box-shadow: 0 1px 6px rgba(102, 126, 234, 0.15) !important;
}
.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15), 0 1px 6px rgba(102, 126, 234, 0.10) !important;
}
</style>