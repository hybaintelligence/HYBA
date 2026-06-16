# Cloudflare Pages build command

HYBA_FULLSTACK must be built on Cloudflare Pages with the npm script runner, not the npm command namespace.

Use this Cloudflare Pages build setting:

```bash
npm run build
```

Use this output directory:

```text
dist
```

Do **not** use:

```bash
npm build
```

`npm build` is not a valid npm command for this project and Cloudflare will fail before Vite or esbuild starts. The repository build script is defined in `package.json` as `scripts.build`, and the deploy aliases `cloudflare:build`, `pages:build`, and `build:ci` all delegate to `npm run build`.

The guard script below verifies that the repo-side build configuration has not drifted:

```bash
node scripts/assert_cloudflare_pages_build_config.mjs
```
