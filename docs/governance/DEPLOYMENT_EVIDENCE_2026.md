# Deployment Evidence 2026

- Date: 2026-06-22
- Agent: A
- Branch: agent-a/sprint1
- Commit SHA: recorded by git for this branch; verify with `git rev-parse HEAD` after final PR amendments.
- Staging endpoint: not executed in this local environment; AWS credentials and cluster access were not present.

## Commands prepared

```bash
./scripts/smoke_test.sh "$HYBA_STAGING_URL"
```

## Current evidence

Repository evidence includes the Helm Redis dependency, build-time `HYBA_GIT_SHA` injection, `/api/health` version/timestamp response, and smoke test script. Live AWS deployment remains an external operational dependency until credentials are supplied.
