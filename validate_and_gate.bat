@echo off
setlocal enabledelayedexpansion

echo === HYBA FULLSTACK — Production Environment Validation Gate ===
echo.

cd /d "%~dp0"
set "PATH=%~dp0;%PATH%"
set "PYTHONPATH=python_backend"

:: Safe production defaults only. Secrets, operator credentials, and pool
:: credentials must be injected by .env, sealed local environment, or secret
:: manager before this gate is run. This file must never contain live secrets.
if not defined NODE_ENV set "NODE_ENV=production"
if not defined HYBA_ENV set "HYBA_ENV=production"
if not defined HYBA_ALLOW_DEV_FIXTURES set "HYBA_ALLOW_DEV_FIXTURES=false"
if not defined HYBA_QUANTUM_CAPACITY_EHS set "HYBA_QUANTUM_CAPACITY_EHS=1.0"
if not defined HYBA_PULVINI_HASHRATE_CAP_EHS set "HYBA_PULVINI_HASHRATE_CAP_EHS=1.0"
if not defined PULVINI_BACKEND_URL set "PULVINI_BACKEND_URL=http://127.0.0.1:3001"
if not defined HYBA_ENABLE_LIVE_STRATUM set "HYBA_ENABLE_LIVE_STRATUM=true"
if not defined HYBA_ENABLE_AUDIT_LOGGING set "HYBA_ENABLE_AUDIT_LOGGING=true"
if not defined HYBA_ENABLE_MINING_AUTOCONNECT set "HYBA_ENABLE_MINING_AUTOCONNECT=false"
if not defined HYBA_ENABLE_LIVE_SHARE_SUBMIT set "HYBA_ENABLE_LIVE_SHARE_SUBMIT=false"

echo Required injected values before live deployment:
echo   JWT_SECRET, HYBA_OPERATOR_CREDENTIALS, and at least one HYBA_POOL_* profile.
echo   Live share submission additionally requires HYBA_LIVE_SHARE_APPROVAL_ID.
echo.

echo [1/4] Validating production environment...
call npm run prod:env:check
if %ERRORLEVEL% neq 0 (
    echo ERROR: Production environment validation failed. Aborting gate.
    exit /b %ERRORLEVEL%
)

echo.
echo [2/4] Running live deployment forensic audit...
call npm run live:audit
if %ERRORLEVEL% neq 0 (
    echo ERROR: Live deployment forensic audit failed. Aborting gate.
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Running runtime mock/static telemetry guard...
call npm run runtime:guard
if %ERRORLEVEL% neq 0 (
    echo ERROR: Runtime mock/static telemetry guard failed. Aborting gate.
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Running Pulvini live-cut preflight readiness check...
call npm run pulvini:live-cut:check
if %ERRORLEVEL% neq 0 (
    echo ERROR: Pulvini live-cut readiness check failed. Aborting gate.
    exit /b %ERRORLEVEL%
)

echo.
echo === Environment Summary ===
echo NODE_ENV=%NODE_ENV%
echo HYBA_ENV=%HYBA_ENV%
echo HYBA_ALLOW_DEV_FIXTURES=%HYBA_ALLOW_DEV_FIXTURES%
echo HYBA_ENABLE_LIVE_STRATUM=%HYBA_ENABLE_LIVE_STRATUM%
echo HYBA_ENABLE_MINING_AUTOCONNECT=%HYBA_ENABLE_MINING_AUTOCONNECT%
echo HYBA_ENABLE_LIVE_SHARE_SUBMIT=%HYBA_ENABLE_LIVE_SHARE_SUBMIT%
echo HYBA_ENABLE_AUDIT_LOGGING=%HYBA_ENABLE_AUDIT_LOGGING%
echo Pool profiles are intentionally not echoed by this gate.
echo.

echo === Evidence Packet Location ===
dir /b artifacts\production_readiness\*.json 2>nul || echo No local production gate packets found yet.
dir /b HYBA_FULLSTACK_COMMAND_ROOM_* 2>nul
echo.
echo Gate complete. Preserve evidence packets and command-room folder with the launch ticket.

endlocal
