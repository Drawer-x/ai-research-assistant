<template>
  <div class="recommendation-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </span>
        <span class="title-text">智能推荐</span>
        <span class="title-badge">{{ recommendations.length }} 篇</span>
      </h1>
      <p class="page-desc">基于你的文献库，AI 推荐相关论文</p>
    </div>

    <!-- ===== 推荐模式切换 ===== -->
    <div class="mode-card">
      <div class="mode-tabs">
        <button
          v-for="mode in modes"
          :key="mode.value"
          class="mode-tab"
          :class="{ active: currentMode === mode.value }"
          @click="switchMode(mode.value)"
        >
          {{ mode.label }}
        </button>
      </div>

      <!-- 基于论文 -->
      <div v-if="currentMode === 'paper'" class="mode-config">
        <div class="config-row">
          <label>选择种子论文</label>
          <el-select
            v-model="seedPaperId"
            placeholder="选择一篇本地论文"
            filterable
            style="width: 300px"
          >
            <el-option
              v-for="p in localPapers"
              :key="p.id"
              :label="p.title"
              :value="p.id"
            />
          </el-select>
          <button class="btn-generate" @click="generateRecommendations" :disabled="loading || !seedPaperId">
            {{ loading ? '生成中...' : '生成推荐' }}
          </button>
        </div>
      </div>

      <!-- 基于文献库 -->
      <div v-if="currentMode === 'library'" class="mode-config">
        <div class="config-row">
          <label>选择种子论文（1-5篇）</label>
          <el-select
            v-model="seedPaperIds"
            placeholder="选择多篇本地论文"
            filterable
            multiple
            style="width: 300px"
          >
            <el-option
              v-for="p in localPapers"
              :key="p.id"
              :label="p.title"
              :value="p.id"
            />
          </el-select>
          <button class="btn-generate" @click="generateRecommendations" :disabled="loading || seedPaperIds.length === 0">
            {{ loading ? '生成中...' : '生成推荐' }}
          </button>
        </div>
      </div>

      <!-- 基于主题 -->
      <div v-if="currentMode === 'topic'" class="mode-config">
        <div class="config-row">
          <label>研究主题</label>
          <input v-model="topicQuery" class="topic-input" placeholder="输入研究主题..." />
          <button class="btn-generate" @click="generateRecommendations" :disabled="loading || !topicQuery.trim()">
            {{ loading ? '生成中...' : '生成推荐' }}
          </button>
        </div>
        <div class="config-row" style="margin-top: 8px;">
          <label>年份范围</label>
          <input v-model.number="topicYearFrom" placeholder="起始" class="year-input" />
          <span>至</span>
          <input v-model.number="topicYearTo" placeholder="结束" class="year-input" />
        </div>
      </div>
    </div>

    <!-- ===== 推荐结果 ===== -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span>生成推荐中...</span>
    </div>

    <div v-else-if="recommendations.length === 0 && hasLoaded" class="empty-state">
      <div class="empty-icon">💡</div>
      <h3>暂无推荐</h3>
      <p>选择种子论文或输入主题生成推荐</p>
    </div>

    <div v-else-if="recommendations.length > 0" class="results-list">
      <div v-for="(item, idx) in recommendations" :key="idx" class="paper-item">
        <div class="paper-content">
          <div class="paper-header">
            <h3 class="paper-title">{{ item.title }}</h3>
            <span class="score-tag">{{ (item.score * 100).toFixed(0) }}%</span>
            <span class="status-tag" data-testid="recommendation-status">{{ item.status }}</span>
          </div>
          <div class="paper-meta">
            <span><strong>作者：</strong>{{ item.authors?.join('、') || '未知' }}</span>
            <span><strong>年份：</strong>{{ item.year || '未知' }}</span>
            <span v-if="item.citation_count"><strong>引用：</strong>{{ item.citation_count }}</span>
          </div>
          <div class="paper-reasons" v-if="item.reasons?.length">
            <span class="reason-tag" v-for="(r, ri) in item.reasons" :key="ri">💡 {{ r }}</span>
          </div>
          <div class="paper-footer">
            <button class="btn-import" @click="importRecommendation(item)" :disabled="item._importing || item._imported">
              {{ item._imported ? '已导入' : item._importing ? '导入中...' : '加入文献库' }}
            </button>
            <button class="btn-feedback" @click="feedbackRecommendation(item, 'like')" :disabled="item._feedback">👍</button>
            <button class="btn-feedback" @click="feedbackRecommendation(item, 'dislike')" :disabled="item._feedback">👎</button>
            <a v-if="item.external_url" :href="item.external_url" target="_blank" class="btn-link">查看原文</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

// ===== 状态 =====
const currentMode = ref('paper')
const loading = ref(false)
const hasLoaded = ref(false)
const recommendations = ref([])

const modes = [
  { value: 'paper', label: '基于论文' },
  { value: 'library', label: '基于文献库' },
  { value: 'topic', label: '基于主题' }
]

// 本地论文列表
const localPapers = ref([])

// 基于论文
const seedPaperId = ref(null)

// 基于文献库
const seedPaperIds = ref([])

// 基于主题
const topicQuery = ref('')
const topicYearFrom = ref('')
const topicYearTo = ref('')

// ===== 加载本地论文 =====
const loadLocalPapers = async () => {
  try {
    const res = await axios.get('/api/papers')
    if (res.data.code === 200 || res.data.code === 0) {
      localPapers.value = (res.data.data || []).map(p => ({
        ...p,
        id: p.paper_id || p.id
      }))
    }
  } catch (error) {
    console.error('加载论文失败:', error)
  }
}

const normalizeRecords = records => records.map(record => ({
  ...record.paper,
  recommendation_id: record.id,
  score: record.score,
  reasons: record.reasons || [],
  is_fallback: Boolean(record.is_fallback),
  status: record.status,
  _imported: record.status === 'imported',
  _importing: false,
  _feedback: false
}))

const loadHistory = async () => {
  const res = await axios.get('/api/recommendations', { params: { page_size: 100 } })
  const data = res.data.data || res.data
  recommendations.value = normalizeRecords(data.items || [])
  hasLoaded.value = recommendations.value.length > 0
}

// ===== 切换模式 =====
const switchMode = (mode) => {
  currentMode.value = mode
  recommendations.value = []
  hasLoaded.value = false
}

// ===== 生成推荐 =====
const generateRecommendations = async () => {
  let params = {}
  let url = ''

  if (currentMode.value === 'paper') {
    if (!seedPaperId.value) {
      ElMessage.warning('请选择一篇种子论文')
      return
    }
    url = '/api/recommendations/by-paper'
    params = { paper_id: Number(seedPaperId.value), limit: 20 }
  } else if (currentMode.value === 'library') {
    if (seedPaperIds.value.length === 0) {
      ElMessage.warning('请至少选择一篇种子论文')
      return
    }
    url = '/api/recommendations/for-library'
    params = { paper_ids: seedPaperIds.value.map(Number), limit: 20 }
  } else if (currentMode.value === 'topic') {
    if (!topicQuery.value.trim()) {
      ElMessage.warning('请输入研究主题')
      return
    }
    url = '/api/recommendations/by-topic'
    params = { topic: topicQuery.value.trim(), limit: 20 }
    if (topicYearFrom.value) params.year_from = topicYearFrom.value
    if (topicYearTo.value) params.year_to = topicYearTo.value
  }

  loading.value = true
  hasLoaded.value = true

  try {
    const res = await axios.post(url, params)
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || res.data
      recommendations.value = normalizeRecords(Array.isArray(data) ? data : data.items || [])
      ElMessage.success(`已生成 ${recommendations.value.length} 条推荐`)
    } else {
      ElMessage.error(res.data.message || '生成推荐失败')
    }
  } catch (error) {
    console.error('生成推荐失败:', error)
    ElMessage.error(error.response?.data?.message || '生成推荐失败，请重试')
  } finally {
    loading.value = false
  }
}

// ===== 导入推荐论文 =====
const importRecommendation = async (item) => {
  if (item._imported) return
  item._importing = true

  try {
    const res = await axios.post(`/api/recommendations/${item.recommendation_id}/import`)
    if (res.data.code === 200 || res.data.code === 0) {
      item._imported = true
      ElMessage.success('导入成功！')
    } else {
      ElMessage.error(res.data.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.message || '导入失败')
  } finally {
    item._importing = false
  }
}

// ===== 反馈 =====
const feedbackRecommendation = async (item, type) => {
  if (item._feedback) return
  item._feedback = true

  try {
    const status = type === 'like' ? 'read_later' : 'not_interested'
    await axios.patch(`/api/recommendations/${item.recommendation_id}/status`, { status })
    item.status = status
    ElMessage.success(type === 'like' ? '已加入稍后阅读' : '已标记为不感兴趣')
  } catch (error) {
    console.error('反馈失败:', error)
    item._feedback = false
  }
}

// ===== 生命周期 =====
onMounted(() => {
  loadLocalPapers()
  loadHistory().catch(error => console.error('加载推荐历史失败:', error))
})
</script>

<style scoped>
.recommendation-container {
  padding: 24px 20px;
  max-width: 1000px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-primary);
}

.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-size: 28px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 12px;
}
.title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--primary-gradient);
  color: #fff;
}
.title-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.title-badge {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: var(--primary-gradient);
  padding: 2px 14px;
  border-radius: 20px;
}
.page-desc {
  color: #8c9aa8;
  font-size: 15px;
  margin-left: 56px;
}

.mode-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.mode-tabs {
  display: flex;
  gap: 4px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 10px;
  margin-bottom: 16px;
}
.mode-tab {
  padding: 8px 24px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}
.mode-tab.active {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  color: #667eea;
}
.mode-tab:hover:not(.active) {
  background: rgba(0,0,0,0.04);
}

.mode-config {
  padding-top: 4px;
}
.config-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.config-row label {
  font-weight: 500;
  color: #4a5a6a;
  min-width: 100px;
}

.btn-generate {
  padding: 8px 28px;
  border: none;
  border-radius: 8px;
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-generate:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102,126,234,0.3);
}
.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.topic-input {
  flex: 1;
  min-width: 200px;
  padding: 8px 16px;
  border: 1px solid #e8ecf1;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}
.topic-input:focus {
  border-color: #667eea;
}
.year-input {
  width: 70px;
  padding: 6px 10px;
  border: 1px solid #e8ecf1;
  border-radius: 6px;
  font-size: 14px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.paper-item {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.paper-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.paper-title {
  font-size: 17px;
  font-weight: 600;
  color: #1a2332;
  margin: 0;
  flex: 1;
}
.score-tag {
  font-size: 13px;
  font-weight: 700;
  color: #667eea;
  background: #f0f4ff;
  padding: 2px 14px;
  border-radius: 20px;
}
.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
  margin: 6px 0;
}
.paper-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 6px 0;
}
.reason-tag {
  font-size: 13px;
  color: #4a5a6a;
  background: #f8f9fb;
  padding: 4px 14px;
  border-radius: 20px;
}
.paper-footer {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.btn-import {
  padding: 6px 18px;
  border: none;
  border-radius: 8px;
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}
.btn-import:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102,126,234,0.3);
}
.btn-import:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-feedback {
  padding: 6px 14px;
  border: 1px solid #e8ecf1;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 16px;
}
.btn-feedback:hover:not(:disabled) {
  border-color: #667eea;
  background: #f0f4ff;
}
.btn-feedback:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.btn-link {
  padding: 6px 16px;
  border: 1px solid #e8ecf1;
  border-radius: 8px;
  color: #667eea;
  text-decoration: none;
  font-size: 13px;
  transition: all 0.3s;
}
.btn-link:hover {
  background: #f0f4ff;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(102,126,234,0.1);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  display: inline-block;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.empty-state .empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a2332;
  margin: 0 0 4px 0;
}
.empty-state p {
  color: #8c9aa8;
}
</style>
