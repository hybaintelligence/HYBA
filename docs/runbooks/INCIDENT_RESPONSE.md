# Incident Response Runbook

## Severity levels

- P0: customer-facing outage, data integrity risk, or suspected secret exposure.
- P1: major degradation of QaaS/QIaaS/CIaaS/Finance for multiple tenants.
- P2: isolated tenant failure or non-critical dependency degradation.
- P3: documentation, cosmetic, or delayed background processing issue.

## Escalation path

1. First responder acknowledges within 15 minutes for P0/P1.
2. Incident commander opens a bridge and assigns communications, operations, and scribe roles.
3. Escalate security/privacy incidents to security owner immediately.
4. Notify PM and customer success for customer-visible P0/P1 incidents.

## First responder checklist

```bash
curl -s "$HYBA_BASE_URL/api/health"
bash scripts/smoke_test.sh "$HYBA_BASE_URL"
kubectl get pods -n hyba
kubectl logs deploy/hyba-api -n hyba --tail=200
```

Expected healthy signals: health reports `status=healthy`, smoke test returns HTTP 200 for all public surfaces, pods are `Running`, and logs have no repeated 5xx stack traces.

## Rollback procedure

```bash
helm rollback hyba-platform -n hyba
bash scripts/smoke_test.sh "$HYBA_BASE_URL"
```

Expected output: Helm reports rollback completed; smoke test passes.

## Post-mortem template

- Incident title:
- Severity:
- Start/end time UTC:
- Customer impact:
- Root cause:
- Detection source:
- What went well:
- What failed:
- Corrective actions with owners and dates:
