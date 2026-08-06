<template>
  <div class="graph-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="4" r="2"/>
            <circle cx="4" cy="16" r="2"/>
            <circle cx="20" cy="16" r="2"/>
            <line x1="12" y1="6" x2="12" y2="10"/>
            <line x1="6" y1="17" x2="10" y2="14"/>
            <line x1="18" y1="17" x2="14" y2="14"/>
            <line x1="12" y1="10" x2="10" y2="14"/>
            <line x1="12" y1="10" x2="14" y2="14"/>
          </svg>
        </span>
        <span class="title-text">文献关系图谱</span>
        <span class="title-badge">{{ nodes.length }} 节点 · {{ edges.length }} 关系</span>
      </h1>
      <p class="page-desc">可视化展示本地论文与外部推荐论文的关系网络</p>
    </div>

    <!-- ===== 工具栏 ===== -->
    <div class="graph-toolbar">
      <div class="toolbar-left">
        <div class="layout-group">
          <button
            v-for="item in layouts"
            :key="item.value"
            class="layout-btn"
            :class="{ active: layout === item.value }"
            @click="layout = item.value; applyLayout()"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
      <div class="toolbar-right">
        <button class="tool-btn" @click="resetZoom">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 8 8 12 12 16"/>
            <line x1="16" y1="12" x2="8" y2="12"/>
          </svg>
          重置视图
        </button>
        <button class="tool-btn" :loading="loading" @click="loadGraphData">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          刷新
        </button>
        <button class="btn-generate" :loading="generating" @click="generateGraph">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="16"/>
            <line x1="8" y1="12" x2="16" y2="12"/>
          </svg>
          生成图谱
        </button>
      </div>
    </div>

    <!-- ===== 增强筛选面板 ===== -->
    <div class="filter-panel">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">节点类型：</span>
          <label class="filter-checkbox"><input type="checkbox" v-model="showLocal" /> 本地</label>
          <label class="filter-checkbox"><input type="checkbox" v-model="showExternal" /> 外部</label>
          <label class="filter-checkbox"><input type="checkbox" v-model="showRecommended" /> 推荐</label>
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">关系类型：</span>
          <label class="filter-checkbox" v-for="rt in relationTypeOptions" :key="rt.value">
            <input type="checkbox" v-model="selectedRelations" :value="rt.value" /> {{ rt.label }}
          </label>
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">权重阈值：</span>
          <input type="range" v-model.number="weightThreshold" min="0" max="1" step="0.05" class="weight-slider" />
          <span class="weight-value">{{ (weightThreshold * 100).toFixed(0) }}%</span>
          <span class="filter-hint">（仅显示权重 ≥ 该值的关系）</span>
        </div>
      </div>
    </div>

    <!-- ===== 图例 ===== -->
    <div class="graph-legend">
      <span class="legend-item">
        <span class="legend-color" style="background: #667eea;"></span>
        本地论文
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #f59e0b;"></span>
        外部论文
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #10b981;"></span>
        推荐论文
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #5fc3e4;"></span>
        引用
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #f093fb;"></span>
        主题相似
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #4facfe;"></span>
        方法相似
      </span>
      <span class="legend-item">
        <span class="legend-color" style="background: #43e97b;"></span>
        同作者
      </span>
      <span class="legend-item" style="margin-left: auto;">
        <label class="switch-label">
          <span class="switch-text">标签</span>
          <button class="switch-btn" :class="{ active: showLabels }" @click="showLabels = !showLabels; renderChart()">
            <span class="switch-track"><span class="switch-thumb"></span></span>
          </button>
        </label>
      </span>
    </div>

    <!-- ===== 图表 ===== -->
    <div class="graph-wrapper">
      <div ref="chartRef" class="graph-chart"></div>
      <div v-if="loading" class="graph-loading">
        <span class="loading-spinner"></span>
        <span>加载图谱数据...</span>
      </div>
      <div v-if="generating" class="graph-loading">
        <span class="loading-spinner"></span>
        <span>AI 正在生成关系图谱...</span>
      </div>
      <div v-else-if="nodes.length === 0" class="empty-graph">
        <div class="empty-graph-icon">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="4" r="2"/>
            <circle cx="4" cy="16" r="2"/>
            <circle cx="20" cy="16" r="2"/>
            <line x1="12" y1="6" x2="12" y2="10"/>
            <line x1="6" y1="17" x2="10" y2="14"/>
            <line x1="18" y1="17" x2="14" y2="14"/>
          </svg>
        </div>
        <h3>暂无关系数据</h3>
        <p>点击「生成图谱」创建论文关系网络</p>
        <button class="btn-generate" @click="generateGraph">生成图谱</button>
      </div>
    </div>

    <!-- ===== 关系列表 ===== -->
    <div class="graph-relations" v-if="displayEdges.length > 0">
      <div class="relations-header">
        <span class="relations-title">关系列表</span>
        <span class="relations-count">{{ displayEdges.length }} 条关系</span>
      </div>
      <div class="relations-list">
        <span
          v-for="(edge, idx) in displayEdges"
          :key="idx"
          class="relation-tag"
          :class="{
            'rel-citation': edge.type === 'citation',
            'rel-topic': edge.type === 'topic_similarity',
            'rel-method': edge.type === 'method_similarity',
            'rel-author': edge.type === 'same_author',
            'rel-recommended': edge.type === 'recommended_from'
          }"
        >
          {{ getNodeName(edge.source) }} → {{ getNodeName(edge.target) }}
          <span class="relation-label">{{ getRelationLabel(edge.type) }}</span>
          <span class="relation-weight-badge" v-if="edge.weight">({{ (edge.weight * 100).toFixed(0) }}%)</span>
        </span>
      </div>
    </div>

    <!-- ===== 节点详情抽屉 ===== -->
    <div class="drawer-overlay" v-if="showDetail" @click="showDetail = false"></div>
    <div class="drawer" :class="{ open: showDetail }">
      <div class="drawer-header">
        <h3 class="drawer-title">论文详情</h3>
        <button class="drawer-close" @click="showDetail = false">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="drawer-body" v-if="selectedNode">
        <h2 class="node-title">{{ selectedNode.label || selectedNode.name }}</h2>
        <div class="node-type-badge" :class="{
          'type-local': selectedNode._type === 'local',
          'type-external': selectedNode._type === 'external',
          'type-recommended': selectedNode._type === 'recommended'
        }">
          {{ selectedNode._type === 'local' ? '📄 本地论文' : selectedNode._type === 'external' ? '🌐 外部论文' : '⭐ 推荐论文' }}
        </div>
        <div class="node-meta">
          <p><span class="meta-label">作者</span>{{ selectedNode.authors || '未知' }}</p>
          <p><span class="meta-label">年份</span>{{ selectedNode.year || '未知' }}</p>
          <p><span class="meta-label">状态</span>
            <span class="status-tag" :class="{
              'status-read': selectedNode.status === '已读',
              'status-reading': selectedNode.status === '在读',
              'status-unread': selectedNode.status === '未读' || !selectedNode.status
            }">{{ selectedNode.status || '未读' }}</span>
          </p>
        </div>
        <div class="node-tags" v-if="selectedNode.tags?.length">
          <span class="meta-label">标签</span>
          <div class="tag-list">
            <span v-for="tag in selectedNode.tags" :key="tag" class="node-tag">#{{ tag }}</span>
          </div>
        </div>
        <div class="node-relations">
          <span class="meta-label">关联关系</span>
          <ul class="relation-list">
            <li v-for="(rel, idx) in nodeRelations" :key="idx" class="relation-item">
              <span class="relation-target">{{ rel.target }}</span>
              <span class="relation-type" :class="{
                'rel-citation': rel.type === 'citation',
                'rel-topic': rel.type === 'topic_similarity',
                'rel-method': rel.type === 'method_similarity',
                'rel-author': rel.type === 'same_author',
                'rel-recommended': rel.type === 'recommended_from'
              }">{{ getRelationLabel(rel.type) }}</span>
              <span v-if="rel.weight" class="relation-weight">({{ (rel.weight * 100).toFixed(0) }}%)</span>
            </li>
          </ul>
        </div>
        <div class="drawer-actions">
          <button class="btn-detail" @click="goToDetail(selectedNode.id)" v-if="selectedNode._type === 'local'">
            查看完整论文
          </button>
          <button class="btn-import" @click="importExternalNode(selectedNode)" v-if="selectedNode._type === 'external' && !selectedNode._imported">
            导入文献库
          </button>
          <button class="btn-expand" @click="expandNode(selectedNode.id)" v-if="selectedNode._type === 'local'">
            🔍 展开相关论文
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from '../utils/axios'

const router = useRouter()
const chartRef = ref(null)
let chartInstance = null

// ===== 状态 =====
const loading = ref(false)
const generating = ref(false)
const nodes = ref([])
const edges = ref([])
const layout = ref('force')
const showLabels = ref(true)
const showDetail = ref(false)
const selectedNode = ref(null)
const nodeRelations = ref([])

// ===== 筛选状态 =====
const showLocal = ref(true)
const showExternal = ref(true)
const showRecommended = ref(true)
const selectedRelations = ref(['citation', 'topic_similarity', 'method_similarity', 'same_author', 'recommended_from'])
const weightThreshold = ref(0)

const relationTypeOptions = [
  { value: 'citation', label: '引用' },
  { value: 'topic_similarity', label: '主题相似' },
  { value: 'method_similarity', label: '方法相似' },
  { value: 'same_author', label: '同作者' },
  { value: 'recommended_from', label: '推荐来源' }
]

const relationLabelMap = {
  citation: '引用',
  topic_similarity: '主题相似',
  method_similarity: '方法相似',
  same_author: '同作者',
  recommended_from: '推荐来源'
}

const layouts = [
  { value: 'force', label: '力导向' },
  { value: 'circular', label: '环形' },
  { value: 'grid', label: '网格' }
]

// ===== 计算筛选后的边 =====
const displayEdges = computed(() => {
  const typeFilter = []
  if (showLocal.value) typeFilter.push('local')
  if (showExternal.value) typeFilter.push('external')
  if (showRecommended.value) typeFilter.push('recommended')
  const filteredNodeIds = new Set(nodes.value.filter(n => typeFilter.includes(n._type)).map(n => n.id))

  return edges.value.filter(e => {
    if (!selectedRelations.value.includes(e.type)) return false
    if (e.weight < weightThreshold.value) return false
    return filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
  })
})

// ===== 获取关系显示名称 =====
const getRelationLabel = (type) => {
  return relationLabelMap[type] || type || '关联'
}

// ===== 加载图谱数据 =====
const loadGraphData = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/graph/enhanced')
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || res.data
      nodes.value = (data.nodes || []).map(n => ({
        ...n,
        _type: n._type || (n.is_local ? 'local' : n.is_recommended ? 'recommended' : 'external')
      }))
      edges.value = data.edges || []
      if (nodes.value.length === 0) {
        ElMessage.info('暂无关系数据，点击「生成图谱」创建')
      }
    } else {
      ElMessage.warning('加载失败，使用示例数据')
      loadMockData()
    }
  } catch (error) {
    console.warn('加载图谱数据失败，使用示例数据:', error)
    loadMockData()
  } finally {
    loading.value = false
    await nextTick()
    renderChart()
  }
}

// ===== 生成图谱 =====
const generateGraph = async () => {
  generating.value = true
  try {
    const res = await axios.post('/api/graph/generate', {})
    if (res.data.code === 200 || res.data.code === 0) {
      ElMessage.success('图谱生成成功')
      await loadGraphData()
    } else {
      ElMessage.warning(res.data.message || '生成失败，使用示例数据')
      loadMockData()
      await nextTick()
      renderChart()
    }
  } catch (error) {
    console.warn('生成图谱失败，使用示例数据:', error)
    loadMockData()
    await nextTick()
    renderChart()
    ElMessage.warning('使用示例数据展示图谱效果')
  } finally {
    generating.value = false
  }
}

// ===== Mock 数据 =====
const loadMockData = () => {
  nodes.value = [
    { id: 'local_1', label: 'Attention Is All You Need', authors: 'Vaswani et al.', year: '2017', status: '已读', _type: 'local', tags: ['Transformer', 'NLP'] },
    { id: 'local_2', label: 'BERT', authors: 'Devlin et al.', year: '2018', status: '在读', _type: 'local', tags: ['BERT', '预训练'] },
    { id: 'external_1', label: 'GPT-3', authors: 'Brown et al.', year: '2020', status: '未读', _type: 'external', tags: ['GPT', '大语言模型'] },
    { id: 'external_2', label: 'T5', authors: 'Raffel et al.', year: '2019', status: '未读', _type: 'external', tags: ['多模态'] },
    { id: 'recommended_1', label: 'XLNet', authors: 'Yang et al.', year: '2019', status: '未读', _type: 'recommended', tags: ['预训练'] }
  ]
  edges.value = [
    { source: 'local_1', target: 'local_2', type: 'citation', weight: 0.9 },
    { source: 'local_1', target: 'external_1', type: 'topic_similarity', weight: 0.85 },
    { source: 'local_2', target: 'external_2', type: 'method_similarity', weight: 0.75 },
    { source: 'external_1', target: 'recommended_1', type: 'recommended_from', weight: 0.65 },
    { source: 'local_1', target: 'recommended_1', type: 'topic_similarity', weight: 0.55 },
    { source: 'local_1', target: 'external_2', type: 'same_author', weight: 0.45 }
  ]
}

// ===== 渲染图表 =====
const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const nodeColors = { local: '#667eea', external: '#f59e0b', recommended: '#10b981' }
  const edgeColors = {
    citation: '#5fc3e4',
    topic_similarity: '#f093fb',
    method_similarity: '#4facfe',
    same_author: '#43e97b',
    recommended_from: '#fa709a'
  }

  const edgeLabels = {
    citation: '引用',
    topic_similarity: '主题相似',
    method_similarity: '方法相似',
    same_author: '同作者',
    recommended_from: '推荐来源'
  }

  const displayNodes = nodes.value.filter(n => {
    if (n._type === 'local' && !showLocal.value) return false
    if (n._type === 'external' && !showExternal.value) return false
    if (n._type === 'recommended' && !showRecommended.value) return false
    return true
  })

  if (displayNodes.length === 0) {
    chartInstance.clear()
    return
  }

  const displayEdgeData = displayEdges.value

  const option = {
    title: {
      text: '文献关系图谱',
      subtext: '点击节点查看详情 · 拖拽可移动',
      left: 'center',
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 600, color: '#1a2332' },
      subtextStyle: { fontSize: 12, color: '#8c9aa8' }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: 'rgba(95,195,228,0.15)',
      borderWidth: 1,
      borderRadius: 12,
      padding: [12, 16],
      textStyle: { fontSize: 13, color: '#1a2332' },
      formatter: (params) => {
        if (params.dataType === 'node') {
          const d = params.data
          const typeLabel = { local: '📄 本地', external: '🌐 外部', recommended: '⭐ 推荐' }
          return `<strong>${d.label}</strong><br/>类型：${typeLabel[d._type] || '未知'}<br/>作者：${d.authors || '未知'}<br/>年份：${d.year || '未知'}`
        }
        const edge = edges.value.find(e => e.source === params.data.source && e.target === params.data.target)
        return `${params.data.source} → ${params.data.target}<br/>类型：${edgeLabels[edge?.type] || edge?.type || '关联'}<br/>权重：${((edge?.weight || 0) * 100).toFixed(0)}%`
      }
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
      data: displayNodes.map(node => ({
        ...node,
        symbolSize: node._type === 'local' ? 50 : node._type === 'recommended' ? 38 : 42,
        itemStyle: {
          color: nodeColors[node._type] || '#667eea',
          shadowBlur: 12,
          shadowColor: 'rgba(0,0,0,0.08)'
        },
        label: {
          show: showLabels.value,
          fontSize: 11,
          fontWeight: 500,
          color: '#4a5a6a',
          offset: [0, 8],
          formatter: (p) => p.data.label?.length > 15 ? p.data.label.slice(0, 15) + '...' : p.data.label
        }
      })),
      links: displayEdgeData.map(edge => ({
        ...edge,
        label: {
          show: true,
          formatter: edgeLabels[edge.type] || edge.type || '关联',
          fontSize: 10,
          color: '#8c9aa8',
          offset: [0, -8]
        },
        lineStyle: {
          color: edgeColors[edge.type] || '#999',
          width: 2 + (edge.weight || 0) * 2,
          curveness: 0.15,
          opacity: 0.7
        }
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

// ===== 更新节点关联关系 =====
const updateNodeRelations = (node) => {
  if (!node) { nodeRelations.value = []; return }
  const related = edges.value
    .filter(e => e.source === node.id || e.target === node.id)
    .map(e => {
      const targetId = e.source === node.id ? e.target : e.source
      const targetNode = nodes.value.find(n => n.id === targetId)
      return { target: targetNode?.label || '未知', type: e.type, weight: e.weight }
    })
  nodeRelations.value = related
}

// ===== 获取节点名称 =====
const getNodeName = (id) => {
  const node = nodes.value.find(n => n.id === id)
  return node?.label || node?.name || id
}

// ===== 展开节点 =====
const expandNode = async (nodeId) => {
  try {
    const res = await axios.post('/api/graph/expand', { node_id: nodeId, limit: 10 })
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || res.data
      const newNodes = (data.nodes || []).map(n => ({
        ...n,
        _type: n._type || 'recommended'
      }))
      const newEdges = data.edges || []
      nodes.value = [...nodes.value, ...newNodes]
      edges.value = [...edges.value, ...newEdges]
      await nextTick()
      renderChart()
      ElMessage.success(`已展开 ${newNodes.length} 篇相关论文`)
    } else {
      ElMessage.warning(res.data.message || '展开失败')
    }
  } catch (error) {
    console.error('展开失败:', error)
    ElMessage.error('展开失败，请重试')
  }
}

// ===== 导入外部节点 =====
const importExternalNode = async (node) => {
  try {
    const res = await axios.post('/api/discovery/import', { external_id: node.id })
    if (res.data.code === 200 || res.data.code === 0) {
      node._imported = true
      ElMessage.success('导入成功！')
      showDetail.value = false
    } else {
      ElMessage.error(res.data.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败，请重试')
  }
}

// ===== 跳转详情 =====
const goToDetail = (id) => {
  const cleanId = id.replace('local_', '')
  router.push(`/papers/${cleanId}`)
}

// ===== 窗口自适应 =====
const handleResize = () => {
  if (chartInstance) chartInstance.resize()
}

// ===== 监听筛选变化 =====
watch([showLocal, showExternal, showRecommended, selectedRelations, weightThreshold], () => {
  renderChart()
})

// ===== 生命周期 =====
onMounted(() => {
  loadGraphData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.graph-container {
  padding: 24px 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(180deg, #f5faff 0%, #eef6fb 100%);
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 800;
  color: #1a2a3a;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  color: #fff;
  flex-shrink: 0;
}
.title-icon svg { stroke: #fff; }

.title-text {
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-badge {
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(135deg, #5fc3e4, #7bc8a4);
  padding: 4px 16px;
  border-radius: 9999px;
  -webkit-text-fill-color: #fff;
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.25);
}

.page-desc {
  color: #8c9aa8;
  font-size: 15px;
  margin: 0;
}

.graph-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 12px 20px;
  margin-bottom: 12px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.04);
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layout-group {
  display: flex;
  gap: 4px;
  background: rgba(248, 250, 255, 0.6);
  padding: 4px;
  border-radius: 14px;
}

.layout-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #8c9aa8;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.layout-btn:hover { color: #4a5a6a; }
.layout-btn.active {
  background: #ffffff;
  color: #5fc3e4;
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.1);
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  border-radius: 9999px;
  background: rgba(248, 250, 255, 0.6);
  color: #6a7a8a;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
}
.tool-btn:hover {
  background: rgba(255, 255, 255, 0.8);
  color: #1a2a3a;
  transform: translateY(-2px);
}

.btn-generate {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 22px;
  border: none;
  border-radius: 9999px;
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.25);
}
.btn-generate:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 28px rgba(95, 195, 228, 0.35);
}
.btn-generate:active { transform: scale(0.96); }

.filter-panel {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 12px 20px;
  margin-bottom: 12px;
  border: 1px solid rgba(255, 255, 255, 0.6);
}
.filter-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 4px 0; }
.filter-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.filter-label { font-weight: 500; color: #4a5a6a; font-size: 13px; }
.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6a7a8a;
  cursor: pointer;
}
.weight-slider { width: 120px; cursor: pointer; }
.weight-value { font-size: 13px; color: #667eea; font-weight: 600; min-width: 44px; }
.filter-hint { font-size: 12px; color: #8c9aa8; }

.graph-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6a7a8a;
  font-weight: 500;
}
.legend-color { width: 18px; height: 4px; border-radius: 4px; }

.switch-label { display: flex; align-items: center; gap: 8px; }
.switch-text { font-size: 13px; color: #6a7a8a; font-weight: 500; }
.switch-btn {
  width: 44px; height: 26px;
  border: none; border-radius: 9999px;
  background: #d0d8e0;
  cursor: pointer; padding: 3px;
  transition: all 0.3s ease; position: relative;
}
.switch-btn.active { background: linear-gradient(135deg, #5fc3e4, #7bc8a4); }
.switch-track {
  display: block; width: 100%; height: 100%;
  border-radius: 9999px; position: relative;
}
.switch-thumb {
  display: block; width: 20px; height: 20px;
  border-radius: 50%; background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.switch-btn.active .switch-thumb { transform: translateX(18px); }

.graph-wrapper {
  position: relative;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  padding: 8px;
  box-shadow: 0 4px 24px rgba(95, 195, 228, 0.04);
  height: calc(100vh - 460px);
  min-height: 450px;
  overflow: hidden;
}
.graph-chart { width: 100%; height: 100%; }

.graph-loading {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  color: #8c9aa8;
}
.loading-spinner {
  width: 36px; height: 36px;
  border: 3px solid rgba(95, 195, 228, 0.1);
  border-top-color: #5fc3e4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-graph {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #8c9aa8;
}
.empty-graph-icon { color: #c8d4e0; margin-bottom: 12px; }
.empty-graph h3 { font-size: 18px; font-weight: 600; color: #4a5a6a; margin: 0 0 4px 0; }
.empty-graph p { margin: 0 0 16px 0; font-size: 14px; }

.graph-relations {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  padding: 14px 20px;
  margin-top: 12px;
  border: 1px solid rgba(255, 255, 255, 0.6);
}
.relations-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.relations-title { font-size: 14px; font-weight: 600; color: #1a2a3a; }
.relations-count {
  font-size: 12px; color: #8c9aa8;
  background: rgba(248, 250, 255, 0.6);
  padding: 2px 12px; border-radius: 9999px;
}
.relations-list { display: flex; flex-wrap: wrap; gap: 6px; }
.relation-tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 12px 4px 14px;
  border-radius: 9999px;
  font-size: 13px; font-weight: 500;
  color: #4a5a6a;
  background: rgba(248, 250, 255, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.03);
}
.relation-tag .relation-label { font-size: 11px; font-weight: 500; opacity: 0.7; margin-left: 4px; }
.relation-tag .relation-weight-badge { font-size: 11px; font-weight: 600; color: #667eea; margin-left: 2px; }

.rel-citation { background: rgba(95, 195, 228, 0.12); color: #4a9ab8; }
.rel-topic { background: rgba(240, 147, 251, 0.12); color: #a87ab8; }
.rel-method { background: rgba(79, 172, 254, 0.12); color: #4a8ab8; }
.rel-author { background: rgba(67, 233, 123, 0.12); color: #3a8a6a; }
.rel-recommended { background: rgba(250, 112, 154, 0.12); color: #b86a7a; }

.drawer-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.2); backdrop-filter: blur(4px);
  z-index: 200; animation: fadeIn 0.25s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.drawer {
  position: fixed; top: 0; right: 0; bottom: 0; width: 420px; max-width: 90vw;
  background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px);
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 201; box-shadow: -8px 0 40px rgba(0, 0, 0, 0.06);
  overflow-y: auto;
}
.drawer.open { transform: translateX(0); }

.drawer-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.drawer-title { font-size: 18px; font-weight: 600; color: #1a2a3a; margin: 0; }
.drawer-close {
  width: 36px; height: 36px;
  border: none; border-radius: 50%;
  background: rgba(0, 0, 0, 0.04); color: #8c9aa8;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.drawer-close:hover { background: rgba(0, 0, 0, 0.08); transform: scale(1.05); }

.drawer-body { padding: 24px; }
.node-title { font-size: 22px; font-weight: 700; color: #1a2a3a; margin: 0 0 12px 0; }
.node-type-badge {
  display: inline-block; padding: 4px 16px;
  border-radius: 20px; font-size: 13px; font-weight: 600;
  margin-bottom: 12px;
}
.type-local { background: rgba(102, 126, 234, 0.12); color: #667eea; }
.type-external { background: rgba(245, 158, 11, 0.12); color: #f59e0b; }
.type-recommended { background: rgba(16, 185, 129, 0.12); color: #10b981; }

.node-meta p {
  display: flex; align-items: center; gap: 12px;
  margin: 6px 0; font-size: 14px; color: #4a5a6a;
}
.meta-label { min-width: 48px; font-weight: 500; color: #8c9aa8; font-size: 13px; }
.status-tag {
  padding: 2px 12px; border-radius: 20px;
  font-size: 13px; font-weight: 500;
}
.status-read { background: rgba(123, 200, 164, 0.15); color: #4a9a7a; }
.status-reading { background: rgba(95, 195, 228, 0.15); color: #4a9ab8; }
.status-unread { background: rgba(200, 210, 220, 0.2); color: #8c9aa8; }

.node-tags { margin-top: 12px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.node-tag {
  padding: 2px 14px; border-radius: 9999px;
  background: rgba(95, 195, 228, 0.06);
  color: #5fc3e4; font-size: 13px; font-weight: 500;
}

.node-relations { margin-top: 16px; }
.relation-list { list-style: none; padding: 0; margin: 8px 0 0 0; }
.relation-item {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0; font-size: 14px; color: #4a5a6a;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
}
.relation-item:last-child { border-bottom: none; }
.relation-target { flex: 1; }
.relation-type { padding: 2px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }
.relation-type.rel-citation { background: rgba(95, 195, 228, 0.1); color: #4a9ab8; }
.relation-type.rel-topic { background: rgba(240, 147, 251, 0.1); color: #a87ab8; }
.relation-type.rel-method { background: rgba(79, 172, 254, 0.1); color: #4a8ab8; }
.relation-type.rel-author { background: rgba(67, 233, 123, 0.1); color: #3a8a6a; }
.relation-type.rel-recommended { background: rgba(250, 112, 154, 0.1); color: #b86a7a; }
.relation-weight { font-size: 12px; color: #8c9aa8; margin-left: 4px; }

.drawer-actions { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
.btn-detail, .btn-import, .btn-expand {
  padding: 10px 20px;
  border: none; border-radius: 12px;
  font-weight: 600; font-size: 14px;
  cursor: pointer; transition: all 0.3s;
}
.btn-detail { background: linear-gradient(135deg, #5fc3e4, #7bc8a4); color: #fff; box-shadow: 0 4px 16px rgba(95,195,228,0.2); }
.btn-import { background: #10b981; color: #fff; }
.btn-expand { background: #f59e0b; color: #fff; }
.btn-detail:hover, .btn-import:hover, .btn-expand:hover { transform: translateY(-2px); }

@media (max-width: 768px) {
  .graph-container { padding: 16px 12px; }
  .page-title { font-size: 22px; flex-wrap: wrap; }
  .title-icon { width: 40px; height: 40px; }
  .graph-toolbar { flex-direction: column; align-items: stretch; gap: 10px; }
  .toolbar-left, .toolbar-right { flex-wrap: wrap; justify-content: center; }
  .graph-wrapper { height: calc(100vh - 500px); min-height: 300px; }
  .drawer { width: 100%; max-width: 100%; }
  .filter-row { flex-direction: column; align-items: flex-start; }
  .graph-legend { gap: 10px; }
  .legend-item { font-size: 11px; }
}
</style>