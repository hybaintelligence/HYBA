# Docker Compose Production Deployment Guide

**Status:** 2026-06-14 Production Readiness  
**Context:** HYBA_FULLSTACK production deployment via docker-compose

## Critical Issue: Argon2id Dollar Sign Escaping

Docker Compose interprets `$` as variable substitution. When Argon2id hashes (which contain multiple `$` characters) are used in environment files, Compose silently blanks parts of the hash.

### Problem Example

```bash
# .env or .env.docker (WRONG - Compose will blank $argon2id, $v, $m, etc.)
HYBA_OPERATOR_CREDENTIALS=operator:$argon2id$v=19$m=65536,t=3,p=4$...:ceo

# Result: HYBA_OPERATOR_CREDENTIALS=operator:::ceo (broken)
```

### Solution: Double-Escape for Compose

```bash
# .env.docker (CORRECT - Use $$ for literal $)
HYBA_OPERATOR_CREDENTIALS=operator:$$argon2id$$v=19$$m=65536,t=3,p=4$$...:ceo

# Compose interprets $$ as literal $
# Result: HYBA_OPERATOR_CREDENTIALS=operator:$argon2id$v=19$m=65536,t=3,p=4$...:ceo (correct)
```

## File Structure

### Local Development (.env)

Use for `npm run dev`, `npm run backend:start`, direct Python/Node execution.

```bash
HYBA_OPERATOR_CREDENTIALS=operator:$argon2id$v=19$m=65536,t=3,p=4$...:ceo
```

Argon2 hashes are NOT interpreted; plain `$` is fine.

### Docker Compose Production (.env.docker or injected)

Use for `docker-compose -f docker-compose.production.yml`.

```bash
# Option 1: Use .env.docker with escaped $$
HYBA_OPERATOR_CREDENTIALS=operator:$$argon2id$$v=19$$m=65536,t=3,p=4$$...:ceo

# Option 2: Inject via runtime environment (recommended for secrets)
export HYBA_OPERATOR_CREDENTIALS='operator:$argon2id$v=19$m=65536,t=3,p=4$...:ceo'
docker-compose -f docker-compose.production.yml up
```

## Recommended Deployment Pattern

For production, inject secrets through runtime environment or secret manager, not .env files:

```bash
#!/bin/bash
# production-deploy.sh

# Load secrets from vault/secret manager
export JWT_SECRET=$(get_secret jwt_secret)
export HYBA_OPERATOR_CREDENTIALS=$(get_secret operator_credentials)  # Plain $ here
export HYBA_POOL_BRAIINS_PASSWORD=$(get_secret pool_password)

# Build and run
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

This avoids .env file escaping issues entirely.

## Verification

After deployment, verify credentials are not blanked:

```bash
# Inside running container
docker exec hyba-backend python -c "import os; print(len(os.getenv('HYBA_OPERATOR_CREDENTIALS', '')))"
# Should print: [length of full credential string, e.g., 140+]
# If prints: 20 or small number, Argon2 hash was blanked
```

## Files

- `.env` — Local development (plain `$` in hashes)
- `.env.docker` — Docker Compose (escaped `$$` in hashes)
- `.env.example` — Template with documentation
- `docker-compose.production.yml` — Production compose file (no escaping needed here; it reads from `.env.docker` or runtime env)

## Changelog

### 2026-06-14

- Identified Docker Compose `$` substitution issue in Argon2id hashes
- Added `.env.docker` with proper `$$` escaping
- Updated `.env.example` with deployment guidance
- Documented recommended pattern: inject secrets at runtime, not via files
