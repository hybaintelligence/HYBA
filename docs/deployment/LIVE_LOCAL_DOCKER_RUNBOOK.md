# HYBA Live Local Docker Runbook

This is the fastest path to get this repository running in production mode on your local machine today.

It is intentionally narrow:

- local Docker/Colima only;
- one real operator credential;
- one real pool profile first;
- live share submission disabled on first bring-up.

## 1. Create the local env file

Use the helper:

```bash
bash scripts/setup_mining.sh
```

Or copy the example manually:

```bash
cp .env.mining.local.example .env.mining.local
```

Then fill in:

- `JWT_SECRET`
- `HYBA_OPERATOR_CREDENTIALS`
- one real pool credential set

## 2. Generate the operator password hash

`HYBA_OPERATOR_CREDENTIALS` must use Argon2id in production mode.

Example:

```bash
python - <<'PY'
from argon2 import PasswordHasher
print(PasswordHasher().hash('replace-with-strong-password'))
PY
```

Then set:

```text
HYBA_OPERATOR_CREDENTIALS=operator:<argon2id-hash>:mining_operator
```

## 3. Keep the first run safe

For first bring-up, keep:

```text
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
HYBA_ALLOW_DEV_FIXTURES=false
```

This allows real pool connectivity without immediately attempting live share submission.

## 4. Start the local container runtime

If you are using Colima:

```bash
colima start
```

## 5. Bring the stack up

```bash
docker compose --env-file .env.mining.local -f docker-compose.production.yml up --build
```

Services:

- `hyba-bridge`: public HTTP entrypoint on `3000`
- `hyba-backend`: internal FastAPI backend on `3001`
- `hyba-runtime`: mining runtime

## 6. Validate health

In a second shell:

```bash
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3000/api/health/readiness
docker compose --env-file .env.mining.local -f docker-compose.production.yml ps
docker compose --env-file .env.mining.local -f docker-compose.production.yml logs --tail=200 hyba-backend hyba-runtime hyba-bridge
```

You want:

- backend healthy;
- bridge healthy;
- runtime not crashing;
- real pool configuration recognized;
- no dev-fixture or placeholder-secret failures.

## 7. Run production env checks

Before enabling live share submission, run:

```bash
set -a
source .env.mining.local
set +a
npm run prod:env:check
npm run runtime:guard
```

## 8. Enable live submission only after bring-up is clean

Edit `.env.mining.local`:

```text
HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
HYBA_LIVE_SHARE_APPROVAL_ID=replace-with-real-approval-id
```

Then restart:

```bash
docker compose --env-file .env.mining.local -f docker-compose.production.yml up --build
```

## 9. Stop the stack

```bash
docker compose --env-file .env.mining.local -f docker-compose.production.yml down
```

## Notes

- Do not commit `.env.mining.local`.
- Start with one real pool, not four.
- Get the container path stable locally before paying for any cloud target.
