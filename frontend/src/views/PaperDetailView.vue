<template>
  <div class="page" v-loading="loading">
    <div class="toolbar">
      <el-button @click="router.push('/papers')">返回文献库</el-button>
      <el-button type="danger" plain @click="removePaper">删除文献</el-button>
    </div>

    <el-card v-if="paper" class="section">
      <template #header><strong>文献信息</strong></template>
      <el-form :model="form" label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="作者"><el-input v-model="form.authors" /></el-form-item>
        <el-form-item label="年份"><el-input-number v-model="form.year" :min="0" :max="9999" /></el-form-item>
        <el-form-item label="发表场所"><el-input v-model="form.venue" /></el-form-item>
        <el-form-item label="摘要"><el-input v-model="form.abstract" type="textarea" :rows="4" /></el-form-item>
        <el-form-item><el-button type="primary" @click="savePaper">保存修改</el-button></el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="paper" class="section">
      <template #header><strong>阅读状态与标签</strong></template>
      <div class="row">
        <el-select v-model="readStatus" @change="saveStatus">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-tag v-for="tag in paper.tags" :key="tag.id" closable @close="removeTag(tag.id)">{{ tag.name }}</el-tag>
        <el-input v-model="newTag" placeholder="新标签" style="width:180px" @keyup.enter="addTag" />
        <el-button @click="addTag">添加标签</el-button>
      </div>
    </el-card>

    <el-card v-if="paper" class="section">
      <template #header><strong>AI 论文阅读</strong></template>
      <el-button type="primary" :loading="summaryLoading" @click="generateSummary">生成 AI 总结</el-button>
      <el-tag v-if="summaryMock" type="warning" class="mock-tag">Mock</el-tag>
      <el-descriptions v-if="summary" :column="1" border class="result">
        <el-descriptions-item v-for="(value, key) in summary" :key="key" :label="summaryLabels[key] || key">{{ value }}</el-descriptions-item>
      </el-descriptions>

      <div class="qa-row">
        <el-input v-model="question" placeholder="输入关于这篇论文的问题" @keyup.enter="askQuestion" />
        <el-button type="success" :loading="qaLoading" @click="askQuestion">提问</el-button>
      </div>
      <el-alert v-if="answer" :title="answer.answer" type="success" :closable="false" show-icon class="result" />
      <ul v-if="answer?.evidence?.length" class="evidence">
        <li v-for="(item, index) in answer.evidence" :key="index">{{ item }}</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../utils/axios'

const route = useRoute()
const router = useRouter()
const paperId = route.params.id
const paper = ref(null)
const loading = ref(false)
const summaryLoading = ref(false)
const qaLoading = ref(false)
const readStatus = ref('unread')
const newTag = ref('')
const question = ref('')
const summary = ref(null)
const summaryMock = ref(false)
const answer = ref(null)
const form = reactive({ title: '', authors: '', year: null, venue: '', abstract: '' })
const statusOptions = [
  ['unread', '未读'], ['rough_read', '粗读'], ['intensive_read', '精读'],
  ['to_reproduce', '待复现'], ['for_review', '待综述'], ['archived', '已归档']
].map(([value, label]) => ({ value, label }))
const summaryLabels = { background: '研究背景', problem: '研究问题', method: '核心方法', experiment: '实验设置', result: '主要结果', innovation: '创新点', limitation: '局限性' }

const applyPaper = (data) => {
  paper.value = data
  Object.assign(form, { title: data.title || '', authors: data.authors || '', year: data.year, venue: data.venue || '', abstract: data.abstract || '' })
  readStatus.value = data.read_status || 'unread'
}
const loadPaper = async () => {
  loading.value = true
  try { applyPaper((await api.get(`/api/papers/${paperId}`)).data.data) }
  catch (error) { ElMessage.error(error.response?.data?.message || '加载文献失败'); router.push('/papers') }
  finally { loading.value = false }
}
const savePaper = async () => {
  const { data } = await api.put(`/api/papers/${paperId}`, form)
  applyPaper(data.data); ElMessage.success('文献信息已保存')
}
const saveStatus = async () => {
  await api.put(`/api/papers/${paperId}/status`, { read_status: readStatus.value })
  paper.value.read_status = readStatus.value; ElMessage.success('阅读状态已更新')
}
const addTag = async () => {
  if (!newTag.value.trim()) return
  await api.post(`/api/papers/${paperId}/tags`, { tag_name: newTag.value.trim() })
  newTag.value = ''; await loadPaper(); ElMessage.success('标签已添加')
}
const removeTag = async (tagId) => {
  await api.delete(`/api/papers/${paperId}/tags/${tagId}`)
  paper.value.tags = paper.value.tags.filter(tag => tag.id !== tagId)
}
const generateSummary = async () => {
  summaryLoading.value = true
  try { const data = (await api.post(`/api/papers/${paperId}/summary`)).data.data; summary.value = data.summary; summaryMock.value = data.is_mock }
  catch (error) { ElMessage.error(error.response?.data?.message || '总结生成失败') }
  finally { summaryLoading.value = false }
}
const askQuestion = async () => {
  if (!question.value.trim()) return
  qaLoading.value = true
  try { answer.value = (await api.post(`/api/papers/${paperId}/qa`, { question: question.value.trim() })).data.data }
  catch (error) { ElMessage.error(error.response?.data?.message || '问答失败') }
  finally { qaLoading.value = false }
}
const removePaper = async () => {
  await ElMessageBox.confirm('确定删除这篇文献吗？', '确认删除', { type: 'warning' })
  await api.delete(`/api/papers/${paperId}`); ElMessage.success('文献已删除'); router.push('/papers')
}
onMounted(loadPaper)
</script>

<style scoped>
.page { min-height: 100vh; padding: 24px; background: #f5f7fa; }
.toolbar { max-width: 1000px; margin: 0 auto 16px; display:flex; justify-content:space-between; }
.section { max-width: 1000px; margin: 0 auto 18px; }
.row, .qa-row { display:flex; align-items:center; flex-wrap:wrap; gap:10px; }
.qa-row { margin-top:24px; flex-wrap:nowrap; }
.result { margin-top:16px; }
.mock-tag { margin-left:10px; }
.evidence { margin:12px 0 0 20px; color:#606266; }
</style>
