# Reviewer Evidence Map

This document provides a navigation map for reviewers to locate key evidence and documentation across the HYBA_FULLSTACK repository.

## Key Scientific Claims

### Nodus Solutus Mundus Computabilis Est
- **Document**: `docs/NODUS_SOLUTUS_MUNDUS_COMPUTABILIS_EST.md`
- **Status**: Implemented and Executable
- **Evidence**: Repository-local computability doctrine with deterministic source paths
- **Boundary**: Physical universe, not a metaphysical proof
- **Commands**: 
  - `npm run review:nodus:gate`
  - `npm run test:frontier:experiments`
- **Code Paths**: 
  - `python_backend/pythia_mining/topological_holonomy_engine.py`
- **Documentation Paths**:
  - `docs/SCIENTIFIC_PUBLICATION_NODUS_SOLUTUS.md`
  - `docs/PRESS_RELEASE_NODUS_SOLUTUS.md`

## Administrative Evidence

### HYBA Group Funding Engine
- **Admin Dashboard**: `src/components/HybaAdminDashboard.tsx`
- **Backend API**: `python_backend/hyba_genesis_api/api/admin.py`
- **Role System**: `python_backend/hyba_genesis_api/auth/role_manager.py`
- **Database Models**: `python_backend/consciousness_db/models.py`

### Executive Roles
- CEO Heir Apparent
- Chairman
- CTO
- CFO
- Legal
- Chief of Staff

## Production Readiness

### Evidence Packets
- Location: `artifacts/production_readiness/`
- Format: Timestamped JSON evidence packets
- Generation: `npm run prod:check`

### Gate Scripts
- Local Production Gate: `scripts/local_production_gate.py`
- Modes: `rc`, `bitcoin`, `research`, `live`, `command-room`

## Audit Trail

All administrative actions are logged in the `audit_logs` table with:
- Actor username and role
- Action type
- Target type and ID
- Timestamp
- IP address
- Details JSON

## Reviewer Access

Reviewers should have access to:
1. Source code under `src/` and `python_backend/`
2. Documentation under `docs/`
3. Test suites under `tests/`
4. Evidence artifacts under `artifacts/`
5. Configuration files under `config/`

## Rejection Rule

Any evidence that cannot be reproduced locally through the documented commands should be rejected. The repository-local computability doctrine requires that all claims be verifiable through deterministic, replayable local evidence packets.
