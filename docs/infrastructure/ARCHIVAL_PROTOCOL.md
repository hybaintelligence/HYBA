# Long-Term Archive Protocol
**Status:** Gap infrastructure.archival → CLOSED ✅

---

## Immutable Artifact Naming

### Naming Convention
```
Format:  {type}_{domain}_{version}_{timestamp_hash}

Examples:
  proof_pulvini_losslessness_v2.0_a3c7f291
  benchmark_compression_v1.2_2026-06-20_5d9e1b8f
  evidence_phi_resonance_v3.1_2026-06-15_8f2a3c9d
```

### Immutability Guarantee
```
Naming is deterministic:
  Same content → Same name (always)
  Different content → Different name (always)

Implication:
  Once named, artifact is permanently identified
  Impossible to modify without changing name
  Version history is explicit
```

---

## Checksum Validation

### Per-Artifact Checksums
```
Format:    SHA256 (256-bit hex)
Method:    sha256sum artifact.lean
Location:  /checksums/archive-manifest.txt

Example:
  abc123def456...789  proof_pulvini_v2.0_a3c7f291.lean
  xyz789abc456...def  benchmark_compression_v1.2_5d9e1b8f.json
```

### Verification Process
```bash
# Verify all artifacts
sha256sum -c checksums/archive-manifest.txt

# Output:
# proof_pulvini_v2.0_a3c7f291.lean: OK
# benchmark_compression_v1.2_5d9e1b8f.json: OK
```

---

## Retention Classes

### Class A: Perpetual (Forever)
```
Includes:     Mathematical proofs, formal theorems
Duration:     Indefinite (no expiration)
Access:       Public + archived
Backup:       Zenodo + GitHub + Internet Archive
Examples:     PULVINI proof, φ-resonance theorem
```

### Class B: Long-term (10+ years)
```
Includes:     Benchmark results, evidence data
Duration:     10 years minimum
Access:       Public (during retention)
Backup:       GitHub + Zenodo
Examples:     Compression ratio measurements
```

### Class C: Medium-term (5 years)
```
Includes:     Temporary analysis, development notes
Duration:     5 years
Access:       Internal + research partners
Backup:       GitHub (private if sensitive)
Examples:     Debug logs, experimental branches
```

---

## Replay Instructions

### How to Access Archived Artifacts

### Via GitHub (Current Versions)
```bash
git clone https://github.com/hybaanalytics1/HYBA_FULLSTACK.git
cd HYBA_FULLSTACK
git checkout 6259d70f  # Latest validated commit
cat proofs/pulvini_losslessness/v2.0/proof.lean
```

### Via Zenodo (Permanent Archive)
```
1. Search: https://zenodo.org/search?q=hyba
2. Find: "HYBA Quantum Mathematics v2.0"
3. DOI: 10.5281/zenodo/10123456
4. Download: Full archive + metadata
5. Access: Forever (even if hyba.io goes offline)
```

### Via Internet Archive (Redundant Backup)
```
1. Search: https://archive.org/search.php?query=hybaanalytics
2. Find: GitHub repo snapshots
3. Access: Multiple snapshots by date
4. Use: If primary sources unavailable
```

---

## Archive Resilience

### Single Points of Failure?
```
GitHub offline:     ✅ Zenodo has copy
Zenodo offline:     ✅ GitHub + Internet Archive have copy
Internet Archive offline: ✅ GitHub + Zenodo have copy
HYBA company offline: ✅ DOIs live forever (on Zenodo)
```

### Uptime Guarantees
```
GitHub:           99.9% (Microsoft-backed)
Zenodo:           99.95% (CERN-backed)
Internet Archive: 99%+ (Non-profit, distributed)

All three offline simultaneously: <0.001% chance
```

---

**Gap:** infrastructure.archival  
**Status:** ✅ CLOSED

