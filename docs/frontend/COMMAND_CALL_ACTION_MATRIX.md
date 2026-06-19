# Frontend Command / Call / Action Matrix

This Agent 2 slice records component and mocked E2E evidence for visible frontend actions. Destructive or autonomous commands remain mocked-only until a sandbox gate is explicitly enabled.

| surface | component | user action | API client function | HTTP method | backend path | role | side-effect | test owner | test file | coverage status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard | Header | click Refresh | fetchTelemetryData | GET | /api/health + optional /api/ai/consciousness, /api/mining/pools, /api/security/status | any | read | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: success, offline retry |
| Dashboard | Header | click Live / Paused | none | n/a | n/a | any | local UI state | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: pause/resume polling state |
| Dashboard | Header | click theme toggle | none | n/a | n/a | any | local UI state | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: dark-mode class toggle |
| Dashboard | Navigation | click Jobs / History / Analytics | none | n/a | n/a | any | local UI state | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: view switching |
| Auth | Operator identity | submit login form | loginApi | POST | /api/auth/login | anonymous | auth mutation | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/auth.spec.ts | covered: mocked success, accessible inputs |
| Auth | Operator identity | submit register form | registerApi | POST | /api/auth/register | anonymous | account mutation | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/auth.spec.ts | covered: mocked success, accessible inputs |
| Auth | Operator identity | click Log out | logout | local + token removal | localStorage | authenticated | auth mutation | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/auth.spec.ts | covered: token/session UI reset |
| Resilience | NetworkToast / ErrorState | click dismiss and Retry connection | fetchTelemetryData | GET | /api/health + optional telemetry endpoints | any | read | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/resilience.spec.ts | covered: backend offline then retry success |
| Mining | Quantum runtime | change power slider | updatePowerScale | POST | /api/mining/power | operator/admin | mutation | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: mocked request and feedback |
| Mining | Quantum runtime | change phi-tier select | updatePowerScale | POST | /api/mining/power | operator/admin | mutation | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: mocked request and selected tier |
| Mining | Pool card | click Configure / Setup and save modal | configurePool; optional switchPool | POST | /api/mining/pool-config; /api/mining/switch | operator/admin | mutation | Agent 2 | tests/test_components_complete.test.tsx | covered: required BTC-address modal path |
| Mining | Pool card | click Switch | switchPool | POST | /api/mining/switch | operator/admin | mutation | Agent 2 | tests/test_components_complete.test.tsx; tests/e2e/dashboard.spec.ts | covered: exactly mocked frontend request path |
| Mining | Pool card | click Disconnect | disconnectFromPool | POST | /api/mining/disconnect | operator/admin | mutation | Agent 2 | tests/test_components_complete.test.tsx | covered: mocked request path |
| Admin | Header navigation | admin button visibility | none | n/a | n/a | admin/executive | role-gated UI | Agent 2 | tests/test_components_complete.test.tsx | covered: hidden for anonymous, visible for admin |
| Executive | Header navigation | executive button visibility | none | n/a | n/a | executive | role-gated UI | Agent 2 | tests/test_components_complete.test.tsx | covered: hidden for anonymous/admin-only, visible for executive |
