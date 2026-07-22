import { defineConfig } from '@playwright/test'

const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH?.trim()

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 20_000 },
  use: {
    baseURL: 'http://127.0.0.1:5174',
    headless: true,
    browserName: 'chromium',
    channel: 'msedge',
    ...(executablePath ? { launchOptions: { executablePath } } : {}),
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  outputDir: 'test-results',
  reporter: [['list']],
})
