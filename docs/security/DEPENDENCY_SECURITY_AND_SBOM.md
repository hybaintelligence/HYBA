# HYBA Dependency Security and SBOM Policy

**Scope:** JavaScript, TypeScript, Python, Docker, and local deployment dependencies.

## Local-First Security Commands

```bash
npm audit --omit=dev
pip-audit -r requirements.txt
python scripts/run_local_security_scan.py
```

`pip-audit` is optional tooling; if it is not installed, the local security scan transcript records the skip. Install it locally for full Python dependency coverage:

```bash
python -m pip install pip-audit
```

## SBOM Baseline

Generate and store SBOM evidence outside source commits unless explicitly approved:

```bash
# JavaScript SBOM, when CycloneDX is installed
npx @cyclonedx/cyclonedx-npm --output-file runtime/evidence/sbom/npm-sbom.json

# Python SBOM, when pip-audit is installed
pip-audit -r requirements.txt -f cyclonedx-json -o runtime/evidence/sbom/python-sbom.json
```

## Policy

1. Production deployments require a fresh local security transcript.
2. Dependency warnings must be classified as exploitable, non-exploitable, or accepted risk.
3. Accepted risk requires a short written reason and expiry date.
4. Do not commit generated SBOMs if they contain local file paths or environment-specific metadata.
5. Do not pin to floating major versions for production-critical dependencies.
6. Do not bypass the dependency gate by claiming GitHub Actions or hosted CI is unavailable; local transcript is the source of truth.

## Remediation Priority

- Critical/high exploitable vulnerabilities: fix before production deployment.
- Medium vulnerabilities: fix before scale-up or document accepted risk.
- Low vulnerabilities: batch during maintenance unless they affect auth, crypto, HTTP parsing, database drivers, or build tooling.
