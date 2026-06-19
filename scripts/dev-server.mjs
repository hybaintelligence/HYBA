import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { createServer as createViteServer } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const scriptDir = path.dirname(__filename);
const projectRoot = path.resolve(scriptDir, '..');

const app = express();
const PORT = Number(process.env.PORT || 3000);
const BACKEND_URL = process.env.PULVINI_BACKEND_URL || `http://127.0.0.1:${process.env.BACKEND_PORT || 3001}`;

// API proxy to backend
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: { '^/api': '/api' },
  logLevel: 'warn',
  on: {
    error: (err, req, res) => {
      console.error('Proxy error:', err.message);
      res.status(503).json({ error: 'backend_unavailable', detail: err.message });
    },
  },
}));

app.use('/health', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: { '^/health': '/health' },
  logLevel: 'warn',
}));

// Create Vite dev server from the repository root, not the scripts directory.
const vite = await createViteServer({
  plugins: [react(), tailwindcss()],
  root: projectRoot,
  server: {
    middlewareMode: true,
    hmr: process.env.DISABLE_HMR !== 'true',
    fs: { strict: false, allow: [projectRoot] },
  },
  appType: 'spa',
});

// Use Vite's connect instance as middleware.
app.use(vite.middlewares);

app.listen(PORT, () => {
  console.log(`\n🚀 HYBA Development Server`);
  console.log(`   Frontend: http://localhost:${PORT}`);
  console.log(`   Backend API: ${BACKEND_URL}`);
  console.log(`   Proxy: /api and /health -> ${BACKEND_URL}\n`);
});
