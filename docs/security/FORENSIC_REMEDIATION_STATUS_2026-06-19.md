# Forensic Remediation Status — 2026-06-19

## Remediated in-repo

- Initial admin seed now requires an operator-supplied runtime secret and rejects missing, short, placeholder, or low-complexity values.
- Committed pool config files are now env-backed templates rather than concrete credential carriers.
- Runtime pool profile loading resolves `${ENV_VAR}` and `env:ENV_VAR` references so local/autonomous mining can keep pushing without committing secrets.
- Local secret hygiene gate added at `scripts/check_secret_hygiene.py`.
- `.gitignore` expanded for local env and local pool config variants.

## Manual purge still required

The connector blocked direct mutation/deletion of already-tracked local environment samples that contain sensitive runtime material. Those files should be removed or rewritten locally with:

```bash
git rm --cached .env.local config/.env.docker
printf '# local file intentionally untracked\n' > .env.local
printf '# docker env generated outside git\n' > config/.env.docker
git add .gitignore scripts/check_secret_hygiene.py config/mining_pools_live.json python_backend/mining_pools_config.json python_backend/pythia_mining/pool_profiles.py python_backend/scripts/seed_admin_user.py
git commit -m "fix(security): purge tracked local runtime env files"
```

## Required local checks

```bash
python scripts/check_secret_hygiene.py
python -m compileall -q python_backend/scripts/seed_admin_user.py python_backend/pythia_mining/pool_profiles.py
```
