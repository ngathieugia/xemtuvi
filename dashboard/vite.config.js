import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Build ra pi_alert/dashboard_dist để Flask phục vụ tại /pi/app/
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: '../pi_alert/dashboard_dist', emptyOutDir: true, chunkSizeWarningLimit: 800 },
  server: {
    // khi dev: chạy `python -m pi_alert.web` (cổng 5000) rồi `npm run dev`
    proxy: { '/pi/api': 'http://127.0.0.1:5000' },
  },
})
