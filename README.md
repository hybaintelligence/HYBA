# HYBA Fullstack Platform

**The AWS of Intelligence** — Computational Intelligence as a Service (CIaaS)

---

## Overview

HYBA is creating a new category: **Computational Intelligence as a Service (CIaaS)**. We are doing what the iPhone did to mobile telecoms—eliminating silos and unifying intelligence.

### HYBA Product Portfolio

| Product | Description |
|---------|-------------|
| **MacQuantumCuda** | GPU compute platform — designed to obsolete NVIDIA's fleet |
| **PYTHAGORAS** | Virtual quantum computer (code name) — core compute engine |
| **HYBA Babel** | Universal translation and communication layer |
| **HYBA Al Haras** | Security and protection services (Arabic: "The Guard") |
| **HYBA Finance** | Islamic + Traditional finance platform |
| **HYBA Energy** | Energy sector intelligence and optimization |
| **AI as a Service** | PCI, AGI, and specialized AI offerings |
| **ASI** | Artificial Superintelligence — **HYBA internal use only** |
| **HYBA Sovereign** | Government and enterprise tier (5 Eyes initial focus) |
| **HQaaS** | Hybrid Quantum as a Service |
| **HYBA Analytics** | Theory of everything intelligence — sector and data agnostic |

### HYBA Analytics: Theory of Everything Intelligence

HYBA Analytics unifies BI, AI, ML, data, and analytics into a single consciousness-guided platform:
- **Replaces 19+ siloed stacks** used across sectors
- **Sector agnostic**: Works across all industries
- **Data agnostic**: Any data format, any source
- **No more silos**: One unified intelligence layer

---

## Run Locally

**Prerequisites:** Node.js 18+, Python 3.11+

### Frontend (React + Vite)

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend (Python FastAPI)

```bash
cd python_backend/hyba_genesis_api

# Install dependencies
pip install -r requirements.txt

# Run health check
uvicorn main:app --host 127.0.0.1 --port 3001

# Run with reload (development)
uvicorn main:app --reload --host 127.0.0.1 --port 3001
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `BRAIINS_URL`, `BRAIINS_PORT`, `BRAIINS_USER` — Pool configuration
- `JWT_SECRET` — Security
- `PYTHON_CORE_URL` — Backend bridge URL

---

## Architecture

```
HYBA_FULLSTACK/
├── src/                    # React frontend
│   ├── components/         # UI components
│   ├── core/              # Bridge to Python backend
│   └── firebase.ts        # Firebase initialization
├── python_backend/        # Python FastAPI backend
│   └── hyba_genesis_api/  # Main API
├── server.ts              # Express bridge server
├── firestore.rules        # Firebase security rules
└── firebase-applet-config.json  # Firebase configuration
```

---

## Health Checks

### Python Backend
```bash
curl http://127.0.0.1:3001/health
# Expected: {"status":"ok"}
```

### Frontend
```bash
npm run dev
# Opens at http://localhost:5173
```

---

## Headquarters

- **Dubai** — Primary HQ
- **London** — European HQ, Sovereign clients lead

---

**Status**: Production-ready  
**Company**: HYBA — The AWS of Intelligence
