import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import prettier from "eslint-config-prettier";
import prettierPlugin from "eslint-plugin-prettier";
import reactHooks from "eslint-plugin-react-hooks";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      prettier: prettierPlugin,
      "react-hooks": reactHooks,
    },
    rules: {
      "prettier/prettier": "warn",
      "react-hooks/exhaustive-deps": "off",
    },
  },
  prettier,
  {
    ignores: [
      "node_modules/",
      "dist/",
      "venv/",
      "python_backend/",
      "scripts/",
      "public/",
      "artifacts/",
      "logs/",
      "functions/",
      "*.config.*",
      "vitest.config.ts",
      "vite.config.build.ts",
      "src/**/__tests__",
    ],
  },
  {
    files: ["src/**/*.{ts,tsx,js,jsx}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2022,
      },
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
        project: "./tsconfig.json",
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "no-console": "off",
      "no-unused-vars": "off",
      "react-hooks/exhaustive-deps": "off",
    },
  },
);
