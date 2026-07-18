<template>
  <div class="papers-container">
    <!-- 顶部欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h1 class="page-title">📚 我的文献库</h1>
        <p class="page-subtitle">管理你的科研文献，让阅读更有条理</p>
      </div>
      <div class="welcome-stats">
        <div class="stat-item">
          <span class="stat-number">{{ papers.length }}</span>
          <span class="stat-label">总文献</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ readCount }}</span>
          <span class="stat-label">已读</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ unreadCount }}</span>
          <span class="stat-label">未读</span>
        </div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="action-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索论文标题、作者..."
          clearable
          prefix-icon="Search"
          size="large"
          class="search-input"
        />
      </div>
      <div class="action-right">
        <el-button type="warning" @click="$router.push('/agent')" :icon="Edit" round>
          Agent 规划
        </el-button>
        <el-button type="success" @click="$router.push('/graph')" :icon="Share" round>
          关系图
        </el-button>
        <el-button type="info" @click="$router.push('/review')" :icon="Edit" round>
          综述辅助
        </el-button>
        <el-button type="primary" @click="showUpload = true" :icon="Upload" round>
          上传论文
        </el-button>
      </div>
    </div>

    <!-- 论文列表 -->
    <div class="papers-list" v-if="filteredPapers.length > 0">
      <div
        v-for="paper in filteredPapers"
        :key="paper.paper_id || paper.id"
        class="paper-item"
        @click="goToDetail(paper.paper_id || paper.id)"
      >
        <div class="paper-icon">
          <span class="icon-emoji">📄</span>
        </div>
        <div class="paper-content">
          <div class="paper-header">
            <h3 class="paper-title">{{ paper.title }}</h3>
            <el-tag :type="getStatusType(paper.status)" size="small" effect="light">
              {{ paper.status || '未读' }}
            </el-tag>
          </div>
          <div class="paper-info">
            <span v-if="paper.authors"><el-icon><User /></el-icon> {{ paper.authors }}</span>
            <span v-if="paper.year"><el-icon><Calendar /></el-icon> {{ paper.year }}</span>
            <span><el-icon><Timer /></el-icon> {{ formatDate(paper.created_at) }}</span>
          </div>
          <div class="paper-tags" v-if="paper.tags && paper.tags.length > 0">
            <span v-for="tag in paper.tags" :key="tag" class="tag">#{{ tag }}</span>
          </div>
        </div>
        <div class="paper-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>还没有文献</h3>
      <p>上传你的第一篇论文，开始科研之旅</p>
      <el-button type="primary" @click="showUpload = true" :icon="Upload" round>
        上传论文
      </el-button>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUpload" title="上传论文" width="480px" destroy-on-close>
      <el-upload
        ref="uploadRef"
        drag
        action="/api/papers/upload"
        :headers="uploadHeaders"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        accept=".pdf"
        name="file"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽 PDF 文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">仅支持 PDF 格式</div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, UploadFilled, User, Calendar, Search, Share, Edit, Timer, ArrowRight } from '@element-plus/icons-vue'
import axios from '../utils/axios'

const router = useRouter()
const papers = ref([])
const searchKeyword = ref('')
const showUpload = ref(false)
const uploadRef = ref(null)

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))

const readCount = computed(() => papers.value.filter(p => p.status === '已读').length)
const unreadCount = computed(() => papers.value.filter(p => p.status === '未读' || !p.status).length)

const filteredPapers = computed(() => {
  if (!searchKeyword.value) return papers.value
  const kw = searchKeyword.value.toLowerCase()
  return papers.value.filter(p =>
    p.title?.toLowerCase().includes(kw) ||
    p.authors?.toLowerCase().includes(kw)
  )
})

const getStatusType = (status) => {
  const map = { '已读': 'success', '在读': 'warning', '未读': 'info' }
  return map[status] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

// ===== 跳转到论文详情（兼容 paper_id 和 id） =====
const goToDetail = (id) => {
  console.log('🔍 [PapersView] goToDetail 被调用，收到的 id:', id, '，类型:', typeof id)
  
  if (!id) {
    console.error('❌ 论文 ID 无效:', id)
    ElMessage.error('论文 ID 无效，无法跳转')
    return
  }
  
  // 确保 ID 是字符串
  const idStr = String(id)
  console.log('📄 跳转到论文详情，ID:', idStr)
  router.push(`/papers/${idStr}`)
}

const loadPapers = async () => {
  try {
    const res = await axios.get('/api/papers')
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || []
      // 兼容处理：确保每个论文对象都有 id 字段（从 paper_id 映射）
      papers.value = data.map(item => ({
        ...item,
        id: item.paper_id || item.id
      }))
      console.log('📚 加载的论文数据:', papers.value)
    } else {
      loadMockPapers()
    }
  } catch (error) {
    console.warn('加载文献列表失败，使用 Mock 数据:', error)
    loadMockPapers()
  }
}

const loadMockPapers = () => {
  papers.value = [
    {
      id: 1,
      paper_id: 1,
      title: 'Attention Is All You Need',
      authors: 'Vaswani et al.',
      year: '2017',
      status: '已读',
      tags: ['Transformer', 'NLP'],
      created_at: '2026-07-10T10:00:00'
    },
    {
      id: 2,
      paper_id: 2,
      title: 'BERT: Pre-training of Deep Bidirectional Transformers',
      authors: 'Devlin et al.',
      year: '2018',
      status: '在读',
      tags: ['BERT', '预训练'],
      created_at: '2026-07-11T14:30:00'
    },
    {
      id: 3,
      paper_id: 3,
      title: 'GPT-3: Language Models are Few-Shot Learners',
      authors: 'Brown et al.',
      year: '2020',
      status: '未读',
      tags: ['GPT', '大语言模型'],
      created_at: '2026-07-12T09:15:00'
    }
  ]
  console.log('📚 Mock 论文数据:', papers.value)
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

onMounted(() => {
  loadPapers()
})
</script>

<style scoped>
.papers-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 40px;
}

/* ===== 欢迎区 ===== */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 16px;
}
.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a2332;
  margin: 0 0 4px 0;
}
.page-subtitle {
  color: #8c8f9c;
  font-size: 15px;
  margin: 0;
}
.welcome-stats {
  display: flex;
  gap: 32px;
}
.stat-item {
  text-align: center;
}
.stat-number {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1a2332;
}
.stat-label {
  font-size: 13px;
  color: #8c8f9c;
}

/* ===== 操作栏 ===== */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}
.action-left {
  flex: 1;
  min-width: 200px;
}
.search-input {
  max-width: 360px;
}
.action-right {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* ===== 论文列表 ===== */
.papers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.paper-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #ffffff;
  border-radius: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1px solid transparent;
}
.paper-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-color: #667eea;
}
.paper-icon .icon-emoji {
  font-size: 28px;
  display: block;
  line-height: 1;
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
  color: #1a2332;
  margin: 0;
  line-height: 1.4;
}
.paper-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #8c8f9c;
  margin-top: 4px;
}
.paper-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.paper-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.tag {
  font-size: 12px;
  color: #b88230;
  background: #fdf6ed;
  padding: 1px 10px;
  border-radius: 12px;
}
.paper-arrow {
  color: #c1c7d0;
  transition: color 0.2s;
}
.paper-item:hover .paper-arrow {
  color: #667eea;
}

/* ===== 空状态 ===== */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.empty-state h3 {
  font-size: 20px;
  color: #1a2332;
  margin: 0 0 8px 0;
}
.empty-state p {
  color: #8c8f9c;
  margin: 0 0 20px 0;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .papers-container { padding: 16px; }
  .welcome-section { flex-direction: column; align-items: stretch; }
  .welcome-stats { justify-content: space-around; }
  .action-bar { flex-direction: column; align-items: stretch; }
  .action-left { width: 100%; }
  .search-input { max-width: 100%; }
  .action-right { justify-content: stretch; }
  .action-right .el-button { flex: 1; }
  .paper-item { padding: 14px 16px; }
  .paper-title { font-size: 14px; }
}
</style>