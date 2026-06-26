# GitHub Secrets - Create These 5 Now

**Repository:** `hybaintelligence/HYBA`  
**Location:** Settings → Secrets and Variables → Actions → New repository secret

---

## 5 Secrets to Create

### 1. JWT_SECRET
```
Name:  JWT_SECRET
Value: T-HjQLuo5vC_FDIsH2WnlmrjCydl1n63x_2AwLxqeU8
```

### 2. HYBA_OPERATOR_CREDENTIALS
```
Name:  HYBA_OPERATOR_CREDENTIALS
Value: operator:$argon2id$v=19$m=65536,t=3,p=4$evdwh5nzDeODqYfk51XwmA$cbGUMInUbNVnDLJ+h9unojYBVyl7mctrgqJTvCe/mI4:mining_operator
```

### 3. HYBA_POOL_VIABTC_URL
```
Name:  HYBA_POOL_VIABTC_URL
Value: stratum+ssl://btc.viabtc.io:3333
```

### 4. HYBA_POOL_VIABTC_USERNAME
```
Name:  HYBA_POOL_VIABTC_USERNAME
Value: PYTHIA.001
```

### 5. HYBA_POOL_VIABTC_PASSWORD
```
Name:  HYBA_POOL_VIABTC_PASSWORD
Value: 123
```

---

## Verify Existing Secrets

Confirm these are already set:
- ✓ DOCKERHUB_USERNAME
- ✓ DOCKERHUB_TOKEN
- ✓ DOCKERHUB_REPOSITORY (optional)

---

## After Creating Secrets

```bash
git push origin main
```

All workflows will trigger automatically and deploy using Docker Build Cloud.
