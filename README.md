<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://ai.google.dev/static/site-assets/images/share-ais-513315318.png" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/48eebfab-04ed-42cd-bfee-0f1fec7066ad

## Run Locally

**Prerequisites:**  Node.js

1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. (Optional) Seed the database:
   `npm run seed`
4. Run the app:
   `npm run dev`
5. Open `http://localhost:3000`

### Production Build
```bash
npm run build
npm start
```

---

# HYBA Fullstack — Quantum ASIC Annihilation Console

> **Dodecahedral Hilbert Space Grover Search** • Substrate Agnostic • Mathematical Quantum Coprocessor

A full-stack quantum mathematical mining console that implements pure-mathematics Grover's amplitude amplification over dodecahedral symmetry groups, with a React frontend, Express/Vite server, Python FastAPI backend bridge, and integrated AI reasoning (PYTHAGORAS-v2).

---

## Architecture Overview

```
HYBA_FULLSTACK/
├── server.ts                  # Express server + Vite middleware + API routes
├── index.html                 # SPA entry point
├── package.json               # Dependencies & scripts
├── vite.config.ts             # Vite build configuration
├── tsconfig.json              # TypeScript configuration
├── metadata.json              # AI Studio metadata
├── src/
│   ├── App.tsx                # Main React application (dashboard)
│   ├── types.ts               # Core TypeScript interfaces
│   ├── apiClient.ts           # API client with auth interceptor & retry logic
│   ├── swaggerSpec.ts         # OpenAPI 3.0 specification (Swagger)
│   ├── index.css              # Tailwind v4 + custom theme tokens
│   ├── main.tsx               # React entry point
│   ├── components/
│   │   ├── ConsoleMetrics.tsx      # Live telemetry stat row
│   │   ├── CoherenceScatterPlot.tsx # D3.js quantum coherence scatter
│   │   ├── GroverVisualizer.tsx    # Interactive Grover amplitude rotor
│   │   ├── MathematicsTests.tsx    # 5-proof verification suite
│   │   ├── NetworkToast.tsx        # Connection status indicator
│   │   ├── PulviniExecutionPanel.tsx  # Pulvini memory engine executor
│   │   ├── PythagorasChat.tsx      # AI chat coprocessor (Gemini/local)
│   │   └── Sparkline.tsx           # Latency sparkline mini-chart
│   ├── hooks/
│   │   ├── useApiRequest.ts        # Fetch with exponential backoff retry
│   │   └── useLatencyMetrics.ts    # Connection ping tracking
│   ├── db/
│   │   ├── db.ts              # JSON file-based database (users, products, logs)
│   │   ├── db.json             # Stored data
│   │   └── seed.ts            # Idempotent database seeder
│   ├── types/
│   │   └── api.ts             # Extended API response types
│   └── utils/
│       └── math.ts            # Pure quantum mathematics engine
├── python_backend/
│   ├── enhanced_ultimate_pulvini_quantum.py  # Advanced quantum simulation
│   └── hyba_genesis_api/
│       └── main.py            # FastAPI-based HYBA Genesis API
└── assets/                    # Static assets
```

---

## Core Mathematical Framework

### 1. Dodecahedral Grover Search

Standard Grover's algorithm searches an unstructured database of size N in O(√N) iterations. This implementation applies **dodecahedral symmetry constraints** — mapping the search space onto a 20-vertex dodecahedral group modulated by golden ratio phase shifts — to reduce the effective search dimension.

**Key equation:**

$$\text{Resonance}_k = (k \cdot \Phi) \pmod L < \epsilon$$

Where $\Phi = \frac{1+\sqrt{5}}{2} \approx 1.6180339887...$ is the Golden Ratio.

### 2. Integrated Information Speedup (O(√I))

By exploiting blockchain structural information (timestamps, Merkle tree branches, difficulty targets), the effective Hilbert space dimension reduces from N to N/I, yielding:

$$\text{Iterations} = \mathcal{O}\left(\sqrt{\frac{N}{I}}\right) = \mathcal{O}(\sqrt{I'})$$

### 3. Five Verification Proofs

The system runs 5 rigorous mathematical tests:

| # | Test | Description |
|---|------|-------------|
| 1 | **Wavefunction Unitary Normalization** | Verifies ∑|ψᵢ|² ≡ 1 under SU(N) |
| 2 | **Hadamard Max Entropy** | Confirms S = log₂(N) after Hadamard transform |
| 3 | **Dodecahedral Phi Resonance** | Validates golden ratio phase alignment |
| 4 | **Grover Amplitude Convergence** | Checks probability amplification > 15x |
| 5 | **Structured O(√I) Speedup** | Demonstrates > 50% iteration reduction |

---

## API Endpoints

The Express server exposes the following endpoints (full Swagger documentation available at `/api-docs` when running):

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register new operator account |
| POST | `/api/auth/login` | Authenticate and receive JWT |
| GET | `/api/auth/profile` | Get authenticated user profile |
| GET | `/api/health` | System health + quantum telemetry |
| GET | `/api/products` | Seeded quantum hardware catalog |
| GET | `/api/tests/run` | Run mathematical verification proofs |
| POST | `/api/predict` | Calibrate wave realignment parameters |
| POST | `/api/ai/chat` | PYTHAGORAS-v2 AI reasoning engine |
| GET | `/api/mining/pools` | Stratum mining pool status |
| GET | `/api/mining/stats` | Mining statistics & quantum performance |
| GET | `/api/security/status` | Phi-Shield defense system status |
| POST | `/api/security/shield` | Calibrate security shield strength |
| GET | `/api/pitfalls` | System pitfall monitoring |
| POST | `/api/toe/experiments` | Theory of Everything experiments |
| POST | `/api/pulvini/execute` | Execute Pulvini memory engine (proxied) |
| GET | `/api/ai/consciousness` | IIT consciousness metrics |
| POST | `/api/ai/consciousness/stimulate` | Stimulate consciousness |

---

## Authentication System

- **JWT-based** with 10-day token expiry
- SHA-256 password hashing with salt
- Role-based access (administrator / operator)
- Bearer token injection via auth interceptor
- Session persisted to `localStorage`

---

## PYTHAGORAS-v2 AI Engine

The chat coprocessor supports two modes:

1. **Gemini API mode** (premium) — Uses `@google/genai` with `gemini-3.5-flash` when `GEMINI_API_KEY` is configured
2. **Local Math Engine** (fallback) — Rule-based deterministic responses covering:
   - Grover amplification mechanics
   - ASIC annihilation vector formulation
   - Dodecahedral symmetry and golden harmonics

---

## Python Backend Bridge

On startup, the Express server spawns:
1. **Pythia Mining Daemon** — Background Python process for mining state management
2. **FastAPI Server** (port 3001) — HYBA Genesis API for quantum computations

State is shared via `pythia_state.json` for cross-process metrics.

---

## Styling & Theming

- **Tailwind CSS v4** with custom theme tokens:
  - `oxford` (#002147) — Primary dark blue
  - `clicquot-gold` (#DF950B) — Accent gold
  - `clicquot-orange` (#FC5F10) — Secondary accent
  - `mckinsey-blue` (#003666) — Tertiary
  - `mckinsey-light` (#0A5C91) — Light blue
  - `lux-slate` (#5F6975) — Muted slate
  - `sand` (#F7F5F0) — Light background
  - `sand-dark` (#EADEC9) — Border color
- **Dark mode** support via `.dark` class toggle
- **Framer Motion** animations (`motion` package)
- **Lucide React** icons throughout

---

## Data Layer

- **JSON file-based database** (`src/db/db.json`) — No external database required
- **Collections**: Users, Quantum Products, Calibration Logs
- **Idempotent seeding** via `npm run seed`

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini AI API key | — |
| `JWT_SECRET` | JWT signing secret | Hardcoded fallback (set in production) |
| `HYBA_BACKEND_URL` | Python backend URL | `http://127.0.0.1:8000/api` |
| `VITE_HYBA_BACKEND_URL` | Frontend backend URL (Vite) | `http://127.0.0.1:8000/api` |
| `VITE_PULVINI_BACKEND_URL` | Pulvini backend URL (Vite) | `http://127.0.0.1:8000/api` |
| `PULVINI_BACKEND_URL` | Pulvini backend URL | `http://127.0.0.1:8000` |

---

## Dependencies

**Key packages:**
- `react` 19 + `react-dom` 19 — UI framework
- `express` 4.21 — Backend server
- `vite` 6 + `@vitejs/plugin-react` — Build tooling
- `@google/genai` — Gemini AI SDK
- `tailwindcss` 4 + `@tailwindcss/vite` — Styling
- `jsonwebtoken` — JWT auth
- `recharts` / `d3` 7 — Data visualization
- `lucide-react` — Icon library
- `motion` — Animation library
- `swagger-ui-express` — API documentation portal
- `http-proxy-middleware` — API proxying
- `tsx` — TypeScript execution
- `esbuild` — Production bundling

---

## Code Review Summary

### Strengths ✅
- **Strong TypeScript usage** with comprehensive interfaces throughout
- **Good separation of concerns** — pure math functions, components, hooks, API client, DB layer
- **Solid error handling** — graceful fallbacks for Gemini API, Express connectivity, Python daemon
- **Clean component design** — loading, error, empty, and success states all handled explicitly
- **Reusable custom hooks** — `useApiRequest` with retry logic, `useLatencyMetrics` with ping tracking
- **Well-documented** — JSDoc on all mathematical functions and API endpoints
- **Interactive visualizations** — Grover amplitude rotor with step scrubbing, D3.js scatter plot

### Areas for Improvement 🔧
- **Python `python3` hardcode** — fails on Windows (`python` vs `python3`)
- **JSON database concurrency** — no protection against simultaneous writes
- **Mock data endpoints** — most APIs return simulated/static data
- **Backend URL mismatch** — `BACKEND_URL` defaults to port 8000, but Express runs on 3000
- **No unit tests** — verification suite exists but isn't integrated into CI (Jest/Vitest)
- **Password hashing** — SHA256 with fixed salt, should use bcrypt/argon2
- **No React error boundary** — runtime errors could crash the entire UI
- **Hardcoded JWT secret** — must use environment variable in production

### Security Notes 🔒
- JWT tokens in `localStorage` — XSS vulnerable; consider httpOnly cookies
- No rate limiting on auth endpoints
- No input sanitization on registration
- CORS not explicitly configured
- Python subprocess inherits full environment variables

---

## Scripts

| Script | Command | Description |
|--------|---------|-------------|
| dev | `tsx server.ts` | Start development server (Express + Vite HMR) |
| build | `vite build && esbuild server.ts --bundle --platform=node` | Build for production |
| start | `node dist/server.cjs` | Start production server |
| clean | `rm -rf dist` | Remove build artifacts |
| lint | `tsc --noEmit` | TypeScript type checking |
| seed | `tsx src/db/seed.ts` | Seed database with default users/products |

---

## View your app in AI Studio

https://ai.studio/apps/48eebfab-04ed-42cd-bfee-0f1fec7066ad

---

## License

© 2026 HYBA GROUP • Verified State Mathematics Secured