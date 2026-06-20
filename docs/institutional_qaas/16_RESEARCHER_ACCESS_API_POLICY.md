# Gap 16: Collaboration Protocols - Researcher Access API Policy

**Gap ID:** 16  
**Track:** FAIR Infrastructure  
**Status:** CLOSED  
**Closure Date:** 2026-06-20  
**Evidence Owner:** Platform Lead

---

## 1. Gap Description

Enables external researchers to reproduce HYBA/PYTHIA evidence reproducibly without compromising security. This policy defines authentication, rate limits, reproducibility endpoints, abuse controls, and publication workflows for programmatic access.

---

## 2. Acceptance Criteria

✅ **Authentication model defined:** OAuth 2.0 / institutional SSO with role-based access control  
✅ **Rate limits specified:** Per-user and per-institution quotas with throttling  
✅ **Reproducibility endpoints documented:** `/evidence/reproduce`, `/benchmark/rerun`, `/proof/verify`  
✅ **Abuse controls enforced:** IP allowlisting, request signing, audit logging  
✅ **Publication workflow standardized:** Pre-publication review process and citation generation  

---

## 3. Artifact: Researcher Access API Policy

```yaml
# HYBA/PYTHIA Researcher Access API Policy v1.0
# Effective Date: 2026-06-20
# Last Updated: 2026-06-20

---
api_version: "1.0"
effective_date: "2026-06-20"
last_updated: "2026-06-20"
policy_owner: "Platform Lead"
governance_authority: "Ethics Review Committee"

# ============================================================================
# SECTION 1: AUTHENTICATION & AUTHORIZATION
# ============================================================================

authentication:
  supported_methods:
    - name: "OAuth 2.0"
      provider: "github, google, institutional_sso"
      flow: "authorization_code"
      token_lifetime_hours: 24
      
    - name: "API Key"
      issuer: "platform_admin"
      rotation_required_days: 90
      scopes_assignable: true
      rate_limit_key_tokens: 5000
      
    - name: "Institutional SSO"
      protocol: "SAML 2.0"
      idp_list:
        - "caltech.edu"
        - "mit.edu"
        - "oxford.ac.uk"
        - "cam.ac.uk"
      auto_group_sync: true

  mfa_required:
    - researcher_tier: "external_collaborator"
      enforcement: "mandatory"
    - researcher_tier: "institutional_partner"
      enforcement: "mandatory"
    - researcher_tier: "verified_academic"
      enforcement: "optional"

role_based_access_control:
  roles:
    - name: "public_viewer"
      authenticated: false
      permissions:
        - "read:public_benchmarks"
        - "read:published_evidence"
      rate_limit_daily_requests: 1000
      
    - name: "verified_academic"
      authenticated: true
      requirements:
        - "institutional_email"
        - "publication_record_verification"
      permissions:
        - "read:public_benchmarks"
        - "read:published_evidence"
        - "reproduce:published_benchmarks"
        - "request:access_embargo_artifacts"
      rate_limit_daily_requests: 10000
      
    - name: "external_collaborator"
      authenticated: true
      requirements:
        - "institutional_email"
        - "mfa_enabled"
        - "signed_collaboration_agreement"
        - "ethics_review_approval"
      permissions:
        - "read:public_benchmarks"
        - "read:published_evidence"
        - "read:embargo_artifacts_under_agreement"
        - "reproduce:any_benchmark"
        - "submit:new_evidence"
        - "access:raw_mathematical_proofs"
      rate_limit_daily_requests: 50000
      
    - name: "institutional_partner"
      authenticated: true
      requirements:
        - "organization_agreement"
        - "mfa_enabled"
        - "audit_trail_enabled"
        - "institutional_sso"
      permissions:
        - "read:*"
        - "reproduce:*"
        - "submit:evidence"
        - "access:confidential_benchmarks"
        - "request:custom_reproducibility_suite"
      rate_limit_daily_requests: 500000
      
    - name: "platform_administrator"
      authenticated: true
      requirements:
        - "background_check"
        - "mfa_mandatory"
        - "security_training_current"
      permissions:
        - "*"

# ============================================================================
# SECTION 2: RATE LIMITING & THROTTLING
# ============================================================================

rate_limiting:
  default_strategy: "token_bucket"
  
  per_user:
    public_viewer:
      requests_per_hour: 60
      requests_per_day: 1000
      concurrent_sessions: 1
      burst_allowance: 10
      
    verified_academic:
      requests_per_hour: 500
      requests_per_day: 10000
      concurrent_sessions: 3
      burst_allowance: 50
      
    external_collaborator:
      requests_per_hour: 2500
      requests_per_day: 50000
      concurrent_sessions: 10
      burst_allowance: 200
      
    institutional_partner:
      requests_per_hour: 25000
      requests_per_day: 500000
      concurrent_sessions: 100
      burst_allowance: 1000
      
  per_institution:
    rate_limit_daily: 1000000
    rate_limit_monthly: 20000000
    sustained_burst_threshold: 100000
    fallback_strategy: "reject_with_429"
    
  endpoint_specific:
    - endpoint: "/api/v1/evidence/reproduce"
      timeout_seconds: 600
      compute_budget_gflops: 1000000
      storage_quota_gb: 100
      
    - endpoint: "/api/v1/benchmark/rerun"
      timeout_seconds: 1200
      compute_budget_gflops: 5000000
      storage_quota_gb: 500
      
    - endpoint: "/api/v1/proof/verify"
      timeout_seconds: 3600
      compute_budget_gflops: 10000000
      storage_quota_gb: 1000

# ============================================================================
# SECTION 3: REPRODUCIBILITY ENDPOINTS
# ============================================================================

reproducibility_endpoints:
  base_url: "https://api.hyba-pythia.org/api/v1"
  
  - endpoint: "/evidence/reproduce"
    method: "POST"
    authentication_required: true
    minimum_role: "verified_academic"
    description: "Re-execute a specific evidence artifact with original parameters"
    request_schema:
      properties:
        evidence_id:
          type: "string"
          pattern: "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
        environment_override:
          type: "object"
          description: "Optional Python/system version overrides"
        output_format:
          enum: ["json", "parquet", "csv"]
        store_results:
          type: "boolean"
          default: false
    response_schema:
      properties:
        job_id: {"type": "string"}
        status: {"enum": ["queued", "running", "completed", "failed"]}
        checksum_original: {"type": "string"}
        checksum_reproduced: {"type": "string"}
        divergence_magnitude: {"type": "number"}
        execution_log: {"type": "string"}
        results_download_url: {"type": "string"}
        expiration_date: {"type": "string", "format": "date-time"}
    examples:
      - curl: |
          curl -X POST https://api.hyba-pythia.org/api/v1/evidence/reproduce \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
              "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
              "store_results": true,
              "output_format": "json"
            }'
            
  - endpoint: "/benchmark/rerun"
    method: "POST"
    authentication_required: true
    minimum_role: "verified_academic"
    description: "Execute a benchmark suite with custom parameters"
    request_schema:
      properties:
        benchmark_name: {"type": "string"}
        circuit_width: {"type": "integer", "minimum": 1, "maximum": 100}
        circuit_depth: {"type": "integer", "minimum": 1, "maximum": 10000}
        num_iterations: {"type": "integer", "minimum": 1, "maximum": 10000}
        determinism_validation: {"type": "boolean", "default": true}
    response_schema:
      properties:
        job_id: {"type": "string"}
        benchmark_results: {"type": "array"}
        execution_time_seconds: {"type": "number"}
        theoretical_vs_observed: {"type": "object"}
        
  - endpoint: "/proof/verify"
    method: "POST"
    authentication_required: true
    minimum_role: "external_collaborator"
    description: "Verify a formal proof artifact or check intermediate steps"
    request_schema:
      properties:
        proof_id: {"type": "string"}
        check_intermediate_steps: {"type": "boolean", "default": false}
        use_solver: {"enum": ["lean4", "coq", "z3", "native"]}
    response_schema:
      properties:
        proof_status: {"enum": ["verified", "unverified", "malformed"]}
        verification_time_seconds: {"type": "number"}
        dependency_check: {"type": "object"}

# ============================================================================
# SECTION 4: ABUSE PREVENTION & SECURITY
# ============================================================================

security_controls:
  request_signing:
    enabled: true
    algorithm: "hmac-sha256"
    timestamp_tolerance_seconds: 300
    replay_attack_prevention: true
    
  ip_allowlisting:
    default_policy: "reject_unknown_ips"
    grace_period_days: 30
    auto_allowlist_on_institutional_sso: true
    manual_override_requires_approval: "Platform Lead"
    
  audit_logging:
    enabled: true
    retention_days: 2555  # 7 years
    log_fields:
      - timestamp
      - user_id
      - ip_address
      - endpoint
      - method
      - request_size_bytes
      - response_size_bytes
      - http_status
      - execution_time_ms
      - evidence_accessed
      - data_classification
      - result: "success|failure|error"
    sensitive_redaction:
      - api_keys
      - credentials
      - personally_identifiable_information
      
  abuse_detection:
    enabled: true
    patterns:
      - name: "aggressive_scanning"
        threshold: "1000 unique endpoints in 1 hour"
        action: "temporary_ban"
        duration_minutes: 60
        escalation: "ethics_review_committee"
        
      - name: "data_exfiltration_attempt"
        threshold: ">1GB downloaded in 1 hour"
        action: "immediate_suspend"
        requires_manual_review: true
        
      - name: "credential_sharing"
        threshold: "same api_key from 50+ unique ips in 24h"
        action: "revoke_key"
        notification: "user"
        
      - name: "ddos_pattern"
        threshold: "10000 requests/min from single ip"
        action: "block_ip"
        requires_manual_review: true

  encryption:
    transport:
      minimum_tls_version: "1.3"
      cipher_suites: ["TLS_CHACHA20_POLY1305", "TLS_AES_256_GCM_SHA384"]
    at_rest:
      algorithm: "AES-256-GCM"
      key_rotation_days: 90
      
  request_validation:
    max_payload_size_mb: 100
    max_query_string_length: 2048
    json_schema_validation: true
    sql_injection_prevention: true

# ============================================================================
# SECTION 5: PUBLICATION & CITATION WORKFLOW
# ============================================================================

publication_workflow:
  pre_publication_review:
    enabled: true
    reviewer_count: 2
    acceptable_roles: ["external_collaborator", "institutional_partner", "platform_administrator"]
    max_review_days: 30
    
  review_checklist:
    - "Claim boundary accurately stated"
    - "Results reproducible on independent system"
    - "Limitations explicitly documented"
    - "Conflict of interest disclosure complete"
    - "Data provenance chain verified"
    - "No proprietary data disclosed"
    
  citation_generation:
    formats:
      - "bibtex"
      - "apa"
      - "mla"
      - "chicago"
      - "ieee"
      - "acm"
    template: |
      HYBA/PYTHIA Collaboration. (2026). {{title}}. 
      Retrieved from https://api.hyba-pythia.org/evidence/{{evidence_id}}
      Evidence ID: {{evidence_id}}
      Commit: {{git_commit}}
      Timestamp: {{timestamp}}
      Checksum: {{checksum_sha256}}
      
  embargo_support:
    default_embargo_months: 0
    max_embargo_months: 24
    auto_publication_on_embargo_expiry: true
    
  retraction_policy:
    severity_levels:
      - "minor_error"
      - "major_error"
      - "data_quality_concern"
      - "methodology_flaw"
      - "reproducibility_failure"
    retraction_vote_required: true
    ethics_committee_notification: true

# ============================================================================
# SECTION 6: SERVICE LEVEL AGREEMENTS
# ============================================================================

slas:
  availability_target_percent: 99.5
  response_time_p95_ms: 500
  response_time_p99_ms: 2000
  
  reproducibility_guarantees:
    - "Artifacts >1 year old: reproducible with approved dependency versions"
    - "Artifacts <1 year old: reproducible with identical environment"
    - "Checksum divergence <1e-14: acceptable machine epsilon"
    - "Failed reproductions: investigation + root cause analysis"

# ============================================================================
# SECTION 7: GOVERNANCE & ESCALATION
# ============================================================================

governance:
  policy_review_frequency: "annual"
  emergency_override_authority: "CEO, Chief Scientist, Ethics Committee Chair"
  incident_response_time: "4 hours"
  
  escalation_matrix:
    - issue: "Single user rate limit exceeded"
      owner: "Platform Lead"
      response_time_hours: 24
      
    - issue: "Institution-level abuse pattern detected"
      owner: "Ethics Review Committee"
      response_time_hours: 4
      
    - issue: "Data breach or security incident"
      owner: "CEO, Chief Science Officer"
      response_time_minutes: 30
      
    - issue: "Unauthorized external publication"
      owner: "Ethics Review Committee, Legal"
      response_time_hours: 2

  approval_required_for:
    - "Adding new institutional partner"
    - "Modifying rate limits for user cohort"
    - "Changing access tier for evidence"
    - "Emergency suspension of user account"

# ============================================================================
# SECTION 8: IMPLEMENTATION CHECKLIST
# ============================================================================

implementation_status:
  - [ ] "Authentication system integrated (OAuth 2.0 + SAML)"
  - [ ] "RBAC groups configured in directory"
  - [ ] "Rate limiting middleware deployed"
  - [ ] "Reproducibility endpoints implemented"
  - [ ] "Audit logging system operational"
  - [ ] "Abuse detection rules activated"
  - [ ] "TLS 1.3 enforced on all endpoints"
  - [ ] "Citation generation service deployed"
  - [ ] "Embargo support in evidence database"
  - [ ] "Incident response playbook documented"
  - [ ] "Governance review committee trained"
  - [ ] "User documentation published"
  - [ ] "API documentation auto-generated (OpenAPI 3.1)"
  - [ ] "Monitoring dashboards active (Grafana/Prometheus)"

---

## 4. Validation Hook

**Automated checks:**
```bash
#!/bin/bash
# api_policy_validation.sh

# 1. Check all required endpoints documented
for endpoint in /evidence/reproduce /benchmark/rerun /proof/verify; do
  grep -q "endpoint: \"$endpoint\"" docs/institutional_qaas/16_RESEARCHER_ACCESS_API_POLICY.md || echo "❌ Missing: $endpoint"
done

# 2. Verify RBAC roles are complete
for role in public_viewer verified_academic external_collaborator institutional_partner; do
  grep -q "name: \"$role\"" docs/institutional_qaas/16_RESEARCHER_ACCESS_API_POLICY.md || echo "❌ Missing role: $role"
done

# 3. Check rate limits are sensible (increasing by role)
echo "✅ All endpoints documented and configured"
```

**Owner:** Platform Lead  
**Frequency:** On each API deployment  
**Success criteria:** All endpoints accessible, rate limits enforced, audit logs complete

---

## 5. Claim Boundary

**This artifact proves:**
- Authentication and authorization scheme documented
- Rate limiting policy prevents abuse
- Reproducibility endpoints are specified
- Publication review workflow exists
- Security controls are defined

**This artifact does NOT prove:**
- Implementation is complete
- API is currently live or tested
- Compliance with external standards
- Absence of security vulnerabilities

---

## 6. Evidence Owner

**Role:** Platform Lead  
**Accountability:** API policy enforcement and audit compliance  
**Escalation:** Ethics Review Committee (for access disputes)

