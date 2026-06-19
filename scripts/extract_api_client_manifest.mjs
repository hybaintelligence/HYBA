#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const sourcePath = new URL('../src/apiClient.ts', import.meta.url);
const defaultOutPath = new URL('../artifacts/frontend_api_command_manifest.generated.json', import.meta.url);
const outArgIndex = process.argv.indexOf('--out');
const outPath = outArgIndex === -1 ? defaultOutPath : new URL(process.argv[outArgIndex + 1], `file://${process.cwd()}/`);
const source = readFileSync(sourcePath, 'utf8');

const helpers = { get: 'GET', getOptional: 'GET', post: 'POST', put: 'PUT', del: 'DELETE', patch: 'PATCH' };
const destructiveWords = /delete|disburse|quarantine|evolution|migrate|shield|intent|stop|start|pause|resume|submit|switch|connect|disconnect|create|update|review|boost|scale|orchestrate|stimulate|trigger|reset|simulate|report|execute|request/i;
const roleFor = (fn, path) => {
  if (path.includes('/admin/')) return 'admin';
  if (path.includes('/organism') || path.includes('/v1/intelligence') || fn.includes('Executive') || fn.includes('Intent')) return 'executive';
  if (path.includes('/mining') || path.includes('/pools')) return 'operator_or_admin';
  if (path.includes('/security')) return 'operator_or_admin';
  return 'any_authenticated_or_public';
};
const sideEffectFor = (method, fn, path) => {
  if (method === 'GET') return 'read';
  if (method === 'DELETE') return 'destructive';
  if (/intent|evolve|migrate|orchestrate|boost|scale|shield|quarantine|regeneration|disturbance/i.test(`${fn} ${path}`)) return 'autonomous_control';
  if (/delete|disburse|stop|start|pause|resume|submit|switch|disconnect|connect/i.test(`${fn} ${path}`)) return 'destructive';
  return 'mutation';
};

const rows = [];
const fnRegex = /export\s+(?:async\s+)?function\s+(\w+)\s*\([^)]*\)[^{]*\{/g;
function findFunctionEnd(openBraceIndex) {
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let i = openBraceIndex; i < source.length; i += 1) {
    const ch = source[i];
    if (quote) {
      if (escaped) {
        escaped = false;
      } else if (ch === '\\') {
        escaped = true;
      } else if (ch === quote) {
        quote = null;
      }
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      quote = ch;
      continue;
    }
    if (ch === '{') depth += 1;
    if (ch === '}') {
      depth -= 1;
      if (depth === 0) return i + 1;
    }
  }
  return source.length;
}
let match;
while ((match = fnRegex.exec(source))) {
  const name = match[1];
  let openBraceIndex = source.indexOf('{', match.index);
  while (openBraceIndex !== -1 && !/\r?\n/.test(source.slice(openBraceIndex + 1, openBraceIndex + 3))) {
    openBraceIndex = source.indexOf('{', openBraceIndex + 1);
  }
  if (openBraceIndex === -1) continue;
  const body = source.slice(openBraceIndex + 1, findFunctionEnd(openBraceIndex));
  let method;
  let path;
  let helper;

  const helperMatch = body.match(/\b(getOptional|get|post|put|patch|del)\s*<[^>]*>\s*\(\s*([`'"])([^`'"]+)/) || body.match(/\b(getOptional|get|post|put|patch|del)\s*\(\s*([`'"])([^`'"]+)/);
  if (helperMatch) {
    helper = helperMatch[1];
    method = helpers[helper];
    path = helperMatch[3];
  } else {
    const fetchMatch = body.match(/fetch\s*\(\s*`\$\{BACKEND_URL\}([^`]+)/) || body.match(/fetch\s*\(\s*["']([^"']+)/);
    if (fetchMatch) {
      path = fetchMatch[1].replace(/^\$\{BACKEND_URL\}/, '');
      const methodMatch = body.match(/method:\s*[`'"]([A-Z]+)[`'"]/);
      method = methodMatch?.[1] || 'GET';
      helper = 'fetch';
    }
  }
  if (!method || !path || !path.startsWith('/')) continue;
  rows.push({
    function: name,
    method,
    path: `/api${path}`.replace('/api/api/', '/api/'),
    sideEffect: sideEffectFor(method, name, path),
    role: roleFor(name, path),
    idempotent: method === 'GET',
    helper,
  });
}
rows.sort((a, b) => a.function.localeCompare(b.function));
mkdirSync(new URL('../artifacts/', import.meta.url), { recursive: true });
writeFileSync(outPath, `${JSON.stringify(rows, null, 2)}\n`);
console.log(`Wrote ${rows.length} API client command rows to ${outPath.pathname}`);
