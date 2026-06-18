# Dependency Hardening — Next Steps

## Current State

Four local release gates have been reported green:

- `npm run lint` — TypeScript compilation passes.
- Python system tests — 302 passed, 6 skipped, 2 warnings.
- `npm run test:integration-fence` — 25/25 passing.
- `package.json` — valid JSON with the current script surface.

The integration fence is now treated as a named release gate:

- No release candidate is valid unless `npm run test:integration-fence` passes.
- The gate is documented in `docs/governance/INTEGRATION_FENCE_RELEASE_GATE.md`.
- The gate is intended to be enforceable at commit and CI level.

## Dependency Conflict

The current frontend dependency graph contains a peer-dependency mismatch between Vite and the React plugin:

```text
vite@8.0.16
└─ @vitejs/plugin-react@4.3.4
   └─ peer vite@^7.0.0
```

A clean npm install without legacy peer dependency resolution can fail with a peer dependency error similar to:

```text
npm ERR! peer dependency peer vite@^7.0.0 from @vitejs/plugin-react@4.3.4
npm ERR! peer dep not specified as a dependency of hyba-fullstack
```

The current workaround is:

```bash
npm install --legacy-peer-deps
```

## Impact

- Local installs work when `--legacy-peer-deps` is supplied.
- CI/CD clean installs can fail if npm uses strict peer dependency resolution.
- New machines can fail unless the installer knows to pass `--legacy-peer-deps`.
- Production dependency hygiene is not yet clean because the graph still contains a known peer mismatch.

## Immediate Mitigation

The repository-level `.npmrc` now sets:

```ini
legacy-peer-deps=true
```

This intentionally makes npm respect legacy peer dependency resolution for this repository so clean installs, CI jobs, and new checkouts do not need to pass `--legacy-peer-deps` manually.

This is a temporary unblocker, not the final dependency-hardening resolution.

## Solution Options

### Option A: Pin Vite to 7.x

```json
{
  "dependencies": {
    "vite": "^7.8.0",
    "@vitejs/plugin-react": "^4.3.4"
  }
}
```

Pros:

- Minimal risk.
- Matches the current `@vitejs/plugin-react@4.3.4` peer range.
- Keeps the dependency graph clean without relying on `.npmrc`.

Cons:

- Stays on an older Vite major version.
- Gives up Vite 8 improvements until the React plugin supports that major.

### Option B: Upgrade `@vitejs/plugin-react` When Vite 8 Support Is Available

```json
{
  "dependencies": {
    "vite": "^8.0.16",
    "@vitejs/plugin-react": "<version-with-vite-8-peer-support>"
  }
}
```

Pros:

- Preserves Vite 8.
- Resolves the peer dependency mismatch once a compatible plugin release exists.

Cons:

- Requires an upstream plugin release that explicitly supports Vite 8.
- May need additional validation if the plugin major version changes behavior.

### Option C: Keep `.npmrc` Temporarily

```ini
legacy-peer-deps=true
```

Pros:

- Unblocks CI and new-machine installs immediately.
- Requires no dependency-version churn in this commit.

Cons:

- Masks the peer dependency mismatch.
- Must be removed once the dependency graph is fixed.

## Recommended Timeline

| Phase | Action | Owner | Target |
| --- | --- | --- | --- |
| Now | Keep `.npmrc` mitigation committed | Agent | Today |
| Week 1 | Check for a Vite 8-compatible `@vitejs/plugin-react` release | Eng Lead | Jun 25, 2026 |
| Week 1-2 | Either upgrade the plugin or pin Vite back to 7.x | Eng Lead | Jun 25-Jul 2, 2026 |
| Week 2+ | Remove `legacy-peer-deps=true` after the graph is clean | Eng Lead | Jul 2, 2026 or later |

## CI/CD Validation

CI should run clean installs and the named gates with commands equivalent to:

```bash
npm ci
npm run lint
npm run test:integration-fence
```

Because `.npmrc` is committed, `npm ci` and `npm install` should automatically use legacy peer dependency resolution while this temporary mitigation remains in place.

## Verification After Mitigation

On a fresh checkout or clean local workspace:

```bash
rm -rf node_modules package-lock.json
npm install
npm run lint
npm run test:integration-fence
```

Do not remove `package-lock.json` in normal development unless intentionally regenerating lock state. The command above is only for validating fresh dependency resolution behavior.

## Future Dependency Audit Script

A small script can be added under `scripts/` to make peer conflicts visible in CI logs:

```bash
#!/usr/bin/env bash
set -euo pipefail
npm ls --depth=0 2>&1 | rg -i "peer|conflict"
```

## Related Documentation

- `package.json` — application manifest and npm script surface.
- `.npmrc` — temporary npm peer-resolution mitigation.
- `docs/governance/INTEGRATION_FENCE_RELEASE_GATE.md` — integration fence release-gate policy.

## Current Status

- Blocked on: a dependency graph that supports Vite 8 without peer overrides, or a deliberate Vite 7 pin.
- Workaround: repository-level `legacy-peer-deps=true` in `.npmrc`.
- Risk level: medium; this affects install clarity and CI dependency hygiene, not runtime application behavior.
- Target resolution window: 1-2 weeks pending upstream release review or a conservative Vite pin.
