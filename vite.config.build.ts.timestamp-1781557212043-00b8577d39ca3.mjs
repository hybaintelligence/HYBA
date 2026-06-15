// vite.config.build.ts
import tailwindcss from "file:///C:/Users/USER/OneDrive/Desktop/HYBA_FULLSTACK/node_modules/@tailwindcss/vite/dist/index.mjs";
import react from "file:///C:/Users/USER/OneDrive/Desktop/HYBA_FULLSTACK/node_modules/@vitejs/plugin-react/dist/index.js";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "file:///C:/Users/USER/OneDrive/Desktop/HYBA_FULLSTACK/node_modules/vite/dist/node/index.js";
var __vite_injected_original_import_meta_url = "file:///C:/Users/USER/OneDrive/Desktop/HYBA_FULLSTACK/vite.config.build.ts";
var __filename = fileURLToPath(__vite_injected_original_import_meta_url);
var projectRoot = path.dirname(__filename);
var vite_config_build_default = defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": projectRoot
      }
    },
    build: {
      rollupOptions: {
        external: ["react-is"]
      }
    },
    server: {
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      hmr: process.env.DISABLE_HMR !== "true",
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === "true" ? null : {},
      // Force file:// scheme for all file serving on Windows to avoid tsx resolver issues
      fs: {
        strict: false,
        allow: [projectRoot]
      }
    },
    // Pin the config file URL scheme to file:// for Windows + OneDrive compatibility
    configFile: false
  };
});
export {
  vite_config_build_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuYnVpbGQudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxVU0VSXFxcXE9uZURyaXZlXFxcXERlc2t0b3BcXFxcSFlCQV9GVUxMU1RBQ0tcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXFVTRVJcXFxcT25lRHJpdmVcXFxcRGVza3RvcFxcXFxIWUJBX0ZVTExTVEFDS1xcXFx2aXRlLmNvbmZpZy5idWlsZC50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvVVNFUi9PbmVEcml2ZS9EZXNrdG9wL0hZQkFfRlVMTFNUQUNLL3ZpdGUuY29uZmlnLmJ1aWxkLnRzXCI7aW1wb3J0IHRhaWx3aW5kY3NzIGZyb20gJ0B0YWlsd2luZGNzcy92aXRlJztcclxuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0JztcclxuaW1wb3J0IHBhdGggZnJvbSAnbm9kZTpwYXRoJztcclxuaW1wb3J0IHsgZmlsZVVSTFRvUGF0aCB9IGZyb20gJ25vZGU6dXJsJztcclxuaW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSc7XHJcblxyXG4vLyBXaW5kb3dzLXNhZmUgcm9vdCByZXNvbHV0aW9uIFx1MjAxNCBleHBsaWNpdGx5IGNvbnZlcnQgdG8gZmlsZTovLyBVUkwgdG8gaGFuZGxlXHJcbi8vIE9uZURyaXZlIHZpcnR1YWxpc2VkIHBhdGhzIHRoYXQgY2FuIGJyZWFrIHRoZSB0c3ggRVNNIHJlc29sdmVyLlxyXG5jb25zdCBfX2ZpbGVuYW1lID0gZmlsZVVSTFRvUGF0aChpbXBvcnQubWV0YS51cmwpO1xyXG5jb25zdCBwcm9qZWN0Um9vdCA9IHBhdGguZGlybmFtZShfX2ZpbGVuYW1lKTtcclxuXHJcbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZygoKSA9PiB7XHJcbiAgcmV0dXJuIHtcclxuICAgIHBsdWdpbnM6IFtyZWFjdCgpLCB0YWlsd2luZGNzcygpXSxcclxuICAgIHJlc29sdmU6IHtcclxuICAgICAgYWxpYXM6IHtcclxuICAgICAgICAnQCc6IHByb2plY3RSb290LFxyXG4gICAgICB9LFxyXG4gICAgfSxcclxuICAgIGJ1aWxkOiB7XHJcbiAgICAgIHJvbGx1cE9wdGlvbnM6IHtcclxuICAgICAgICBleHRlcm5hbDogWydyZWFjdC1pcyddLFxyXG4gICAgICB9LFxyXG4gICAgfSxcclxuICAgIHNlcnZlcjoge1xyXG4gICAgICAvLyBITVIgaXMgZGlzYWJsZWQgaW4gQUkgU3R1ZGlvIHZpYSBESVNBQkxFX0hNUiBlbnYgdmFyLlxyXG4gICAgICBobXI6IHByb2Nlc3MuZW52LkRJU0FCTEVfSE1SICE9PSAndHJ1ZScsXHJcbiAgICAgIC8vIERpc2FibGUgZmlsZSB3YXRjaGluZyB3aGVuIERJU0FCTEVfSE1SIGlzIHRydWUgdG8gc2F2ZSBDUFUgZHVyaW5nIGFnZW50IGVkaXRzLlxyXG4gICAgICB3YXRjaDogcHJvY2Vzcy5lbnYuRElTQUJMRV9ITVIgPT09ICd0cnVlJyA/IG51bGwgOiB7fSxcclxuICAgICAgLy8gRm9yY2UgZmlsZTovLyBzY2hlbWUgZm9yIGFsbCBmaWxlIHNlcnZpbmcgb24gV2luZG93cyB0byBhdm9pZCB0c3ggcmVzb2x2ZXIgaXNzdWVzXHJcbiAgICAgIGZzOiB7XHJcbiAgICAgICAgc3RyaWN0OiBmYWxzZSxcclxuICAgICAgICBhbGxvdzogW3Byb2plY3RSb290XSxcclxuICAgICAgfSxcclxuICAgIH0sXHJcbiAgICAvLyBQaW4gdGhlIGNvbmZpZyBmaWxlIFVSTCBzY2hlbWUgdG8gZmlsZTovLyBmb3IgV2luZG93cyArIE9uZURyaXZlIGNvbXBhdGliaWxpdHlcclxuICAgIGNvbmZpZ0ZpbGU6IGZhbHNlLFxyXG4gIH07XHJcbn0pO1xyXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQWlWLE9BQU8saUJBQWlCO0FBQ3pXLE9BQU8sV0FBVztBQUNsQixPQUFPLFVBQVU7QUFDakIsU0FBUyxxQkFBcUI7QUFDOUIsU0FBUyxvQkFBb0I7QUFKc0wsSUFBTSwyQ0FBMkM7QUFRcFEsSUFBTSxhQUFhLGNBQWMsd0NBQWU7QUFDaEQsSUFBTSxjQUFjLEtBQUssUUFBUSxVQUFVO0FBRTNDLElBQU8sNEJBQVEsYUFBYSxNQUFNO0FBQ2hDLFNBQU87QUFBQSxJQUNMLFNBQVMsQ0FBQyxNQUFNLEdBQUcsWUFBWSxDQUFDO0FBQUEsSUFDaEMsU0FBUztBQUFBLE1BQ1AsT0FBTztBQUFBLFFBQ0wsS0FBSztBQUFBLE1BQ1A7QUFBQSxJQUNGO0FBQUEsSUFDQSxPQUFPO0FBQUEsTUFDTCxlQUFlO0FBQUEsUUFDYixVQUFVLENBQUMsVUFBVTtBQUFBLE1BQ3ZCO0FBQUEsSUFDRjtBQUFBLElBQ0EsUUFBUTtBQUFBO0FBQUEsTUFFTixLQUFLLFFBQVEsSUFBSSxnQkFBZ0I7QUFBQTtBQUFBLE1BRWpDLE9BQU8sUUFBUSxJQUFJLGdCQUFnQixTQUFTLE9BQU8sQ0FBQztBQUFBO0FBQUEsTUFFcEQsSUFBSTtBQUFBLFFBQ0YsUUFBUTtBQUFBLFFBQ1IsT0FBTyxDQUFDLFdBQVc7QUFBQSxNQUNyQjtBQUFBLElBQ0Y7QUFBQTtBQUFBLElBRUEsWUFBWTtBQUFBLEVBQ2Q7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
