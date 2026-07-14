<template>
  <div class="graph-container">
    <!-- 顶部操作栏 -->
    <div class="graph-header">
      <div class="header-left">
        <h1 class="page-title">🔗 文献关系图谱</h1>
        <el-tag type="info" size="large">节点 {{ nodes.length }} 个 · 关系 {{ edges.length }} 条</el-tag>
      </div>
      <div class="header-right">
        <el-radio-group v-model="layout" size="small" @change="applyLayout">
          <el-radio-button value="force">力导向</el-radio-button>
          <el-radio-button value="circular">环形</el-radio-button>
          <el-radio-button value="grid">网格</el-radio-button>
        </el-radio-group>
        <el-button size="small" @click="resetZoom" style="margin-left: 8px">
          <el-icon><Refresh /></el-icon> 重置
        </el-button>
        <el-button size="small" type="primary" :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 图例 -->
    <div class="graph-legend">
      <span class="legend-item">
        <span class="legend-color" style="background: #667eea;"></span> 引用关系
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #f093fb;"></span> 主题相似
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #4facfe;"></span> 方法相似
      </span>
      <span class="legend-item" style="margin-left: auto;">
        <el-switch v-model="showLabels" size="small" active-text="标签" inactive-text="标签" />
      </span>
    </div>

    <!-- 图表 -->
    <div class="graph-wrapper">
      <div ref="chartRef" class="graph-chart"></div>
      <div v-if="loading" class="graph-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载图谱数据...</span>
      </div>
      <el-empty v-else-if="nodes.length === 0" description="暂无关系数据" />
    </div>

    <!-- 节点详情抽屉 -->
    <el-drawer v-model="showDetail" title="论文详情" direction="rtl" size="420px">
      <div v-if="selectedNode" class="node-detail">
        <h2 class="node-title">{{ selectedNode.label || selectedNode.name }}</h2>
        <div class="node-meta">
          <p><strong>作者：</strong>{{ selectedNode.authors || '未知' }}</p>
          <p><strong>年份：</strong>{{ selectedNode.year || '未知' }}</p>
          <p><strong>状态：</strong>
            <el-tag :type="getStatusType(selectedNode.status)" size="small">
              {{ selectedNode.status || '未读' }}
            </el-tag>
          </p>
        </div>
        <div class="node-tags" v-if="selectedNode.tags?.length">
          <strong>标签：</strong>
          <el-tag v-for="tag in selectedNode.tags" :key="tag" size="small" type="warning" style="margin-right:4px;">
            #{{ tag }}
          </el-tag>
        </div>
        <div class="node-relations">
          <strong>关联关系：</strong>
          <ul>
            <li v-for="(rel, idx) in nodeRelations" :key="idx">
              {{ rel.target }} — <el-tag size="small" :type="getRelationType(rel.type)">{{ rel.type }}</el-tag>
            </li>
          </ul>
        </div>
        <el-button type="primary" @click="goToDetail(selectedNode.id)" style="margin-top:16px; width:100%;">
          查看完整论文
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from '../utils/axios'

const router = useRouter()
const chartRef = ref(null)
let chartInstance = null

// ===== 状态 =====
const loading = ref(false)
const nodes = ref([])
const edges = ref([])
const layout = ref('force')
const showLabels = ref(true)
const showDetail = ref(false)
const selectedNode = ref(null)
const nodeRelations = ref([])

// ===== 加载数据 =====
const loadData = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/graph/papers')
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || res.data
      nodes.value = data.nodes || []
      edges.value = data.edges || []
      if (nodes.value.length === 0) {
        ElMessage.info('暂无关系数据，使用示例数据')
        loadMockData()
      }
    } else {
      loadMockData()
    }
  } catch {
    loadMockData()
  } finally {
    loading.value = false
    await nextTick()
    renderChart()
  }
}

// ===== Mock 数据 =====
const loadMockData = () => {
  nodes.value = [
    { id: 1, label: 'Attention Is All You Need', authors: 'Vaswani et al.', year: '2017', status: '已读', tags: ['Transformer', 'NLP'], category: 0 },
    { id: 2, label: 'BERT', authors: 'Devlin et al.', year: '2018', status: '在读', tags: ['BERT', '预训练'], category: 0 },
    { id: 3, label: 'GPT-3', authors: 'Brown et al.', year: '2020', status: '未读', tags: ['GPT', '大语言模型'], category: 0 },
    { id: 4, label: 'ResNet', authors: 'He et al.', year: '2016', status: '已读', tags: ['CNN', 'CV'], category: 1 },
    { id: 5, label: 'GAN', authors: 'Goodfellow et al.', year: '2014', status: '在读', tags: ['生成模型', 'CV'], category: 1 },
    { id: 6, label: 'CLIP', authors: 'Radford et al.', year: '2021', status: '未读', tags: ['多模态', 'CV'], category: 1 }
  ]
  edges.value = [
    { source: 1, target: 2, type: '引用', category: 0 },
    { source: 1, target: 3, type: '引用', category: 0 },
    { source: 2, target: 3, type: '方法相似', category: 2 },
    { source: 1, target: 4, type: '主题相似', category: 1 },
    { source: 4, target: 5, type: '引用', category: 0 },
    { source: 4, target: 6, type: '主题相似', category: 1 },
    { source: 5, target: 6, type: '方法相似', category: 2 }
  ]
}

// ===== 渲染图表 =====
const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const colors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#fee140']
  const categoryMap = ['引用关系', '主题相似', '方法相似']

  const option = {
    title: {
      text: '文献关系图谱',
      subtext: '点击节点查看详情 · 拖拽可移动',
      left: 'center',
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 600 },
      subtextStyle: { fontSize: 12, color: '#999' }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          const d = params.data
          return `<strong>${d.label}</strong><br/>作者：${d.authors || '未知'}<br/>年份：${d.year || '未知'}`
        }
        return `${params.data.source} → ${params.data.target}<br/>类型：${params.data.type}`
      }
    },
    legend: {
      data: categoryMap,
      top: 60,
      left: 'center',
      icon: 'roundRect',
      itemWidth: 16,
      itemHeight: 10
    },
    series: [{
      type: 'graph',
      layout: layout.value === 'force' ? 'force' : 'none',
      force: {
        repulsion: 500,
        edgeLength: [180, 350],
        gravity: 0.1
      },
      roam: true,
      draggable: true,
      data: nodes.value.map((node, idx) => ({
        ...node,
        symbolSize: 35 + Math.random() * 30,
        itemStyle: {
          color: colors[idx % colors.length],
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.08)'
        },
        label: {
          show: showLabels.value,
          fontSize: 11,
          fontWeight: 500,
          color: '#333',
          offset: [0, 8],
          formatter: (p) => {
            const text = p.data.label || p.data.name || ''
            return text.length > 15 ? text.slice(0, 15) + '...' : text
          }
        }
      })),
      links: edges.value.map(edge => ({
        ...edge,
        label: {
          show: true,
          formatter: edge.label || edge.relation_type || edge.type,
          fontSize: 10,
          color: '#999',
          offset: [0, -8]
        },
        lineStyle: {
          color: edge.category === 0 ? '#667eea' : edge.category === 1 ? '#f093fb' : '#4facfe',
          width: 2,
          curveness: 0.15,
          opacity: 0.7
        }
      })),
      categories: categoryMap.map((name, i) => ({
        name,
        itemStyle: { color: ['#667eea', '#f093fb', '#4facfe'][i] }
      })),
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 8],
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3 }
      }
    }]
  }

  chartInstance.setOption(option, true)
  chartInstance.resize()

  chartInstance.off('click')
  chartInstance.on('click', (params) => {
    if (params.dataType === 'node') {
      selectedNode.value = params.data
      updateNodeRelations(params.data)
      showDetail.value = true
    }
  })
}

// ===== 切换布局 =====
const applyLayout = () => renderChart()

// ===== 重置视图 =====
const resetZoom = () => {
  if (chartInstance) chartInstance.dispatchAction({ type: 'restore' })
}

// ===== 更新关联关系 =====
const updateNodeRelations = (node) => {
  if (!node) { nodeRelations.value = []; return }
  const related = edges.value
    .filter(e => e.source === node.id || e.target === node.id)
    .map(e => {
      const targetId = e.source === node.id ? e.target : e.source
      const targetNode = nodes.value.find(n => n.id === targetId)
      return {
        target: targetNode?.label || targetNode?.name || '未知',
        type: e.label || e.relation_type || e.type || '关联'
      }
    })
  nodeRelations.value = related
}

// ===== 跳转详情 =====
const goToDetail = (id) => router.push(`/papers/${id}`)

// ===== 辅助 =====
const getStatusType = (s) => ({ '已读': 'success', '在读': 'warning', '未读': 'info' }[s] || 'info')
const getRelationType = (t) => ({ '引用': 'primary', '主题相似': 'warning', '方法相似': 'success' }[t] || 'info')

// ===== 窗口自适应 =====
const handleResize = () => chartInstance?.resize()

// ===== 监听标签开关 =====
watch(showLabels, () => renderChart())

// ===== 生命周期 =====
onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.graph-container {
  padding: 24px 40px;
  min-height: 100vh;
  background: #f5f7fa;
}
.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.header-right { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.page-title { font-size: 24px; font-weight: 600; color: #1a2332; margin: 0; }

.graph-legend {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 20px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}
.legend-color {
  width: 20px;
  height: 4px;
  border-radius: 2px;
}

.graph-wrapper {
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  height: calc(100vh - 220px);
  min-height: 450px;
  overflow: hidden;
}
.graph-chart { width: 100%; height: 100%; }

.graph-loading {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #909399;
}
.graph-loading .el-icon { font-size: 36px; }

/* 抽屉样式 */
.node-detail h2 { font-size: 20px; font-weight: 600; color: #1a2332; margin-bottom: 16px; }
.node-detail p { margin: 6px 0; color: #555; }
.node-tags { margin-top: 12px; }
.node-relations { margin-top: 16px; }
.node-relations ul { padding-left: 20px; margin: 8px 0; }
.node-relations li { margin: 4px 0; color: #555; }

@media (max-width: 768px) {
  .graph-container { padding: 16px; }
  .graph-header { flex-direction: column; align-items: stretch; }
  .graph-wrapper { height: calc(100vh - 300px); min-height: 300px; }
}
</style>
