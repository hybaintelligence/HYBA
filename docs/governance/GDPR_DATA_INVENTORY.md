# GDPR Data Inventory

| Field | Personal data category | Storage location | Retention period | Deletion mechanism | Status |
|---|---|---|---|---|---|
| `customer_id` | Customer account identifier | Customer registry, billing audit, invoices | Active contract + finance retention | Delete/anonymise customer registry and billing evidence after retention | gap |
| `customer_name` | Customer account name | `customer_access.CustomerInfo` | Active contract | Admin customer deletion workflow not yet implemented | gap |
| `email` | User contact data | Admin user database | Active employment/contract | Admin user delete/deactivate | partially_implemented |
| `api_key_hash` / `key_hash` | Pseudonymous credential hash | Customer registry and portal store | Until key revocation + retention | Key revocation endpoint marks inactive | implemented |
| Raw API key | Secret shown once to customer | API response only | Not stored | Not persisted by design | implemented |
| IP address | Network identifier | Access/audit logs where configured | Log retention policy | Log rotation/deletion procedure | gap |
| `request_id` / `trace_id` | Operational identifier | Response headers, audit events | Observability retention | Trace/log TTL | partially_implemented |
| Payment method last4 | Payment metadata | Customer portal store | Active billing relationship | Payment method deletion endpoint not yet implemented | gap |
| Workload context | Customer-supplied data | Execution request/audit stores where configured | Contract-specific | Tenant data deletion workflow not yet implemented | gap |

This inventory is a data-processing map, not a legal determination. Rows marked `gap` require operational deletion controls before external compliance claims.
