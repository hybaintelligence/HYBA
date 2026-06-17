# Production Readiness Checklist

This document provides a structured checklist that teams should complete before deploying a new service or major change to production.  It complements code review and QA tests by focusing on operational and security readiness.

## 1. Monitoring and observability

- [ ] **Metrics defined** – Identify key performance indicators (e.g., request latency, error rate, mining throughput) and instrument them via Prometheus.  Export them to dashboards.
- [ ] **Dashboards created** – Create or update Grafana dashboards for all new functionality.
- [ ] **Alerts configured** – Configure alert thresholds for critical metrics (e.g., CPU usage, error rates) and integrate them with incident management tooling (PagerDuty, Opsgenie, etc.).
- [ ] **Structured logging** – Ensure logs are JSON‑structured, include request IDs and are searchable.  Include sufficient context to trace and debug issues.
- [ ] **Health/readiness endpoints** – Verify `/health` and `/api/substrate` endpoints return 200 only when the service is ready.

## 2. Incident response and runbooks

- [ ] **On‑call awareness** – Notify the on‑call engineer of the upcoming deployment and ensure coverage during the rollout.
- [ ] **Runbooks written** – Document common failure modes and step‑by‑step remediation procedures.  Link runbooks from dashboards and alerts.
- [ ] **Escalation paths** – Define escalation contacts and procedures for critical incidents.
- [ ] **Rollback plan** – Write and test rollback steps.  Validate that the application can be reverted safely if deployment issues arise.
- [ ] **Recovery drills** – Practice incident scenarios (e.g., mining pool outage, database corruption) and verify runbooks.

## 3. Security and compliance

- [ ] **Secrets management** – Store secrets (JWT keys, operator credentials, pool passwords) in a secure vault.  Do not commit secrets to the repository.
- [ ] **Authentication and authorization** – Ensure all sensitive endpoints enforce JWT authentication and role‑based access control.
- [ ] **Dependency scanning** – Run vulnerability scans for Python/Node dependencies (e.g., pip‑audit, npm audit) and remediate critical issues.
- [ ] **Static code analysis** – Use tools like bandit and eslint to detect common security flaws.
- [ ] **Input validation** – Validate and sanitize all external inputs; enforce body size limits and rate limits.
- [ ] **Compliance** – Document handling of personal data and ensure compliance with applicable laws (GDPR, etc.).

## 4. Performance and scalability

- [ ] **Load testing** – Perform load testing (e.g., using Locust or k6) to measure API latency and throughput under expected and peak loads.
- [ ] **Caching and rate limiting** – Implement caching where appropriate; ensure rate limits protect downstream resources.
- [ ] **Resource limits** – Set CPU/memory limits on container deployments and tune concurrency settings.
- [ ] **Async and background tasks** – Offload CPU‑intensive operations to background workers or separate services to prevent blocking the API.
- [ ] **Database resilience** – Use a production‑grade database (e.g., PostgreSQL) with backups and automated migrations.
- [ ] **Autonomy state storage bound** – PYTHIA reflexive-state writes retain at most `state_backup_retention_count=5` backups by default in `HYBA_AUTONOMY_STATE_DIR`; each backup is one prior `reflexive_state.json` snapshot, so provision at least 6x the observed state-file size plus temporary-write headroom. Stale persistence locks are reclaimed only after `HYBA_AUTONOMY_STATE_LOCK_STALE_SECONDS` (default 300s).

## 5. Documentation and deployment

- [ ] **Documentation updated** – Update API docs, README, and runbooks to reflect the new functionality and configuration requirements.
- [ ] **Release notes** – Prepare release notes summarizing changes, migration steps, and known issues.
- [ ] **Infrastructure as Code** – Use version‑controlled deployment scripts (e.g., Docker Compose, Terraform) and ensure they are up to date.
- [ ] **Environment verification** – Validate environment variables (JWT_SECRET length, Argon2 credentials) and file permissions before deployment.
- [ ] **Evidence capture** – Capture logs, metrics and test results as evidence for the readiness review.

Completing this checklist and obtaining sign‑off from engineering, SRE, and security stakeholders ensures that the service can be safely operated in production.  Adapt the checklist to the risk profile and regulatory requirements of your organisation.
