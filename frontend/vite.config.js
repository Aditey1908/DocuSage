import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/process': process.env.VITE_API_URL || 'http://localhost:5000',
      '/threads': process.env.VITE_API_URL || 'http://localhost:5000',
    },
  },
})
