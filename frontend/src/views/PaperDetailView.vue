<template>
  <div class="detail-container" v-loading="pageLoading">
    <!-- 返回按钮 -->
    <div class="detail-header">
      <el-button @click="$router.back()" type="text" size="large">
        <el-icon><ArrowLeft /></el-icon> 返回文献列表
      </el-button>
    </div>

    <!-- ===== 论文信息卡片 ===== -->
    <div class="detail-card">
      <div v-if="paper" class="paper-info">
        <h1 class="paper-title">{{ paper.title || '未命名论文' }}</h1>
        <div class="paper-meta">
          <span><el-icon><User /></el-icon> {{ paper.authors || '未知作者' }}</span>
          <span><el-icon><Calendar /></el-icon> {{ paper.year || '未知年份' }}</span>
          <el-tag :type="getStatusType(paper.status)" size="small" effect="light">
            {{ paper.status || '未读' }}
          </el-tag>
        </div>
        <div class="paper-tags" v-if="paper.tags && paper.tags.length > 0">
          <el-tag
            v-for="tag in paper.tags"
            :key="tag"
            size="small"
            type="warning"
            effect="plain"
            style="margin-right: 6px; margin-top: 4px"
          >
            #{{ tag }}
          </el-tag>
        </div>
        <div class="paper-abstract">
          <h3>📄 摘要</h3>
          <p>{{ paper.abstract || '暂无摘要' }}</p>
        </div>
      </div>
      <el-empty v-else description="论文不存在或已被删除" />
    </div>

    <!-- ===== AI 总结区域 ===== -->
    <div class="summary-card">
      <div class="summary-header">
        <div class="summary-header-left">
          <span class="summary-icon">🤖</span>
          <h3>AI 论文总结</h3>
          <span class="summary-badge" v-if="summary">{{ summaryIsMock ? 'Fallback/模拟结果' : '已生成' }}</span>
        </div>
        <el-button
          type="primary"
          size="small"
          :loading="summaryLoading"
          @click="generateSummary"
          :disabled="!paper"
        >
          {{ summaryLoading ? '生成中...' : summary ? '重新生成' : '生成总结' }}
        </el-button>
      </div>

      <!-- 加载状态 -->
      <div v-if="summaryLoading" class="summary-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>AI 正在深度阅读论文，请稍候...</span>
        <span class="loading-hint">这可能需要 5-10 秒</span>
      </div>

      <!-- 总结内容 -->
      <div v-else-if="summary" class="summary-content">
        <div class="summary-grid">
          <div class="summary-item">
            <div class="summary-item-icon">📌</div>
            <div class="summary-item-body">
              <span class="summary-item-label">研究背景</span>
              <p>{{ summary.background || '暂无' }}</p>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-item-icon">🎯</div>
            <div class="summary-item-body">
              <span class="summary-item-label">研究问题</span>
              <p>{{ summary.problem || '暂无' }}</p>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-item-icon">⚙️</div>
            <div class="summary-item-body">
              <span class="summary-item-label">核心方法</span>
              <p>{{ summary.method || '暂无' }}</p>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-item-icon">📊</div>
            <div class="summary-item-body">
              <span class="summary-item-label">实验与结果</span>
              <p>{{ [summary.experiment, summary.result].filter(Boolean).join('；') || '暂无' }}</p>
            </div>
          </div>
          <div class="summary-item highlight">
            <div class="summary-item-icon">💡</div>
            <div class="summary-item-body">
              <span class="summary-item-label">创新点</span>
              <p>{{ summary.innovation || '暂无' }}</p>
            </div>
          </div>
          <div class="summary-item warning">
            <div class="summary-item-icon">⚠️</div>
            <div class="summary-item-body">
              <span class="summary-item-label">局限性</span>
              <p>{{ summary.limitation || '暂无' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="点击「生成总结」按钮，AI 将为你深度分析这篇论文" :image-size="80">
        <template #description>
          <p style="color: #999; font-size: 14px; margin: 0;">点击「生成总结」按钮</p>
          <p style="color: #ccc; font-size: 13px; margin: 0;">AI 将为你深度分析这篇论文</p>
        </template>
      </el-empty>
    </div>

    <!-- ===== AI 问答区域 ===== -->
    <div class="qa-card">
      <div class="qa-header">
        <div class="qa-header-left">
          <span class="qa-icon">💬</span>
          <h3>论文问答</h3>
          <span class="qa-badge" v-if="qaHistory.length > 0">{{ qaHistory.length }} 个问答</span>
        </div>
      </div>

      <!-- 问答历史 -->
      <div class="qa-history" v-if="qaHistory.length > 0" ref="qaHistoryRef">
        <div v-for="(item, index) in qaHistory" :key="index" class="qa-item">
          <div class="qa-question">
            <span class="qa-avatar">👤</span>
            <span class="qa-text">{{ item.question }}</span>
          </div>
          <div class="qa-answer">
            <span class="qa-avatar">🤖</span>
            <span class="qa-text">{{ item.answer }}</span>
          </div>
          <div v-if="item.evidence?.length" class="qa-evidence">
            <strong>证据：</strong>
            <div v-for="(evidence, evidenceIndex) in item.evidence" :key="evidenceIndex">{{ evidence }}</div>
          </div>
          <el-tag v-if="item.is_mock" size="small" type="warning">Fallback/模拟结果</el-tag>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="还没有提问，输入问题开始对话" :image-size="60">
        <template #description>
          <p style="color: #999; font-size: 14px; margin: 0;">还没有提问</p>
          <p style="color: #ccc; font-size: 13px; margin: 0;">输入问题，AI 将基于论文内容为你解答</p>
        </template>
      </el-empty>

      <!-- 输入区 -->
      <div class="qa-input">
        <el-input
          v-model="question"
          placeholder="输入你想问的问题，例如：这篇论文用了什么数据集？"
          @keyup.enter="askQuestion"
          :disabled="qaLoading || !paper"
          size="large"
        >
          <template #prefix>
            <el-icon><Edit /></el-icon>
          </template>
        </el-input>
        <el-button
          type="primary"
          size="large"
          :loading="qaLoading"
          @click="askQuestion"
          :disabled="!paper || !question.trim()"
          class="qa-submit-btn"
        >
          {{ qaLoading ? '思考中...' : '提问' }}
        </el-button>
      </div>

      <!-- 快捷提问 -->
      <div class="qa-quick-questions" v-if="quickQuestions.length > 0 && qaHistory.length === 0">
        <span class="quick-label">快速提问：</span>
        <el-tag
          v-for="q in quickQuestions"
          :key="q"
          size="small"
          type="info"
          effect="plain"
          class="quick-tag"
          @click="question = q; askQuestion()"
        >
          {{ q }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, User, Calendar, Loading, Edit } from '@element-plus/icons-vue'
import axios from '../utils/axios'

const route = useRoute()
const router = useRouter()

// ============================================================
// ===== 安全获取论文 ID（使用 computed） =====
// ============================================================
const paperId = computed(() => {
  // 1. 优先从路由参数获取
  if (route.params.id) {
    console.log('✅ 从 route.params.id 获取 ID:', route.params.id)
    return route.params.id
  }
  // 2. 从路径中解析数字 ID
  const match = route.path.match(/\/papers\/(\d+)/)
  if (match) {
    console.log('✅ 从路径中解析 ID:', match[1])
    return match[1]
  }
  // 3. 从 query 参数获取
  if (route.query.id) {
    console.log('✅ 从 route.query.id 获取 ID:', route.query.id)
    return route.query.id
  }
  // 4. 都没有则报错
  console.error('❌ 无法从路由中提取论文 ID，当前路由:', route.path, route.params)
  return null
})

// ============================================================
// ===== 状态 =====
// ============================================================
const pageLoading = ref(false)
const paper = ref(null)
const summary = ref(null)
const summaryLoading = ref(false)
const summaryIsMock = ref(false)
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

// ============================================================
// ===== 获取论文详情 =====
// ============================================================
const fetchPaperDetail = async () => {
  const id = paperId.value
  if (!id) {
    ElMessage.error('论文 ID 不存在，请从文献列表重新进入')
    return
  }

  console.log('📄 正在获取论文详情，ID:', id)

  pageLoading.value = true
  try {
    const res = await axios.get(`/api/papers/${id}`)
    console.log('📄 论文详情响应:', res.data)
    
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data
      // 兼容 paper_id 和 id
      paper.value = {
        ...data,
        id: data.paper_id || data.id
      }
      await Promise.all([loadSummaryHistory(), loadQaHistory()])
    } else {
      ElMessage.error(res.data.message || '获取论文详情失败')
    }
  } catch (error) {
    console.error('获取论文详情失败:', error)
    ElMessage.error(error.response?.data?.message || '获取论文详情失败，请检查网络')
  } finally {
    pageLoading.value = false
  }
}

// ============================================================
// ===== AI 总结 =====
// ============================================================
const generateSummary = async () => {
  const id = paperId.value
  if (!paper.value) {
    ElMessage.warning('请先加载论文')
    return
  }

  summaryLoading.value = true
  try {
    const res = await axios.post(`/api/papers/${id}/summary`)
    console.log('📄 AI 总结响应:', res.data)
    
    if (res.data.code === 200 || res.data.code === 0) {
      summary.value = res.data.data.summary
      summaryIsMock.value = Boolean(res.data.data.is_mock)
      ElMessage.success('AI 总结生成成功！')
    } else {
      ElMessage.error(res.data.message || '生成总结失败')
    }
  } catch (error) {
    console.error('生成总结失败:', error)
    ElMessage.error(error.response?.data?.message || '生成总结失败')
  } finally {
    summaryLoading.value = false
  }
}

const loadSummaryHistory = async () => {
  const res = await axios.get(`/api/papers/${paperId.value}/summaries`)
  const latest = res.data.data?.[0]
  summary.value = latest?.content || null
  summaryIsMock.value = Boolean(latest?.is_mock)
}

const loadQaHistory = async () => {
  const res = await axios.get(`/api/papers/${paperId.value}/qa-records`)
  qaHistory.value = res.data.data || []
}

// ============================================================
// ===== AI 问答 =====
// ============================================================
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
    const res = await axios.post(`/api/papers/${id}/qa`, { question: q })
    console.log('📄 问答响应:', res.data)
    
    if (res.data.code === 200 || res.data.code === 0) {
      qaHistory.value.push({
        question: q,
        answer: res.data.data.answer || '暂无回答',
        evidence: res.data.data.evidence || [],
        is_mock: Boolean(res.data.data.is_mock)
      })
      question.value = ''
      await nextTick()
      scrollToBottom()
    } else {
      ElMessage.error(res.data.message || '问答失败')
    }
  } catch (error) {
    console.error('问答失败:', error)
    ElMessage.error(error.response?.data?.message || '问答失败')
  } finally {
    qaLoading.value = false
  }
}


const scrollToBottom = () => {
  if (qaHistoryRef.value) {
    qaHistoryRef.value.scrollTop = qaHistoryRef.value.scrollHeight
  }
}

const getStatusType = (status) => {
  const map = { '已读': 'success', '在读': 'warning', '未读': 'info' }
  return map[status] || 'info'
}

onMounted(() => {
  fetchPaperDetail()
})
</script>

<style scoped>
/* ============================================================
   ===== 容器 =====
   ============================================================ */
.detail-container {
  padding: 24px 40px;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f0f4f9;
}

.detail-header {
  margin-bottom: 20px;
}
.detail-header .el-button {
  font-size: 15px;
  font-weight: 500;
  color: #667eea;
}

/* ============================================================
   ===== 论文信息卡片 =====
   ============================================================ */
.detail-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.paper-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a2332;
  margin-bottom: 12px;
  line-height: 1.4;
}
.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}
.paper-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.paper-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 16px;
}
.paper-abstract h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 8px;
}
.paper-abstract p {
  color: #555;
  line-height: 1.8;
}

/* ============================================================
   ===== AI 总结卡片 =====
   ============================================================ */
.summary-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.summary-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.summary-icon {
  font-size: 24px;
}
.summary-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a2332;
}
.summary-badge {
  font-size: 12px;
  color: #67c23a;
  background: #e8f5e9;
  padding: 2px 12px;
  border-radius: 12px;
}

.summary-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
  color: #909399;
}
.summary-loading .el-icon {
  font-size: 32px;
  animation: rotating 1.5s linear infinite;
}
.loading-hint {
  font-size: 13px;
  color: #b0b3bf;
}
@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.summary-item {
  display: flex;
  gap: 12px;
  padding: 14px 18px;
  background: #f8f9fb;
  border-radius: 10px;
  transition: background 0.2s;
}
.summary-item:hover {
  background: #f0f2f5;
}
.summary-item.highlight {
  background: #f0f4ff;
  border: 1px solid rgba(102, 126, 234, 0.15);
}
.summary-item.warning {
  background: #fdf6ed;
  border: 1px solid rgba(230, 162, 60, 0.15);
}
.summary-item-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}
.summary-item-body {
  flex: 1;
  min-width: 0;
}
.summary-item-label {
  display: block;
  font-weight: 600;
  color: #1a2332;
  font-size: 13px;
  margin-bottom: 2px;
}
.summary-item-body p {
  color: #555;
  line-height: 1.6;
  margin: 0;
  font-size: 14px;
}

/* ============================================================
   ===== 问答区域 =====
   ============================================================ */
.qa-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
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
  font-size: 24px;
}
.qa-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a2332;
}
.qa-badge {
  font-size: 12px;
  color: #667eea;
  background: #f0f4ff;
  padding: 2px 12px;
  border-radius: 12px;
}

.qa-history {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 16px;
  padding-right: 4px;
}
.qa-history::-webkit-scrollbar {
  width: 4px;
}
.qa-history::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 2px;
}

.qa-item {
  margin-bottom: 14px;
}
.qa-item:last-child {
  margin-bottom: 0;
}
.qa-question {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: #f0f4ff;
  border-radius: 12px 12px 4px 12px;
  margin-bottom: 6px;
}
.qa-answer {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: #f8f9fb;
  border-radius: 12px 12px 12px 4px;
}
.qa-avatar {
  font-size: 18px;
  flex-shrink: 0;
}
.qa-text {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}
.qa-answer .qa-text {
  color: #555;
}

.qa-input {
  display: flex;
  gap: 12px;
}
.qa-input .el-input {
  flex: 1;
}
.qa-submit-btn {
  flex-shrink: 0;
  padding: 0 28px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
}
.qa-submit-btn:hover {
  box-shadow: 0 8px 28px rgba(102, 126, 234, 0.35) !important;
}

.qa-quick-questions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #f0f2f5;
}
.quick-label {
  font-size: 13px;
  color: #8c8f9c;
}
.quick-tag {
  cursor: pointer;
  transition: all 0.2s;
}
.quick-tag:hover {
  background: #667eea !important;
  color: #fff !important;
  border-color: #667eea !important;
  transform: translateY(-1px);
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 768px) {
  .detail-container { padding: 16px; }
  .detail-card, .summary-card, .qa-card { padding: 20px; }
  .paper-title { font-size: 20px; }
  .summary-grid { grid-template-columns: 1fr; }
  .summary-header { flex-direction: column; gap: 12px; align-items: stretch; }
  .qa-input { flex-direction: column; }
  .qa-submit-btn { padding: 0 !important; height: 44px; }
  .qa-quick-questions { flex-direction: column; align-items: flex-start; }
}
</style>
