# Mathematical Archive Protocol
**Status:** Gap governance.knowledge → CLOSED ✅

---

## Versioned Proofs

### Structure
```
Location: /proofs/

Per theorem:
  v1.0/
    ├─ statement.lean (Lean 4 formalization)
    ├─ proof.lean (proof code)
    ├─ comment.md (intuition for humans)
    ├─ metadata.json (dependencies, axioms)
    └─ hash.txt (immutable checksum)
```

### Example: PULVINI Losslessness Theorem
```
proofs/pulvini_losslessness/
├─ v1.0/
│  ├─ statement.lean
│  ├─ proof.lean
│  ├─ comment.md ("Lossless compression via φ-folding...")
│  ├─ metadata.json ({"depends_on": ["linear_algebra"], ...})
│  └─ hash.txt (sha256: abc123...)
├─ v1.1/
│  └─ (revised after peer review)
├─ v2.0/
│  └─ (with formal verification completed)
└─ DOI: 10.xxxx/hyba.proofs.pulvini.v2.0
```

---

## DOI Registration

### Process
```
1. Complete proof + peer review
2. Submit to Zenodo (open science archive)
3. Zenodo assigns DOI (permanent)
4. DOI resolves to proof forever (even if hyba.io goes down)

Example DOI:
  10.5281/zenodo.10123456
  Resolves to: https://zenodo.org/record/10123456
  Citable as: "HYBA Proofs v2.0 (2026) DOI:10.5281/zenodo.10123456"
```

---

## Retention Policy

### How Long?
```
Proofs:       Forever (open source, non-commercial)
Code:         Forever (GitHub + Zenodo mirrors)
Evidence:     10+ years (industry standard)
Metadata:     Forever (small file size)
```

### Access
```
Current: https://github.com/hybaanalytics1/HYBA_FULLSTACK
Archive: https://zenodo.org/communities/hyba-mathematics
Backup:  Internet Archive (Wayback Machine)
```

### If HYBA Goes Offline
```
Scenario: HYBA company dissolves
Resolution: Proofs already in Zenodo (permanent)
Access: DOI links live forever
Impact: Science preserved, company gone
```

---

## Artifact Types

### Type 1: Mathematical Proofs
```
Format: Lean 4 or Coq code
Access: Public (open science)
Citation: By DOI
Example: PULVINI losslessness proof
```

### Type 2: Experimental Evidence
```
Format: Reproducible code + data
Access: Public (containerized)
Citation: By GitHub commit hash
Example: φ-resonance validation dataset
```

### Type 3: Benchmark Results
```
Format: JSON metadata + CSV data
Access: Public (standardization)
Citation: By timestamp + git commit
Example: Compression ratio benchmarks
```

---

**Gap:** governance.knowledge  
**Status:** ✅ CLOSED

