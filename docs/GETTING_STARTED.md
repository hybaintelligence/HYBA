# HYBA Getting Started

Goal: clone HYBA, run the FastAPI backend, and make the first authenticated request in under 15 minutes.

## Prerequisites

- Python 3.12+
- Node.js 22+ only if you also run the frontend
- `curl`

## 1. Clone and install

```bash
git clone <repo-url> HYBA_FULLSTACK
cd HYBA_FULLSTACK
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Expected output: `Successfully installed ...` with no unresolved dependency errors.

## 2. Run the backend locally

```bash
export HYBA_API_KEY_SECRET="local-dev-secret-change-me"
export JWT_SECRET="local-dev-jwt-secret-change-me"
export HYBA_CORS_ORIGINS="http://localhost:3000"
python -m uvicorn hyba_genesis_api.main:app --app-dir python_backend --host 127.0.0.1 --port 3001
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:3001
```

## 3. Verify health

```bash
curl -s http://127.0.0.1:3001/api/health
```

Expected output resembles:

```json
{"status":"healthy","version":"<git_sha>","timestamp":"2026-06-22T00:00:00Z"}
```

If `/api/health` is unavailable in your branch, use the compatibility endpoint:

```bash
curl -s http://127.0.0.1:3001/health
```

## 4. Create or obtain an API key

For local onboarding, create a tenant/key through the customer portal or admin customer-access API according to `docs/runbooks/CUSTOMER_ONBOARDING.md`. Store it only in your shell:

```bash
export HYBA_API_KEY="hyba_test_your_key_here"
```

## 5. First authenticated calls

QaaS provision:

```bash
curl -s -X POST http://127.0.0.1:3001/api/v1/fault-tolerant-computers \
  -H "X-API-Key: $HYBA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"dev-ftqc","tier":"developer","code_distance":7,"logical_qubits":8}'
```

QIaaS query:

```bash
curl -s -X POST http://127.0.0.1:3001/api/qiaas/query \
  -H "X-API-Key: $HYBA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query_type":"predict","context":{"question":"first workload"},"confidence_threshold":0.7}'
```

Finance capability map:

```bash
curl -s http://127.0.0.1:3001/api/quantum-finance/capability-map \
  -H "X-API-Key: $HYBA_API_KEY"
```

## Troubleshooting

1. **`ModuleNotFoundError: hyba_genesis_api`** — run uvicorn with `--app-dir python_backend` from the repository root.
2. **`401 Unauthorized`** — verify `X-API-Key` is present, not expired, and created for the active tenant.
3. **Startup fails on secrets** — set `HYBA_API_KEY_SECRET` and `JWT_SECRET` to non-placeholder values before starting the backend.
