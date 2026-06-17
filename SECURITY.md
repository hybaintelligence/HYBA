# Security Policy

## Supported Versions

We maintain security updates for the latest major version of HYBA_FULLSTACK.  Older versions are not actively maintained.  Refer to the repository for the current version number.

## Reporting a Vulnerability

If you discover a security vulnerability in this repository, please contact the security team privately so we can coordinate a fix before public disclosure.  You can reach us via:

- Email: security@hyba.ai  
- GitHub Security Advisory: https://github.com/hybaanalytics1/HYBA_FULLSTACK/security/advisories/new

Please include a description of the vulnerability, reproduction steps, and potential impact.  We respond to reports within 3 business days.

## Security Best Practices

To help ensure a secure deployment of HYBA_FULLSTACK:

- **Use secret managers** (e.g., HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager) to manage secrets such as JWT keys, Argon2id operator credentials, and pool passwords.  Do not commit secrets to the repository.
- **Rotate secrets regularly** and enforce strong passwords.  Minimum secret length should be 32 bytes.
- **Enable dependency scanning** (e.g., GitHub Dependabot, pip‑audit, npm audit) and remediate critical vulnerabilities promptly.
- **Run static analysis** (e.g., bandit, mypy, eslint) as part of CI to detect common security issues.
- **Restrict access** to sensitive endpoints through authentication and role‑based authorization.  Ensure tokens include expiration and issuer claims.
- **Use TLS** for all network communication, including connections to mining pools (Stratum v1/v2) and database services.
- **Protect against injection attacks** by validating and sanitizing all user input.  Use parameterized SQL queries; avoid string concatenation for queries.
- **Monitor logs** and alert on suspicious activity, such as repeated failed login attempts or unexpected API usage patterns.

## Responsible Disclosure

We follow a coordinated disclosure process and appreciate your help in making this project more secure.  Publicly disclosing vulnerabilities without coordination could put downstream users at risk.
