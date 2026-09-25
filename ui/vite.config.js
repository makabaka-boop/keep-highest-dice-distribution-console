import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// 开发/预览时把 /api 代理到本机 Flask；容器部署时由 ui 容器的 nginx 反代到 odds 服务
const oddsTarget = process.env.ODDS_URL || 'http://localhost:5000';

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: { '/api': oddsTarget },
  },
  preview: {
    proxy: { '/api': oddsTarget },
  },
});
