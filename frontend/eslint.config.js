import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'scripts', 'node_modules']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Allow `_prefixed` args/vars for intentional discards — typical when
      // destructuring to strip props from a spread. `caughtErrors: 'none'`
      // permits empty `catch` blocks used as a "best-effort" boundary.
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' },
      ],
    },
  },
  // Third-party pixel snippets (GA4, Meta, TikTok) are vendored from provider
  // docs and use `any` + `arguments` by design. Silence type-strictness for
  // these files only; the rest of the codebase stays strict.
  {
    files: ['src/lib/analytics.ts', 'src/hooks/useAnalytics.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'prefer-rest-params': 'off',
      'prefer-spread': 'off',
      '@typescript-eslint/no-unused-expressions': 'off',
      'no-empty': 'off',
    },
  },
  // ContactForm uses Formspree's untyped callback surface.
  {
    files: ['src/components/ContactForm.tsx'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
])
