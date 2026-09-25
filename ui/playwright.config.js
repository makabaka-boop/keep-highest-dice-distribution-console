import { defineConfig } from '@playwright/test';

// 默认对 vite preview（本地联调）；对 Docker Compose 用 UI_BASE_URL=http://localhost:8080
const baseURL = process.env.UI_BASE_URL || 'http://localhost:4173';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 0,
  use: { baseURL },
  reporter: [['list']],
});
