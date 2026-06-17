# Release notes – Production Hardening (2026‑06‑17)

This release marks the completion of the production‑readiness hardening for HYBA_FULLSTACK. It consolidates a wide range of improvements across security, observability, reliability and documentation.

## Notable changes

- **Security and compliance**
  - Added `SECURITY.md` detailing security policies and best practices.
  - Introduced a CI security workflow running `pip-audit`, `bandit` and `npm audit` on every push.
  - Added comprehensive compliance guidelines covering legal obligations, AML/KYC, data protection and audits.
  - Added secrets management guidance and updated `.env.production.example` to include `POSTGRES_*` variables.

- **Operational readiness**
  - Added runbooks for mining pool outages and a generic incident response template.
  - Added a rollback and escalation plan document with clear roles and procedures.
  - Added a production readiness checklist and created a load testing guide with Locust/k6 examples.

- **Observability**
  - Implemented structured JSON logging and in‑process metrics collection via the telemetry middleware.
  - Added guidance on defining metrics, creating dashboards and configuring alerts.
  - Added a caching and rate limiting guide to improve performance and resilience.

- **Database and persistence**
  - Added SQLAlchemy ORM models for core tables and introduced Alembic for schema migrations.
  - Added an Alembic environment script and an initial migration to create `experiments` and `consciousness_snapshots` tables.
  - Added a PostgreSQL deployment guide and a Docker Compose override file for a Postgres service.

- **Performance and scalability**
  - Introduced an asynchronous executor utility to offload CPU‑bound tasks from the event loop.
  - Added energy efficiency and sustainability guidelines.
  - Added a database migration plan describing steps for migrating from SQLite to PostgreSQL.

- **Documentation**
  - Added or updated numerous documentation files across `docs/` (energy efficiency, compliance, database migration, secrets management, observability, caching, release notes).
  - Updated the database migration plan to reflect actual Alembic scripts and usage.

This release completes the primary hardening phase. Future work may involve fully integrating the asynchronous executor into the mining runtime, implementing real‑time Prometheus exporters, and refining dashboards based on operational experience.
