import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/drone-image-viewer',
  server: {
    port: 8080,
    strictPort: true
  }
})
