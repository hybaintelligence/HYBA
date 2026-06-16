# Python Dependencies Cleanup for Monorepo Consistency

**Issue Found:**
- Three separate `requirements*.txt` files with overlapping but inconsistent dependencies
- `requirements.txt` had `PyJWT` (capitalized), others had `pyjwt` (lowercase)
- `requirements.txt` included `noiseprotocol==0.3.1` missing from others
- Phase-transition requirements file created fragmentation

**Solution Implemented:**

1. **Consolidated to single canonical `python_backend/requirements.txt`**
   - Unified all Python dependencies in one place
   - Clear annotations for each dependency group
   - Pinned versions for reproducibility

2. **Updated Dockerfile**
   - Changed from `requirements.phase-transition.txt` → `requirements.txt`
   - Simpler, more discoverable build process
   - Aligned with standard Python packaging practice

3. **Removed fragmentation**
   - `requirements.phase-transition.txt` no longer used
   - `hyba_genesis_api/requirements.txt` subsumed into main
   - Single source of truth for all Python runtime dependencies

**Maintenance Going Forward:**

For local development:
```bash
cd python_backend
pip install -r requirements.txt
```

For Docker builds:
```bash
docker-compose -f docker-compose.production.yml build
```

For updating dependencies:
```bash
# After modifying requirements.txt
pip install -r python_backend/requirements.txt
pip freeze > python_backend/requirements.lock  # optional lock generation
```

**Files Changed:**
- `python_backend/requirements.txt` — Consolidated from three sources
- `Dockerfile` — Updated to use canonical requirements.txt

**Notes:**
- `requirements.phase-transition.txt` can be archived or removed after Docker build confirmation
- All dependencies now in one discoverable location
- Easier for CI/CD and dependency scanning tools to analyze
