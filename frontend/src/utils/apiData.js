export const unwrapApiData = (response) => {
  const envelope = response?.data ?? response
  if (envelope && typeof envelope === 'object' && 'code' in envelope) {
    if (envelope.code !== 200 && envelope.code !== 0) {
      throw new Error(envelope.message || '请求失败')
    }
    return envelope.data
  }
  return envelope
}

export const readableValue = (value) => {
  if (value == null || value === '') return '暂无'
  if (Array.isArray(value)) return value.map(readableValue).join('\n')
  if (typeof value === 'object') {
    return Object.entries(value).map(([key, item]) => `${key}: ${readableValue(item)}`).join('\n')
  }
  return String(value)
}

export const normalizeSummary = (response) => {
  const data = unwrapApiData(response) || {}
  const content = data.summary ?? data.content ?? data.result ?? data
  const summary = content && typeof content === 'object' ? content : { result: content }
  return {
    fields: ['background', 'problem', 'method', 'experiment', 'result', 'innovation', 'limitation']
      .map(key => ({ key, value: readableValue(summary[key]) })),
    is_mock: Boolean(data.is_mock),
    model_name: data.model_name || '',
  }
}

export const normalizeGraphData = (response) => {
  const data = unwrapApiData(response) || {}
  const nodes = Array.isArray(data.nodes) ? data.nodes.map(node => {
    const id = String(node.id ?? node.paper_id)
    const localMatch = id.match(/^local:(\d+)$/)
    const numericPaperId = node.paper_id ?? (localMatch ? Number(localMatch[1]) : /^\d+$/.test(id) ? Number(id) : null)
    return {
      ...node,
      id,
      // ECharts graph links resolve string endpoints against node.name.
      // Keep it identical to the normalized edge ids while label remains display text.
      name: id,
      paper_id: numericPaperId == null ? null : Number(numericPaperId),
      label: node.title || node.label || node.name || `论文 ${id}`,
    }
  }) : []
  const edges = Array.isArray(data.edges) ? data.edges.map(edge => ({
    ...edge,
    source: String(edge.source),
    target: String(edge.target),
    type: edge.relation_type || edge.type || 'relation',
    category: ({ citation: 0, topic_similarity: 1, method_similarity: 2 })[edge.relation_type || edge.type] ?? 0,
    weight: Number(edge.weight ?? edge.confidence ?? 0),
    description: edge.description || edge.relation_reason || '',
  })) : []
  return { nodes, edges }
}

export const normalizePaperList = response => {
  const data = unwrapApiData(response)
  return Array.isArray(data) ? data.map(item => ({ ...item, id: Number(item.paper_id ?? item.id) })) : []
}

export const normalizeCurrentUser = response => {
  const data = unwrapApiData(response) || {}
  const user = data.user && typeof data.user === 'object' ? data.user : data
  return { id: user.id ?? user.user_id, username: user.username || user.name || user.email || '', email: user.email || '' }
}
