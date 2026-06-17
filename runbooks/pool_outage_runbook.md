# Runbook: Mining Pool Outage

## Overview

This runbook describes the steps to diagnose and remediate a mining pool outage affecting HYBA_FULLSTACK.  It assumes that mining is currently configured with primary and secondary pool profiles (e.g., ViaBTC, NiceHash) via environment variables.

- **Service/component:** Mining subsystem (Stratum layer)
- **Responsible team:** Backend/DevOps
- **Runbook owner:** On‑call engineer
- **Related dashboards:** Mining pool connection dashboard, hashrate dashboards, error logs

## Purpose

To ensure continuous mining operations by failing over to backup pools and restoring connectivity when the primary mining pool is unavailable.

## Preconditions

- Valid credentials for configured pools are stored in the secret manager.
- Backup pools are enabled in environment variables (e.g., `HYBA_POOL_VIABTC`, `HYBA_POOL_NICEHASH`).
- On‑call engineer has SSH access to mining nodes or container runtime.

## Detection

- Alerts triggered by loss of accepted shares or a sudden drop in hashrate.
- Error logs indicating failed Stratum connections (e.g., connection refused, timeout).
- `/api/mining/status` reports pool connection errors or an empty job queue.

## Immediate actions

1. **Verify alert**
   - Confirm that the hashrate drop is not due to scheduled maintenance or reduced autonomy settings.
   - Check public status pages of the mining pool for outages.

2. **Fail over to backup pool**
   - If the `HYBA_ENABLE_LIVE_STRATUM` feature is enabled, ensure that the mining controller has automatically switched to the secondary pool.
   - If automatic failover is disabled, manually update environment variables or configuration to point to the backup pool and restart the mining service:
     ```bash
     export HYBA_POOL_PRIMARY_URL="$HYBA_POOL_NICEHASH_URL"
     export HYBA_POOL_PRIMARY_USERNAME="$HYBA_POOL_NICEHASH_WORKER"
     export HYBA_POOL_PRIMARY_PASSWORD="$HYBA_POOL_NICEHASH_PASSWORD"
     docker-compose restart hyba-miner
     ```
   - Monitor `/api/mining/status` and logs to confirm successful reconnection.

3. **Communicate**
   - Notify stakeholders (operations channel, product team) about the failover.
   - Document the incident start time and actions taken.

## Detailed remediation steps

1. **Gather logs**
   - Fetch the last 100 lines of the mining service logs:
     ```bash
     docker-compose logs --tail=100 hyba-miner
     ```
   - Capture any stack traces or error messages.

2. **Verify configuration**
   - Check that environment variables for the pool are correctly set and not expired.
   - Ensure the DNS resolution for the pool hostname is working:
     ```bash
     dig +short btc.viabtc.com
     ```

3. **Test connectivity**
   - From inside the miner container, test TCP connectivity to the pool:
     ```bash
     docker exec -it hyba-miner /bin/bash -c "nc -vz $HYBA_POOL_PRIMARY_HOST $HYBA_POOL_PRIMARY_PORT"
     ```
   - If connection fails, the issue is likely upstream; continue using backup pools.

4. **Monitor after failover**
   - Monitor accepted share rate and hashrate for at least 30 minutes to ensure stability.
   - If the backup pool also fails, pause mining until further notice to avoid wasted energy.

## Post‑incident actions

- **Root cause analysis** – Investigate the primary pool outage once resolved.  Determine whether the issue was with the pool, network routing, or local configuration.
- **Update failover logic** – If the failover did not occur automatically, improve the mining controller to detect outages and switch pools gracefully.
- **Review runbook** – Update this runbook with lessons learned and ensure that environment variables and backup pools are correctly configured.
- **Communicate resolution** – Send a summary of the incident, its impact, and the remediation steps to stakeholders.

## Contacts

- **Primary on‑call engineer:** On‑call rotation (e.g., oncall@hyba.ai)
- **Escalation:** DevOps lead (e.g., devops-lead@hyba.ai)
- **Pool provider support:** Contact channels for ViaBTC, NiceHash, etc.
