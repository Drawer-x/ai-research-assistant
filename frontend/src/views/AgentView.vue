<template>
  <div class="agent-container">
    <!-- ===== 顶部 ===== -->
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </span>
        <span class="title-text">Agent 科研规划</span>
        <span class="title-badge">AI 驱动</span>
      </h1>
      <p class="page-desc">输入研究目标，AI 将为你生成个性化的科研阅读路线与阶段计划</p>
    </div>

    <!-- ===== 输入卡片 ===== -->
    <div class="agent-input-card">
      <!-- 研究目标 -->
      <div class="input-group">
        <label class="input-label">研究目标</label>
        <el-input
          v-model="form.topic"
          type="textarea"
          :rows="3"
          placeholder="例如：我想研究图神经网络在药物分子性质预测中的应用"
          maxlength="500"
          show-word-limit
          class="input-textarea"
        />
      </div>

      <!-- 选项行 -->
      <div class="input-options">
        <div class="input-group">
          <label class="input-label">研究水平</label>
          <div class="option-group">
            <button
              v-for="level in levels"
              :key="level.value"
              class="option-btn"
              :class="{ active: form.level === level.value }"
              @click="form.level = level.value"
            >
              {{ level.label }}
            </button>
          </div>
        </div>

        <div class="input-group">
          <label class="input-label">计划周数</label>
          <div class="week-selector">
            <button class="week-btn" @click="form.duration_weeks = Math.max(2, form.duration_weeks - 1)">−</button>
            <span class="week-number">{{ form.duration_weeks }}</span>
            <button class="week-btn" @click="form.duration_weeks = Math.min(8, form.duration_weeks + 1)">+</button>
            <span class="week-unit">周</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="input-actions">
        <button class="btn-primary" :disabled="!form.topic.trim() || loading" @click="generatePlan">
          {{ loading ? '生成中...' : '生成科研计划' }}
        </button>
        <button class="btn-ghost" @click="loadExample">示例</button>
        <button class="btn-ghost" @click="clearPlan" :disabled="!plan">清空</button>
        <button class="btn-outline" @click="$router.push('/plans')">历史计划</button>
      </div>
    </div>

    <!-- ===== 计划结果 ===== -->
    <div v-if="plan" class="plan-result">
      <!-- 概览 -->
      <div class="plan-overview">
        <div class="overview-item">
          <span class="overview-label">研究目标</span>
          <span class="overview-value">{{ plan.topic || form.topic }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">总时长</span>
          <span class="overview-value">{{ plan.total_weeks || form.duration_weeks + ' 周' }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">阶段数</span>
          <span class="overview-value">{{ plan.stages?.length || 0 }} 个阶段</span>
        </div>
        <div class="overview-item" v-if="plan.plan_id">
          <span class="overview-label">计划编号</span>
          <span class="overview-value plan-id">#{{ plan.plan_id }}</span>
        </div>
      </div>

      <!-- 阶段详情 -->
      <div class="plan-phases">
        <div
          v-for="(stage, index) in plan.stages"
          :key="index"
          class="phase-card"
          :style="{ borderLeftColor: phaseColors[index % phaseColors.length] }"
        >
          <div class="phase-header">
            <div class="phase-title">
              <span class="phase-number">阶段 {{ index + 1 }}</span>
              <h3>{{ stage.name }}</h3>
            </div>
            <span class="phase-week">{{ stage.weeks || '第 ' + (index + 1) + ' 周' }}</span>
          </div>

          <div class="phase-goal" v-if="stage.goal">
            <span class="phase-label">目标</span>
            <p>{{ stage.goal }}</p>
          </div>

          <div class="phase-tasks" v-if="stage.tasks?.length">
            <span class="phase-label">任务清单</span>
            <ul>
              <li v-for="(task, ti) in stage.tasks" :key="ti">
                <span class="task-dot"></span>
                {{ task }}
              </li>
            </ul>
          </div>

          <div class="phase-reading" v-if="stage.reading_list?.length">
            <span class="phase-label">阅读清单</span>
            <div class="reading-tags">
              <span v-for="(paper, pi) in stage.reading_list" :key="pi" class="reading-tag">
                {{ paper }}
              </span>
            </div>
          </div>

          <div class="phase-deliverable" v-if="stage.output">
            <span class="phase-label">产出</span>
            <p>{{ stage.output }}</p>
          </div>
        </div>
      </div>

      <!-- 周计划 -->
      <div class="weekly-plan" v-if="plan.weekly_plan?.length">
        <h4>周计划</h4>
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
        <h4>风险提醒</h4>
        <ul>
          <li v-for="(risk, idx) in plan.risks" :key="idx">
            <span class="risk-dot"></span>
            {{ risk }}
          </li>
        </ul>
      </div>

      <!-- 操作按钮 -->
      <div class="plan-actions">
        <button class="btn-primary-outline" @click="exportPlan">导出计划</button>
        <button class="btn-ghost" @click="copyPlan">复制内容</button>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <h3>开始你的科研规划</h3>
      <p>输入研究目标，AI 将为你生成个性化科研路线</p>
      <p class="empty-hint">示例：我想研究图神经网络在药物分子性质预测中的应用</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const router = useRouter()

const form = reactive({
  topic: '',
  level: 'intermediate',
  duration_weeks: 4
})

const loading = ref(false)
const plan = ref(null)

const levels = [
  { value: 'beginner', label: '初级' },
  { value: 'intermediate', label: '中级' },
  { value: 'advanced', label: '高级' }
]

const phaseColors = ['#5fc3e4', '#7bc8a4', '#f5a0a0', '#b8a9d4', '#ffd93d']

// ===== 生成计划 =====
const generatePlan = async () => {
  if (!form.topic.trim()) {
    ElMessage.warning('请输入研究目标')
    return
  }

  loading.value = true
  try {
    const res = await axios.post('/api/agent/research-plan', {
      topic: form.topic.trim(),
      level: form.level,
      duration_weeks: form.duration_weeks
    })

    if (res.data.code === 200 || res.data.code === 0) {
      plan.value = res.data.data || res.data
      ElMessage.success('科研计划生成成功')
    } else {
      ElMessage.error(res.data.message || '生成失败')
      loadMockPlan()
    }
  } catch (error) {
    console.error('生成计划失败:', error)
    loadMockPlan()
    ElMessage.warning('使用示例数据展示效果')
  } finally {
    loading.value = false
  }
}

// ===== Mock 数据 =====
const loadMockPlan = () => {
  const weeks = form.duration_weeks || 4
  const topic = form.topic || '图神经网络在药物分子性质预测中的应用'

  plan.value = {
    topic: topic,
    total_weeks: weeks + ' 周',
    plan_id: Date.now(),
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
      }
    ],
    weekly_plan: Array.from({ length: Math.min(weeks, 7) }, (_, i) => ({
      week: i + 1,
      goal: `第 ${i+1} 周目标：${i === 0 ? '了解基础概念' : i === 1 ? '阅读核心论文' : '推进研究任务'}`,
      tasks: [`任务 ${i+1}.1`, `任务 ${i+1}.2`]
    })),
    risks: [
      '图数据规模较大，需注意显存管理',
      '不同数据集的分子性质差异大，泛化能力可能受限'
    ]
  }
}

// ===== 清空 =====
const clearPlan = () => {
  plan.value = null
  ElMessage.info('已清空计划')
}

// ===== 加载示例 =====
const loadExample = () => {
  form.topic = '我想研究图神经网络在药物分子性质预测中的应用，包括 GCN、GAT、MPNN 等方法'
  form.level = 'intermediate'
  form.duration_weeks = 4
  generatePlan()
}

// ===== 导出 =====
const exportPlan = () => {
  if (!plan.value) return
  let text = `科研计划\n`
  text += `研究目标：${plan.value.topic}\n`
  text += `总时长：${plan.value.total_weeks}\n\n`
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

// ===== 复制 =====
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
    ElMessage.warning('复制失败')
  })
}
</script>

<style scoped>
/* ============================================================
   ===== 容器 =====
   ============================================================ */
.agent-container {
  padding: 24px 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(180deg, #f5faff 0%, #eef6fb 100%);
}

/* ===== 顶部 ===== */
.page-header {
  margin-bottom: 28px;
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

.title-icon svg {
  stroke: #fff;
}

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

/* ===== 输入卡片 ===== */
.agent-input-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 24px;
  padding: 28px 24px;
  box-shadow: 0 4px 24px rgba(95, 195, 228, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
  margin-bottom: 24px;
}

.input-group {
  margin-bottom: 18px;
}

.input-group:last-of-type {
  margin-bottom: 20px;
}

.input-label {
  display: block;
  font-weight: 600;
  font-size: 14px;
  color: #4a5a6a;
  margin-bottom: 8px;
}

.input-textarea :deep(.el-textarea__inner) {
  min-height: 80px;
  border-radius: 16px;
  background: rgba(248, 250, 255, 0.8);
  border: 2px solid rgba(95, 195, 228, 0.12);
  transition: all 0.3s ease;
  font-size: 15px;
  padding: 14px 16px;
  font-family: inherit;
}

.input-textarea :deep(.el-textarea__inner):hover {
  border-color: rgba(95, 195, 228, 0.3);
}

.input-textarea :deep(.el-textarea__inner):focus {
  background: #ffffff;
  border-color: #5fc3e4;
  box-shadow: 0 0 0 4px rgba(95, 195, 228, 0.08);
}

.input-options {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.option-group {
  display: flex;
  gap: 6px;
  background: rgba(248, 250, 255, 0.6);
  padding: 4px;
  border-radius: 16px;
}

.option-btn {
  padding: 6px 18px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: #8c9aa8;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.option-btn:hover {
  color: #4a5a6a;
}

.option-btn.active {
  background: #ffffff;
  color: #5fc3e4;
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.12);
  transform: translateY(-2px);
}

.week-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.week-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(248, 250, 255, 0.8);
  color: #4a5a6a;
  font-size: 20px;
  font-weight: 300;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.week-btn:hover {
  background: #ffffff;
  color: #5fc3e4;
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.12);
  transform: scale(1.05);
}

.week-btn:active {
  transform: scale(0.92);
}

.week-number {
  font-size: 22px;
  font-weight: 700;
  color: #1a2a3a;
  min-width: 36px;
  text-align: center;
}

.week-unit {
  font-size: 14px;
  color: #8c9aa8;
  margin-left: 4px;
}

/* ===== 操作按钮 ===== */
.input-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding-top: 4px;
}

.btn-primary {
  padding: 12px 32px;
  border: none;
  border-radius: 9999px;
  background: linear-gradient(135deg, #5fc3e4 0%, #7bc8a4 100%);
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 20px rgba(95, 195, 228, 0.25);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 32px rgba(95, 195, 228, 0.35);
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.96);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-ghost {
  padding: 12px 20px;
  border: none;
  border-radius: 9999px;
  background: rgba(248, 250, 255, 0.6);
  color: #6a7a8a;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.btn-ghost:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.8);
  color: #1a2a3a;
  transform: translateY(-2px);
}

.btn-ghost:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-outline {
  padding: 12px 20px;
  border: 2px solid rgba(95, 195, 228, 0.2);
  border-radius: 9999px;
  background: transparent;
  color: #5fc3e4;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.btn-outline:hover {
  border-color: #5fc3e4;
  background: rgba(95, 195, 228, 0.04);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.06);
}

/* ============================================================
   ===== 计划结果 =====
   ============================================================ */
.plan-result {
  animation: slideUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.plan-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  padding: 18px 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.04);
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.overview-label {
  font-size: 12px;
  color: #8c9aa8;
  font-weight: 500;
}

.overview-value {
  font-size: 15px;
  font-weight: 600;
  color: #1a2a3a;
}

.overview-value.plan-id {
  font-size: 13px;
  color: #8c9aa8;
  font-weight: 500;
}

/* ===== 阶段卡片 ===== */
.plan-phases {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
}

.phase-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  padding: 20px 22px;
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-left: 5px solid #5fc3e4;
  transition: all 0.3s ease;
}

.phase-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(95, 195, 228, 0.08);
}

.phase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.phase-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.phase-number {
  font-size: 11px;
  font-weight: 600;
  color: #5fc3e4;
  background: rgba(95, 195, 228, 0.08);
  padding: 2px 14px;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.phase-title h3 {
  font-size: 17px;
  font-weight: 600;
  color: #1a2a3a;
  margin: 0;
}

.phase-week {
  font-size: 13px;
  font-weight: 500;
  color: #8c9aa8;
  background: rgba(248, 250, 255, 0.6);
  padding: 2px 14px;
  border-radius: 9999px;
}

.phase-goal,
.phase-tasks,
.phase-reading,
.phase-deliverable {
  margin-top: 8px;
}

.phase-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #6a7a8a;
  margin-bottom: 4px;
}

.phase-goal p,
.phase-deliverable p {
  color: #4a5a6a;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

.phase-tasks ul {
  padding-left: 0;
  margin: 4px 0 0 0;
  list-style: none;
}

.phase-tasks li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 3px 0;
  color: #4a5a6a;
  font-size: 14px;
  line-height: 1.5;
}

.task-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5fc3e4, #7bc8a4);
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
  color: #5fc3e4;
  background: rgba(95, 195, 228, 0.06);
  padding: 2px 14px;
  border-radius: 9999px;
  font-weight: 500;
}

/* ===== 周计划 ===== */
.weekly-plan {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  padding: 18px 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 12px rgba(95, 195, 228, 0.04);
}

.weekly-plan h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a2a3a;
}

.weekly-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.weekly-item {
  background: rgba(248, 250, 255, 0.6);
  border-radius: 16px;
  padding: 12px 14px;
  transition: all 0.2s ease;
}

.weekly-item:hover {
  background: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(95, 195, 228, 0.04);
}

.weekly-week {
  font-weight: 600;
  color: #5fc3e4;
  display: block;
  margin-bottom: 2px;
  font-size: 13px;
}

.weekly-goal {
  font-size: 13px;
  color: #4a5a6a;
  display: block;
  margin-bottom: 4px;
}

.weekly-item ul {
  padding-left: 16px;
  margin: 4px 0 0 0;
}

.weekly-item li {
  font-size: 12px;
  color: #8c9aa8;
  padding: 1px 0;
}

/* ===== 风险 ===== */
.plan-risks {
  background: rgba(255, 138, 92, 0.04);
  border-radius: 20px;
  padding: 14px 20px;
  margin-bottom: 20px;
  border-left: 5px solid #ff8a5c;
}

.plan-risks h4 {
  margin: 0 0 6px 0;
  font-size: 14px;
  font-weight: 600;
  color: #e07c4a;
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
  color: #8a6a4a;
  font-size: 14px;
  padding: 2px 0;
  line-height: 1.5;
}

.risk-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ff8a5c;
  flex-shrink: 0;
  margin-top: 7px;
}

/* ===== 操作 ===== */
.plan-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-primary-outline {
  padding: 10px 24px;
  border: 2px solid #5fc3e4;
  border-radius: 9999px;
  background: transparent;
  color: #5fc3e4;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.btn-primary-outline:hover {
  background: #5fc3e4;
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(95, 195, 228, 0.2);
}

.btn-primary-outline:active {
  transform: scale(0.96);
}

/* ===== 空状态 ===== */
.empty-state {
  text-align: center;
  padding: 50px 20px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.empty-icon {
  color: #c8d4e0;
  margin-bottom: 12px;
}

.empty-icon svg {
  stroke: #c8d4e0;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1a2a3a;
  margin: 0 0 6px 0;
}

.empty-state p {
  color: #8c9aa8;
  margin: 0 0 2px 0;
  font-size: 15px;
}

.empty-state .empty-hint {
  color: #b8c4d0;
  font-size: 13px;
  margin-top: 8px;
}

/* ============================================================
   ===== 响应式 =====
   ============================================================ */
@media (max-width: 768px) {
  .agent-container {
    padding: 16px 12px;
  }

  .page-title {
    font-size: 22px;
    flex-wrap: wrap;
  }

  .title-icon {
    width: 40px;
    height: 40px;
  }

  .title-icon svg {
    width: 20px;
    height: 20px;
  }

  .agent-input-card {
    padding: 20px 16px;
    border-radius: 20px;
  }

  .input-options {
    flex-direction: column;
    gap: 14px;
  }

  .input-actions {
    flex-direction: column;
  }

  .input-actions button {
    width: 100%;
    justify-content: center;
  }

  .phase-card {
    padding: 16px;
  }

  .phase-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .phase-title h3 {
    font-size: 15px;
  }

  .plan-overview {
    grid-template-columns: 1fr 1fr;
    padding: 14px 16px;
  }

  .weekly-grid {
    grid-template-columns: 1fr;
  }

  .empty-state {
    padding: 40px 16px;
  }
}

@media (max-width: 480px) {
  .plan-overview {
    grid-template-columns: 1fr;
  }

  .option-group {
    flex-wrap: wrap;
  }

  .option-btn {
    flex: 1;
    text-align: center;
    padding: 6px 12px;
    font-size: 12px;
  }

  .page-title {
    font-size: 19px;
  }

  .title-badge {
    font-size: 10px;
    padding: 2px 12px;
  }
}
</style>