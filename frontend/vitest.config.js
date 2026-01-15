import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/__tests__/**/*.{test,spec}.{js,ts}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/__tests__/',
      ],
      thresholds: {
        // Global thresholds - set conservatively to not break CI
        // Increase these values as test coverage improves
        statements: 0,
        branches: 0,
        functions: 0,
        lines: 0
      },
      // Report will show coverage metrics and highlight files below thresholds
      // To enforce stricter thresholds later, increase the values above
    }
  }
})
