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

## Secrets Management

### Never Commit Secrets to Version Control

The following must never be committed to the repository:
- Production credentials files (e.g., `config/production_credentials.env`, `config/production_credentials_static.env`)
- JWT secrets and API keys
- Database connection strings with passwords
- Mining pool passwords and authentication tokens
- Private keys (SSH, TLS certificates, etc.)
- Firebase configuration files with API keys

These files are already excluded in `.gitignore`. If secrets have been accidentally committed, they must be removed from git history using `git filter-repo` or equivalent tools.

### Recommended Secret Management Approach

1. **Use a secrets manager for production:**
   - HashiCorp Vault: Industry-standard with dynamic secrets and encryption
   - AWS Secrets Manager: Integrated with AWS services
   - GCP Secret Manager: Integrated with Google Cloud
   - Azure Key Vault: Integrated with Azure services

2. **Local development:**
   - Use `.env.local` files (already in `.gitignore`)
   - Reference `config/mining.pools.example.env` as a template
   - Never commit `.env.local` or similar files

3. **CI/CD pipelines:**
   - Inject secrets at runtime using environment variables
   - Use GitHub Secrets, GitLab CI/CD variables, or equivalent
   - Never log secrets in build output

4. **Secret rotation:**
   - Rotate JWT secrets quarterly or after any suspected compromise
   - Rotate pool passwords monthly or after personnel changes
   - Use automated rotation where possible (e.g., AWS Secrets Manager auto-rotation)

### Credential File Permissions

Production credential files must have restricted permissions:
```bash
chmod 600 config/production_credentials.env
chmod 600 config/production_credentials_static.env
```

### Audit Secrets Regularly

Run periodic audits to ensure no secrets have been accidentally committed:
```bash
# Scan git history for potential secrets
git log --all --full-history --source -- "**/production_credentials.env"
git log --all --full-history --source -- "**/*.pem"
git log --all --full-history --source -- "**/*.key"

# Use tools like truffleHog or git-secrets for automated scanning
```

## Responsible Disclosure

We follow a coordinated disclosure process and appreciate your help in making this project more secure.  Publicly disclosing vulnerabilities without coordination could put downstream users at risk.
