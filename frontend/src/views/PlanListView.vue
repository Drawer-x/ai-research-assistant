<template>
  <div class="plan-list-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </span>
        <span class="title-text">科研计划列表</span>
        <span class="title-badge">{{ plans.length }} 个</span>
      </h1>
      <p class="page-desc">查看所有已保存的科研计划</p>
    </div>

    <!-- ===== 加载状态 ===== -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span>加载中...</span>
    </div>

    <!-- ===== 计划列表 ===== -->
    <div v-else-if="plans.length > 0" class="plan-list">
      <div
        v-for="plan in plans"
        :key="plan.plan_id || plan.id"
        class="plan-item"
        @click="goToDetail(plan.plan_id || plan.id)"
      >
        <div class="plan-item-left">
          <div class="plan-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="plan-content">
            <h3 class="plan-title">{{ plan.topic }}</h3>
            <div class="plan-meta">
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                {{ formatDate(plan.created_at) }}
              </span>
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ plan.total_weeks || plan.duration_weeks + ' 周' }}
              </span>
              <span class="meta-tag">{{ plan.stages?.length || 0 }} 个阶段</span>
            </div>
          </div>
        </div>
        <div class="plan-item-right">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
      </div>
      <h3>还没有科研计划</h3>
      <p>去 Agent 页面生成你的第一个科研计划</p>
      <button class="btn-primary" @click="$router.push('/agent')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
        去生成计划
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const router = useRouter()
const loading = ref(false)
const plans = ref([])

// ===== 加载计划列表 =====
const loadPlans = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/agent/research-plans')
    if (res.data.code === 200 || res.data.code === 0) {
      plans.value = res.data.data || []
      if (plans.value.length === 0) {
        ElMessage.info('暂无科研计划')
      }
    } else {
      ElMessage.warning(res.data.message || '加载失败，使用示例数据')
      loadMockPlans()
    }
  } catch (error) {
    console.warn('加载计划列表失败，使用示例数据:', error)
    loadMockPlans()
  } finally {
    loading.value = false
  }
}

// ===== Mock 数据 =====
const loadMockPlans = () => {
  plans.value = [
    {
      plan_id: 1,
      topic: '时间序列预测中的 Transformer 方法',
      total_weeks: '4 周',
      stages: [{ name: '基础学习' }, { name: '文献调研' }],
      created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      plan_id: 2,
      topic: '图神经网络在药物分子性质预测中的应用',
      total_weeks: '6 周',
      stages: [{ name: 'GNN 基础' }, { name: '模型复现' }, { name: '论文撰写' }],
      created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      plan_id: 3,
      topic: '大语言模型在医疗问答中的应用',
      total_weeks: '5 周',
      stages: [{ name: 'LLM 基础' }, { name: '微调实验' }, { name: '评估' }],
      created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
    }
  ]
}

// ===== 格式化日期 =====
const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

// ===== 跳转到详情 =====
const goToDetail = (id) => {
  router.push(`/plans/${id}`)
}

onMounted(() => {
  loadPlans()
})
</script>

<style scoped>
/* ============================================================
   ===== 容器 =====
   ============================================================ */
.plan-list-container {
  padding: 24px 20px;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.04) 0%, transparent 50%);
}

/* ============================================================
   ===== 顶部 =====
   ============================================================ */
.page-header {
  margin-bottom: 28px;
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  background: var(--primary-gradient);
  color: #fff;
  flex-shrink: 0;
}

.title-icon svg {
  stroke: #fff;
}

.title-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-badge {
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  background: var(--primary-gradient);
  padding: 4px 16px;
  border-radius: var(--radius-full);
  -webkit-text-fill-color: #fff;
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.2);
}

.page-desc {
  color: var(--text-muted);
  font-size: 15px;
  margin: 0;
}

/* ============================================================
   ===== 加载状态 =====
   ============================================================ */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--text-muted);
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(95, 195, 228, 0.1);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ============================================================
   ===== 计划列表 =====
   ============================================================ */
.plan-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.plan-item:hover {
  transform: translateX(6px);
  box-shadow: var(--shadow-md);
  border-color: rgba(95, 195, 228, 0.2);
}

.plan-item-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.plan-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: rgba(95, 195, 228, 0.08);
  color: var(--primary-500);
  flex-shrink: 0;
}

.plan-icon svg {
  stroke: currentColor;
}

.plan-content {
  flex: 1;
  min-width: 0;
}

.plan-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  line-height: 1.4;
}

.plan-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.meta-item svg {
  stroke: currentColor;
}

.meta-tag {
  font-size: 12px;
  font-weight: 500;
  color: var(--primary-500);
  background: rgba(95, 195, 228, 0.08);
  padding: 2px 12px;
  border-radius: var(--radius-full);
}

.plan-item-right {
  color: var(--text-muted);
  transition: color 0.2s ease;
  flex-shrink: 0;
}

.plan-item-right svg {
  stroke: currentColor;
}

.plan-item:hover .plan-item-right {
  color: var(--primary-500);
}

/* ============================================================
   ===== 空状态 =====
   ============================================================ */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.empty-icon {
  color: var(--text-muted);
  opacity: 0.4;
  margin-bottom: 12px;
}

.empty-icon svg {
  stroke: currentColor;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.empty-state p {
  color: var(--text-muted);
  margin: 0 0 20px 0;
  font-size: 15px;
}

/* ============================================================
   ===== 按钮 =====
   ============================================================ */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 28px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.2);
}

.btn-primary:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(95, 195, 228, 0.3);
}

.btn-primary:active {
  transform: scale(0.96);
}

.btn-primary svg {
  stroke: #fff;
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 768px) {
  .plan-list-container {
    padding: 16px 12px;
  }

  .page-title {
    font-size: 22px;
  }

  .title-icon {
    width: 38px;
    height: 38px;
  }

  .title-icon svg {
    width: 20px;
    height: 20px;
  }

  .title-badge {
    font-size: 10px;
    padding: 2px 12px;
  }

  .plan-item {
    padding: 14px 16px;
  }

  .plan-title {
    font-size: 14px;
  }

  .plan-meta {
    gap: 10px;
  }

  .meta-item {
    font-size: 12px;
  }

  .plan-icon {
    width: 36px;
    height: 36px;
  }

  .plan-icon svg {
    width: 20px;
    height: 20px;
  }

  .empty-state {
    padding: 40px 16px;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 19px;
  }

  .title-icon {
    width: 32px;
    height: 32px;
  }

  .title-icon svg {
    width: 16px;
    height: 16px;
  }

  .plan-item-left {
    gap: 10px;
  }

  .plan-meta {
    flex-direction: column;
    gap: 4px;
  }

  .plan-item-right {
    display: none;
  }

  .empty-state h3 {
    font-size: 18px;
  }

  .empty-state p {
    font-size: 14px;
  }
}
</style>