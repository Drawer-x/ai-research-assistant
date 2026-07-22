<template>
  <div class="papers-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </span>
        <span class="title-text">我的文献库</span>
        <span class="title-badge">{{ papers.length }} 篇</span>
      </h1>
      <p class="page-desc">管理你的科研文献，让阅读更有条理</p>
    </div>

    <!-- ===== 操作栏 ===== -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索论文标题、作者..."
          />
        </div>
      </div>
      <div class="toolbar-right">
        <button class="tool-btn" @click="$router.push('/agent')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
          Agent 规划
        </button>
        <button class="tool-btn" @click="$router.push('/graph')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="4" r="2"/>
            <circle cx="4" cy="16" r="2"/>
            <circle cx="20" cy="16" r="2"/>
            <line x1="12" y1="6" x2="12" y2="10"/>
            <line x1="6" y1="17" x2="10" y2="14"/>
            <line x1="18" y1="17" x2="14" y2="14"/>
          </svg>
          关系图
        </button>
        <button class="tool-btn" @click="$router.push('/review')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"/>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
          </svg>
          综述辅助
        </button>
        <button class="btn-primary" @click="showUpload = true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          上传论文
        </button>
      </div>
    </div>

    <!-- ===== 统计 ===== -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-number">{{ papers.length }}</span>
        <span class="stat-label">总文献</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ readCount }}</span>
        <span class="stat-label">已读</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ readingCount }}</span>
        <span class="stat-label">在读</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ unreadCount }}</span>
        <span class="stat-label">未读</span>
      </div>
    </div>

    <!-- ===== 论文列表 ===== -->
    <div v-if="filteredPapers.length > 0" class="papers-list">
      <div
        v-for="paper in filteredPapers"
        :key="paper.paper_id || paper.id"
        class="paper-item"
      >
        <div class="paper-icon" @click="goToDetail(paper.paper_id || paper.id)">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </div>
        <div class="paper-content" @click="goToDetail(paper.paper_id || paper.id)">
          <div class="paper-header">
            <h3 class="paper-title">{{ paper.title }}</h3>
            <span 
              class="status-tag" 
              :class="{
                'status-read': getDisplayStatus(paper.status) === '已读',
                'status-reading': getDisplayStatus(paper.status) === '在读',
                'status-unread': getDisplayStatus(paper.status) === '未读' || !paper.status
              }"
              @click.stop="toggleStatus(paper)"
            >
              {{ getDisplayStatus(paper.status) || '未读' }}
            </span>
          </div>
          <div class="paper-meta">
            <span v-if="paper.authors">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {{ paper.authors }}
            </span>
            <span v-if="paper.year">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {{ paper.year }}
            </span>
            <span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ formatDate(paper.created_at) }}
            </span>
          </div>
          <div v-if="paper.tags && paper.tags.length > 0" class="paper-tags">
            <span v-for="tag in paper.tags" :key="tag" class="tag">#{{ tag }}</span>
          </div>
        </div>
        <div class="paper-actions">
          <button class="paper-delete" :disabled="deletingIds.has(paper.id)" @click.stop="deletePaper(paper)">
            {{ deletingIds.has(paper.id) ? '删除中...' : '删除' }}
          </button>
          <button class="paper-view" @click="goToDetail(paper.id)">查看</button>
        </div>
        <div class="paper-arrow" @click="goToDetail(paper.paper_id || paper.id)">
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
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
      </div>
      <h3>还没有文献</h3>
      <p>上传你的第一篇论文，开始科研之旅</p>
      <button class="btn-primary" @click="showUpload = true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        上传论文
      </button>
    </div>

    <!-- ===== 上传对话框 ===== -->
    <div class="dialog-overlay" v-if="showUpload" @click="showUpload = false"></div>
    <div class="dialog" :class="{ open: showUpload }">
      <div class="dialog-header">
        <h3 class="dialog-title">上传论文</h3>
        <button class="dialog-close" @click="showUpload = false">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="dialog-body">
        <el-upload
          ref="uploadRef"
          drag
          :action="uploadUrl"
          :headers="uploadHeaders"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
          accept=".pdf"
          name="file"
          class="upload-area"
        >
          <div class="upload-content">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <div class="upload-text">
              拖拽 PDF 文件到此处，或 <span class="upload-link">点击上传</span>
            </div>
            <div class="upload-tip">仅支持 PDF 格式</div>
          </div>
        </el-upload>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from '../utils/axios'

const router = useRouter()
const route = useRoute()
const papers = ref([])
const searchKeyword = ref('')
const showUpload = ref(false)
const uploadRef = ref(null)
const deletingIds = ref(new Set())

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))
const uploadUrl = computed(() => {
  const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
  return `${base}/api/papers/upload`
})

// ===== 状态映射 =====
const displayStatusMap = {
  'unread': '未读',
  'rough_read': '在读',
  'intensive_read': '已读',
  'to_reproduce': '待复现',
  'for_review': '待评审',
  'archived': '已归档'
}

const backendStatusMap = {
  '未读': 'unread',
  '在读': 'rough_read',
  '已读': 'intensive_read'
}

const statusCycle = ['unread', 'rough_read', 'intensive_read']

// ===== 获取显示状态 =====
const getDisplayStatus = (status) => {
  if (!status) return '未读'
  return displayStatusMap[status] || status
}

// ===== 统计 =====
const readCount = computed(() => {
  return papers.value.filter(p => getDisplayStatus(p.status) === '已读').length
})

const readingCount = computed(() => {
  return papers.value.filter(p => getDisplayStatus(p.status) === '在读').length
})

const unreadCount = computed(() => {
  return papers.value.filter(p => getDisplayStatus(p.status) === '未读' || !p.status).length
})

const filteredPapers = computed(() => {
  if (!searchKeyword.value) return papers.value
  const kw = searchKeyword.value.toLowerCase()
  return papers.value.filter(p =>
    p.title?.toLowerCase().includes(kw) ||
    p.authors?.toLowerCase().includes(kw)
  )
})

// ===== 格式化日期 =====
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

// ===== 跳转详情 =====
const goToDetail = (id) => {
  if (!id) {
    ElMessage.error('论文 ID 无效')
    return
  }
  router.push(`/papers/${id}`)
}

// ===== 切换阅读状态 =====
const toggleStatus = async (paper) => {
  const currentDisplay = getDisplayStatus(paper.status)
  const currentBackend = backendStatusMap[currentDisplay] || 'unread'
  
  const currentIndex = statusCycle.indexOf(currentBackend)
  const nextBackend = statusCycle[(currentIndex + 1) % statusCycle.length]
  const nextDisplay = displayStatusMap[nextBackend]

  try {
    const res = await axios.put(`/api/papers/${paper.paper_id || paper.id}/status`, {
      read_status: nextBackend
    })
    if (res.data.code === 200 || res.data.code === 0) {
      paper.status = nextBackend
      ElMessage.success(`状态已更新为「${nextDisplay}」`)
    } else {
      ElMessage.error(res.data.message || '更新失败')
    }
  } catch (error) {
    console.error('更新状态失败:', error)
    ElMessage.error(error.response?.data?.message || '更新状态失败，请重试')
  }
}

// ===== 加载论文列表 =====
const loadPapers = async () => {
  try {
    const res = await axios.get('/api/papers')
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || []
      papers.value = data.map(item => ({
        ...item,
        id: item.paper_id || item.id
      }))
    } else {
      papers.value = []
      ElMessage.error(res.data.message || '加载文献列表失败')
    }
  } catch (error) {
    console.warn('加载文献列表失败:', error)
    papers.value = []
    ElMessage.error(error.response?.data?.message || '加载文献列表失败，请稍后重试')
  }
}

const deletePaper = async (paper) => {
  const id = Number(paper.id ?? paper.paper_id)
  if (!Number.isInteger(id) || id <= 0 || deletingIds.value.has(id)) return
  try {
    await ElMessageBox.confirm(`确认删除“${paper.title || '该论文'}”吗？`, '删除论文', { type: 'warning' })
  } catch { return }
  deletingIds.value.add(id)
  deletingIds.value = new Set(deletingIds.value)
  try {
    const res = await axios.delete(`/api/papers/${id}`)
    if (res.data.code !== 200 && res.data.code !== 0) throw new Error(res.data.message || '删除失败')
    papers.value = papers.value.filter(item => Number(item.id ?? item.paper_id) !== id)
    ElMessage.success('论文已删除')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || error.message || '删除失败')
  } finally {
    deletingIds.value.delete(id)
    deletingIds.value = new Set(deletingIds.value)
  }
}

const onUploadSuccess = (response) => {
  if (response.code === 200 || response.code === 0) {
    ElMessage.success('上传成功！')
    showUpload.value = false
    loadPapers()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const onUploadError = () => {
  ElMessage.error('上传失败，请重试')
}

// ===== 监听路由变化，从详情页返回时刷新 =====
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/papers') {
      loadPapers()
    }
  }
)

onMounted(() => {
  loadPapers()
})
</script>

<style scoped>
.papers-container {
  padding: 24px 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.04) 0%, transparent 50%),
                    radial-gradient(ellipse at 90% 80%, rgba(123, 200, 164, 0.04) 0%, transparent 50%);
}

.page-header {
  margin-bottom: 24px;
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

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 12px 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.toolbar-left {
  flex: 1;
  min-width: 180px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(248, 250, 255, 0.6);
  border-radius: var(--radius-full);
  padding: 0 16px;
  transition: all 0.3s ease;
}

.search-box:focus-within {
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(95, 195, 228, 0.08);
}

.search-box svg {
  stroke: var(--text-muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  padding: 10px 0;
  border: none;
  background: transparent;
  font-size: 14px;
  font-family: inherit;
  color: var(--text-primary);
  outline: none;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.toolbar-right {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(248, 250, 255, 0.6);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tool-btn:hover {
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-primary);
  transform: translateY(-2px);
}

.tool-btn svg {
  stroke: currentColor;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

.stats-row {
  display: flex;
  gap: 32px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(4px);
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat-number {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.papers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paper-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.paper-item:hover {
  transform: translateX(6px);
  box-shadow: var(--shadow-md);
  border-color: rgba(95, 195, 228, 0.2);
}

.paper-icon {
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

.paper-icon svg {
  stroke: currentColor;
}

.paper-content {
  flex: 1;
  min-width: 0;
}

.paper-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.paper-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.4;
}

.status-tag {
  padding: 2px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.status-tag:hover {
  transform: scale(1.05);
}

.status-tag:active {
  transform: scale(0.95);
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

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 3px;
}

.paper-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.paper-meta svg {
  stroke: currentColor;
}

.paper-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.tag {
  font-size: 12px;
  color: var(--primary-500);
  background: rgba(95, 195, 228, 0.06);
  padding: 1px 12px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.paper-arrow {
  color: var(--text-muted);
  transition: color 0.2s ease;
  flex-shrink: 0;
}

.paper-actions { display: flex; gap: 8px; flex-shrink: 0; }
.paper-actions button { padding: 6px 12px; border-radius: var(--radius-full); cursor: pointer; }
.paper-view { border: 1px solid rgba(95,195,228,.3); color: var(--primary-500); background: white; }
.paper-delete { border: 1px solid rgba(220,80,80,.25); color: #c45f5f; background: rgba(245,160,160,.08); }
.paper-delete:disabled { opacity: .55; cursor: wait; }

.paper-arrow svg {
  stroke: currentColor;
}

.paper-item:hover .paper-arrow {
  color: var(--primary-500);
}

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

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(4px);
  z-index: 200;
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.dialog {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) translateY(100%);
  width: 520px;
  max-width: 92vw;
  max-height: 80vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  box-shadow: 0 -8px 40px rgba(0, 0, 0, 0.08);
  z-index: 201;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}

.dialog.open {
  transform: translateX(-50%) translateY(0);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.dialog-close {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.dialog-close:hover {
  background: rgba(0, 0, 0, 0.08);
}

.dialog-body {
  padding: 24px;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  border-radius: var(--radius-lg);
  padding: 40px 20px;
  border: 2px dashed rgba(95, 195, 228, 0.2);
  background: rgba(248, 250, 255, 0.6);
  transition: all 0.3s ease;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-500);
  background: rgba(255, 255, 255, 0.8);
}

.upload-area :deep(.el-upload-dragger.is-dragover) {
  border-color: var(--primary-500);
  background: rgba(95, 195, 228, 0.04);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
}

.upload-content svg {
  stroke: var(--text-muted);
  opacity: 0.5;
}

.upload-text {
  font-size: 15px;
}

.upload-link {
  color: var(--primary-500);
  font-weight: 600;
  cursor: pointer;
}

.upload-tip {
  font-size: 13px;
  opacity: 0.6;
}

@media (max-width: 768px) {
  .papers-container { padding: 16px 12px; }
  .page-title { font-size: 22px; }
  .title-icon { width: 38px; height: 38px; }
  .title-icon svg { width: 20px; height: 20px; }
  .title-badge { font-size: 10px; padding: 2px 12px; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-right { justify-content: stretch; }
  .toolbar-right button { flex: 1; justify-content: center; }
  .stats-row { gap: 16px; padding: 12px 16px; }
  .stat-number { font-size: 18px; }
  .paper-item { padding: 14px 16px; }
  .paper-title { font-size: 14px; }
  .dialog { width: 100%; max-width: 100%; }
}

@media (max-width: 480px) {
  .page-title { font-size: 19px; }
  .title-icon { width: 32px; height: 32px; }
  .title-icon svg { width: 16px; height: 16px; }
  .stats-row { gap: 12px; }
  .stat-number { font-size: 16px; }
  .stat-label { font-size: 12px; }
  .paper-meta { gap: 10px; font-size: 12px; }
  .paper-icon { width: 36px; height: 36px; }
  .paper-icon svg { width: 20px; height: 20px; }
  .empty-state { padding: 40px 16px; }
}
</style>
