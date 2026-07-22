<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="not-found-icon">
        <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h1 class="not-found-title">404</h1>
      <p class="not-found-desc">页面走丢了</p>
      <p class="not-found-hint">你访问的页面可能已被删除或地址有误</p>
      <button class="not-found-btn" @click="$router.push('/papers')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        返回文献库
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ============================================================
   ===== 404 页面 =====
   ============================================================ */
.not-found-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 20% 30%, rgba(95, 195, 228, 0.04) 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 70%, rgba(123, 200, 164, 0.04) 0%, transparent 60%);
  padding: 24px;
}

.not-found-content {
  text-align: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-lg);
  max-width: 480px;
  width: 100%;
}

.not-found-icon {
  color: var(--text-muted);
  margin-bottom: 16px;
  opacity: 0.5;
}

.not-found-icon svg {
  stroke: var(--text-muted);
}

.not-found-title {
  font-size: 72px;
  font-weight: 800;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1;
}

.not-found-desc {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 12px 0 6px 0;
}

.not-found-hint {
  color: var(--text-muted);
  font-size: 15px;
  margin: 0 0 28px 0;
}

/* ===== 按钮 ===== */
.not-found-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 20px rgba(95, 195, 228, 0.25);
}

.not-found-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 32px rgba(95, 195, 228, 0.35);
}

.not-found-btn:active {
  transform: scale(0.96);
}

.not-found-btn svg {
  stroke: #fff;
  flex-shrink: 0;
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 480px) {
  .not-found-content {
    padding: 28px 20px;
  }

  .not-found-title {
    font-size: 56px;
  }

  .not-found-desc {
    font-size: 18px;
  }

  .not-found-hint {
    font-size: 13px;
  }

  .not-found-btn {
    padding: 10px 24px;
    font-size: 14px;
  }

  .not-found-icon svg {
    width: 80px;
    height: 80px;
  }
}
</style>