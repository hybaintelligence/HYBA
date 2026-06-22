# Customer Onboarding Runbook

## 1. Create tenant

Use the customer-access admin API or portal workflow for the target environment.

```bash
curl -s -X POST "$HYBA_BASE_URL/api/admin/customer-api-keys" \
  -H "Authorization: Bearer $HYBA_ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"tenant-demo","customer_name":"Demo Tenant","tier":"developer"}'
```

Expected output: a key response with `customer_id`, `key_id`, and one-time API key material.

## 2. Store API key securely

```bash
export HYBA_CUSTOMER_API_KEY="<one-time-key>"
```

Expected output: no terminal output. Never commit the key.

## 3. Verify quota plan

```bash
curl -s "$HYBA_BASE_URL/api/customer/tenant-demo/dashboard" -H "X-API-Key: $HYBA_CUSTOMER_API_KEY"
```

Expected output: dashboard JSON with plan/tier, quota, usage, and billing summary fields.

## 4. Verify first workload

```bash
curl -s -X POST "$HYBA_BASE_URL/api/qiaas/query" \
  -H "X-API-Key: $HYBA_CUSTOMER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query_type":"predict","context":{"onboarding":true}}'
```

Expected output: QIaaS envelope with `qi_execution_id`, `usage_meter`, and `evidence_packet`.

## 5. Generate first invoice

```bash
curl -s "$HYBA_BASE_URL/api/customer/tenant-demo/billing/invoices" -H "X-API-Key: $HYBA_CUSTOMER_API_KEY"
```

Expected output: invoice list or empty list before billing close; after chargeable usage, invoices include tenant, line items, and totals.
