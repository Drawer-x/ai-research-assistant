<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="not-found-icon">🔍</div>
      <h1 class="not-found-title">404</h1>
      <p class="not-found-desc">页面不存在</p>
      <p class="not-found-hint">你访问的页面可能已被删除或地址有误</p>
      <el-button type="primary" @click="$router.push('/papers')" round>
        返回文献库
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f4f9;
}
.not-found-content {
  text-align: center;
  padding: 40px;
}
.not-found-icon {
  font-size: 72px;
  margin-bottom: 16px;
}
.not-found-title {
  font-size: 72px;
  font-weight: 700;
  color: #1a2332;
  margin: 0;
  line-height: 1;
}
.not-found-desc {
  font-size: 24px;
  font-weight: 500;
  color: #333;
  margin: 12px 0 8px;
}
.not-found-hint {
  color: #8c8f9c;
  margin-bottom: 24px;
}
</style>