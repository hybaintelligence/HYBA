# Secrets Management

Production deployments of HYBA_FULLSTACK require sensitive secrets such as JWT signing keys, database credentials, operator passphrases and pool passwords. Secrets MUST NOT be committed to the repository or stored in plain text configuration files. This document outlines recommended patterns for managing secrets securely in different environments.

## Principles

- **Use a secret manager:** Leverage managed secret stores (e.g. AWS Secrets Manager, Hashicorp Vault, Google Secret Manager) to store and version secrets. Retrieve them at runtime via API or environment injection.
- **Environment variables only:** The application reads secrets from environment variables (`JWT_SECRET`, `POSTGRES_PASSWORD`, `POOL_PASSWORDS`, etc.). Avoid hard‑coding secrets in code or `.env` files checked into source control.
- **Least privilege:** Scope secrets per environment (development, staging, production) and restrict access to only the services that need them.
- **Rotation and auditing:** Rotate credentials regularly and enable auditing on secret access events.

## Implementation guidelines

### Kubernetes / container platforms

1. **Define Kubernetes Secrets or platform‑specific secret resources** holding the following keys (non‑exhaustive):
   - `JWT_SECRET`: strong, random key used for signing JWT tokens.
   - `POSTGRES_USER` / `POSTGRES_PASSWORD`: database credentials.
   - `HYBA_POOL_CONFIG_PATH`: path to encrypted pool configuration files if applicable.
   - `OPERATOR_CREDENTIALS`: Argon2id‑hashed operator username/password for console login.

2. **Mount secrets as environment variables** by referencing them in the pod spec. The FastAPI backend will read them at startup.

3. **Restrict RBAC** so that only the API deployment has permission to read its secrets.

### Docker Compose

For local containerised deployments, store secrets in an `.env.docker` file that is not committed to git. Use `docker-compose --env-file .env.docker` to supply values. Alternatively, use Docker secrets (`./secrets/<name>`) and configure the compose file accordingly.

### Local development

For developers working on non‑production environments, sample `.env.example` and `.env.production.example` files illustrate the required variables. Developers should create their own `.env` files outside of version control and may override credentials with dummy values.

Follow these practices to ensure secrets remain confidential and production deployments remain secure.
