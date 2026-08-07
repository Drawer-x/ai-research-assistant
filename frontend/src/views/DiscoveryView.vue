<template>
  <div class="discovery-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </span>
        <span class="title-text">论文发现</span>
        <span class="title-badge">{{ searchResults.length }} 篇</span>
      </h1>
      <p class="page-desc">搜索 Crossref 收录的真实学术论文</p>
    </div>

    <!-- ===== 搜索栏 ===== -->
    <div class="search-card">
      <div class="search-row">
        <input
          v-model="searchQuery"
          class="search-input"
          placeholder="输入关键词搜索论文，例如：Transformer"
          @keyup.enter="searchPapers(1)"
        />
        <button class="search-btn" @click="searchPapers(1)" :disabled="loading">
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <label>年份范围</label>
          <input v-model.number="yearFrom" type="number" placeholder="起始" class="filter-input" />
          <span>至</span>
          <input v-model.number="yearTo" type="number" placeholder="结束" class="filter-input" />
        </div>
        <div class="filter-group">
          <label>开放获取</label>
          <select v-model="openAccess" class="filter-select">
            <option value="all">全部</option>
            <option value="true">仅开放获取</option>
            <option value="false">非开放获取</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ===== 结果列表 ===== -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span>搜索中...</span>
    </div>

    <div v-else-if="searchResults.length === 0 && searched" class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>未找到论文</h3>
      <p>尝试调整关键词或筛选条件</p>
    </div>

    <div v-else-if="searchResults.length > 0" class="results-list">
      <div v-for="paper in searchResults" :key="paper.external_id || paper.id" class="paper-item">
        <div class="paper-content">
          <div class="paper-header">
            <h3 class="paper-title">{{ paper.title }}</h3>
            <span v-if="paper.open_access" class="oa-tag">开放获取</span>
            <span v-else class="oa-tag closed">非开放</span>
          </div>
          <div class="paper-meta">
            <span><strong>作者：</strong>{{ paper.authors?.join('、') || '未知' }}</span>
            <span><strong>年份：</strong>{{ paper.year || '未知' }}</span>
            <span v-if="paper.venue"><strong>发表：</strong>{{ paper.venue }}</span>
            <span v-if="paper.citation_count"><strong>引用：</strong>{{ paper.citation_count }}</span>
          </div>
          <div class="paper-abstract" v-if="paper.abstract">
            <p>{{ truncateText(paper.abstract, 200) }}</p>
          </div>
          <div class="paper-footer">
            <button class="btn-import" @click="importPaper(paper)" :disabled="paper._importing || paper._imported">
              {{ paper._imported ? '已导入' : paper._importing ? '导入中...' : '加入文献库' }}
            </button>
            <a v-if="paper.external_url" :href="paper.external_url" target="_blank" class="btn-link">查看原文</a>
          </div>
        </div>
      </div>

      <!-- ===== 分页 ===== -->
      <div class="pagination" v-if="totalPages > 1">
        <button class="page-btn" @click="prevPage" :disabled="currentPage === 1">上一页</button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button class="page-btn" @click="nextPage" :disabled="currentPage === totalPages">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const router = useRouter()

// ===== 状态 =====
const searchQuery = ref('')
const searchResults = ref([])
const loading = ref(false)
const searched = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20

const yearFrom = ref('')
const yearTo = ref('')
const openAccess = ref('all')

// ===== 搜索 =====
const searchPapers = async (page = 1) => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  searched.value = true
  currentPage.value = page

  try {
    const params = {
      query: searchQuery.value,
      page,
      page_size: pageSize,
    }
    if (yearFrom.value) params.year_from = yearFrom.value
    if (yearTo.value) params.year_to = yearTo.value
    if (openAccess.value !== 'all') params.open_access = openAccess.value === 'true'

    const res = await axios.get('/api/discovery/search', { params })

    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || res.data
      searchResults.value = (data.items || []).map(p => ({
        ...p,
        _imported: Boolean(p.is_imported),
        _importing: false
      }))
      totalPages.value = Math.max(1, Math.ceil((data.total || 0) / pageSize))
    } else {
      ElMessage.error(res.data.message || '搜索失败')
    }
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error(error.response?.data?.message || '搜索失败，请重试')
  } finally {
    loading.value = false
  }
}

// ===== 导入论文 =====
const importPaper = async (paper) => {
  if (paper._imported) return

  paper._importing = true
  try {
    const res = await axios.post('/api/discovery/import', {
      provider: 'crossref',
      external_id: paper.external_id || paper.id
    })

    if (res.data.code === 200 || res.data.code === 0) {
      paper._imported = true
      ElMessage.success('导入成功！')
      const data = res.data.data || res.data
      if (data.paper_id) {
        setTimeout(() => {
          if (confirm('查看导入的论文详情？')) {
            router.push(`/papers/${data.paper_id}`)
          }
        }, 500)
      }
    } else {
      ElMessage.error(res.data.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.message || '导入失败，请重试')
  } finally {
    paper._importing = false
  }
}

// ===== 分页 =====
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    searchPapers(currentPage.value + 1)
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    searchPapers(currentPage.value - 1)
  }
}

// ===== 工具 =====
const truncateText = (text, maxLen) => {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}
</script>

<style scoped>
.discovery-container {
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

.search-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.search-row {
  display: flex;
  gap: 12px;
}
.search-input {
  flex: 1;
  padding: 12px 18px;
  border: 2px solid #e8ecf1;
  border-radius: 10px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.3s;
}
.search-input:focus {
  border-color: #667eea;
}
.search-btn {
  padding: 12px 32px;
  border: none;
  border-radius: 10px;
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102,126,234,0.3);
}
.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.filter-row {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}
.filter-group label {
  font-weight: 500;
}
.filter-input {
  width: 70px;
  padding: 6px 10px;
  border: 1px solid #e8ecf1;
  border-radius: 6px;
  font-size: 14px;
}
.filter-select {
  padding: 6px 12px;
  border: 1px solid #e8ecf1;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
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
}
.oa-tag {
  font-size: 11px;
  padding: 2px 12px;
  border-radius: 20px;
  background: #d1fae5;
  color: #065f46;
}
.oa-tag.closed {
  background: #f3f4f6;
  color: #6b7280;
}
.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
  margin: 6px 0;
}
.paper-abstract p {
  font-size: 14px;
  color: #4a5a6a;
  line-height: 1.6;
  margin: 6px 0;
}
.paper-footer {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.btn-import {
  padding: 8px 20px;
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
.btn-link {
  padding: 8px 16px;
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}
.page-btn {
  padding: 8px 20px;
  border: 1px solid #e8ecf1;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
}
.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.page-info {
  font-size: 14px;
  color: #6b7280;
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
