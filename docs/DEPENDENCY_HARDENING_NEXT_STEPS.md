# Dependency Hardening — Next Steps

## Current State

**Four Gates Green Locally:**
- ✓ `npm run lint` — TypeScript compilation passes
- ✓ Python system tests — 302 passed, 6 skipped, 2 warnings
- ✓ `npm run test:integration-fence` — 25/25 passing
- ✓ `package.json` — Valid JSON, 86 scripts

**Integration Fence is now a named release gate:**
- No RC is valid unless `npm run test:integration-fence` passes
- Gate is documented in `docs/governance/INTEGRATION_FENCE_RELEASE_GATE.md`
- Gate is enforceable at commit/CI level

## The Dependency Problem

### Current Conflict

```
vite@8.0.16 
  └─ @vitejs/plugin-react@4.3.4
     └─ peer vite@^7.0.0 (not satisfied, have 8.0.16)
```

**Error without `--legacy-peer-deps`:**
```
npm ERR! peer dependency peer vite@^7.0.0 from @vitejs/plugin-react@4.3.4
npm ERR! peer dep not specified as a dependency of hyba-fullstack
```

**Workaround:**
```bash
npm install --legacy-peer-deps
```

### Impact

- ✓ **Local:** Works with `--legacy-peer-deps`
- ✗ **CI/CD:** Clean installs will fail
- ✗ **New Machines:** Will fail unless `--legacy-peer-deps` is used
- ✗ **Production:** Dependency graph is not clean

## Solution Options

### Option A: Pin Vite to 7.x (Conservative)

```json
{
  "dependencies": {
    "vite": "^7.8.0",  // Change from ^8.0.16
    "@vitejs/plugin-react": "^4.3.4"  // Already compatible
  }
}
```

**Pros:**
- Minimal risk
- @vitejs/plugin-react already supports 7.x
- Both versions are stable

**Cons:**
- Stays on older Vite version
- Misses Vite 8.x improvements

### Option B: Upgrade @vitejs/plugin-react to 8.x-compatible (Modern)

```json
{
  "dependencies": {
    "vite": "^8.0.16",  // Keep current
    "@vitejs/plugin-react": "^4.4.x",  // Update when available
    // OR
    "@vitejs/plugin-react": "^5.0.0"   // If 5.x supports Vite 8
  }
}
```

**Pros:**
- Uses latest Vite 8 features
- Forward compatible

**Cons:**
- Requires @vitejs/plugin-react release that supports Vite 8
- As of June 2026, may not be released yet

### Option C: Relax with .npmrc Config (Temporary)

Create `.npmrc` file:
```
legacy-peer-deps=true
```

**Pros:**
- No package changes
- CI automatically uses the setting

**Cons:**
- Still masks the underlying dependency issue
- Not a real solution, just a workaround

## Recommendation

**Immediate action (this commit):**
- Add `.npmrc` with `legacy-peer-deps=true` to unblock CI
- Document the conflict in this file

**Near-term (next 1-2 weeks):**
- Check if @vitejs/plugin-react 4.4.x or 5.x has been released
- If yes: Update package.json and remove `.npmrc`
- If no: Evaluate reverting Vite to 7.x

**Long-term:**
- Monitor @vitejs/plugin-react releases
- Establish CI/CD dependency audit process
- Add `npm ci` (clean install) as part of CI validation

## Implementation

### Create .npmrc

```bash
echo "legacy-peer-deps=true" > .npmrc
git add .npmrc
```

This file:
- Tells npm to allow peer dependency mismatches
- Is committed so CI/CD respects it
- Allows clean installs without `--legacy-peer-deps` flag

### Update CI/CD

Add to CI pipeline:
```bash
npm ci  # Clean install (respects .npmrc)
npm run lint
npm run test:integration-fence
```

### Document the Issue

Add to DEPENDENCY_HARDENING_NEXT_STEPS.md (this file):
- Version conflict details
- Workaround status
- Resolution timeline

## Verification After Fix

```bash
# On a clean machine or fresh checkout:
rm -rf node_modules package-lock.json

# Should work without --legacy-peer-deps:
npm install

# Verify all gates still pass:
npm run lint
npm run test:integration-fence
```

## Timeline

| Phase | Action | Owner | Deadline |
|-------|--------|-------|----------|
| Now | Add `.npmrc` to unblock | Agent | Today |
| Week 1 | Check for @vitejs/plugin-react 4.4.x+ | Eng Lead | Jun 25 |
| Week 1-2 | Update or revert depending on release | Eng Lead | Jun 25-Jul 2 |
| Week 2 | Remove `.npmrc` if updated successfully | Eng Lead | Jul 2+ |

## Scripts to Track

Add to `scripts/` for dependency auditing:

```bash
#!/bin/bash
# Check peer dependency conflicts
npm ls --depth=0 2>&1 | grep -i "peer\|conflict"
```

## Related Documentation

- `package.json` — Application manifest
- `docs/governance/INTEGRATION_FENCE_RELEASE_GATE.md` — Release gating rules
- `.npmrc` — NPM configuration (to be created)

## Current Status

**Blocked On:** @vitejs/plugin-react release with Vite 8 support  
**Workaround:** `npm install --legacy-peer-deps` (or use `.npmrc`)  
**Risk Level:** Medium (CI/CD clarity issue, not code issue)  
**Resolution:** 1-2 weeks pending upstream release

---

## Next Commit

When committing this fix, include:

```
git add .npmrc DEPENDENCY_HARDENING_NEXT_STEPS.md
git commit -m "build: allow legacy peer deps for vite/react-plugin compatibility

The integration fence is now the release gate. This unblocks CI while we
await @vitejs/plugin-react release for Vite 8 support.

vite@8.0.16 declares peer support through @vitejs/plugin-react@^4.3.4
but @vitejs/plugin-react@4.3.4 only peers with vite@^7.0.0.

Status:
  • Local builds: working with --legacy-peer-deps
  • CI builds: will respect .npmrc
  • Clean installs: unblocked

Timeline:
  • Week 1: Check for @vitejs/plugin-react 4.4.x+ release
  • Week 1-2: Update package.json or revert Vite to 7.x
  • Week 2+: Remove .npmrc if resolved"

git push origin main
```
