import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import typescriptEslint from '@typescript-eslint/eslint-plugin'
import * as tsParser from '@typescript-eslint/parser'
import * as vueParser from 'vue-eslint-parser'

export default [
  {
    ignores: ['node_modules/**', 'dist/**', 'build/**']
  },
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      }
    }
  },
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 'latest',
        sourceType: 'module'
      }
    },
    plugins: {
      vue: pluginVue
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/no-unused-vars': 'warn',
      'vue/no-unused-components': 'warn',
      'vue/require-default-prop': 'off',
      'vue/require-prop-types': 'warn',
      semi: ['error', 'never'],
      quotes: ['error', 'single', { avoidEscape: true }],
      'comma-dangle': ['error', 'never']
    }
  },
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
      }
    },
    plugins: {
      '@typescript-eslint': typescriptEslint
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/ban-ts-comment': 'warn',
      semi: ['error', 'never'],
      quotes: ['error', 'single', { avoidEscape: true }],
      'comma-dangle': ['error', 'never']
    }
  },
  {
    files: ['**/*.js'],
    rules: {
      semi: ['error', 'never'],
      quotes: ['error', 'single', { avoidEscape: true }],
      'comma-dangle': ['error', 'never']
    }
  },
  {
    rules: {
      'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
      'no-unused-vars': 'warn'
    }
  }
]
