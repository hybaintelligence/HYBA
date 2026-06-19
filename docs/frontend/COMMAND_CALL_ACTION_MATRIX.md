# Frontend Command / Call / Action Matrix

This matrix is the E2E hardening slice owned by Cloud Agent 4. Rows marked `covered-agent4` are exercised through Playwright with deterministic route mocks unless the test file is under `tests/e2e-live`, which is an explicit live/sandbox smoke check and must not silently skip unavailable services.

| surface | component | user action | API client function / call | HTTP method | backend path | role | side-effect | test owner | test file | coverage status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard | App header | open unauthenticated dashboard | `fetchTelemetryData` aggregate | GET | `/api/health`, `/api/consciousness/telemetry`, `/api/mining/pools`, `/api/security/status` | any | read | Agent 4 | `tests/e2e/accessibility.spec.ts` | covered-agent4 |
| Dashboard | ErrorState / NetworkToast | backend offline, inspect retry and alert state | `fetchTelemetryData` aggregate | GET | `/api/health`, `/api/consciousness/telemetry`, `/api/mining/pools`, `/api/security/status` | any | read/error | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4 |
| Dashboard | ErrorState retry | backend recovers, click retry | `fetchTelemetryData` aggregate | GET | `/api/health`, `/api/consciousness/telemetry`, `/api/mining/pools`, `/api/security/status` | any | read/retry | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4 |
| Dashboard | Header theme toggle | click color theme toggle | DOM theme toggle | n/a | n/a | any | UI-only | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4 |
| Auth | Operator identity | submit login form | `loginApi` | POST | `/api/auth/login` | operator | auth mutation | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4; mocked only |
| Mining | App quantum runtime | change power-scale slider | `updatePowerScale` | POST | `/api/mining/power` | operator/admin | mutation | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4 |
| Mining | Pool config modal | submit missing required BTC address | browser validation before `configurePool` | POST | `/api/mining/pool-config` | operator/admin | validation | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4; asserts no request |
| Mining | Pool config modal | save configured pool and connect | `configurePool` + `switchPool` | POST | `/api/mining/pool-config`, `/api/mining/switch` | operator/admin | mutation | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4; mocked only |
| Mining | Stratum mining pools | double-click pool switch | `switchPool` | POST | `/api/mining/switch` | operator/admin | mutation | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4; asserts one request |
| Mining | Stratum mining pools | double-click active pool disconnect | `disconnectFromPool` | POST | `/api/mining/disconnect` | operator/admin | mutation | Agent 4 | `tests/e2e/mining-ops.spec.ts` | covered-agent4; asserts one request |
| Admin | App header | non-admin attempts to access admin navigation | `fetchProfileApi` / route-gated UI | GET | `/api/auth/profile` | operator | denied read | Agent 4 | `tests/e2e/admin.spec.ts` | covered-agent4 |
| Admin | AdminPanel | create disposable user | direct `fetch` | POST | `/api/admin/users` | admin | mutation | Agent 4 | `tests/e2e/admin.spec.ts` | covered-agent4; mocked only |
| Admin | AdminPanel | edit disposable user | direct `fetch` | PUT | `/api/admin/users/{id}` | admin | mutation | Agent 4 | `tests/e2e/admin.spec.ts` | covered-agent4; mocked only |
| Admin | AdminPanel | delete disposable user after confirmation | direct `fetch` | DELETE | `/api/admin/users/{id}` | admin | destructive | Agent 4 | `tests/e2e/admin.spec.ts` | covered-agent4; mocked only |
| Executive | App header / HybaAdminDashboard | executive opens console | `fetchProfileApi`, `getAdminStats` | GET | `/api/auth/profile`, `/api/admin/stats` | executive | read | Agent 4 | `tests/e2e/executive.spec.ts` | covered-agent4 |
| Executive | HybaAdminDashboard Quantum | executive switches pool from executive console | `switchPool` | POST | `/api/mining/switch` | executive | mutation/autonomous-adjacent | Agent 4 | `tests/e2e/executive.spec.ts` | covered-agent4; mocked only; asserts one request |
| Executive | App header | operator cannot access executive surface | `fetchProfileApi` / route-gated UI | GET | `/api/auth/profile` | operator | denied read | Agent 4 | `tests/e2e/executive.spec.ts` | covered-agent4 |
| Accessibility | App, Admin, Executive | inspect named landmarks/buttons | DOM accessibility smoke | n/a | n/a | any/admin/executive | read | Agent 4 | `tests/e2e/accessibility.spec.ts` | covered-agent4 |
| Live stack | sandbox frontend | load frontend document without silent skip | browser navigation | GET | `/` | any | read | Agent 4 | `tests/e2e-live/live-stack.spec.ts` | covered-agent4-live; requires `LIVE_E2E_SANDBOX=true` |

## Agent 4 safety rules

- Destructive admin actions use fixture usernames prefixed with `agent4-` and Playwright route mocks.
- Mining and executive mutations are route-mocked by default and count requests to detect duplicate mutation calls.
- `tests/e2e-live/live-stack.spec.ts` performs only a non-destructive document/render check and is excluded from default mocked E2E unless `LIVE_E2E_SANDBOX=true`.
- Live destructive or autonomous calls remain prohibited unless a future workflow explicitly sets `LIVE_E2E_SANDBOX=true` and points at seeded disposable test data.
