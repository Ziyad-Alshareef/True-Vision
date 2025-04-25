import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    rollupOptions: {
      external: []
    },
    cssCodeSplit: false,
    assetsInlineLimit: 0,
    minify: true,
  },
  optimizeDeps: {
    include: ['clsx', 'tailwind-merge']
  },
  css: {
    postcss: './postcss.config.js',
    devSourcemap: true,
  }
}) 