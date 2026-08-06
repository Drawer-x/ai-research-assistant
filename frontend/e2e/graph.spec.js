import { expect, test } from '@playwright/test'

function pdfBuffer(title) {
  const text = `${title} Author Graph Tester Abstract RAG Transformer academic research. Method retrieval augmented generation embedding vector retrieval Transformer attention. Results effective graph relation. References RAG Transformer Foundations.`
  const escape = value => value.replace(/([\\()])/g, '\\$1')
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
    `<< /Length ${text.length + 36} >>\nstream\nBT /F1 11 Tf 50 740 Td (${escape(text)}) Tj ET\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ]
  let pdf = '%PDF-1.4\n'
  const offsets = [0]
  objects.forEach((object, index) => { offsets.push(Buffer.byteLength(pdf)); pdf += `${index + 1} 0 obj\n${object}\nendobj\n` })
  const xref = Buffer.byteLength(pdf)
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`
  offsets.slice(1).forEach(offset => { pdf += `${String(offset).padStart(10, '0')} 00000 n \n` })
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`
  return Buffer.from(pdf)
}

test('real graph is visible with live nodes and edges', async ({ page }) => {
  const errors = []
  const responses = {}
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('pageerror', error => errors.push(error.message))
  page.on('response', async response => {
    const path = new URL(response.url()).pathname
    if (path === '/api/graph/generate' || path === '/api/graph/enhanced') {
      const body = await response.json().catch(() => null)
      const data = body?.data || {}
      responses[path] = { status: response.status(), nodes: data.nodes?.length || 0, edges: data.edges?.length || 0 }
    }
  })

  const suffix = `${Date.now()}_${Math.random().toString(16).slice(2, 8)}`
  const username = `g${suffix.replace(/\D/g, '').slice(-8)}${Math.random().toString(16).slice(2, 6)}`
  const password = 'Graph-test-123456'
  await page.goto('/register')
  const registerInputs = page.locator('input')
  await registerInputs.nth(0).fill(username)
  await registerInputs.nth(1).fill(`${username}@example.com`)
  await registerInputs.nth(2).fill(password)
  await registerInputs.nth(3).fill(password)
  const registerResponsePromise = page.waitForResponse(response => new URL(response.url()).pathname === '/api/auth/register')
  await page.locator('.register-btn').click()
  const registerResponse = await registerResponsePromise
  expect(registerResponse.status()).toBe(200)
  await page.waitForURL('**/login')
  await expect(page.locator('.login-btn')).toBeVisible()
  const loginInputs = page.locator('.login-form input')
  await loginInputs.nth(0).fill(username)
  await loginInputs.nth(1).fill(password)
  const loginResponsePromise = page.waitForResponse(response => new URL(response.url()).pathname === '/api/auth/login')
  await page.locator('.login-btn').click()
  const loginResponse = await loginResponsePromise
  expect(loginResponse.status()).toBe(200)
  await page.waitForURL('**/papers')

  for (let index = 1; index <= 3; index += 1) {
    await page.getByRole('button', { name: /上传论文/ }).first().click()
    await page.locator('input[type=file]').setInputFiles({ name: `rag-transformer-${index}.pdf`, mimeType: 'application/pdf', buffer: pdfBuffer(`RAG Transformer Study ${index}`) })
    await expect(page.locator('.paper-item')).toHaveCount(index, { timeout: 30_000 })
  }

  await page.goto('/graph')
  await expect(page.locator('[data-testid=graph-chart]')).toBeVisible()
  await page.locator('.btn-generate').first().click()
  await expect.poll(() => responses['/api/graph/generate']?.status).toBe(200)
  await expect.poll(() => responses['/api/graph/enhanced']?.nodes || 0).toBeGreaterThan(0)
  await expect.poll(() => responses['/api/graph/enhanced']?.edges || 0).toBeGreaterThan(0)

  const chart = page.locator('[data-testid=graph-chart]')
  await expect(chart).toHaveAttribute('data-chart-ready', 'true')
  await expect.poll(async () => Number(await chart.getAttribute('data-graph-nodes'))).toBeGreaterThan(0)
  await expect.poll(async () => Number(await chart.getAttribute('data-graph-edges'))).toBeGreaterThan(0)
  const rect = await chart.boundingBox()
  expect(rect.width).toBeGreaterThan(100)
  expect(rect.height).toBeGreaterThan(100)
  const canvas = chart.locator('canvas').first()
  await expect(canvas).toBeVisible()
  const canvasRect = await canvas.boundingBox()
  expect(canvasRect.width).toBeGreaterThan(100)
  expect(canvasRect.height).toBeGreaterThan(100)

  const runtime = await chart.evaluate(element => {
    const style = getComputedStyle(element)
    const instance = element.__echartsInstance
    const option = instance?.getOption()
    const graphSeries = option?.series?.find(series => series.type === 'graph')
    const graphModel = instance?.getModel().getSeriesByIndex(0)
    const graphData = graphModel?.getData()
    const topElement = document.elementFromPoint(
      element.getBoundingClientRect().left + element.getBoundingClientRect().width / 2,
      element.getBoundingClientRect().top + element.getBoundingClientRect().height / 2,
    )
    return {
      style: {
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        position: style.position,
        overflow: style.overflow,
        zIndex: style.zIndex,
        width: style.width,
        height: style.height,
      },
      canvasCount: element.querySelectorAll('canvas').length,
      svgCount: element.querySelectorAll('svg').length,
      chartFound: Boolean(instance),
      seriesCount: option?.series?.length || 0,
      graphFound: Boolean(graphSeries),
      dataCount: graphSeries?.data?.length || 0,
      linksCount: graphSeries?.links?.length || 0,
      renderedElementCount: instance?.getZr().storage.getDisplayList().length || 0,
      nodeLayouts: graphData ? Array.from({ length: graphData.count() }, (_, index) => graphData.getItemLayout(index)) : [],
      centerCoveredByChart: element.contains(topElement),
    }
  })
  expect(runtime.style.display).not.toBe('none')
  expect(runtime.style.visibility).toBe('visible')
  expect(Number(runtime.style.opacity)).toBeGreaterThan(0)
  expect(runtime.canvasCount + runtime.svgCount).toBeGreaterThan(0)
  expect(runtime.chartFound).toBe(true)
  expect(runtime.seriesCount).toBeGreaterThan(0)
  expect(runtime.graphFound).toBe(true)
  expect(runtime.dataCount).toBeGreaterThan(0)
  expect(runtime.linksCount).toBeGreaterThan(0)
  expect(runtime.renderedElementCount).toBeGreaterThan(10)
  expect(runtime.centerCoveredByChart).toBe(true)
  await expect(page.locator('.graph-loading')).toHaveCount(0)
  await expect(page.locator('.empty-graph')).toHaveCount(0)

  const [nodeX, nodeY] = runtime.nodeLayouts[0]
  await canvas.click({ position: { x: nodeX, y: nodeY } })
  await expect(page.locator('.drawer.open')).toBeVisible()
  await expect(page.locator('.drawer.open .node-title')).not.toBeEmpty()
  await expect(page.locator('.drawer.open .node-title')).not.toHaveText('[object Object]')
  await page.locator('.drawer-close').click()
  await canvas.hover()
  await page.mouse.wheel(0, -200)
  await page.screenshot({ path: 'test-results/graph-visible.png', fullPage: true })
  expect(errors.filter(message => /echarts|canvas|uncaught/i.test(message))).toEqual([])

  await page.reload()
  await expect(chart).toHaveAttribute('data-chart-ready', 'true')
  await expect(chart.locator('canvas')).toBeVisible()
  console.log(JSON.stringify({ graphGenerate: responses['/api/graph/generate'], graphQuery: responses['/api/graph/enhanced'], chartRect: rect, canvasRect, runtime }))
})
