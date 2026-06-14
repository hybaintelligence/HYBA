import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { createServer as createViteServer } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const projectRoot = path.dirname(__filename);

const app = express();
const PORT = 3000;
const BACKEND_PORT = 8000;

// API proxy to backend
app.use('/api', createProxyMiddleware({
  target: `http://127.0.0.1:${BACKEND_PORT}`,
  changeOrigin: true,
  logLevel: 'warn',
  onError: (err, req, res) => {
    console.error('Proxy error:', err.message);
    res.status(500).json({ error: 'Backend unavailable', detail: err.message });
  }
}));

// Create Vite dev server
const vite = await createViteServer({
  plugins: [react(), tailwindcss()],
  root: projectRoot,
  server: { 
    middlewareMode: true,
    hmr: process.env.DISABLE_HMR !== 'true',
  },
  appType: 'spa'
});

// Use Vite's connect instance as middleware
app.use(vite.middlewares);

// Start server
app.listen(PORT, () => {
  console.log(`\n🚀 HYBA Development Server`);
  console.log(`   Frontend: http://localhost:${PORT}`);
  console.log(`   Backend API: http://localhost:${BACKEND_PORT}`);
  console.log(`   Proxy: /api -> http://localhost:${BACKEND_PORT}\n`);
});
