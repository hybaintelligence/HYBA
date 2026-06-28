@echo off
REM HYBA Local Deployment Script (Windows)
REM Based on Gordon's Tier 1 Deployment Strategy
REM This script deploys HYBA locally using Docker Compose

echo ==========================================
echo HYBA Local Deployment (Gordon's Tier 1)
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Create necessary directories
echo Creating runtime directories...
if not exist runtime\evidence mkdir runtime\evidence
if not exist runtime\memos mkdir runtime\memos
if not exist config mkdir config

REM Check if .env.local exists
if not exist .env.local (
    echo Warning: .env.local not found. Creating from template...
    copy .env.example .env.local
    echo Please edit .env.local with your local configuration before running this script again.
    exit /b 1
)

REM Check if prometheus config exists
if not exist config\prometheus.yml (
    echo Creating default prometheus configuration...
    (
        echo global:
        echo   scrape_interval: 15s
        echo   evaluation_interval: 15s
        echo.
        echo scrape_configs:
        echo   - job_name: 'hyba-backend'
        echo     static_configs:
        echo       - targets: ['backend:3000']
        echo   - job_name: 'prometheus'
        echo     static_configs:
        echo       - targets: ['localhost:9090']
    ) > config\prometheus.yml
)

REM Check if grafana datasource config exists
if not exist config\grafana-datasources.yml (
    echo Creating default grafana datasource configuration...
    (
        echo apiVersion: 1
        echo.
        echo datasources:
        echo   - name: Prometheus
        echo     type: prometheus
        echo     access: proxy
        echo     url: http://prometheus:9090
        echo     isDefault: true
        echo     editable: true
    ) > config\grafana-datasources.yml
)

set "COMPOSE_CMD=docker-compose"
docker-compose version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Docker Compose is not installed. Please install it and try again.
        exit /b 1
    )
    set "COMPOSE_CMD=docker compose"
)

echo Pulling Docker image from Docker Cloud...
%COMPOSE_CMD% -f docker-compose.local.yml pull

echo Starting services...
%COMPOSE_CMD% -f docker-compose.local.yml up -d

echo.
echo ==========================================
echo Deployment Complete!
echo ==========================================
echo.
echo Services:
echo   Frontend (Bridge):  http://localhost:3000
echo   Backend API:       http://localhost:3001
echo   PostgreSQL:        localhost:5432
echo   Redis:             localhost:6379
echo   Prometheus:        http://localhost:9090
echo   Grafana:           http://localhost:3002 (admin/admin)
echo.
echo Governance Rail: treasury
echo Evidence Storage: .\runtime\evidence (local filesystem)
echo.
echo Useful Commands:
echo   View logs:        docker-compose -f docker-compose.local.yml logs -f
echo   Stop services:    docker-compose -f docker-compose.local.yml down
echo   Restart services:  docker-compose -f docker-compose.local.yml restart
echo   Check status:      docker-compose -f docker-compose.local.yml ps
echo.
echo To enable mining, edit .env.local and set:
echo   HYBA_ENABLE_MINING_AUTOCONNECT=true
echo   HYBA_ENABLE_LIVE_STRATUM=true
echo.
