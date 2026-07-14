<template>
  <div class="agent-container">
    <!-- 顶部 -->
    <div class="agent-header">
      <h1 class="page-title">🧠 Agent 科研规划</h1>
      <p class="page-desc">输入你的研究目标，AI 将为你生成个性化的科研阅读路线和阶段计划</p>
    </div>

    <!-- 输入区 -->
    <div class="agent-input-card">
      <div class="input-area">
        <el-input
          v-model="researchTopic"
          type="textarea"
          :rows="3"
          placeholder="请输入你的研究目标，例如：我想研究时间序列预测中的 Transformer 方法，重点关注其在金融领域的应用"
          maxlength="500"
          show-word-limit
        />
        <div class="input-actions">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="generatePlan"
            :disabled="!researchTopic.trim()"
          >
            {{ loading ? '生成中...' : '🚀 生成科研计划' }}
          </el-button>
          <el-button size="large" @click="clearPlan" :disabled="!plan">
            清空结果
          </el-button>
        </div>
      </div>
    </div>

    <!-- 计划结果 -->
    <div v-if="plan" class="plan-result">
      <!-- 概览 -->
      <div class="plan-overview">
        <div class="overview-item">
          <span class="overview-label">研究目标</span>
          <span class="overview-value">{{ plan.topic || researchTopic }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">总时长</span>
          <span class="overview-value">{{ plan.weekly_plan?.length || 4 }} 周</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">阶段数</span>
          <span class="overview-value">{{ plan.stages?.length || 0 }} 个阶段</span>
        </div>
      </div>

      <!-- 阶段详情 -->
      <div class="plan-phases">
        <div
          v-for="(phase, index) in plan.stages"
          :key="index"
          class="phase-card"
          :style="{ borderLeftColor: phaseColors[index % phaseColors.length] }"
        >
          <div class="phase-header">
            <div class="phase-title">
              <span class="phase-number">Phase {{ index + 1 }}</span>
              <h3>{{ phase.name }}</h3>
            </div>
            <el-tag :type="phaseTags[index % phaseTags.length]" size="large">
              {{ phase.weeks || '第 ' + (index + 1) + ' 周' }}
            </el-tag>
          </div>

          <div class="phase-goal">
            <strong>🎯 目标：</strong>{{ phase.goal || phase.output }}
          </div>

          <div class="phase-tasks">
            <strong>📋 任务清单：</strong>
            <ul>
              <li v-for="(task, ti) in phase.tasks" :key="ti">
                <el-icon><Check /></el-icon>
                {{ task }}
              </li>
            </ul>
          </div>

          <div class="phase-reading" v-if="phase.reading_list?.length">
            <strong>📖 阅读清单：</strong>
            <div class="reading-tags">
              <el-tag
                v-for="(paper, pi) in phase.reading_list"
                :key="pi"
                size="small"
                type="primary"
                style="margin: 4px 6px 4px 0;"
              >
                {{ paper }}
              </el-tag>
            </div>
          </div>

          <div class="phase-deliverable" v-if="phase.output || phase.deliverable">
            <strong>📦 产出：</strong>{{ phase.output || phase.deliverable }}
          </div>
        </div>
      </div>

      <!-- 风险提醒 -->
      <div class="plan-risks" v-if="plan.risks?.length">
        <h4>⚠️ 风险提醒</h4>
        <ul>
          <li v-for="(risk, idx) in plan.risks" :key="idx">
            <el-icon><Warning /></el-icon>
            {{ risk }}
          </li>
        </ul>
      </div>

      <!-- 操作按钮 -->
      <div class="plan-actions">
        <el-button type="success" @click="exportPlan">
          <el-icon><Download /></el-icon> 导出计划
        </el-button>
        <el-button @click="copyPlan">
          <el-icon><CopyDocument /></el-icon> 复制内容
        </el-button>
      </div>
    </div>

    <!-- 空状态 / 示例 -->
    <el-empty v-else description="输入研究目标，AI 将为你生成科研计划" :image-size="120">
      <template #description>
        <p style="color: #999; font-size: 14px;">输入研究目标，AI 将为你生成科研计划</p>
        <p style="color: #ccc; font-size: 13px;">示例：我想研究时间序列预测中的 Transformer 方法</p>
      </template>
      <el-button type="primary" @click="loadExample">查看示例</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Warning, Download, CopyDocument } from '@element-plus/icons-vue'
import axios from '../utils/axios'

// ===== 状态 =====
const researchTopic = ref('')
const loading = ref(false)
const plan = ref(null)

// ===== 颜色 =====
const phaseColors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
const phaseTags = ['primary', 'warning', 'success', 'danger', 'info']

// ===== 生成计划 =====
const generatePlan = async () => {
  if (!researchTopic.value.trim()) {
    ElMessage.warning('请输入研究目标')
    return
  }

  loading.value = true
  try {
    const res = await axios.post('/api/agent/research-plan', {
      topic: researchTopic.value.trim(),
      level: 'beginner',
      duration_weeks: 4
    })

    if (res.data.code === 200 || res.data.code === 0) {
      plan.value = res.data.data || res.data
      ElMessage.success('科研计划生成成功！')
    } else {
      // 接口失败时使用 Mock
      ElMessage.warning('接口暂不可用，使用示例数据')
      loadMockPlan()
    }
  } catch (error) {
    console.warn('接口请求失败，使用 Mock 数据:', error)
    loadMockPlan()
  } finally {
    loading.value = false
  }
}

// ===== Mock 计划数据 =====
const loadMockPlan = () => {
  plan.value = {
    topic: researchTopic.value || '时间序列预测中的 Transformer 方法',
    total_weeks: '4 周',
    stages: [
      {
        name: '基础知识构建',
        goal: '掌握时间序列分析和 Transformer 的基础知识',
        weeks: '第 1 周',
        tasks: [
          '复习时间序列分析基础（ARIMA、指数平滑等）',
          '学习 Transformer 架构原理（Attention、Positional Encoding）',
          '熟悉 PyTorch 基础操作'
        ],
        reading_list: [
          'Attention Is All You Need (Vaswani et al., 2017)',
          'Time Series Analysis: Forecasting and Control (Box et al.)',
          'PyTorch 官方教程'
        ],
        deliverable: '学习笔记 + 代码环境搭建完成'
      },
      {
        name: '文献调研与复现',
        goal: '阅读核心论文，理解不同 Transformer 变体在时间序列中的应用',
        weeks: '第 2 周',
        tasks: [
          '阅读 Informer、Autoformer、PatchTST 等论文',
          '复现至少一个模型的 PyTorch 实现',
          '对比不同模型的性能差异'
        ],
        reading_list: [
          'Informer: Beyond Efficient Transformer (Zhou et al., 2021)',
          'Autoformer: Decomposition Transformers (Wu et al., 2021)',
          'PatchTST: A Time Series Transformer (Nie et al., 2022)'
        ],
        deliverable: '模型复现代码 + 实验报告'
      },
      {
        name: '金融场景应用设计',
        goal: '设计基于 Transformer 的金融时间序列预测方案',
        weeks: '第 3 周',
        tasks: [
          '收集金融时间序列数据（股价、交易量等）',
          '设计数据预处理和特征工程方案',
          '实现金融预测模型并调优'
        ],
        reading_list: [
          'Financial Time Series Forecasting with Transformer',
          'Quantitative Trading with Machine Learning'
        ],
        deliverable: '金融预测模型原型'
      },
      {
        name: '论文撰写与总结',
        goal: '整理研究成果，撰写科研论文',
        weeks: '第 4 周',
        tasks: [
          '整理实验数据和结果',
          '撰写论文初稿（Introduction、Method、Experiment）',
          '准备相关图表和可视化'
        ],
        reading_list: [
          '相关领域顶级会议论文（NeurIPS、ICML、ICLR）'
        ],
        deliverable: '科研论文初稿'
      }
    ],
    risks: [
      'Transformer 模型在长序列上计算复杂度高，需关注内存使用',
      '金融数据的信噪比较低，预测效果可能不如预期',
      '模型训练时间可能较长，建议提前规划算力资源'
    ]
  }
  ElMessage.success('使用示例数据生成完成！')
}

// ===== 清空 =====
const clearPlan = () => {
  plan.value = null
  ElMessage.info('已清空计划')
}

// ===== 加载示例 =====
const loadExample = () => {
  researchTopic.value = '我想研究时间序列预测中的 Transformer 方法，重点关注其在金融领域的应用'
  generatePlan()
}

// ===== 导出计划（TXT） =====
const exportPlan = () => {
  if (!plan.value) return
  let text = `📚 科研计划\n`
  text += `研究目标：${plan.value.topic}\n`
  text += `总时长：${plan.value.weekly_plan?.length || 4} 周\n\n`
  plan.value.stages.forEach((p, i) => {
    text += `【Phase ${i+1}】${p.name}（${p.weeks}）\n`
    text += `目标：${p.goal}\n`
    text += `任务：\n${p.tasks.map(t => `  - ${t}`).join('\n')}\n`
    if (p.reading_list?.length) {
      text += `阅读清单：\n${p.reading_list.map(r => `  - ${r}`).join('\n')}\n`
    }
    text += `产出：${p.deliverable}\n\n`
  })
  if (plan.value.risks?.length) {
    text += `⚠️ 风险提醒：\n${plan.value.risks.map(r => `  - ${r}`).join('\n')}\n`
  }

  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `科研计划_${new Date().toISOString().slice(0,10)}.txt`
  link.click()
  ElMessage.success('导出成功！')
}

// ===== 复制计划 =====
const copyPlan = () => {
  if (!plan.value) return
  let text = `📚 科研计划：${plan.value.topic}\n\n`
  plan.value.stages.forEach((p, i) => {
    text += `【Phase ${i+1}】${p.name}\n`
    text += `目标：${p.goal}\n`
    text += `任务：${p.tasks.join('；')}\n`
    if (p.reading_list?.length) {
      text += `阅读：${p.reading_list.join('；')}\n`
    }
    text += `产出：${p.deliverable}\n\n`
  })
  navigator.clipboard?.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板！')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动选择复制')
  })
}
</script>

<style scoped>
.agent-container {
  padding: 24px 40px;
  max-width: 900px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f5f7fa;
}

.agent-header {
  margin-bottom: 28px;
}
.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a2332;
  margin-bottom: 8px;
}
.page-desc {
  color: #8c8f9c;
  font-size: 15px;
}

.agent-input-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px 32px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  margin-bottom: 24px;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.input-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* ===== 计划结果 ===== */
.plan-result {
  animation: fadeUp 0.4s ease;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.plan-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.overview-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.overview-label {
  font-size: 13px;
  color: #999;
}
.overview-value {
  font-size: 16px;
  font-weight: 600;
  color: #1a2332;
}

.plan-phases {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.phase-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border-left: 4px solid #667eea;
}
.phase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}
.phase-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.phase-number {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
  background: #f0f2ff;
  padding: 2px 12px;
  border-radius: 20px;
}
.phase-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a2332;
  margin: 0;
}

.phase-goal,
.phase-tasks,
.phase-reading,
.phase-deliverable {
  margin-top: 10px;
  color: #555;
  font-size: 14px;
  line-height: 1.7;
}
.phase-tasks ul {
  padding-left: 20px;
  margin: 4px 0;
}
.phase-tasks li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 2px 0;
  color: #555;
}
.phase-tasks li .el-icon {
  color: #67c23a;
  margin-top: 3px;
}
.reading-tags {
  display: flex;
  flex-wrap: wrap;
  margin-top: 4px;
}

.plan-risks {
  background: #fdf6ed;
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 20px;
  border-left: 4px solid #e6a23c;
}
.plan-risks h4 {
  margin: 0 0 8px 0;
  color: #b88230;
}
.plan-risks ul {
  padding-left: 20px;
  margin: 0;
}
.plan-risks li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #b88230;
  padding: 2px 0;
}

.plan-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 600px) {
  .agent-container { padding: 16px; }
  .agent-input-card { padding: 20px; }
  .phase-card { padding: 16px; }
  .phase-header { flex-direction: column; align-items: flex-start; }
  .plan-overview { grid-template-columns: 1fr; }
}
</style>
