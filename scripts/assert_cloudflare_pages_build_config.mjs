#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const packageJsonPath = path.join(root, 'package.json');
const wranglerPath = path.join(root, 'wrangler.toml');

function fail(message) {
  console.error(`Cloudflare Pages build config error: ${message}`);
  process.exitCode = 1;
}

const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const scripts = packageJson.scripts || {};

if (!scripts.build) {
  fail('package.json must define scripts.build for Cloudflare Pages.');
}

for (const alias of ['build:ci', 'cloudflare:build', 'pages:build']) {
  if (scripts[alias] !== 'npm run build') {
    fail(`package.json scripts.${alias} must be "npm run build".`);
  }
}

if (!fs.existsSync(wranglerPath)) {
  fail('wrangler.toml is required so Cloudflare can read the Pages output directory.');
} else {
  const wrangler = fs.readFileSync(wranglerPath, 'utf8');
  if (!/^pages_build_output_dir\s*=\s*["']dist["']/m.test(wrangler)) {
    fail('wrangler.toml must set pages_build_output_dir = "dist".');
  }
}

if (process.exitCode) {
  process.exit(process.exitCode);
}

console.log('Cloudflare Pages build config OK: use build command "npm run build" and output directory "dist".');
