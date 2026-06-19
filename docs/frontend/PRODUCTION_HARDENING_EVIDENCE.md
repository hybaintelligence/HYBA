# Frontend Production Hardening Evidence

This document records the hardening gates installed for HYBA_FULLSTACK frontend production readiness.

## Elevated gates added

| Gate | Evidence file | Production purpose |
| --- | --- | --- |
| Axe accessibility scan | `tests/e2e/accessibility.spec.ts` | Runs Playwright plus `@axe-core/playwright` across anonymous, operator, admin, and executive surfaces. |
| Full role matrix | `tests/e2e/role-matrix.spec.ts` | Proves ordinary, invalid-session, admin, and executive roles receive the correct navigation surface. |
| Command safety E2E | `tests/e2e/command-safety.spec.ts` | Proves passive dashboard/admin/executive navigation does not accidentally dispatch high-impact command routes. |
| Manifest evidence gate | `tests/test_frontend_production_hardening.test.ts` | Proves the generated command inventory remains broad and high-impact commands remain explicitly tracked in behavioural status. |

## Production standard

A generated route inventory is not behavioural proof. Production readiness requires both:

1. the command exists in `artifacts/frontend_api_command_manifest.generated.json`; and
2. the command has behavioural evidence in `artifacts/frontend_api_command_coverage_status.json` and the relevant unit/component/E2E test file.

High-impact command families include production mining, funding disbursement/review, intelligence scaling, security shield activation, organism quarantine/evolution/migration, and executive mining intent.

## Merge expectation

Run the following once npm registry access is available:

```bash
npm ci
npm run lint
npm run test:frontend:unit
npm run test:frontend:components
npx playwright test tests/e2e/accessibility.spec.ts tests/e2e/role-matrix.spec.ts tests/e2e/command-safety.spec.ts
npm run build
```

A command must not be marked `covered` unless the evidence names UI/E2E coverage, role or auth coverage, and failure or retry/offline behaviour.
