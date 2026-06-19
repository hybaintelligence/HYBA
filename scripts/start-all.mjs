#!/usr/bin/env node
/**
 * HYBA Full Stack Launcher
 * Starts both backend (Python FastAPI) and frontend (Vite dev server) concurrently
 */

import { spawn } from 'node:child_process';
import { platform } from 'node:os';

const IS_WINDOWS = platform() === 'win32';
const PYTHON_CMD = process.env.PYTHON || (IS_WINDOWS ? 'python' : 'python3');

console.log('🚀 Starting HYBA Full Stack...\n');

// Start Python Backend
console.log('📡 Starting Python Backend on port 3001...');
const backend = spawn(
  PYTHON_CMD,
  [
    '-m',
    'uvicorn',
    'hyba_genesis_api.main:app',
    '--app-dir',
    'python_backend',
    '--host',
    '127.0.0.1',
    '--port',
    '3001',
    '--reload'
  ],
  {
    stdio: 'inherit',
    shell: IS_WINDOWS,
    env: {
      ...process.env,
      PYTHONPATH: 'python_backend'
    }
  }
);

// Start Frontend Dev Server
console.log('🎨 Starting Frontend Dev Server on port 3000...\n');
const frontend = spawn(
  'node',
  ['scripts/dev-server.mjs'],
  {
    stdio: 'inherit',
    shell: IS_WINDOWS
  }
);

// Handle process termination
const cleanup = (signal) => {
  console.log(`\n🛑 Received ${signal}, shutting down gracefully...`);
  backend.kill();
  frontend.kill();
  process.exit(0);
};

process.on('SIGINT', () => cleanup('SIGINT'));
process.on('SIGTERM', () => cleanup('SIGTERM'));

backend.on('exit', (code) => {
  console.log(`\n❌ Backend exited with code ${code}`);
  frontend.kill();
  process.exit(code || 1);
});

frontend.on('exit', (code) => {
  console.log(`\n❌ Frontend exited with code ${code}`);
  backend.kill();
  process.exit(code || 1);
});

console.log('✨ Both services are starting...');
console.log('   Press Ctrl+C to stop all services\n');
