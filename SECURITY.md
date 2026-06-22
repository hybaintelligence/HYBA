# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Salamander team takes security seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to **security@salamander.yourorg.com** or through our [vulnerability disclosure program](https://yourorg.com/security).

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include as much of the following information as possible:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Security Features

### Cryptographic Audit Trail

All regeneration events are cryptographically signed using HMAC-SHA256:

```python
import hmac
import hashlib
import json

def sign_regeneration_event(event_id, pending_event, result):
    secret_key = "salamander_regeneration_secret_key_change_in_production"
    payload = {
        "event_id": event_id,
        "module_id": pending_event.get("module_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result_status": result.get("status"),
    }
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret_key.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature
```

**Production Recommendation**: Use a proper key management system (AWS KMS, HashiCorp Vault, etc.) instead of hardcoded secrets.

### Rate Limiting

AI-triggered regenerations are rate-limited to prevent runaway behavior:

- **Limit**: 5 regenerations per 60 seconds per module
- **Enforcement**: Server-side token bucket algorithm
- **Response**: HTTP 429 with `Retry-After` header

### Approval Workflows

Sensitive operations require human approval:

- **Sensitive Paths**: Security, auth, payment, config, credentials, keys, secrets
- **High Impact**: Impact score > 0.8
- **Critical Modules**: Core infrastructure components

### Immutable Audit Logs

All regeneration events are logged to an append-only log:

- **Retention**: 7 years (configurable)
- **Immutability**: Cryptographic chaining (each event signed with previous event's hash)
- **Accessibility**: CEO Terminal, API, export to SIEM

## Security Best Practices

### For Users

1. **API Key Management**
   - Rotate API keys regularly (every 90 days)
   - Use different keys for development/staging/production
   - Never commit API keys to version control
   - Use environment variables or secret management systems

2. **Network Security**
   - Deploy behind VPN or private network
   - Use TLS/SSL for all API communications
   - Configure firewall rules to restrict access
   - Enable WebSocket authentication

3. **Access Control**
   - Implement least-privilege access
   - Use role-based access control (RBAC)
   - Regularly audit access logs
   - Enable multi-factor authentication (MFA)

4. **Monitoring**
   - Enable real-time monitoring via CEO Terminal
   - Set up alerts for suspicious regeneration patterns
   - Review audit logs regularly
   - Monitor rate limit violations

### For Developers

1. **Secure Coding**
   - Validate all inputs (Pydantic models)
   - Use parameterized queries (no SQL injection)
   - Sanitize outputs (prevent XSS)
   - Handle errors securely (no information leakage)

2. **Dependency Management**
   - Regularly update dependencies (Dependabot)
   - Scan for vulnerabilities (Snyk, safety)
   - Use pinned versions in production
   - Review dependency licenses

3. **Cryptography**
   - Use established libraries (cryptography, PyJWT)
   - Never roll your own crypto
   - Use secure random number generators
   - Implement proper key rotation

4. **Testing**
   - Write security-focused unit tests
   - Conduct regular penetration testing
   - Perform code reviews (security checklist)
   - Use static analysis tools (Bandit, Semgrep)

## Known Limitations

1. **Quantum Hardware**: The quantum-inspired formalism runs on classical hardware. No quantum speedup is claimed except for explicitly marked functions requiring quantum hardware.

2. **PPT Criterion**: Positive partial transpose does not prove separability for DIM > 2×3. This is a documented limitation of the separability test.

3. **Context Signal Dependency**: Without positional memory (Clifford index), regeneration fails with InnervationFailure. Ensure context signals are properly maintained.

4. **Rate Limits**: Default rate limits may need adjustment for high-throughput environments. Monitor and tune as needed.

## Compliance

### SOC 2 Type II

- **Security**: Cryptographic audit trails, access controls, encryption
- **Availability**: 99.9% uptime SLA, disaster recovery
- **Processing Integrity**: Verification suite, rollback tracking
- **Confidentiality**: Data encryption, access logging
- **Privacy**: Data minimization, retention policies

### ISO 27001

- **A.9 Access Control**: Role-based access, API key management
- **A.12 Operations Security**: Logging, monitoring, incident management
- **A.14 System Acquisition**: Secure development lifecycle
- **A.15 Supplier Relationships**: Third-party security assessments
- **A.16 Incident Management**: Vulnerability disclosure, breach response

### NIST Cybersecurity Framework

- **Identify**: Asset management, risk assessment
- **Protect**: Access control, encryption, maintenance
- **Detect**: Anomalies, continuous monitoring
- **Respond**: Response planning, communications
- **Recover**: Recovery planning, improvements

## Security Contacts

- **Security Team**: security@salamander.yourorg.com
- **PGP Key**: [Download from keyserver](https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xSECURITY_KEY)
- **Vulnerability Disclosure**: https://yourorg.com/security/disclosure
- **Security Status**: https://status.salamander.yourorg.com

## Acknowledgments

We thank the following security researchers for their responsible disclosures:

- [List of security researchers]

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/r5/upd-1/final)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [SANS Secure Coding Practices](https://www.sans.org/white-papers/33901/)

---

**Last Updated**: 2026-06-22  
**Next Review**: 2026-07-22  
**Owner**: Security Team