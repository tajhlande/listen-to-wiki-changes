import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    target: 'esnext', // this makes vue happy with top-level awaits,
    outDir: 'dist' // Github Pages doesn't like dist but we're not using GHP anymore!
  },
  base: '/app' // create relative paths when rendering
})
