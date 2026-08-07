<template>
  <div class="plan-detail-container" v-loading="loading">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </span>
        <span class="title-text">计划详情</span>
      </h1>
      <p class="page-desc">查看科研计划的完整内容和进度</p>
    </div>

    <!-- ===== 返回按钮 ===== -->
    <div class="detail-nav">
      <button class="back-btn" @click="$router.back()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        返回列表
      </button>
      <button class="back-btn" @click="$router.push('/agent')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
        新建计划
      </button>
    </div>

    <!-- ===== 计划内容 ===== -->
    <div v-if="plan" class="plan-content">
      <!-- 标题区 -->
      <div class="plan-header">
        <h2 class="plan-title">{{ plan.topic }}</h2>
        <div class="plan-meta">
          <span class="meta-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            {{ formatDate(plan.created_at) }}
          </span>
          <span class="meta-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {{ plan.total_weeks || plan.duration_weeks + ' 周' }}
          </span>
          <span class="meta-tag">{{ plan.stages?.length || 0 }} 个阶段</span>
          <span v-if="plan.plan_id" class="meta-id">#{{ plan.plan_id }}</span>
        </div>
      </div>

      <!-- 阶段列表 -->
      <div class="stages">
        <h3 class="section-title">阶段计划</h3>
        <div
          v-for="(stage, index) in plan.stages"
          :key="index"
          class="stage-card"
          :style="{ borderLeftColor: phaseColors[index % phaseColors.length] }"
        >
          <div class="stage-header">
            <div class="stage-title-left">
              <span class="stage-number">阶段 {{ index + 1 }}</span>
              <h4>{{ stage.name }}</h4>
            </div>
            <span class="stage-week">{{ stage.weeks || '第 ' + (index + 1) + ' 周' }}</span>
          </div>

          <div class="stage-goal" v-if="stage.goal">
            <span class="stage-label">目标</span>
            <p>{{ stage.goal }}</p>
          </div>

          <div class="stage-tasks" v-if="stage.tasks?.length">
            <span class="stage-label">任务清单</span>
            <ul>
              <li v-for="(task, ti) in stage.tasks" :key="ti">
                <span class="task-dot"></span>
                {{ task }}
              </li>
            </ul>
          </div>

          <div class="stage-reading" v-if="stage.reading_list?.length">
            <span class="stage-label">阅读清单</span>
            <div class="reading-tags">
              <span v-for="(paper, pi) in stage.reading_list" :key="pi" class="reading-tag">
                {{ paper }}
              </span>
            </div>
          </div>

          <div class="stage-deliverable" v-if="stage.output">
            <span class="stage-label">产出</span>
            <p>{{ stage.output }}</p>
          </div>
        </div>
      </div>

      <!-- 周计划 -->
      <div class="weekly-plan" v-if="plan.weekly_plan?.length">
        <h3 class="section-title">周计划</h3>
        <div class="weekly-grid">
          <div v-for="(week, idx) in plan.weekly_plan" :key="idx" class="weekly-item">
            <span class="weekly-week">第 {{ week.week || idx + 1 }} 周</span>
            <span class="weekly-goal">{{ week.goal }}</span>
            <ul>
              <li v-for="(task, ti) in week.tasks" :key="ti">{{ task }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 风险提醒 -->
      <div class="plan-risks" v-if="plan.risks?.length">
        <h3 class="section-title">风险提醒</h3>
        <ul>
          <li v-for="(risk, idx) in plan.risks" :key="idx">
            <span class="risk-dot"></span>
            {{ risk }}
          </li>
        </ul>
      </div>

      <!-- 操作按钮 -->
      <div class="plan-actions">
        <button class="btn-primary-outline" @click="exportPlan">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          导出计划
        </button>
        <button class="btn-ghost" @click="copyPlan">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          复制内容
        </button>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
      </div>
      <h3>计划不存在</h3>
      <p>该计划可能已被删除或 ID 无效</p>
      <button class="btn-primary" @click="$router.push('/plans')">返回计划列表</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const route = useRoute()
const router = useRouter()
const planId = ref(route.params.id)
const loading = ref(false)
const plan = ref(null)

const phaseColors = ['#5fc3e4', '#7bc8a4', '#f5a0a0', '#b8a9d4', '#ffd93d']

// ===== 加载计划详情 =====
const loadPlanDetail = async () => {
  if (!planId.value) {
    ElMessage.error('计划 ID 不存在')
    return
  }

  loading.value = true
  try {
    const res = await axios.get(`/api/agent/research-plans/${planId.value}`)
    if (res.data.code === 200 || res.data.code === 0) {
      const data = res.data.data || res.data
      plan.value = { ...data, topic: data.topic || data.research_topic }
    } else {
      ElMessage.warning(res.data.message || '加载失败，使用示例数据')
      loadMockDetail()
    }
  } catch (error) {
    console.warn('加载计划详情失败，使用示例数据:', error)
    loadMockDetail()
  } finally {
    loading.value = false
  }
}

// ===== Mock 数据 =====
const loadMockDetail = () => {
  plan.value = {
    plan_id: Number(planId.value),
    topic: '图神经网络在药物分子性质预测中的应用',
    total_weeks: '7 周',
    created_at: new Date().toISOString(),
    stages: [
      {
        name: '基础知识构建',
        goal: '掌握图神经网络和药物分子性质预测的基础知识',
        weeks: '第 1-2 周',
        tasks: [
          '学习图神经网络基础（GCN、GAT、GraphSAGE）',
          '了解药物分子性质预测任务（溶解度、毒性、活性）',
          '熟悉常用数据集（MoleculeNet、ZINC）'
        ],
        reading_list: [
          'A Comprehensive Survey on Graph Neural Networks',
          'MoleculeNet: A Benchmark for Molecular ML'
        ],
        output: 'GNN 学习笔记 + 环境搭建'
      },
      {
        name: '文献深度调研',
        goal: '深入阅读核心论文，理解不同方法',
        weeks: '第 3-4 周',
        tasks: [
          '阅读 MPNN、SchNet 等核心论文',
          '对比不同方法的优缺点和适用场景'
        ],
        reading_list: [
          'Message Passing Neural Networks',
          'SchNet: A Continuous-filter CNN'
        ],
        output: '文献综述笔记 + 方法对比表'
      },
      {
        name: '模型复现与实验',
        goal: '复现经典模型，在标准数据集上验证效果',
        weeks: '第 5-6 周',
        tasks: [
          '实现 GCN、GAT 在 MoleculeNet 上的基线模型',
          '复现 MPNN 或 SchNet 模型',
          '设计实验对比不同模型的预测精度'
        ],
        reading_list: [
          'MoleculeNet 论文和官方代码',
          'PyTorch Geometric 文档'
        ],
        output: '复现代码 + 实验报告'
      },
      {
        name: '论文撰写与总结',
        goal: '整理研究成果，撰写科研论文或技术报告',
        weeks: '第 7 周',
        tasks: [
          '整理所有实验数据和结果图表',
          '撰写论文：Introduction、Method、Experiment',
          '讨论方法的局限性和未来方向'
        ],
        reading_list: [
          '参考 NeurIPS、ICML、ICLR 等顶会论文格式'
        ],
        output: '科研论文初稿'
      }
    ],
    weekly_plan: [
      { week: 1, goal: '熟悉 GNN 基础和图数据表示', tasks: ['学习 GCN、GAT 原理', '安装 PyTorch Geometric'] },
      { week: 2, goal: '了解药物分子数据集和任务', tasks: ['阅读 MoleculeNet 论文', '下载 ZINC 数据集'] },
      { week: 3, goal: '精读核心预测模型论文', tasks: ['阅读 MPNN、SchNet 论文', '做好笔记'] },
      { week: 4, goal: '精读生成模型和综述论文', tasks: ['阅读 GraphAF、MolGAN', '整理方法对比表'] },
      { week: 5, goal: '实现基线模型', tasks: ['实现 GCN、GAT', '在 MoleculeNet 上运行'] },
      { week: 6, goal: '复现并改进经典模型', tasks: ['复现 MPNN 或 SchNet', '对比实验结果'] },
      { week: 7, goal: '撰写论文初稿', tasks: ['整理图表', '撰写各章节'] }
    ],
    risks: [
      '分子图数据规模较大，需注意显存管理',
      '不同数据集的分子性质差异大，模型泛化能力可能受限',
      '复现经典模型可能需要较多计算资源'
    ]
  }
}

// ===== 格式化日期 =====
const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

// ===== 导出计划 =====
const exportPlan = () => {
  if (!plan.value) return
  let text = `科研计划\n`
  text += `研究目标：${plan.value.topic}\n`
  text += `总时长：${plan.value.total_weeks}\n`
  text += `创建时间：${formatDate(plan.value.created_at)}\n\n`
  plan.value.stages?.forEach((p, i) => {
    text += `【阶段 ${i+1}】${p.name}（${p.weeks}）\n`
    text += `目标：${p.goal}\n`
    text += `任务：${p.tasks?.map(t => `  - ${t}`).join('\n') || '无'}\n`
    if (p.reading_list?.length) {
      text += `阅读：${p.reading_list.join('、')}\n`
    }
    text += `产出：${p.output || '无'}\n\n`
  })
  if (plan.value.risks?.length) {
    text += `风险提醒：${plan.value.risks.join('；')}\n`
  }
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `科研计划_${new Date().toISOString().slice(0,10)}.txt`
  link.click()
  ElMessage.success('导出成功')
}

// ===== 复制计划 =====
const copyPlan = () => {
  if (!plan.value) return
  let text = `科研计划：${plan.value.topic}\n\n`
  plan.value.stages?.forEach((p, i) => {
    text += `【阶段 ${i+1}】${p.name}\n`
    text += `目标：${p.goal}\n`
    text += `任务：${p.tasks?.join('；') || '无'}\n\n`
  })
  navigator.clipboard?.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动选择复制')
  })
}

onMounted(() => {
  loadPlanDetail()
})
</script>

<style scoped>
/* ============================================================
   ===== 容器 =====
   ============================================================ */
.plan-detail-container {
  padding: 24px 20px;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-primary);
  background-image: radial-gradient(ellipse at 10% 20%, rgba(95, 195, 228, 0.04) 0%, transparent 50%);
}

/* ============================================================
   ===== 顶部 =====
   ============================================================ */
.page-header {
  margin-bottom: 20px;
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

.page-desc {
  color: var(--text-muted);
  font-size: 15px;
  margin: 0;
}

/* ============================================================
   ===== 返回按钮 =====
   ============================================================ */
.detail-nav {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(-4px);
}

.back-btn svg {
  stroke: currentColor;
}

/* ============================================================
   ===== 计划内容 =====
   ============================================================ */
.plan-content {
  animation: fadeUp 0.4s ease;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== 标题区 ===== */
.plan-header {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.plan-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.plan-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.meta-item svg {
  stroke: var(--text-muted);
}

.meta-tag {
  font-size: 13px;
  font-weight: 500;
  color: var(--primary-500);
  background: rgba(95, 195, 228, 0.08);
  padding: 2px 14px;
  border-radius: var(--radius-full);
}

.meta-id {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

/* ============================================================
   ===== 阶段 =====
   ============================================================ */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.stages {
  margin-bottom: 24px;
}

.stage-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  margin-bottom: 14px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
  border-left: 4px solid var(--primary-500);
  transition: all 0.3s ease;
}

.stage-card:last-child {
  margin-bottom: 0;
}

.stage-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.stage-title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stage-number {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary-500);
  background: rgba(95, 195, 228, 0.08);
  padding: 2px 14px;
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stage-title-left h4 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.stage-week {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  background: rgba(248, 250, 255, 0.6);
  padding: 2px 14px;
  border-radius: var(--radius-full);
}

.stage-goal,
.stage-tasks,
.stage-reading,
.stage-deliverable {
  margin-top: 10px;
}

.stage-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stage-goal p,
.stage-deliverable p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

.stage-tasks ul {
  padding-left: 0;
  margin: 4px 0 0 0;
  list-style: none;
}

.stage-tasks li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 4px 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.task-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary-gradient);
  flex-shrink: 0;
  margin-top: 7px;
}

.reading-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.reading-tag {
  font-size: 13px;
  color: var(--primary-500);
  background: rgba(95, 195, 228, 0.06);
  padding: 2px 14px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

/* ============================================================
   ===== 周计划 =====
   ============================================================ */
.weekly-plan {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
}

.weekly-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.weekly-item {
  background: rgba(248, 250, 255, 0.6);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  transition: all 0.2s ease;
}

.weekly-item:hover {
  background: #ffffff;
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.weekly-week {
  font-weight: 600;
  color: var(--primary-500);
  display: block;
  margin-bottom: 2px;
  font-size: 13px;
}

.weekly-goal {
  font-size: 13px;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 4px;
}

.weekly-item ul {
  padding-left: 16px;
  margin: 4px 0 0 0;
}

.weekly-item li {
  font-size: 13px;
  color: var(--text-muted);
  padding: 1px 0;
}

/* ============================================================
   ===== 风险 =====
   ============================================================ */
.plan-risks {
  background: rgba(245, 160, 160, 0.04);
  border-radius: var(--radius-xl);
  padding: 20px 24px;
  margin-bottom: 24px;
  border: 1px solid rgba(245, 160, 160, 0.1);
  border-left: 4px solid #f5a0a0;
}

.plan-risks .section-title {
  color: #c47a7a;
  margin-bottom: 10px;
}

.plan-risks ul {
  padding-left: 0;
  margin: 0;
  list-style: none;
}

.plan-risks li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #8a5a5a;
  font-size: 14px;
  padding: 3px 0;
  line-height: 1.5;
}

.risk-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f5a0a0;
  flex-shrink: 0;
  margin-top: 7px;
}

/* ============================================================
   ===== 操作按钮 =====
   ============================================================ */
.plan-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-primary-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: 2px solid var(--primary-500);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--primary-500);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.btn-primary-outline:hover {
  background: var(--primary-gradient);
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.2);
}

.btn-primary-outline:active {
  transform: scale(0.96);
}

.btn-primary-outline svg {
  stroke: currentColor;
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-full);
  background: rgba(248, 250, 255, 0.6);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-primary);
  transform: translateY(-2px);
}

.btn-ghost svg {
  stroke: currentColor;
}

/* ============================================================
   ===== 空状态 =====
   ============================================================ */
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

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 28px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.2);
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

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 768px) {
  .plan-detail-container {
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

  .plan-header {
    padding: 18px 16px;
  }

  .plan-title {
    font-size: 20px;
  }

  .stage-card {
    padding: 16px;
  }

  .stage-title-left h4 {
    font-size: 15px;
  }

  .stage-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .weekly-plan {
    padding: 16px 18px;
  }

  .weekly-grid {
    grid-template-columns: 1fr;
  }

  .plan-risks {
    padding: 16px 18px;
  }

  .detail-nav {
    flex-wrap: wrap;
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

  .plan-title {
    font-size: 18px;
  }

  .plan-meta {
    gap: 10px;
  }

  .meta-item {
    font-size: 13px;
  }

  .stage-title-left h4 {
    font-size: 14px;
  }

  .stage-tasks li {
    font-size: 13px;
  }

  .reading-tag {
    font-size: 12px;
  }

  .plan-actions {
    flex-direction: column;
  }

  .plan-actions button {
    width: 100%;
    justify-content: center;
  }
}
</style>
