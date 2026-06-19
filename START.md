# HYBA Full Stack - Quick Start Guide

## One Command to Start Everything

```bash
npm run dev:full
```

This single command starts:
- ✅ **Python Backend** (FastAPI) on `http://localhost:3001`
- ✅ **Frontend Dev Server** (Vite + React) on `http://localhost:3000`
- ✅ **API Proxy** (automatic routing from `/api` to backend)

## Alternative: Start Services Separately

### Backend Only
```bash
npm run backend:start
```

### Frontend Only
```bash
npm run dev
```

## Production Build & Start

### Build
```bash
npm run build
```

### Start Production Server
```bash
npm start
```

## Environment Configuration

Environment variables are loaded from `.env.local` in the project root.

Key variables:
- `JWT_SECRET` - ✅ Already configured
- `NODE_ENV` - Set to `development` or `production`
- `HYBA_POOL_*` - Mining pool configuration (optional)
- `PULVINI_BACKEND_URL` - Backend URL (default: http://127.0.0.1:3001)

## Requirements

- Node.js >= 20.18.0
- Python 3.x
- uvicorn (Python package for FastAPI)

## Stopping the Servers

Press `Ctrl+C` in the terminal to gracefully shut down both services.
