import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const readJson = (filePath) => JSON.parse(fs.readFileSync(path.join(root, filePath), 'utf8'));
const readText = (filePath) => fs.readFileSync(path.join(root, filePath), 'utf8');
const exists = (filePath) => fs.existsSync(path.join(root, filePath));
const failures = [];
const pass = (condition, message) => {
  if (!condition) failures.push(message);
};

const packageJson = readJson('package.json');
const generatedManifest = readJson('artifacts/frontend_api_command_manifest.generated.json');
const coverageStatus = readJson('artifacts/frontend_api_command_coverage_status.json');
const frontendCi = readText('.github/workflows/frontend-ci.yml');
const e2eWorkflow = readText('.github/workflows/frontend-e2e.yml');
const dockerfile = readText('Dockerfile');
const spaEntrypointHardener = readText('scripts/ensure_spa_entrypoint.mjs');

for (const filePath of [
  'tests/e2e/accessibility.spec.ts',
  'tests/e2e/role-matrix.spec.ts',
  'tests/e2e/command-safety.spec.ts',
  'tests/e2e-live/live-stack.spec.ts',
  'tests/test_frontend_production_hardening.test.ts',
  'tests/test_frontend_release_readiness.test.ts',
  'tests/test_production_spa_entrypoint.test.ts',
  'scripts/ensure_spa_entrypoint.mjs',
  'docs/frontend/PRODUCTION_HARDENING_EVIDENCE.md',
]) {
  pass(exists(filePath), `Missing required frontend evidence file: ${filePath}`);
}

for (const scriptName of ['lint', 'test:frontend:unit', 'test:frontend:components', 'test:frontend:coverage', 'test:frontend:e2e', 'test:frontend:gate', 'build', 'prod:check']) {
  pass(Boolean(packageJson.scripts?.[scriptName]), `Missing package script: ${scriptName}`);
}

for (const dependencyName of ['@axe-core/playwright', '@playwright/test', '@testing-library/react', 'msw', 'jsdom']) {
  pass(Boolean(packageJson.devDependencies?.[dependencyName]), `Missing dev dependency: ${dependencyName}`);
}

pass(dockerfile.includes('RUN npm run build'), 'Dockerfile must build the frontend before runtime image assembly');
pass(dockerfile.includes('RUN node scripts/ensure_spa_entrypoint.mjs'), 'Dockerfile must harden the SPA entrypoint after build');
pass(
  dockerfile.indexOf('RUN node scripts/ensure_spa_entrypoint.mjs') > dockerfile.indexOf('RUN npm run build'),
  'SPA entrypoint hardening must run after npm run build',
);
pass(spaEntrypointHardener.includes('app.get("/bridge/status"'), 'SPA entrypoint hardener must preserve bridge status on /bridge/status');
pass(spaEntrypointHardener.includes('production root route still intercepts the SPA'), 'SPA entrypoint hardener must fail closed when / still intercepts the SPA');

pass(generatedManifest.length >= 80, `Generated command manifest is too small: ${generatedManifest.length}`);
pass(generatedManifest.every((entry) => entry.tested === undefined), 'Generated manifest must not include direct tested claims');
pass(new Set(generatedManifest.map((entry) => entry.function)).size === generatedManifest.length, 'Generated manifest has duplicate function names');

const manifestNames = new Set(generatedManifest.map((entry) => entry.function));
const statusNames = new Set(coverageStatus.map((entry) => entry.function));
for (const entry of coverageStatus) {
  pass(['covered', 'partial', 'required', 'blocked'].includes(entry.coverageStatus), `Invalid coverageStatus for ${entry.function}`);
  pass(manifestNames.has(entry.function), `Coverage status references unknown function: ${entry.function}`);
  pass(Array.isArray(entry.evidence) && entry.evidence.length > 0, `Coverage status lacks evidence for ${entry.function}`);
}

for (const entry of generatedManifest.filter((item) => item.method !== 'GET' || item.sideEffect !== 'read')) {
  pass(statusNames.has(entry.function), `Side-effect command missing behavioural status: ${entry.function}`);
  pass(entry.idempotent === false, `Side-effect command must default to non-idempotent: ${entry.function}`);
  pass(entry.sideEffect !== 'read', `Side-effect command cannot be read: ${entry.function}`);
}

for (const entry of coverageStatus.filter((item) => item.coverageStatus === 'covered' && item.sideEffect !== 'read')) {
  const evidence = entry.evidence.join('\n').toLowerCase();
  pass(/api|client|contract/.test(evidence), `Covered side-effect row lacks API/client evidence: ${entry.function}`);
  pass(/playwright|e2e|ui/.test(evidence), `Covered side-effect row lacks UI/E2E evidence: ${entry.function}`);
  pass(/auth|role/.test(evidence), `Covered side-effect row lacks auth/role evidence: ${entry.function}`);
  pass(/failure|4xx|5xx|retry|offline/.test(evidence), `Covered side-effect row lacks failure/retry/offline evidence: ${entry.function}`);
}

pass(frontendCi.includes('npm ci'), 'Frontend CI must run npm ci');
pass(frontendCi.includes('npm run lint'), 'Frontend CI must run lint');
pass(frontendCi.includes('npm run test:frontend:coverage'), 'Frontend CI must run frontend coverage');
pass(frontendCi.includes('npm run test:e2e:frontend'), 'Frontend CI must run frontend E2E');
pass(e2eWorkflow.includes('LIVE_E2E_SANDBOX'), 'E2E workflow must include sandbox toggle');
pass(e2eWorkflow.includes('PLAYWRIGHT_BASE_URL'), 'E2E workflow must include sandbox base URL');
pass(e2eWorkflow.includes('tests/e2e-live/live-stack.spec.ts'), 'E2E workflow must include live-stack spec');

if (process.env.REQUIRE_LIVE_SANDBOX === 'true') {
  pass(process.env.LIVE_E2E_SANDBOX === 'true', 'REQUIRE_LIVE_SANDBOX requires LIVE_E2E_SANDBOX=true');
  pass(Boolean(process.env.PLAYWRIGHT_BASE_URL), 'REQUIRE_LIVE_SANDBOX requires PLAYWRIGHT_BASE_URL');
}

if (failures.length > 0) {
  console.error('Frontend readiness check failed:');
  for (const failure of failures) console.error(` - ${failure}`);
  process.exit(1);
}

console.log(`frontend readiness ok: ${generatedManifest.length} commands, ${coverageStatus.length} status rows`);
