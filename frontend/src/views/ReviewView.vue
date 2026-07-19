<template>
  <div class="review-container">
    <!-- 顶部 -->
    <div class="review-header">
      <h1 class="page-title">📝 综述辅助</h1>
      <p class="page-desc">选择多篇论文，AI 帮你生成对比分析和综述大纲</p>
    </div>

    <!-- 论文选择 -->
    <div class="selection-card">
      <div class="selection-header">
        <span class="selection-label">选择论文（已选 {{ selectedPapers.length }} 篇）</span>
        <div>
          <el-button size="small" @click="clearSelection">清空</el-button>
          <el-button size="small" type="primary" @click="generateCompare" :loading="compareLoading" :disabled="selectedPapers.length < 2">
            生成对比分析
          </el-button>
          <el-button size="small" type="success" @click="generateOutline" :disabled="selectedPapers.length < 2">
            生成综述大纲
          </el-button>
        </div>
      </div>
      <div class="paper-select-list">
        <div
          v-for="paper in allPapers"
          :key="paper.id"
          class="paper-select-item"
          :class="{ selected: isSelected(paper.id) }"
          @click="toggleSelect(paper.id)"
        >
          <el-checkbox :model-value="isSelected(paper.id)" @click.stop />
          <span class="select-title">{{ paper.title }}</span>
          <span class="select-meta">{{ paper.authors }} · {{ paper.year }}</span>
        </div>
      </div>
    </div>

    <!-- 对比结果 -->
    <div v-if="compareResult" class="result-card">
      <div class="result-header">
        <h3>📊 论文对比分析</h3>
        <el-button size="small" @click="compareResult = null">关闭</el-button>
      </div>
      <el-tag v-if="compareIsMock" type="warning" size="small">Fallback/模拟结果</el-tag>
      <el-table :data="compareResult" border stripe style="width: 100%; margin-top: 12px">
        <el-table-column prop="title" label="论文" width="180" />
        <el-table-column prop="problem" label="研究问题" />
        <el-table-column prop="method" label="核心方法" width="150" />
        <el-table-column prop="dataset" label="数据集" width="140" />
        <el-table-column prop="result" label="主要结果" />
        <el-table-column prop="limitation" label="局限性" width="140" />
      </el-table>
      <p class="comparison-summary">{{ compareSummary }}</p>
    </div>

    <!-- 综述大纲 -->
    <div v-if="outlineResult" class="result-card">
      <div class="result-header">
        <h3>📑 综述大纲</h3>
        <el-button size="small" @click="outlineResult = null">关闭</el-button>
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

    <!-- 空状态 -->
    <el-empty v-if="!compareResult && !outlineResult" description="选择至少两篇论文，生成对比分析或综述大纲" :image-size="100" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

// ===== 论文数据（从文献列表同步） =====
const allPapers = ref([])

const selectedIds = ref([])
const compareResult = ref(null)
const outlineResult = ref(null)
const compareLoading = ref(false)
const compareSummary = ref('')
const compareIsMock = ref(false)

// ===== 辅助 =====
const selectedPapers = computed(() => allPapers.value.filter(p => selectedIds.value.includes(p.id)))

const isSelected = (id) => selectedIds.value.includes(id)

const toggleSelect = (id) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

const clearSelection = () => {
  selectedIds.value = []
  compareResult.value = null
  outlineResult.value = null
}

const loadPapers = async () => {
  try {
    const response = await axios.get('/api/papers')
    allPapers.value = response.data.data || []
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '加载论文列表失败')
  }
}

const loadComparisonHistory = async () => {
  try {
    const response = await axios.get('/api/papers/comparisons')
    const latest = response.data.data?.[0]
    if (latest?.result) {
      compareResult.value = latest.result.comparison_table || []
      compareSummary.value = latest.result.summary || ''
      compareIsMock.value = Boolean(latest.is_mock)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '加载对比历史失败')
  }
}

// ===== 调用后端生成并持久化对比分析 =====
const generateCompare = async () => {
  if (selectedPapers.value.length < 2) {
    ElMessage.warning('请至少选择2篇论文')
    return
  }

  compareLoading.value = true
  try {
    const response = await axios.post('/api/papers/compare', {
      paper_ids: selectedIds.value,
      compare_dimensions: ['problem', 'method', 'dataset', 'result', 'limitation']
    })
    const data = response.data.data
    compareResult.value = data.comparison_table || []
    compareSummary.value = data.summary || ''
    compareIsMock.value = Boolean(data.is_mock)
    ElMessage.success('对比分析生成完成！')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '对比分析失败')
  } finally {
    compareLoading.value = false
  }
}

// ===== 生成综述大纲（Mock） =====
const generateOutline = () => {
  if (selectedPapers.value.length < 2) {
    ElMessage.warning('请至少选择2篇论文')
    return
  }

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
      subsections: selectedPapers.value.map(p => `${p.title} 核心思想与贡献`)
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

onMounted(() => Promise.all([loadPapers(), loadComparisonHistory()]))
</script>

<style scoped>
.review-container {
  padding: 24px 40px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f7fa;
}

.review-header {
  margin-bottom: 28px;
}
.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a2332;
  margin-bottom: 4px;
}
.page-desc {
  color: #8c8f9c;
  font-size: 15px;
}

.selection-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 24px;
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
  color: #1a2332;
}

.paper-select-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 300px;
  overflow-y: auto;
}
.paper-select-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border: 1px solid transparent;
}
.paper-select-item:hover {
  background: #f5f7fa;
}
.paper-select-item.selected {
  background: #ecf5ff;
  border-color: #667eea;
}
.select-title {
  font-weight: 500;
  color: #1a2332;
  flex: 1;
}
.select-meta {
  font-size: 13px;
  color: #999;
}

.result-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 24px;
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
  margin: 0;
  font-size: 18px;
  color: #1a2332;
}

.outline-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.comparison-summary { color: #555; line-height: 1.7; }
.outline-section h4 {
  color: #1a2332;
  margin: 0 0 6px 0;
  font-size: 16px;
}
.outline-section ul {
  padding-left: 20px;
  margin: 0;
}
.outline-section li {
  padding: 2px 0;
  color: #555;
}

@media (max-width: 768px) {
  .review-container { padding: 16px; }
  .selection-header { flex-direction: column; align-items: stretch; }
}
</style>
