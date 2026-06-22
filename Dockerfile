# Production-ready Dockerfile for HYBA Fullstack
# Builds the React/Vite bridge and Python FastAPI backend in one reproducible image.
# Standardized to Node.js 22.15.0 and Python 3.12.13.

FROM node:22.15.0-bookworm-slim AS node-deps
WORKDIR /app

COPY package.json package-lock.json* ./

ARG NPM_CONFIG_PROXY=
ARG NPM_CONFIG_HTTPS_PROXY=
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=

RUN npm config delete proxy || true \
    && npm config delete https-proxy || true \
    && npm config set registry https://registry.npmjs.org/ \
    && npm ci --legacy-peer-deps --no-audit --no-fund

FROM node:22.15.0-bookworm-slim AS frontend-build
WORKDIR /app

COPY --from=node-deps /app/node_modules ./node_modules
COPY package*.json ./
COPY index.html ./
COPY src ./src
COPY public ./public
COPY scripts ./scripts
COPY assets ./assets
COPY *.config.* ./
COPY tsconfig*.json ./

ARG NPM_CONFIG_PROXY=
ARG NPM_CONFIG_HTTPS_PROXY=
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=

RUN npm config delete proxy || true \
    && npm config delete https-proxy || true \
    && npm config set registry https://registry.npmjs.org/ \
    && npm run lint \
    && npm run build \
    && node scripts/ensure_spa_entrypoint.mjs

FROM python:3.12.13-slim AS python-deps
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY python_backend/hyba_genesis_api/requirements.txt /app/python_backend/hyba_genesis_api/requirements.txt

RUN python -m venv /opt/hyba-venv \
    && /opt/hyba-venv/bin/python -m pip install --upgrade pip \
    && /opt/hyba-venv/bin/python -m pip install --no-cache-dir -r /app/python_backend/hyba_genesis_api/requirements.txt

FROM python:3.12.13-slim AS runtime

ENV NODE_ENV=production \
    HYBA_ENV=production \
    HYBA_PHASE_TRANSITION_CONTAINER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/python_backend \
    HOST=0.0.0.0 \
    PORT=3000 \
    PULVINI_BACKEND_URL=http://127.0.0.1:3001 \
    HYBA_BACKEND_HOST=127.0.0.1 \
    HYBA_BACKEND_PORT=3001 \
    HYBA_SPAWN_BACKEND=false \
    HYBA_ENABLE_MINING_AUTOCONNECT=false \
    BACKEND_PROXY_TIMEOUT_MS=30000 \
    UVICORN_WORKERS=2 \
    PATH=/opt/hyba-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKDIR /app

COPY --from=node-deps /usr/local/bin/node /usr/local/bin/node
COPY --from=node-deps /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=python-deps /opt/hyba-venv /opt/hyba-venv

RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && node --version \
    && npm --version

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json* ./

ARG NPM_CONFIG_PROXY=
ARG NPM_CONFIG_HTTPS_PROXY=
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=

RUN npm config delete proxy || true \
    && npm config delete https-proxy || true \
    && npm config set registry https://registry.npmjs.org/ \
    && npm ci --omit=dev --legacy-peer-deps --no-audit --no-fund \
    && npm cache clean --force

COPY --from=frontend-build /app/dist ./dist
COPY python_backend ./python_backend
COPY scripts ./scripts

RUN chmod +x /app/scripts/hyba-runtime-entrypoint.sh \
    && useradd --create-home --shell /usr/sbin/nologin hyba \
    && chown -R hyba:hyba /app /opt/hyba-venv

USER hyba

EXPOSE 3000 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://127.0.0.1:3000/bridge/health || exit 1

ENTRYPOINT ["tini", "--", "/app/scripts/hyba-runtime-entrypoint.sh"]
