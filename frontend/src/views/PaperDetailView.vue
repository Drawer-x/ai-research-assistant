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
          <span class="summary-badge" v-if="summary">已生成</span>
        </div>
        <el-button
          type="primary"
          size="small"
          :loading="summaryLoading"
          @click="generateSummary"
          :disabled="!paper"
          :icon="summary ? 'Refresh' : 'Plus'"
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
              <span class="summary-item-label">主要结论</span>
              <p>{{ summary.conclusion || '暂无' }}</p>
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
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, User, Calendar, Loading, Edit } from '@element-plus/icons-vue'
import axios from '../utils/axios'

const route = useRoute()
const router = useRouter()
const paperId = ref(route.params.id)

// ===== 状态 =====
const pageLoading = ref(false)
const paper = ref(null)
const summary = ref(null)
const summaryLoading = ref(false)
const question = ref('')
const qaLoading = ref(false)
const qaHistory = ref([])
const qaHistoryRef = ref(null)

// ===== 快捷问题 =====
const quickQuestions = [
  '这篇论文主要解决了什么问题？',
  '用了什么方法和模型？',
  '实验用了什么数据集？',
  '主要结论是什么？',
  '有什么创新点？'
]

// ===== 获取论文详情 =====
const fetchPaperDetail = async () => {
  if (!paperId.value) {
    ElMessage.error('论文 ID 不存在')
    return
  }
  pageLoading.value = true
  try {
    const res = await axios.get(`/api/papers/${paperId.value}`)
    if (res.data.code === 200 || res.data.code === 0) {
      paper.value = res.data.data
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
  if (!paper.value) {
    ElMessage.warning('请先加载论文')
    return
  }
  summaryLoading.value = true
  try {
    const res = await axios.post(`/api/papers/${paperId.value}/summary`)
    if (res.data.code === 200 || res.data.code === 0) {
      summary.value = res.data.data
      ElMessage.success('AI 总结生成成功！')
    } else {
      ElMessage.error(res.data.message || '生成总结失败')
    }
  } catch (error) {
    console.error('生成总结失败:', error)
    // 使用 Mock 数据兜底
    summary.value = {
      background: '近年来，深度学习在自然语言处理领域取得了显著进展，但传统的序列建模方法仍面临并行计算效率低和长距离依赖捕捉困难的问题。',
      problem: '如何设计一种能够高效并行计算且能有效捕捉长距离依赖的序列建模架构？',
      method: '提出了 Transformer 架构，核心是自注意力机制（Self-Attention）和多头注意力（Multi-Head Attention），完全摒弃了 RNN 和 CNN。',
      conclusion: '在 WMT 2014 英德翻译任务上达到 28.4 BLEU，比之前最好的结果提高了 2 BLEU 以上，且训练速度大幅提升。',
      innovation: '1) 首次提出完全基于注意力的序列模型；2) 多头注意力机制捕捉不同子空间的特征；3) 为后续 BERT、GPT 等大模型奠定了基础。',
      limitation: '计算复杂度随序列长度平方增长，在处理超长序列时内存消耗大；模型的可解释性仍有待提高。'
    }
    ElMessage.warning('使用示例数据展示总结效果')
  } finally {
    summaryLoading.value = false
  }
}

// ===== AI 问答 =====
const askQuestion = async () => {
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
    const res = await axios.post(`/api/papers/${paperId.value}/qa`, { question: q })
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
    }
  } catch (error) {
    console.error('问答失败:', error)
    // 使用 Mock 回答兜底
    const mockAnswers = [
      '根据论文内容，该研究主要关注序列建模与机器翻译任务，提出了基于自注意力机制的 Transformer 架构。',
      '论文使用了 WMT 2014 英德翻译数据集（约 450 万对句子）和英法翻译数据集（约 3600 万对句子）。',
      '主要的创新点包括：1) 完全基于注意力的架构；2) 多头注意力机制；3) 位置编码处理序列顺序。',
      '实验结果表明，Transformer 在 WMT 2014 英德翻译上达到 28.4 BLEU，训练时间相比传统序列模型大幅减少。',
      '该架构为 BERT、GPT 等后续大模型奠定了基础，是自然语言处理领域的重要突破。'
    ]
    qaHistory.value.push({
      question: q,
      answer: mockAnswers[qaHistory.value.length % mockAnswers.length]
    })
    question.value = ''
    await nextTick()
    scrollToBottom()
    ElMessage.warning('使用示例回答展示效果')
  } finally {
    qaLoading.value = false
  }
}

// ===== 滚动到底部 =====
const scrollToBottom = () => {
  if (qaHistoryRef.value) {
    qaHistoryRef.value.scrollTop = qaHistoryRef.value.scrollHeight
  }
}

// ===== 辅助函数 =====
const getStatusType = (status) => {
  const map = { '已读': 'success', '在读': 'warning', '未读': 'info' }
  return map[status] || 'info'
}

// ===== 生命周期 =====
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