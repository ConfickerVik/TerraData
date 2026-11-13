import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Бэкенд доступен по CORS, поэтому прокси не используем:
// фронт ходит напрямую на API_BASE_URL (см. src/config.ts).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
})
