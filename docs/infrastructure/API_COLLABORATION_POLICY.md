# Researcher Access API Policy
**Status:** Gap infrastructure.collaboration → CLOSED ✅

---

## Authentication Model

### API Key Authentication
```
Method: HMAC-SHA256 signing
Key format: Bearer token (HTTPS required)
Rate limit: Tier-dependent
Rotation: Annually (or on-demand)
Revocation: Immediate + audit logged
```

### Token Lifecycle
```
Generated:   Random 256-bit key
Hashed:      HMAC-SHA256 (plaintext never stored)
Displayed:   Once on creation
Rotated:     Annually
Revoked:     Immediately on user request
Logged:      Every API call with hashed key
```

---

## Rate Limits

### Starter Tier
```
Requests:    100/hour
Concurrent:  1 connection
Burst:       10 requests/second
Timeout:     30 seconds
```

### Professional Tier
```
Requests:    10,000/hour
Concurrent:  10 connections
Burst:       100 requests/second
Timeout:     60 seconds
```

### Enterprise Tier
```
Requests:    Unlimited (negotiated)
Concurrent:  50+ (custom)
Burst:       Custom
Timeout:     Custom
```

---

## Reproducibility Endpoints

### GET /api/v1/evidence/proof/{id}
```
Returns:     Full proof code (Lean/Coq)
Format:      JSON + raw source
Reproducible: Fresh-clone deterministic
Example:
  GET /api/v1/evidence/proof/pulvini-losslessness-v2.0
  Response: {"code": "...", "hash": "abc123...", "doi": "10.5281/zenodo/..."}
```

### POST /api/v1/evidence/validate
```
Request:     Proof code + claim
Validates:   Against canonical version
Returns:     Checksum match + metadata
Example:
  POST /api/v1/evidence/validate
  Body: {"proof": "...", "claim": "PULVINI_Losslessness"}
  Response: {"valid": true, "hash_match": true}
```

### GET /api/v1/evidence/manifest
```
Returns:     Full evidence manifest
Filters:     By date, author, version
Format:      JSON array
Example:
  GET /api/v1/evidence/manifest?from=2026-06-01&to=2026-06-30
  Response: [{"id": "...", "doi": "...", ...}]
```

---

## Publication Workflow

### Step 1: Research
```
Researcher conducts experiment on HYBA
Logs results automatically to evidence store
```

### Step 2: Review
```
Call: GET /api/v1/evidence/proof/{id}
Peer reviews code + methodology
```

### Step 3: Publish
```
Call: POST /api/v1/evidence/publish
  Body: {"claim": "...", "evidence": "...", "journal": "..."}
Generates: DOI + citation metadata
```

### Step 4: Archive
```
Published evidence auto-archived to Zenodo
DOI resolves forever (even if HYBA shuts down)
```

---

**Gap:** infrastructure.collaboration  
**Status:** ✅ CLOSED

