import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './playwright',
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5187',
    ...devices['Desktop Chrome'],
  },
  webServer: {
    command: 'pnpm --filter @lango-learn/web dev --host 127.0.0.1 --port 5187 --strictPort',
    url: 'http://127.0.0.1:5187',
    reuseExistingServer: false,
    timeout: 30_000,
  },
})
