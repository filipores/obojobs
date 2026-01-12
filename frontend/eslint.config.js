import pluginVue from 'eslint-plugin-vue'
import js from '@eslint/js'

export default [
  // JavaScript recommended rules
  js.configs.recommended,

  // Vue 3 essential rules (less strict than recommended, focuses on errors not style)
  ...pluginVue.configs['flat/essential'],

  // Global configuration
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly',
        File: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        HTMLElement: 'readonly',
        Event: 'readonly',
        alert: 'readonly',
        confirm: 'readonly',
        prompt: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        history: 'readonly',
        // DOM API globals
        Node: 'readonly',
        NodeFilter: 'readonly',
        Range: 'readonly',
        Selection: 'readonly',
        // Node globals (for config files)
        process: 'readonly',
      }
    },
    rules: {
      // Relax some Vue rules for existing codebase
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'warn',
      'vue/require-default-prop': 'off',
      'vue/require-prop-types': 'warn',

      // JavaScript rules
      'no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_'
      }],
      'no-console': 'warn',
      'no-debugger': 'error',
    }
  },

  // Ignore patterns
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      '*.config.js',
      'vitest.config.js'
    ]
  }
]
