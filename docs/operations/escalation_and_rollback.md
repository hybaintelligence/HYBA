# Escalation and Rollback Plan

When incidents occur in production, timely escalation and a clear rollback procedure are essential. This document outlines roles, communication channels and the steps to revert changes safely.

## Escalation paths

1. **Primary on‑call engineer** – The engineer assigned to the on‑call rotation for HYBA_FULLSTACK. Responsible for initial triage and mitigation. Contact via Slack/Teams or PagerDuty.
2. **Secondary engineer** – If the issue cannot be resolved quickly, contact the secondary engineer for support.
3. **SRE lead** – Escalate to the site‑reliability lead for infrastructure‑level issues, persistent outages, or when cross‑team coordination is required.
4. **Leadership / stakeholders** – Notify the product owner and leadership when user impact is high or when rollbacks/downtime are imminent.

Always record the incident in the incident tracking system and link to relevant runbooks.

## Rollback procedure

Rollback should be planned for every deployment. Follow these steps if a release must be reverted:

1. **Assess the impact** – Confirm that the current deployment is causing regressions or outages. Check logs, metrics and error reports.
2. **Freeze incoming changes** – Stop new deployments and inform the team.
3. **Prepare the previous release** – Identify the last known good commit/tag (e.g. `vX.Y.Z`) and ensure the build artefacts are available.
4. **Database considerations** – If the deployment included schema migrations:
   - Ensure the database is backed up before rollback.
   - Use Alembic to downgrade to the previous revision: `alembic downgrade <previous_revision_id>`.
   - For destructive rollbacks, coordinate with database administrators.
5. **Redeploy the previous version** – Use your CI/CD pipeline or deployment scripts to roll back the application components (backend, bridge, mining runtime) to the previous release.
6. **Verify** – Run health checks (`/health`, `/api/substrate`) and monitor dashboards to confirm the system is healthy. Validate that key functionality has been restored.
7. **Communicate** – Inform stakeholders that the rollback is complete and update incident notes. Schedule a post‑mortem to analyse the root cause and prevent recurrence.

Having a tested rollback plan reduces the risk of prolonged downtime and ensures that production can be stabilised quickly.
