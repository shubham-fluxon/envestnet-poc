import { defineConfig } from 'vite'

export default defineConfig({
  root: '.',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/agent': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/chart': 'http://localhost:8000',
    },
  },
})
