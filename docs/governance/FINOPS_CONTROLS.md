# FinOps Controls

## Monthly budget limits

- Staging: budget owner sets a monthly AWS Budget per environment tag.
- Production: budget owner sets per-customer and per-API-surface budgets once tagging is confirmed.
- Required tags: `Environment`, `Customer`, `ApiSurface`, `CostCenter`.

## Alert thresholds

- 80% forecast or actual spend: notify engineering lead and PM; review top services.
- 100% forecast or actual spend: incident commander opens P2 FinOps incident; freeze non-critical scale-up.
- 125% actual spend: escalate to executive sponsor; require written approval for continued burst capacity.

## AWS Budgets setup

1. Open AWS Billing and Cost Management → Budgets.
2. Create cost budget for `Environment=staging` and `Environment=production`.
3. Add notification thresholds at 80%, 100%, and 125% actual/forecast spend.
4. Add SNS/email recipients for engineering, PM, and finance owner.
5. Validate tags in Cost Explorer before relying on per-customer allocation.

## Over-budget response

```bash
python scripts/finops_report.py > /tmp/hyba-finops.json
cat /tmp/hyba-finops.json
```

Expected output: JSON showing last-30-day cost by AWS service, `Customer` tag, and `ApiSurface` tag. If tag groups are empty, tagging is a control gap and costs must be allocated manually until fixed.
