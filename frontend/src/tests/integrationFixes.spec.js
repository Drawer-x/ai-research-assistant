import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { normalizeCurrentUser, normalizeGraphData, normalizePaperList, normalizeSummary, readableValue, unwrapApiData } from '../utils/apiData'

describe('unified API mapping', () => {
  it('unwraps exactly one unified response layer', () => {
    expect(unwrapApiData({ data: { code: 200, message: 'success', data: { id: 7 } } })).toEqual({ id: 7 })
  })

  it('normalizes generated and historical summaries with readable complex values', () => {
    const generated = normalizeSummary({ data: { code: 200, data: { summary: { background: '真实背景', experiment: ['实验一'], result: { score: 0.9 } }, is_mock: false } } })
    expect(generated.is_mock).toBe(false)
    expect(generated.fields.find(item => item.key === 'background').value).toBe('真实背景')
    expect(generated.fields.find(item => item.key === 'result').value).toContain('score: 0.9')
    const historical = normalizeSummary({ content: { method: ['RAG', 'Transformer'] }, is_mock: true })
    expect(historical.is_mock).toBe(true)
    expect(historical.fields.find(item => item.key === 'method').value).toContain('RAG')
    expect(readableValue({ nested: ['a', 'b'] })).not.toContain('[object Object]')
  })

  it('normalizes graph node and edge identifiers for ECharts', () => {
    const graph = normalizeGraphData({ data: { code: 200, data: { nodes: [{ id: 3, title: '真实论文' }], edges: [{ source: 3, target: 4, relation_type: 'citation', weight: 0.8 }] } } })
    expect(graph.nodes[0]).toMatchObject({ id: '3', paper_id: 3, label: '真实论文' })
    expect(graph.edges[0]).toMatchObject({ source: '3', target: '4', type: 'citation', category: 0 })
  })

  it('normalizes current user from login and me response shapes', () => {
    expect(normalizeCurrentUser({ data: { code: 200, data: { username: 'alice', email: 'a@example.com' } } }).username).toBe('alice')
    expect(normalizeCurrentUser({ user: { username: 'bob' } }).username).toBe('bob')
  })

  it('keeps real integer paper identifiers for Agent selection and deletion', () => {
    expect(normalizePaperList({ data: { code: 200, data: [{ paper_id: 11, title: 'P' }] } })).toEqual([{ paper_id: 11, id: 11, title: 'P' }])
  })
})

describe('five repaired component contracts', () => {
  const source = name => readFileSync(resolve('src/views', name), 'utf8')

  it('PapersView confirms and calls DELETE with the real paper id', () => {
    const text = source('PapersView.vue')
    expect(text).toContain('ElMessageBox.confirm')
    expect(text).toContain('axios.delete(`/api/papers/${id}`)')
    expect(text).toContain("'删除'")
  })

  it('PaperDetailView renders normalized summary fields immediately and from history', () => {
    const text = source('PaperDetailView.vue')
    expect(text).toContain('summary.value = normalizeSummary(res)')
    expect(text).toContain('loadSummaryHistory')
    expect(text).toContain('v-for="field in summary.fields"')
  })

  it('NavBar restores the real current user instead of a fixed username', () => {
    const text = readFileSync(resolve('src/components/NavBar.vue'), 'utf8')
    expect(text).toContain('await loadCurrentUser()')
    expect(text).toContain("authState.user?.username")
  })

  it('GraphView feeds normalized live nodes and links to ECharts', () => {
    const text = source('GraphView.vue')
    expect(text).toContain('normalizeGraphData(res)')
    expect(text).toContain('chartInstance.setOption(option, true)')
    expect(text).toContain('new ResizeObserver(handleResize)')
  })

  it('AgentView loads real papers and submits selected paper_ids', () => {
    const text = source('AgentView.vue')
    expect(text).toContain('multiple filterable clearable')
    expect(text).toContain("axios.get('/api/papers')")
    expect(text).toContain('paper_ids: form.paper_ids.map(Number).filter(Number.isInteger)')
  })
})
