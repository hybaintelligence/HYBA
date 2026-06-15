import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';

// Windows-safe root resolution — explicitly convert to file:// URL to handle
// OneDrive virtualised paths that can break the tsx ESM resolver.
const __filename = fileURLToPath(import.meta.url);
const projectRoot = path.dirname(__filename);

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': projectRoot,
      },
    },
    build: {
      rollupOptions: {
        external: ['react-is'],
      },
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
      // Force file:// scheme for all file serving on Windows to avoid tsx resolver issues
      fs: {
        strict: false,
        allow: [projectRoot],
      },
    },
    // Pin the config file URL scheme to file:// for Windows + OneDrive compatibility
    configFile: false,
  };
});
