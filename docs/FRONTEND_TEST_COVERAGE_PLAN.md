# Frontend Test Coverage Plan — Target 100%

## Current State
- **Overall Coverage:** 26.91% statements, 42.79% branches, 17.81% functions, 27.44% lines
- **Test Files:** 5 passing, 1 failing (JSX parse error)
- **Main Gaps:**
  - `src/apiClient.ts`: 14% coverage (lines 91-2439 uncovered)
  - `src/utils/math.ts`: 47.7% coverage (lines 145-378 uncovered)
  - `src/components/*`: 0% coverage (24 components untested)
  - `src/core/*`: 0% coverage (13 modules untested)
  - `src/hooks/*`: 0% coverage (2 hooks untested)
  - `src/db/*`: 0% coverage (2 files untested)
  - `src/server.ts`: 0% coverage
  - `src/bridge_security.ts`: 0% coverage

## Agent Assignments

### Agent 1: API Client & Core Utilities (Target: 100% coverage)
**Files to test:**
- `src/apiClient.ts` (2440 lines) — 80+ API endpoints
- `src/utils/math.ts` (379 lines) — quantum math utilities
- `src/core/constants.ts` (already at 100%, maintain)
- `src/governance.ts` (already at 100%, maintain)

**Test Strategy:**
1. **apiClient.ts** — Create `tests/test_apiClient_complete.test.ts`
   - Mock fetch for all 80+ endpoints
   - Test auth interceptor (already covered, extend)
   - Test error handling, retries, timeouts
   - Test all request/response type guards
   - Cover lines 91-2439 with endpoint-specific tests
   - Target: 100% statement coverage

2. **math.ts** — Extend `tests/test_property_frontend.test.ts`
   - Add tests for lines 145-378 (Grover, entropy bounds, dodecahedron, phi resonance)
   - Already has 35 property tests, add 15-20 more
   - Target: 100% statement coverage

**Deliverables:**
- `tests/test_apiClient_complete.test.ts` (new, ~800 lines)
- Updated `tests/test_property_frontend.test.ts` (+20 tests)

---

### Agent 2: React Components (Target: 100% coverage)
**Files to test:**
- `src/components/*.tsx` (24 components)
- `src/App.tsx` (root component)
- `src/main.tsx` (entry point)

**Test Strategy:**
1. **Create component test suite** — `tests/test_components_complete.test.ts`
   - Use React Testing Library + jsdom
   - Fix JSX parse error by ensuring proper vitest config
   - Test each component with mocked props and state
   - Test error boundaries, loading states, edge cases
   - Components to cover:
     - AIAssistant.tsx
     - AdminPanel.tsx
     - AnalyticsSection.tsx
     - AuthProvider.tsx
     - CoherenceScatterPlot.tsx
     - ConsoleMetrics.tsx
     - ErrorBoundary.tsx
     - ExecutiveSummary.tsx
     - GroverVisualizer.tsx
     - HilbertSpaceVisualizer.tsx
     - HistoricalDataSection.tsx
     - HybaAdminDashboard.tsx
     - MathematicsTests.tsx
     - MiningJobsSection.tsx
     - NetworkToast.tsx
     - PoolSecretsConfig.tsx
     - PoolSelector.tsx
     - PulviniExecutionPanel.tsx
     - PythagorasChat.tsx
     - SovereignCommandPost.tsx
     - SovereignGenesisPanel.tsx
     - Sparkline.tsx

2. **Fix test_frontend_components.test.ts**
   - Resolve JSX parse error (`<App />` not recognized)
   - Ensure proper React transform in vitest config

**Deliverables:**
- `tests/test_components_complete.test.ts` (new, ~1500 lines)
- Fixed `tests/test_frontend_components.test.ts`

---

### Agent 3: Core Logic & Hooks (Target: 100% coverage)
**Files to test:**
- `src/core/*.ts` (13 modules)
- `src/hooks/*.ts` (2 hooks)
- `src/bridge_security.ts`
- `src/types.ts`, `src/types/api.ts`

**Test Strategy:**
1. **Core modules** — Create `tests/test_core_complete.test.ts`
   - Test each module in isolation with mocked dependencies
   - Modules to cover:
     - bridge.ts
     - emergent_intelligence.ts
     - hebbian_learner.ts
     - intelligence_service.ts
     - intelligence_types.ts
     - metacognitive_intelligence.ts
     - metacognitive_shield.ts
     - perturbation_analyzer.ts
     - phi_shield.ts
     - predictive_intel.ts
     - recursive_self_learning.ts
     - security_swarm.ts
     - substrate.ts
     - telemetry.ts
     - temporal_integration.ts

2. **Hooks** — Create `tests/test_hooks_complete.test.ts`
   - Test `useApiRequest.ts` with mocked fetch
   - Test `useLatencyMetrics.ts` with mocked performance API

3. **Bridge security** — Create `tests/test_bridge_security.test.ts`
   - Test circuit breaker logic
   - Test rate limiting
   - Test request validation

**Deliverables:**
- `tests/test_core_complete.test.ts` (new, ~1200 lines)
- `tests/test_hooks_complete.test.ts` (new, ~300 lines)
- `tests/test_bridge_security.test.ts` (new, ~400 lines)

---

### Agent 4: Integration, DB & Server (Target: 100% coverage)
**Files to test:**
- `src/db/db.ts`, `src/db/seed.ts`
- `src/server.ts`
- `src/firebase.ts`, `src/lib/firebase.ts`
- `src/swaggerSpec.ts`
- Integration tests for frontend-backend contracts

**Test Strategy:**
1. **Database layer** — Create `tests/test_db_complete.test.ts`
   - Test db.ts with mocked Firebase/Firestore
   - Test seed.ts with mocked data
   - Test CRUD operations, error handling

2. **Server entrypoint** — Create `tests/test_server.test.ts`
   - Test server.ts with mocked Express app
   - Test middleware, routes, error handlers

3. **Firebase integration** — Create `tests/test_firebase.test.ts`
   - Test firebase.ts and lib/firebase.ts with mocked SDK
   - Test auth, database, storage interactions

4. **Swagger spec** — Create `tests/test_swagger.test.ts`
   - Test swaggerSpec.ts generation
   - Validate OpenAPI schema

5. **E2E contracts** — Extend `tests/test_frontend_backend_e2e.test.ts`
   - Add more contract tests for API consistency
   - Test request/response schemas

**Deliverables:**
- `tests/test_db_complete.test.ts` (new, ~400 lines)
- `tests/test_server.test.ts` (new, ~300 lines)
- `tests/test_firebase.test.ts` (new, ~300 lines)
- `tests/test_swagger.test.ts` (new, ~200 lines)
- Updated `tests/test_frontend_backend_e2e.test.ts` (+10 tests)

---

## Execution Order

### Phase 1: Infrastructure (All Agents)
1. Verify vitest config supports React/JSX transform
2. Ensure test environment has jsdom, @testing-library/react
3. Create test utilities/mocks directory (`tests/__mocks__/`)
4. Set up coverage thresholds in vitest.config.ts

### Phase 2: Parallel Implementation (Agents 1-4)
- Each agent works on their assigned files independently
- Daily sync points to resolve conflicts
- Agents share mock patterns and test utilities

### Phase 3: Integration & Verification
1. Merge all test files
2. Run full test suite with coverage
3. Identify remaining gaps
4. Fix failing tests
5. Achieve 100% coverage

## Success Criteria
- **Statement Coverage:** 100%
- **Branch Coverage:** 100%
- **Function Coverage:** 100%
- **Line Coverage:** 100%
- **All tests passing:** 0 failures
- **No skipped tests:** 0 skipped

## Estimated Effort
- **Agent 1:** 2-3 days (apiClient.ts is large, 2440 lines)
- **Agent 2:** 2-3 days (24 components, varying complexity)
- **Agent 3:** 1-2 days (15 core modules, mostly unit tests)
- **Agent 4:** 1-2 days (DB, server, Firebase, integration)
- **Total:** 6-10 days with 4 agents working in parallel

## Risk Mitigation
1. **JSX parse error:** Fix vitest config first (Agent 1 can help)
2. **Mock complexity:** Create shared mock utilities in `tests/__mocks__/`
3. **Test flakiness:** Use deterministic mocks, avoid real network calls
4. **Merge conflicts:** Use clear file ownership per agent, sync daily

## Files to Create/Modify

### New Test Files
- `tests/test_apiClient_complete.test.ts` (Agent 1)
- `tests/test_components_complete.test.ts` (Agent 2)
- `tests/test_core_complete.test.ts` (Agent 3)
- `tests/test_hooks_complete.test.ts` (Agent 3)
- `tests/test_bridge_security.test.ts` (Agent 3)
- `tests/test_db_complete.test.ts` (Agent 4)
- `tests/test_server.test.ts` (Agent 4)
- `tests/test_firebase.test.ts` (Agent 4)
- `tests/test_swagger.test.ts` (Agent 4)

### Files to Modify
- `tests/test_property_frontend.test.ts` (Agent 1, +20 tests)
- `tests/test_frontend_components.test.ts` (Agent 2, fix JSX error)
- `tests/test_frontend_backend_e2e.test.ts` (Agent 4, +10 tests)
- `vitest.config.ts` (all agents, ensure React transform)
- `tests/__mocks__/` (new directory, shared mocks)

## Coverage Breakdown by File

| File | Current | Target | Agent |
|------|---------|--------|-------|
| src/apiClient.ts | 14% | 100% | 1 |
| src/utils/math.ts | 47.7% | 100% | 1 |
| src/components/*.tsx | 0% | 100% | 2 |
| src/core/*.ts | 0% | 100% | 3 |
| src/hooks/*.ts | 0% | 100% | 3 |
| src/bridge_security.ts | 0% | 100% | 3 |
| src/db/*.ts | 0% | 100% | 4 |
| src/server.ts | 0% | 100% | 4 |
| src/firebase.ts | 0% | 100% | 4 |
| src/lib/firebase.ts | 0% | 100% | 4 |
| src/swaggerSpec.ts | 0% | 100% | 4 |
| src/App.tsx | 0% | 100% | 2 |
| src/main.tsx | 0% | 100% | 2 |
| src/governance.ts | 100% | 100% | 1 (maintain) |
| src/core/constants.ts | 100% | 100% | 1 (maintain) |

## Next Steps
1. Assign agents to tasks above
2. Create shared test utilities (`tests/__mocks__/`, `tests/utils/`)
3. Fix vitest config for React/JSX
4. Begin parallel implementation
5. Daily sync and integration
6. Final coverage verification