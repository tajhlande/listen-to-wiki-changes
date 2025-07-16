import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  root: 'web_app', // Still uses web_app as root
  plugins: [vue()],
  build: {
    target: 'esnext', // this makes vue happy with top-level awaits,
    outDir: 'dist', // Github Pages doesn't like dist but we're not using GHP anymore!
    emptyOutDir: true,
  },
  base: '/app', // create relative paths when rendering
  server: {
    // for local network viewing and debugging from phone
    allowedHosts: true,
    cors: true,
  }
})
