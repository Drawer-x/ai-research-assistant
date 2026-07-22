<template>
  <div class="detail-container" v-loading="pageLoading">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </span>
        <span class="title-text">论文详情</span>
      </h1>
      <p class="page-desc">查看论文完整信息，AI 智能分析与问答</p>
    </div>

    <!-- ===== 返回按钮 ===== -->
    <div class="detail-nav">
      <button class="back-btn" @click="$router.back()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        返回文献列表
      </button>
    </div>

    <!-- ===== 论文信息卡片 ===== -->
    <div class="detail-card">
      <div v-if="paper" class="paper-info">
        <h2 class="paper-title">{{ paper.title || '未命名论文' }}</h2>
        <div class="paper-meta">
          <span class="meta-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            {{ paper.authors || '未知作者' }}
          </span>
          <span class="meta-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {{ paper.year || '未知年份' }}
          </span>
          <span 
            class="status-tag" 
            :class="{
              'status-read': getDisplayStatus(paper.status) === '已读',
              'status-reading': getDisplayStatus(paper.status) === '在读',
              'status-unread': getDisplayStatus(paper.status) === '未读' || !paper.status
            }"
          >
            {{ getDisplayStatus(paper.status) || '未读' }}
          </span>
        </div>
        <div class="paper-tags" v-if="paper.tags && paper.tags.length > 0">
          <span v-for="tag in paper.tags" :key="tag" class="tag-item">#{{ tag }}</span>
        </div>
        <div class="paper-abstract">
          <h4>摘要</h4>
          <p>{{ paper.abstract || '暂无摘要' }}</p>
        </div>
      </div>
      <div v-else class="empty-paper">
        <span class="empty-icon">📄</span>
        <p>论文不存在或已被删除</p>
      </div>
    </div>

    <!-- ===== AI 总结区域 ===== -->
    <div class="summary-card">
      <div class="summary-header">
        <div class="summary-header-left">
          <span class="summary-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </span>
          <h3>AI 论文总结</h3>
          <span v-if="summary" class="summary-badge">已生成</span>
        </div>
        <button
          class="summary-btn"
          :class="{ loading: summaryLoading }"
          :disabled="summaryLoading || !paper"
          @click="generateSummary"
        >
          <span v-if="summaryLoading" class="btn-spinner"></span>
          <span v-else>{{ summary ? '重新生成' : '生成总结' }}</span>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="summaryLoading" class="summary-loading">
        <span class="loading-spinner"></span>
        <span>AI 正在深度阅读论文，请稍候...</span>
        <span class="loading-hint">这可能需要 30-60 秒</span>
      </div>

      <!-- 总结内容 -->
      <div v-else-if="summary" class="summary-content">
        <div class="summary-grid">
          <div class="summary-item">
            <span class="summary-item-label">研究背景</span>
            <p>{{ summary.background || '暂无' }}</p>
          </div>
          <div class="summary-item">
            <span class="summary-item-label">研究问题</span>
            <p>{{ summary.problem || '暂无' }}</p>
          </div>
          <div class="summary-item">
            <span class="summary-item-label">核心方法</span>
            <p>{{ summary.method || '暂无' }}</p>
          </div>
          <div class="summary-item">
            <span class="summary-item-label">主要结论</span>
            <p>{{ summary.conclusion || '暂无' }}</p>
          </div>
          <div class="summary-item highlight">
            <span class="summary-item-label">创新点</span>
            <p>{{ summary.innovation || '暂无' }}</p>
          </div>
          <div class="summary-item warning">
            <span class="summary-item-label">局限性</span>
            <p>{{ summary.limitation || '暂无' }}</p>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="summary-empty">
        <span class="empty-icon">🤖</span>
        <p>点击「生成总结」按钮</p>
        <span class="empty-hint">AI 将为你深度分析这篇论文</span>
      </div>
    </div>

    <!-- ===== AI 问答区域 ===== -->
    <div class="qa-card">
      <div class="qa-header">
        <div class="qa-header-left">
          <span class="qa-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </span>
          <h3>论文问答</h3>
          <span v-if="qaHistory.length > 0" class="qa-badge">{{ qaHistory.length }} 个问答</span>
        </div>
      </div>

      <!-- 问答历史 -->
      <div v-if="qaHistory.length > 0" class="qa-history" ref="qaHistoryRef">
        <div v-for="(item, index) in qaHistory" :key="index" class="qa-item">
          <div class="qa-question">
            <span class="qa-avatar">Q</span>
            <span class="qa-text">{{ item.question }}</span>
          </div>
          <div class="qa-answer">
            <span class="qa-avatar">A</span>
            <span class="qa-text">{{ item.answer }}</span>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="qa-empty">
        <span class="empty-icon">💬</span>
        <p>还没有提问</p>
        <span class="empty-hint">输入问题，AI 将基于论文内容为你解答</span>
      </div>

      <!-- 输入区 -->
      <div class="qa-input">
        <input
          v-model="question"
          class="qa-input-field"
          placeholder="输入你想问的问题..."
          :disabled="qaLoading || !paper"
          @keyup.enter="askQuestion"
        />
        <button
          class="qa-submit-btn"
          :disabled="!paper || !question.trim() || qaLoading"
          @click="askQuestion"
        >
          <span v-if="qaLoading" class="btn-spinner"></span>
          <span v-else>提问</span>
        </button>
      </div>

      <!-- 快捷提问 -->
      <div v-if="quickQuestions.length > 0 && qaHistory.length === 0" class="qa-quick">
        <span class="quick-label">快速提问：</span>
        <button
          v-for="q in quickQuestions"
          :key="q"
          class="quick-tag"
          @click="question = q; askQuestion()"
        >
          {{ q }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const route = useRoute()
const router = useRouter()

// ===== 状态映射 =====
const displayStatusMap = {
  'unread': '未读',
  'rough_read': '在读',
  'intensive_read': '已读',
  'to_reproduce': '待复现',
  'for_review': '待评审',
  'archived': '已归档'
}

// ===== 获取显示状态 =====
const getDisplayStatus = (status) => {
  if (!status) return '未读'
  return displayStatusMap[status] || status
}

// ===== 安全获取论文 ID =====
const paperId = computed(() => {
  if (route.params.id) return route.params.id
  const match = route.path.match(/\/papers\/(\d+)/)
  if (match) return match[1]
  if (route.query.id) return route.query.id
  return null
})

// ===== 状态 =====
const pageLoading = ref(false)
const paper = ref(null)
const summary = ref(null)
const summaryLoading = ref(false)
const question = ref('')
const qaLoading = ref(false)
const qaHistory = ref([])
const qaHistoryRef = ref(null)

const quickQuestions = [
  '这篇论文主要解决了什么问题？',
  '用了什么方法和模型？',
  '实验用了什么数据集？',
  '主要结论是什么？',
  '有什么创新点？'
]

// ===== 获取论文详情 =====
const fetchPaperDetail = async () => {
  const id = paperId.value
  if (!id) {
    ElMessage.error('论文 ID 不存在')
    return
  }

  pageLoading.value = true
  try {
    const res = await axios.get(`/api/papers/${id}`)
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data
      paper.value = {
        ...data,
        id: data.paper_id || data.id,
        tags: data.tags || data.tag_list || []
      }
    } else {
      ElMessage.error(res.data.message || '获取论文详情失败')
    }
  } catch (error) {
    console.error('获取论文详情失败:', error)
    ElMessage.error(error.response?.data?.message || '获取论文详情失败')
  } finally {
    pageLoading.value = false
  }
}

// ===== AI 总结 =====
const generateSummary = async () => {
  const id = paperId.value
  if (!paper.value) {
    ElMessage.warning('请先加载论文')
    return
  }

  summaryLoading.value = true
  ElMessage.info({
    message: 'AI 正在深度阅读论文，预计需要 30-60 秒...',
    duration: 5000
  })

  try {
    const res = await axios.post(`/api/papers/${id}/summary`, {}, {
      timeout: 120000
    })
    if (res.data.code === 200 || res.data.code === 0) {
      summary.value = res.data.data
      ElMessage.success('AI 总结生成成功！')
    } else {
      ElMessage.error(res.data.message || '生成总结失败')
      loadMockSummary()
    }
  } catch (error) {
    console.error('生成总结失败:', error)
    if (error.code === 'ECONNABORTED') {
      ElMessage.warning('AI 响应超时，请稍后重试或使用示例数据')
    } else {
      ElMessage.warning('使用示例数据展示效果')
    }
    loadMockSummary()
  } finally {
    summaryLoading.value = false
  }
}

const loadMockSummary = () => {
  summary.value = {
    background: '近年来，深度学习在自然语言处理领域取得了显著进展，但传统的序列建模方法仍面临并行计算效率低和长距离依赖捕捉困难的问题。',
    problem: '如何设计一种能够高效并行计算且能有效捕捉长距离依赖的序列建模架构？',
    method: '提出了 Transformer 架构，核心是自注意力机制和多头注意力，完全摒弃了 RNN 和 CNN。',
    conclusion: '在 WMT 2014 英德翻译任务上达到 28.4 BLEU，比之前最好的结果提高了 2 BLEU 以上。',
    innovation: '1) 首次提出完全基于注意力的序列模型；2) 多头注意力机制捕捉不同子空间的特征。',
    limitation: '计算复杂度随序列长度平方增长，在处理超长序列时内存消耗大。'
  }
}

// ===== AI 问答 =====
const askQuestion = async () => {
  const id = paperId.value
  if (!paper.value) {
    ElMessage.warning('请先加载论文')
    return
  }

  const q = question.value.trim()
  if (!q) {
    ElMessage.warning('请输入问题')
    return
  }

  qaLoading.value = true
  try {
    const res = await axios.post(`/api/papers/${id}/qa`, { question: q }, {
      timeout: 60000
    })
    if (res.data.code === 200 || res.data.code === 0) {
      qaHistory.value.push({
        question: q,
        answer: res.data.data.answer || '暂无回答'
      })
      question.value = ''
      await nextTick()
      scrollToBottom()
    } else {
      ElMessage.error(res.data.message || '问答失败')
      addMockAnswer(q)
    }
  } catch (error) {
    console.error('问答失败:', error)
    addMockAnswer(q)
    ElMessage.warning('使用示例回答展示效果')
  } finally {
    qaLoading.value = false
  }
}

const addMockAnswer = (q) => {
  const mockAnswers = [
    '根据论文内容，该研究主要关注序列建模与机器翻译任务，提出了基于自注意力机制的 Transformer 架构。',
    '论文使用了 WMT 2014 英德翻译数据集（约 450 万对句子）和英法翻译数据集（约 3600 万对句子）。',
    '主要的创新点包括：1) 完全基于注意力的架构；2) 多头注意力机制；3) 位置编码处理序列顺序。',
    '实验结果表明，Transformer 在 WMT 2014 英德翻译上达到 28.4 BLEU，训练时间大幅减少。',
    '该架构为 BERT、GPT 等后续大模型奠定了基础。'
  ]
  qaHistory.value.push({
    question: q,
    answer: mockAnswers[qaHistory.value.length % mockAnswers.length]
  })
  question.value = ''
  setTimeout(() => {
    scrollToBottom()
  }, 100)
}

const scrollToBottom = () => {
  if (qaHistoryRef.value) {
    qaHistoryRef.value.scrollTop = qaHistoryRef.value.scrollHeight
  }
}

// ===== 监听 ID 变化，重新获取详情 =====
watch(
  () => route.params.id,
  () => {
    fetchPaperDetail()
  },
  { immediate: true }
)

onMounted(() => {
  fetchPaperDetail()
})
</script>

<style scoped>
.detail-container {
  padding: 24px 20px;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.04) 0%, transparent 50%);
}

.page-header {
  margin-bottom: 20px;
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

.page-desc {
  color: var(--text-muted);
  font-size: 15px;
  margin: 0;
}

.detail-nav {
  margin-bottom: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(-4px);
}

.back-btn svg {
  stroke: currentColor;
}

.detail-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.paper-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.meta-item svg {
  stroke: var(--text-muted);
}

.status-tag {
  padding: 2px 14px;
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 500;
}

.status-read {
  background: rgba(123, 200, 164, 0.15);
  color: #2d7a5a;
}
.status-reading {
  background: rgba(95, 195, 228, 0.15);
  color: #2a7a9a;
}
.status-unread {
  background: rgba(200, 210, 220, 0.2);
  color: var(--text-muted);
}

.paper-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.tag-item {
  padding: 2px 14px;
  border-radius: var(--radius-full);
  background: rgba(95, 195, 228, 0.06);
  color: var(--primary-500);
  font-size: 13px;
  font-weight: 500;
}

.paper-abstract h4 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 6px 0;
}

.paper-abstract p {
  color: var(--text-secondary);
  line-height: 1.8;
  font-size: 14px;
  margin: 0;
}

.empty-paper {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted);
}

.empty-paper .empty-icon {
  font-size: 40px;
  display: block;
  margin-bottom: 8px;
}

.summary-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--primary-gradient);
  color: #fff;
}

.summary-icon svg {
  stroke: #fff;
}

.summary-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.summary-badge {
  font-size: 11px;
  font-weight: 600;
  color: #4a9a7a;
  background: rgba(123, 200, 164, 0.12);
  padding: 2px 12px;
  border-radius: var(--radius-full);
}

.summary-btn {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 12px rgba(95, 195, 228, 0.2);
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 90px;
  justify-content: center;
}

.summary-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(95, 195, 228, 0.3);
}

.summary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.summary-btn.loading {
  opacity: 0.7;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.summary-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 30px 0;
  color: var(--text-muted);
}

.summary-loading .loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(95, 195, 228, 0.1);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-hint {
  font-size: 13px;
  color: var(--text-muted);
  opacity: 0.7;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.summary-item {
  padding: 14px 18px;
  background: rgba(248, 250, 255, 0.6);
  border-radius: var(--radius-md);
}

.summary-item-label {
  display: block;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 2px;
}

.summary-item p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}

.summary-item.highlight {
  background: rgba(95, 195, 228, 0.06);
  border: 1px solid rgba(95, 195, 228, 0.1);
}

.summary-item.warning {
  background: rgba(245, 160, 160, 0.06);
  border: 1px solid rgba(245, 160, 160, 0.1);
}

.summary-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--text-muted);
}

.summary-empty .empty-icon {
  font-size: 36px;
  display: block;
  margin-bottom: 4px;
}

.summary-empty p {
  margin: 0;
  font-size: 15px;
}

.summary-empty .empty-hint {
  font-size: 13px;
  opacity: 0.7;
}

.qa-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.qa-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qa-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--primary-gradient);
  color: #fff;
}

.qa-icon svg {
  stroke: #fff;
}

.qa-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.qa-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--primary-500);
  background: rgba(95, 195, 228, 0.08);
  padding: 2px 12px;
  border-radius: var(--radius-full);
}

.qa-history {
  max-height: 350px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.qa-item {
  margin-bottom: 12px;
}

.qa-item:last-child {
  margin-bottom: 0;
}

.qa-question {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(95, 195, 228, 0.06);
  border-radius: var(--radius-md) var(--radius-md) 4px var(--radius-md);
}

.qa-answer {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(248, 250, 255, 0.6);
  border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
  margin-top: 4px;
}

.qa-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.qa-question .qa-avatar {
  background: var(--primary-gradient);
}

.qa-answer .qa-avatar {
  background: linear-gradient(135deg, #7bc8a4, #5cb88a);
}

.qa-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.qa-empty {
  text-align: center;
  padding: 16px 0;
  color: var(--text-muted);
}

.qa-empty .empty-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 4px;
}

.qa-empty p {
  margin: 0;
  font-size: 15px;
}

.qa-empty .empty-hint {
  font-size: 13px;
  opacity: 0.7;
}

.qa-input {
  display: flex;
  gap: 10px;
}

.qa-input-field {
  flex: 1;
  padding: 10px 16px;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-family: inherit;
  transition: all 0.3s ease;
  outline: none;
}

.qa-input-field:hover {
  background: #ffffff;
  border-color: rgba(95, 195, 228, 0.2);
}

.qa-input-field:focus {
  background: #ffffff;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 4px rgba(95, 195, 228, 0.08);
}

.qa-input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qa-submit-btn {
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 12px rgba(95, 195, 228, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
}

.qa-submit-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(95, 195, 228, 0.3);
}

.qa-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.qa-quick {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}

.quick-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-right: 4px;
}

.quick-tag {
  padding: 4px 14px;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(248, 250, 255, 0.6);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-tag:hover {
  background: rgba(95, 195, 228, 0.08);
  color: var(--primary-500);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .detail-container { padding: 16px 12px; }
  .page-title { font-size: 22px; }
  .title-icon { width: 38px; height: 38px; }
  .title-icon svg { width: 20px; height: 20px; }
  .detail-card, .summary-card, .qa-card { padding: 18px 16px; }
  .paper-title { font-size: 20px; }
  .summary-grid { grid-template-columns: 1fr; }
  .summary-header { flex-direction: column; gap: 12px; align-items: flex-start; }
  .qa-input { flex-direction: column; }
  .qa-submit-btn { width: 100%; padding: 12px; }
}

@media (max-width: 480px) {
  .paper-title { font-size: 18px; }
  .paper-meta { gap: 10px; }
  .meta-item { font-size: 13px; }
  .summary-item { padding: 10px 14px; }
  .qa-quick { flex-direction: column; align-items: flex-start; }
}
</style>