# PostgreSQL Integration for Docker Compose

**Status:** 2026-06-17 Production Readiness  
**Context:** Configuring HYBA_FULLSTACK to use PostgreSQL in containerized environments.

## Overview

HYBA_FULLSTACK ships with a default SQLite database for local development. For production workloads you should use a more robust database like PostgreSQL. The repository now includes:

- `.env.production.example` with `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` placeholders.
- `docker-compose.db.yml` which defines a standalone Postgres service for Docker Compose.

## Recommended Deployment

1. **Set environment variables**  
   Populate `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and `DATABASE_URL` in your secret store or environment file. For Compose, you can set them in `.env.docker` or export them in your deployment script. For example:

   ```bash
   export POSTGRES_USER=hyba
   export POSTGRES_PASSWORD=change-me
   export POSTGRES_DB=hyba_db
   export DATABASE_URL=postgresql+psycopg2://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB
   ```

2. **Launch Postgres alongside application**  
   Include the `docker-compose.db.yml` file when starting Compose so that the database service is created:

   ```bash
   docker-compose -f docker-compose.production.yml -f docker-compose.db.yml up -d
   ```

   Compose will merge the services from both files. The `db` service will be available at hostname `db` on port 5432.

3. **Configure the backend to use Postgres**  
   Ensure `DATABASE_URL` is exported or present in `.env.docker`. The FastAPI backend reads this variable and will connect to the Postgres service automatically.

## Notes

- Use a managed secret store or infrastructure secrets to set `POSTGRES_PASSWORD` and other sensitive values.
- The Postgres service persists its data in the `postgres_data` volume defined in `docker-compose.db.yml`.
- If you need to scale or manage the database separately, replace the `db` service with an external Postgres service and point `DATABASE_URL` accordingly.
