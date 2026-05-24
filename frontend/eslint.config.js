import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      // Prevent `import type { X }` — enforce inline `import { type X }` instead
      // This is required for oxc/rolldown compatibility in @vitest/coverage-v8
      '@typescript-eslint/consistent-type-imports': [
        'error',
        {
          prefer: 'no-type-imports',
          fixStyle: 'inline-type-imports',
          disallowTypeAnnotations: false,
        },
      ],
      // Allow common patterns without strictness overhead
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    // Ignore build artifacts and generated files
    ignores: [
      'dist/**',
      'android/**',
      'node_modules/**',
      'coverage/**',
    ],
  }
);
