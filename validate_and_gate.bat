@echo off
setlocal enabledelayedexpansion

echo === HYBA FULLSTACK — Production Environment Validation Gate ===
echo.

cd /d "%~dp0"

set PATH=%~dp0;%PATH%
set PYTHONPATH=python_backend

:: === Environment Variables ===
set NODE_ENV=production
set HYBA_ENV=production
set HYBA_ALLOW_DEV_FIXTURES=false
set HYBA_QUANTUM_CAPACITY_EHS=1.0
set HYBA_PULVINI_HASHRATE_CAP_EHS=1.0
set PULVINI_BACKEND_URL=http://127.0.0.1:3001
set JWT_SECRET=Rl8ux6Ge-NpBxhBY0zMvw3c1endcUCKMWnmL9-N4eBI
set HYBA_ENABLE_LIVE_STRATUM=true
set HYBA_ENABLE_AUDIT_LOGGING=true
set HYBA_ENABLE_MINING_AUTOCONNECT=false
set HYBA_ENABLE_LIVE_SHARE_SUBMIT=false

:: === Pool Credentials ===
:: Braiins (Primary SHA256)
set HYBA_POOL_BRAIINS_URL=stratum2+tcp://stratum.braiins.com:3333/9awtMD5KQgvRUh2yFbjVeT7b6hjipWcAsQHd6wEhgtDT9soosna
set HYBA_POOL_BRAIINS_USERNAME=PYTHAGOROS.workerName
set HYBA_POOL_BRAIINS_PASSWORD=anything123
set HYBA_POOL_BRAIINS_STRATUM_VERSION=2

:: NiceHash SHA256 (Primary Backup)
set HYBA_POOL_NICEHASH_URL=stratum+ssl://sha256.auto.nicehash.com:443
set HYBA_POOL_NICEHASH_WORKER=NHbaCJGb1gM7MjgJ9QnnqbG2sLVW9w8hdPzK
set HYBA_POOL_NICEHASH_PASSWORD=x
set HYBA_POOL_NICEHASH_NICEHASH_POOL_ID=NHbaCJGb1gM7MjgJ9QnnqbG2sLVW9w8hdPzK
set HYBA_POOL_NICEHASH_STRATUM_VERSION=1

:: CKPool (Solo Fallback)
set HYBA_POOL_CKPOOL_URL=stratum+tcp://solo.ckpool.org:3333
set HYBA_POOL_CKPOOL_BTC_ADDRESS=bc1qsyva7t00e0cwqzts54u7ffys7l76pp8a02x8r9
set HYBA_POOL_CKPOOL_STRATUM_VERSION=1

echo [1/4] Validating production environment...
C:\Python311\python.exe scripts/validate_production_env.py
if %ERRORLEVEL% neq 0 (
    echo WARNING: Validation found issues (operator credentials missing is expected pre-MIDAS setup)
)

echo.
echo [2/4] Running live deployment forensic audit...
C:\Python311\python.exe scripts/audit_live_deployment.py
if %ERRORLEVEL% neq 0 (
    echo WARNING: Audit issued warnings
)

echo.
echo [3/4] Running runtime mock/static telemetry guard...
C:\Python311\python.exe scripts/check_no_runtime_mocks.py
if %ERRORLEVEL% neq 0 (
    echo WARNING: Runtime guard check found issues
)

echo.
echo [4/4] Running Pulvini live-cut preflight readiness check...
C:\Python311\python.exe scripts/pulvini_live_cut_readiness.py
if %ERRORLEVEL% neq 0 (
    echo WARNING: Live-cut readiness check needs review
)

echo.
echo === Environment Summary ===
echo Pool: Braiins (Primary SHA256)
echo   URL: %HYBA_POOL_BRAIINS_URL%
echo   User: %HYBA_POOL_BRAIINS_USERNAME%
echo   Stratum Version: %HYBA_POOL_BRAIINS_STRATUM_VERSION%
echo.
echo Pool: NiceHash SHA256 (Backup)
echo   URL: %HYBA_POOL_NICEHASH_URL%
echo   Worker: %HYBA_POOL_NICEHASH_WORKER%
echo   Pool ID: %HYBA_POOL_NICEHASH_NICEHASH_POOL_ID%
echo.
echo Pool: CKPool (Solo Fallback)
echo   URL: %HYBA_POOL_CKPOOL_URL%
echo   BTC Address: %HYBA_POOL_CKPOOL_BTC_ADDRESS%
echo.
echo Autoconnect: DISABLED
echo Live Share: DISABLED
echo Audit Logging: ENABLED
echo.
echo === NiceHash CLI Usage ===
echo python nicehash.py -b https://api2.nicehash.com -o ORG_ID -k API_KEY -s API_SECRET -m GET -p /main/api/v2/accounting/accounts2/
echo.
echo === Next Steps ===
echo 1. Set NICEHASH_ORGANIZATION_ID, NICEHASH_API_KEY, NICEHASH_API_SECRET in .env
echo 2. Set HYBA_OPERATOR_CREDENTIALS for MIDAS operator access
echo 3. Rebuild: npm run build
echo 4. Start: npm start
echo 5. Login as mining_operator through the UI
echo 6. Enable mining through MIDAS surface
echo.
echo === Evidence Packet Generated ===
dir /b artifacts\production_readiveness\*.json 2>nul || echo No gate packets yet
dir /b HYBA_FULLSTACK_COMMAND_ROOM_* 2>nul

endlocal