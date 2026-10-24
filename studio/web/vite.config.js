import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: { dedupe: ['react', 'react-dom', 'framer-motion'] },
  server: {
    host: '127.0.0.1',
    fs: { allow: ['../..'] },
    proxy: {
      '/api/rrremergen': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
