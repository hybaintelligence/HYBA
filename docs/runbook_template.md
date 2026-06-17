# Runbook Template

This template provides a consistent structure for writing incident runbooks.  Runbooks should be concise, version controlled, and easily discoverable (e.g., linked from dashboards and alerts).

## 1. Overview

- **Service/component:**  _(e.g., HYBA Genesis API, Pythia Mining Core)_
- **Responsible team:**  _(e.g., Backend, SRE)_
- **Runbook owner:**  _(person or distribution list)_
- **Last updated:**  _(date)_
- **Related dashboards:**  _(links to Grafana/Prometheus dashboards)_

## 2. Purpose

Describe the purpose of this runbook.  For example: “Recover from mining pool connectivity failures” or “Resolve elevated 5xx rates on the API”.

## 3. Preconditions

List any preconditions that must hold before following the remediation steps (e.g., ensure the on‑call has access to the secret manager).  Identify any dependent services or external systems.

## 4. Detection

How is this incident detected?  Provide sample alert messages or log entries.  Include links to queries that confirm the condition.

## 5. Immediate actions

1. **Triage** – Assess the impact and verify whether the alert is valid.  Communicate with affected teams as needed.
2. **Mitigation** – Describe immediate actions to mitigate the impact (e.g., disable self‑optimisation loop, fail over to backup pool, increase rate limits).
3. **Rollback** – If applicable, roll back the last deployment or configuration change.  Provide specific commands/scripts.

## 6. Detailed remediation steps

Provide step‑by‑step instructions to restore normal service.  Use numbered lists and ensure commands/scripts are accurate.  Include:  
- How to access logs and metrics.  
- How to examine queue lengths, mining workers, or DB state.  
- How to update or redeploy services.  
- Expected outcomes at each stage.

## 7. Post‑incident actions

- **Root cause analysis** – Document the root cause once understood.  Use a template (e.g., 5 whys, fishbone diagram).
- **Follow‑up tasks** – List tasks to prevent recurrence (e.g., improve monitors, update runbook, add tests).
- **Communication** – Summarise the incident and remediation in an incident report to stakeholders.

## 8. Contacts

- **Primary on‑call engineer:**  _(Name/email)_
- **Escalation:**  _(Team lead/SRE manager)_
- **External stakeholders:**  _(Compliance, security, product)_

---

*Remember to keep runbooks up to date.  Review them regularly and perform simulations to ensure instructions remain valid.*
