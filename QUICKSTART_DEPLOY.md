# HYBA Frontend: Quick Deploy

## 1. Set Secrets (Required)
```bash
export JWT_SECRET="$(openssl rand -base64 32)"
export HYBA_API_KEY_SECRET="$(openssl rand -base64 32)"
export HYBA_CORS_ORIGINS="https://yourdomain.com"
```

## 2. Customer Mode (Production)
```bash
export HYBA_CUSTOMER_MODE=true
export HYBA_INTERNAL_MODE=false
export NODE_ENV=production
```

## 3. Deploy
```bash
./scripts/production_deploy.sh
npm run start
```

## 4. Verify
```bash
curl http://localhost:3000/api/health
```

**Done. Mathematics speaks.**
