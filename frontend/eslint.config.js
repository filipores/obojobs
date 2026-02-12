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
        URLSearchParams: 'readonly',
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

      // ── Architecture: API calls must go through api/client.js ──
      // All HTTP requests must use the shared API client (src/api/client.js)
      // which handles auth tokens, error toasts, and session expiry.
      'no-restricted-imports': ['error', {
        paths: [
          {
            name: 'axios',
            message:
              'Do not import axios directly. ' +
              'Use `import api from \'@/api/client\'` instead. ' +
              'The shared client handles auth headers, error toasts, and session expiry automatically.'
          }
        ],
        patterns: [
          {
            group: ['axios/*'],
            message:
              'Do not import from axios submodules. ' +
              'Use `import api from \'@/api/client\'` for all HTTP requests.'
          }
        ]
      }],

      // ── Architecture: Composition API only (no Options API) ──
      // The project uses Vue 3 Composition API with <script setup>.
      // Options API (export default { data(), methods, computed, ... }) is forbidden.
      'no-restricted-syntax': ['error',
        {
          selector: 'ExportDefaultDeclaration > ObjectExpression > Property[key.name="data"][value.type="FunctionExpression"]',
          message:
            'Options API detected: `data()` function found. ' +
            'Use Composition API with `<script setup>` and `ref()`/`reactive()` instead. ' +
            'See docs/frontend-patterns.md for examples.'
        },
        {
          selector: 'ExportDefaultDeclaration > ObjectExpression > Property[key.name="methods"]',
          message:
            'Options API detected: `methods` property found. ' +
            'Use Composition API with `<script setup>` and define functions directly. ' +
            'See docs/frontend-patterns.md for examples.'
        },
        {
          selector: 'ExportDefaultDeclaration > ObjectExpression > Property[key.name="computed"]',
          message:
            'Options API detected: `computed` property found. ' +
            'Use Composition API with `<script setup>` and `computed()` from vue. ' +
            'See docs/frontend-patterns.md for examples.'
        },
        {
          selector: 'ExportDefaultDeclaration > ObjectExpression > Property[key.name="watch"]',
          message:
            'Options API detected: `watch` property found. ' +
            'Use Composition API with `<script setup>` and `watch()`/`watchEffect()` from vue. ' +
            'See docs/frontend-patterns.md for examples.'
        },
        {
          selector: 'ExportDefaultDeclaration > ObjectExpression > Property[key.name="mounted"]',
          message:
            'Options API detected: `mounted` lifecycle hook found. ' +
            'Use Composition API with `<script setup>` and `onMounted()` from vue. ' +
            'See docs/frontend-patterns.md for examples.'
        },
        {
          selector: 'ExportDefaultDeclaration > ObjectExpression > Property[key.name="created"]',
          message:
            'Options API detected: `created` lifecycle hook found. ' +
            'Use Composition API with `<script setup>` — code at the top level of <script setup> runs on creation. ' +
            'See docs/frontend-patterns.md for examples.'
        },
      ],
    }
  },

  // Allow axios import in the API client itself (it's the single source of truth)
  {
    files: ['src/api/client.js'],
    rules: {
      'no-restricted-imports': 'off',
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
