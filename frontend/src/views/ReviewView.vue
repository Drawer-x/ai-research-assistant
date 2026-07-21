<template>
  <div class="review-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"/>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
          </svg>
        </span>
        <span class="title-text">综述辅助</span>
        <span class="title-badge">{{ allPapers.length }} 篇可对比</span>
      </h1>
      <p class="page-desc">选择多篇论文，AI 帮你生成对比分析和综述大纲</p>
    </div>

    <!-- ===== 论文选择 ===== -->
    <div class="selection-card">
      <div class="selection-header">
        <span class="selection-label">选择论文（已选 {{ selectedIds.length }} 篇）</span>
        <div class="selection-actions">
          <button class="btn-ghost-sm" @click="selectAll">全选</button>
          <button class="btn-ghost-sm" @click="clearSelection">清空</button>
          <button 
            class="btn-primary-sm" 
            @click="generateCompare" 
            :disabled="selectedIds.length < 2 || compareLoading"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
              <line x1="15" y1="3" x2="15" y2="21"/>
            </svg>
            {{ compareLoading ? '生成中...' : '对比分析' }}
          </button>
          <button 
            class="btn-primary-sm btn-success" 
            @click="generateOutline" 
            :disabled="selectedIds.length < 2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
            生成大纲
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <span class="loading-spinner"></span>
        <span>加载论文列表...</span>
      </div>

      <!-- 论文列表 -->
      <div v-else-if="allPapers.length > 0" class="paper-select-list">
        <div
          v-for="paper in allPapers"
          :key="paper.id"
          class="paper-select-item"
          :class="{ selected: isSelected(paper.id) }"
          @click="toggleSelect(paper.id)"
        >
          <div class="checkbox" :class="{ checked: isSelected(paper.id) }">
            <svg v-if="isSelected(paper.id)" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <span class="select-title">{{ paper.title }}</span>
          <span class="select-meta">{{ paper.authors }} · {{ paper.year }}</span>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-papers">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </div>
        <p>暂无文献，请先去文献库上传论文</p>
        <button class="btn-primary-sm" @click="$router.push('/papers')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          去上传
        </button>
      </div>
    </div>

    <!-- ===== 对比结果 ===== -->
    <div v-if="compareResult" class="result-card">
      <div class="result-header">
        <h3>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <line x1="9" y1="3" x2="9" y2="21"/>
            <line x1="15" y1="3" x2="15" y2="21"/>
          </svg>
          论文对比分析
          <span v-if="compareIsMock" class="mock-badge">示例数据</span>
        </h3>
        <button class="btn-ghost-sm" @click="compareResult = null">关闭</button>
      </div>
      <div class="table-wrapper">
        <table class="compare-table">
          <thead>
            <tr>
              <th>论文</th>
              <th>研究问题</th>
              <th>核心方法</th>
              <th>数据集</th>
              <th>主要结果</th>
              <th>局限性</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in compareResult" :key="idx">
              <td><strong>{{ row.paper }}</strong></td>
              <td>{{ row.problem }}</td>
              <td>{{ row.method }}</td>
              <td>{{ row.dataset }}</td>
              <td>{{ row.result }}</td>
              <td>{{ row.limitation }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===== 综述大纲 ===== -->
    <div v-if="outlineResult" class="result-card">
      <div class="result-header">
        <h3>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"/>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
          </svg>
          综述大纲
        </h3>
        <button class="btn-ghost-sm" @click="outlineResult = null">关闭</button>
      </div>
      <div class="outline-content">
        <div v-for="(section, idx) in outlineResult" :key="idx" class="outline-section">
          <h4>{{ idx + 1 }}. {{ section.title }}</h4>
          <ul>
            <li v-for="(sub, si) in section.subsections" :key="si">{{ sub }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-if="!compareResult && !outlineResult && allPapers.length > 0" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20h9"/>
          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
        </svg>
      </div>
      <h3>选择论文进行对比</h3>
      <p>选择至少 2 篇论文，生成对比分析或综述大纲</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

// ===== 状态 =====
const allPapers = ref([])
const selectedIds = ref([])
const compareResult = ref(null)
const outlineResult = ref(null)
const loading = ref(false)
const compareLoading = ref(false)
const compareIsMock = ref(false)

// ===== 固定的 5 篇 Mock 论文 =====
const mockPapers = [
  { id: 1, title: 'Attention Is All You Need', authors: 'Vaswani et al.', year: '2017', tags: ['Transformer'] },
  { id: 2, title: 'BERT: Pre-training of Deep Bidirectional Transformers', authors: 'Devlin et al.', year: '2018', tags: ['BERT'] },
  { id: 3, title: 'GPT-3: Language Models are Few-Shot Learners', authors: 'Brown et al.', year: '2020', tags: ['GPT'] },
  { id: 4, title: 'ResNet: Deep Residual Learning', authors: 'He et al.', year: '2016', tags: ['CNN'] },
  { id: 5, title: 'GAN: Generative Adversarial Nets', authors: 'Goodfellow et al.', year: '2014', tags: ['GAN'] }
]

// ===== 获取论文列表（合并真实 + Mock） =====
const loadPapers = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/papers')
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || []
      const realPapers = data.map(item => ({
        id: item.paper_id || item.id,
        title: item.title || '未命名论文',
        authors: item.authors || '未知作者',
        year: item.year || '未知年份',
        tags: item.tags || []
      }))
      
      // 合并：真实论文 + Mock 论文（去重）
      const realIds = new Set(realPapers.map(p => p.id))
      const merged = [...realPapers]
      mockPapers.forEach(m => {
        if (!realIds.has(m.id)) {
          merged.push(m)
        }
      })
      allPapers.value = merged
      
      if (allPapers.value.length === 0) {
        ElMessage.info('暂无文献')
      }
    } else {
      // 接口失败，直接使用 Mock
      allPapers.value = [...mockPapers]
      ElMessage.warning('加载失败，使用示例数据')
    }
  } catch (error) {
    console.error('加载论文列表失败:', error)
    // 接口异常，使用 Mock
    allPapers.value = [...mockPapers]
    ElMessage.warning('网络异常，使用示例数据')
  } finally {
    loading.value = false
  }
}

// ===== 选择逻辑 =====
const isSelected = (id) => selectedIds.value.includes(id)

const toggleSelect = (id) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

const selectAll = () => {
  selectedIds.value = allPapers.value.map(p => p.id)
}

const clearSelection = () => {
  selectedIds.value = []
  compareResult.value = null
  outlineResult.value = null
}

// ===== 生成对比分析 =====
const generateCompare = async () => {
  if (selectedIds.value.length < 2) {
    ElMessage.warning('请至少选择 2 篇论文')
    return
  }

  compareLoading.value = true
  compareIsMock.value = false

  try {
    const res = await axios.post('/api/papers/compare', {
      paper_ids: selectedIds.value,
      compare_dimensions: ['problem', 'method', 'dataset', 'result', 'limitation']
    })
    
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data
      if (data.comparison_table && data.comparison_table.length > 0) {
        compareResult.value = data.comparison_table.map(row => ({
          paper: row.title || row.paper,
          problem: row.problem || '—',
          method: row.method || '—',
          dataset: row.dataset || '—',
          result: row.result || '—',
          limitation: row.limitation || '—'
        }))
        ElMessage.success('对比分析生成完成！')
        compareLoading.value = false
        return
      }
    }
    // 接口返回格式异常，使用 Mock
    generateMockCompare()
  } catch (error) {
    console.error('对比失败:', error)
    if (error.response?.status === 422) {
      ElMessage.warning('接口参数错误，使用示例数据')
    } else {
      ElMessage.warning('接口调用失败，使用示例数据')
    }
    generateMockCompare()
  } finally {
    compareLoading.value = false
  }
}

// ===== Mock 对比数据 =====
const generateMockCompare = () => {
  compareIsMock.value = true
  const topics = ['Transformer 架构研究', '预训练语言模型', '大规模语言模型', '残差网络优化', '生成对抗网络']
  const methods = ['Multi-Head Attention', 'Masked LM', 'Few-shot Learning', 'Residual Learning', 'Adversarial Training']
  const datasets = ['WMT 2014', 'BookCorpus', 'Common Crawl', 'ImageNet', 'MNIST']
  const results = ['BLEU 28.4', 'SOTA on GLUE', '175B parameters', 'Top-5 Error 3.57%', 'Realistic Image Generation']
  const limitations = ['长序列计算量大', '预训练成本高', '推理延迟大', '需要大量标注数据', '训练不稳定']

  const selectedPapers = allPapers.value.filter(p => selectedIds.value.includes(p.id))
  compareResult.value = selectedPapers.map((p, i) => ({
    paper: p.title,
    problem: topics[i % topics.length],
    method: methods[i % methods.length],
    dataset: datasets[i % datasets.length],
    result: results[i % results.length],
    limitation: limitations[i % limitations.length]
  }))
  
  if (!compareResult.value || compareResult.value.length === 0) {
    compareResult.value = [
      { paper: '论文 A', problem: '示例问题', method: '示例方法', dataset: '示例数据集', result: '示例结果', limitation: '示例局限性' },
      { paper: '论文 B', problem: '示例问题', method: '示例方法', dataset: '示例数据集', result: '示例结果', limitation: '示例局限性' }
    ]
  }
  ElMessage.info('使用示例数据展示对比效果')
}

// ===== 生成综述大纲 =====
const generateOutline = () => {
  if (selectedIds.value.length < 2) {
    ElMessage.warning('请至少选择 2 篇论文')
    return
  }

  const selectedPapers = allPapers.value.filter(p => selectedIds.value.includes(p.id))

  outlineResult.value = [
    {
      title: '引言',
      subsections: [
        '研究背景与意义',
        '当前研究现状与挑战',
        '本文综述范围与结构'
      ]
    },
    {
      title: '相关方法综述',
      subsections: selectedPapers.map(p => `${p.title} 核心思想与贡献`)
    },
    {
      title: '方法对比分析',
      subsections: [
        '模型架构对比',
        '训练策略对比',
        '性能对比分析'
      ]
    },
    {
      title: '未来展望',
      subsections: [
        '当前方法的局限性',
        '未来研究方向',
        '总结与结论'
      ]
    }
  ]

  ElMessage.success('综述大纲生成完成！')
}

// ===== 页面加载 =====
onMounted(() => {
  loadPapers()
})
</script>

<style scoped>
/* ===== 容器 ===== */
.review-container {
  padding: 24px 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.04) 0%, transparent 50%),
                    radial-gradient(ellipse at 90% 80%, rgba(123, 200, 164, 0.04) 0%, transparent 50%);
}

/* ===== 顶部 ===== */
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
  flex-wrap: wrap;
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

/* ===== 选择卡片 ===== */
.selection-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.selection-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 15px;
}

.selection-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* ===== 按钮 ===== */
.btn-ghost-sm {
  padding: 6px 16px;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(248, 250, 255, 0.6);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-ghost-sm:hover {
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-primary);
}

.btn-primary-sm {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 18px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.2);
}

.btn-primary-sm:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 20px rgba(95, 195, 228, 0.3);
}

.btn-primary-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-primary-sm.btn-success {
  background: linear-gradient(135deg, #7bc8a4, #5cb88a);
  box-shadow: 0 2px 12px rgba(123, 200, 164, 0.2);
}

.btn-primary-sm.btn-success:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(123, 200, 164, 0.3);
}

.btn-primary-sm svg {
  stroke: #fff;
}

/* ===== 加载状态 ===== */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 30px 0;
  color: var(--text-muted);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(95, 195, 228, 0.1);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== 论文选择列表 ===== */
.paper-select-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 340px;
  overflow-y: auto;
}

.paper-select-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.paper-select-item:hover {
  background: rgba(248, 250, 255, 0.6);
}

.paper-select-item.selected {
  background: rgba(95, 195, 228, 0.06);
  border-color: rgba(95, 195, 228, 0.15);
}

.checkbox {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 2px solid #d0d5dd;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.checkbox.checked {
  background: var(--primary-gradient);
  border-color: var(--primary-500);
}

.checkbox.checked svg {
  stroke: #fff;
}

.select-title {
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  font-size: 14px;
}

.select-meta {
  font-size: 13px;
  color: var(--text-muted);
  flex-shrink: 0;
}

/* ===== 空论文 ===== */
.empty-papers {
  text-align: center;
  padding: 30px 20px;
  color: var(--text-muted);
}

.empty-papers .empty-icon {
  opacity: 0.4;
  margin-bottom: 8px;
}

.empty-papers p {
  margin: 0 0 12px 0;
  font-size: 14px;
}

/* ===== 结果卡片 ===== */
.result-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
  animation: fadeUp 0.3s ease;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.result-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-header h3 svg {
  stroke: var(--text-primary);
}

.mock-badge {
  font-size: 11px;
  font-weight: 500;
  color: #c47a7a;
  background: rgba(245, 160, 160, 0.1);
  padding: 2px 12px;
  border-radius: var(--radius-full);
}

/* ===== 对比表格 ===== */
.table-wrapper {
  overflow-x: auto;
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.compare-table thead {
  background: rgba(248, 250, 255, 0.6);
}

.compare-table th {
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 2px solid rgba(0, 0, 0, 0.05);
  white-space: nowrap;
}

.compare-table td {
  padding: 10px 14px;
  color: var(--text-secondary);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  line-height: 1.5;
}

.compare-table tbody tr:hover {
  background: rgba(248, 250, 255, 0.4);
}

.compare-table tbody tr:last-child td {
  border-bottom: none;
}

.compare-table td strong {
  color: var(--text-primary);
}

/* ===== 综述大纲 ===== */
.outline-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.outline-section h4 {
  color: var(--text-primary);
  margin: 0 0 6px 0;
  font-size: 16px;
  font-weight: 600;
}

.outline-section ul {
  padding-left: 20px;
  margin: 0;
}

.outline-section li {
  padding: 3px 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

/* ===== 空状态 ===== */
.empty-state {
  text-align: center;
  padding: 50px 20px;
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
  margin: 0;
  font-size: 15px;
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 768px) {
  .review-container {
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

  .selection-card {
    padding: 18px 16px;
  }

  .selection-header {
    flex-direction: column;
    align-items: stretch;
  }

  .selection-actions {
    justify-content: stretch;
  }

  .selection-actions button {
    flex: 1;
    justify-content: center;
  }

  .result-card {
    padding: 18px 16px;
  }

  .compare-table th,
  .compare-table td {
    padding: 8px 10px;
    font-size: 13px;
  }

  .outline-section h4 {
    font-size: 15px;
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

  .compare-table th,
  .compare-table td {
    padding: 6px 8px;
    font-size: 12px;
  }

  .select-meta {
    font-size: 12px;
  }

  .checkbox {
    width: 18px;
    height: 18px;
  }

  .paper-select-item {
    padding: 8px 10px;
  }
}
</style>