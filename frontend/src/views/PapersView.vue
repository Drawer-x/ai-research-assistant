<template>
  <div class="papers-container">
    <!-- 顶部操作栏 -->
    <div class="papers-header">
      <div class="header-left">
        <h1 class="page-title">📄 我的文献库</h1>
        <el-tag type="info" size="large">共 {{ papers.length }} 篇</el-tag>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索论文标题..."
          style="width: 260px; margin-right: 16px"
          clearable
          prefix-icon="Search"
        />
        <el-button type="warning" @click="$router.push('/agent')" style="margin-right: 12px;">
          <el-icon><Magic /></el-icon> Agent 规划
        </el-button>
        <el-button type="success" @click="$router.push('/graph')" style="margin-right: 12px;">
          <el-icon><Share /></el-icon> 关系图
        </el-button>
        <el-button type="info" @click="$router.push('/review')" style="margin-right: 12px;">
          <el-icon><Edit /></el-icon> 综述辅助
        </el-button>
        <el-button type="primary" size="large" @click="showUpload = true">
          <el-icon><Upload /></el-icon>
          上传论文
        </el-button>
      </div>
    </div>

    <!-- 论文卡片网格 -->
    <div class="papers-grid" v-if="filteredPapers.length > 0">
      <el-card
        v-for="paper in filteredPapers"
        :key="paper.id"
        class="paper-card"
        shadow="hover"
        @click="goToDetail(paper.id)"
      >
        <div class="paper-card-header">
          <h3 class="paper-title">{{ paper.title }}</h3>
          <el-tag :type="getStatusType(paper.status)" size="small">
            {{ paper.status || '未读' }}
          </el-tag>
        </div>
        <div class="paper-meta">
          <span v-if="paper.authors" class="paper-authors">
            <el-icon><User /></el-icon>
            {{ paper.authors }}
          </span>
          <span v-if="paper.year" class="paper-year">
            <el-icon><Calendar /></el-icon>
            {{ paper.year }}
          </span>
        </div>
        <div class="paper-tags" v-if="paper.tags && paper.tags.length > 0">
          <el-tag
            v-for="tag in paper.tags"
            :key="tag"
            size="small"
            type="warning"
            style="margin-right: 4px; margin-top: 4px"
          >
            #{{ tag }}
          </el-tag>
        </div>
        <div class="paper-card-footer">
          <span class="paper-date">上传于 {{ formatDate(paper.created_at) }}</span>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无文献，点击右上角上传你的第一篇论文吧！" />

    <!-- 上传对话框 -->
    <el-dialog v-model="showUpload" title="上传论文" width="500px">
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
          <div class="el-upload__tip">
            仅支持 PDF 格式，文件大小不超过 50MB
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, UploadFilled, User, Calendar, Search, Magic, Share, Edit } from '@element-plus/icons-vue'
import axios from '../utils/axios'

const router = useRouter()
const papers = ref([])
const searchKeyword = ref('')
const showUpload = ref(false)
const uploadRef = ref(null)

// ===== 上传请求头 =====
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))

// ===== 搜索过滤 =====
const filteredPapers = computed(() => {
  if (!searchKeyword.value) return papers.value
  return papers.value.filter(p =>
    p.title?.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// ===== 辅助函数 =====
const getStatusType = (status) => {
  const map = {
    '已读': 'success',
    '在读': 'warning',
    '未读': 'info'
  }
  return map[status] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

// ===== 跳转详情 =====
const goToDetail = (id) => {
  router.push(`/papers/${id}`)
}

// ===== 加载文献列表 =====
const loadPapers = async () => {
  try {
    const res = await axios.get('/api/papers')
    if (res.data.code === 200 || res.data.code === 0) {
      papers.value = res.data.data || []
    } else {
      loadMockPapers()
    }
  } catch (error) {
    console.warn('加载文献列表失败，使用 Mock 数据:', error)
    loadMockPapers()
  }
}

// ===== Mock 数据 =====
const loadMockPapers = () => {
  papers.value = [
    {
      id: 1,
      title: 'Attention Is All You Need',
      authors: 'Vaswani et al.',
      year: '2017',
      status: '已读',
      tags: ['Transformer', 'NLP'],
      created_at: '2026-07-10T10:00:00'
    },
    {
      id: 2,
      title: 'BERT: Pre-training of Deep Bidirectional Transformers',
      authors: 'Devlin et al.',
      year: '2018',
      status: '在读',
      tags: ['BERT', '预训练'],
      created_at: '2026-07-11T14:30:00'
    },
    {
      id: 3,
      title: 'GPT-3: Language Models are Few-Shot Learners',
      authors: 'Brown et al.',
      year: '2020',
      status: '未读',
      tags: ['GPT', '大语言模型'],
      created_at: '2026-07-12T09:15:00'
    },
    {
      id: 4,
      title: 'ResNet: Deep Residual Learning for Image Recognition',
      authors: 'He et al.',
      year: '2016',
      status: '已读',
      tags: ['CNN', '计算机视觉'],
      created_at: '2026-07-13T08:00:00'
    },
    {
      id: 5,
      title: 'Generative Adversarial Nets',
      authors: 'Goodfellow et al.',
      year: '2014',
      status: '在读',
      tags: ['GAN', '生成模型'],
      created_at: '2026-07-13T09:30:00'
    }
  ]
}

// ===== 上传成功 =====
const onUploadSuccess = (response) => {
  if (response.code === 200 || response.code === 0) {
    ElMessage.success('上传成功！')
    showUpload.value = false
    loadPapers()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

// ===== 上传失败 =====
const onUploadError = (error) => {
  console.error('上传失败:', error)
  ElMessage.error('上传失败，请重试')
}

// ===== 页面加载 =====
onMounted(() => {
  loadPapers()
})
</script>

<style scoped>
.papers-container {
  padding: 24px 40px;
  min-height: 100vh;
  background: #f5f7fa;
}

.papers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a2332;
  margin: 0;
}

.papers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.paper-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
}

.paper-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.paper-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.paper-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a2332;
  margin: 0 0 8px 0;
  line-height: 1.4;
  flex: 1;
}

.paper-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #8c8f9c;
  margin-bottom: 10px;
}

.paper-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.paper-tags {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.paper-card-footer {
  border-top: 1px solid #f0f2f5;
  padding-top: 12px;
  font-size: 12px;
  color: #b0b3bf;
}

@media (max-width: 768px) {
  .papers-container { padding: 16px; }
  .papers-header { flex-direction: column; align-items: stretch; }
  .header-right { flex-wrap: wrap; }
  .header-right .el-input { width: 100% !important; margin-right: 0 !important; }
  .papers-grid { grid-template-columns: 1fr; }
}
</style>