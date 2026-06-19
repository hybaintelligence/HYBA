# Frontend Command / Call / Action Coverage Matrix

This matrix is the frontend source of truth for command, call, UI action, autonomous-action, and test ownership coverage. Agent 1 seeds the matrix and the API manifest; Agents 2-4 must mark rows complete only after success, validation failure, 4xx, 5xx/offline, role denial, loading/double-click protection, audit expectation, and no-real-destructive-side-effect evidence exist.

| surface | component | user action | API client function | HTTP method | backend path | role | side-effect | test owner | test file | coverage status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard | Runtime console | page load / refresh | fetchTelemetryData | GET | /api/health + /api/ai/consciousness + /api/mining/pools + /api/security/status | any | read | Agent 2 | tests/e2e/dashboard.spec.ts | partial |
| Dashboard | Security card | status refresh | getSecurityStatus | GET | /api/security/status | operator_or_admin | read | Agent 1/3 | tests/test_apiClient_manifest.test.ts + API safety tests | partial |
| Mining | Pool configure modal | submit pool config | configurePool | POST | /api/mining/pool-config | operator_or_admin | mutation | Agent 2/3 | component + API contract tests | partial |
| Mining | Pool connect | click connect | connectToPool | POST | /api/mining/connect | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | required |
| Mining | Pool switch | click switch pool | switchPool | POST | /api/mining/switch | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | partial |
| Mining | Pool disconnect | click disconnect | disconnectFromPool | POST | /api/mining/disconnect | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | partial |
| Mining | Submit share | submit job/share | submitJob | POST | /api/mining/submit | operator_or_admin | destructive_or_autonomous | Agent 3 | tests/test_apiClient_mining.test.ts | required |
| Mining | Pause mining | click pause | pauseMining | POST | /api/mining/pause | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | partial |
| Mining | Resume mining | click resume | resumeMining | POST | /api/mining/resume | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | partial |
| Mining | Power scale slider | drag/change slider | updatePowerScale | POST | /api/mining/power | operator_or_admin | mutation | Agent 2/3 | component + E2E | partial |
| Production mining | Start pipeline | click start | startMiningProduction | POST | /api/v1/mining-production/start | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | required |
| Production mining | Stop pipeline | click stop | stopMiningProduction | POST | /api/v1/mining-production/stop | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract + E2E | required |
| Production mining | Submit share | submit share | submitMiningProductionShare | POST | /api/v1/mining-production/submit-share | operator_or_admin | destructive_or_autonomous | Agent 3 | tests/test_apiClient_mining.test.ts | required |
| Admin | Create user | submit modal | createAdminUser | POST | /api/admin/users | admin | mutation | Agent 4 | tests/e2e/admin.spec.ts | partial |
| Admin | Update user | submit edit modal | updateAdminUser | PUT | /api/admin/users/{user_id} | admin | mutation | Agent 4 | tests/e2e/admin.spec.ts | partial |
| Admin | Delete user | confirm delete | deleteAdminUser | DELETE | /api/admin/users/{user_id} | admin | destructive | Agent 4 | mocked/sandbox E2E only | partial |
| Funding | Disburse allocation | confirm disbursement | disburseFunding | POST | /api/admin/funding/allocations/{allocation_id}/disburse | admin | destructive | Agent 3/4 | mocked contract only | required |
| Funding | Review request | approve/reject request | reviewFundingRequest | PUT | /api/admin/funding/requests/{request_id}/review | admin | mutation | Agent 3/4 | mocked contract only | required |
| Intelligence | Scale intelligence | submit scaling request | scaleIntelligence | POST | /api/v1/intelligence/scale | executive | autonomous control | Agent 3/4 | safety contract | required |
| Intelligence | Boost consciousness | submit boost | boostConsciousness | POST | /api/v1/intelligence/consciousness/boost | executive | autonomous control | Agent 3/4 | safety contract | required |
| Intelligence | Orchestrate | submit orchestration | intelligenceOrchestrate | POST | /api/v1/intelligence/orchestrate | executive | autonomous control | Agent 3/4 | safety contract | required |
| Security | Activate shield | confirm shield | securityShield | POST | /api/security/shield | operator_or_admin | destructive_or_autonomous | Agent 3/4 | mocked contract only | required |
| Organism | Quarantine lane | confirm quarantine | quarantineLane | POST | /api/organism/immune/quarantine/{lane_id} | executive | destructive_or_autonomous | Agent 3/4 | mocked contract only | required |
| Organism | Apply evolution | confirm evolution | applyEvolution | POST | /api/organism/cognition/evolve/{conjecture_id} | executive | autonomous control | Agent 3/4 | mocked contract only | required |
| Executive | Set mining intent | activate/quiesce/stasis | setMiningIntent | POST | /api/organism/executive/intent | executive | autonomous control | Agent 3/4 | contract + safety tests | partial |
| Executive | Migrate habitat | confirm migration | migrateToHabitat | POST | /api/organism/pools/migrate/{pool_name} | executive | destructive_or_autonomous | Agent 3/4 | mocked contract only | required |

## Generated API manifest

Run `node scripts/extract_api_client_manifest.mjs` to refresh `artifacts/frontend_api_command_manifest.generated.json`. The generated manifest is a route inventory only and does not assert behavioural test completion. Behavioural evidence is tracked separately in `artifacts/frontend_api_command_coverage_status.json`, whose statuses must be one of `covered`, `partial`, `required`, or `blocked`. Normal Vitest manifest checks write to a temporary file so they do not mutate committed artifacts.

## Coverage ratchet and current baseline

The current documented frontend baseline is materially below production-grade coverage (26.91% statements, 42.79% branches, 17.81% functions, 27.44% lines). The CI threshold should start at that realistic baseline, then ratchet after coverage-bearing PRs land:

| phase | statements | branches | functions | lines | owner |
| --- | ---: | ---: | ---: | ---: | --- |
| Agent 1 infrastructure baseline | 25% | 40% | 17% | 27% | Agent 1 |
| API/client + component expansion | 70% | 60% | 70% | 70% | Agents 2-3 |
| E2E/safety hardening | 80% | 70% | 80% | 80% | Agents 3-4 |
| production confidence | 90%+ | 85%+ | 90%+ | 90%+ | all agents |

Critical command paths still target 100% behavioural coverage even before global coverage reaches 90%.

## Still-uncovered command groups

The current status language is intentionally conservative: `partial` means some API/component/E2E evidence exists but not the full success, validation failure, auth/role denial, retry/no-retry, payload, loading/double-click, audit, and UI confirmation set; `required` means no meaningful behavioural proof has been committed; `blocked` means evidence requires an unavailable environment or credential. The following remain explicitly incomplete until focused hardening adds behavioural tests:

- UI action coverage for every button, form, tab, modal, select, slider, auth action, retry action, and navigation path.
- Role-matrix coverage for anonymous, operator, analyst, miner, admin, executive, expired token, malformed token, and unavailable-profile states.
- Full API-client success/failure/auth/retry/no-retry/payload tests for every exported call.
- Destructive/autonomous safety tests for mining, production-mining, admin, funding, intelligence, security, organism, and executive commands.
- Playwright accessibility, mobile, visual smoke, admin, mining, executive, resilience, and sandbox-only live-stack coverage.
