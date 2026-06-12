FROM node:22.15.0-bookworm-slim AS node-deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:22.15.0-bookworm-slim AS frontend-build
WORKDIR /app
COPY --from=node-deps /app/node_modules ./node_modules
COPY package*.json ./
COPY . .
RUN npm run lint
RUN npm run build

FROM node:22.15.0-bookworm-slim AS runtime
ENV NODE_ENV=production \
    HYBA_ENV=production \
    HYBA_PHASE_TRANSITION_CONTAINER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/python_backend \
    HOST=0.0.0.0 \
    PORT=3000 \
    PULVINI_BACKEND_URL=http://127.0.0.1:3001 \
    HYBA_SPAWN_BACKEND=false \
    HYBA_ENABLE_MINING_AUTOCONNECT=false \
    BACKEND_PROXY_TIMEOUT_MS=30000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv curl ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

COPY python_backend/requirements.phase-transition.txt /app/python_backend/requirements.phase-transition.txt
RUN python3 -m venv /opt/hyba-venv \
    && /opt/hyba-venv/bin/python -m pip install --upgrade pip \
    && /opt/hyba-venv/bin/python -m pip install --no-cache-dir -r /app/python_backend/requirements.phase-transition.txt
ENV PATH="/opt/hyba-venv/bin:${PATH}"

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=frontend-build /app/dist ./dist
COPY python_backend ./python_backend
COPY scripts ./scripts
RUN chmod +x /app/scripts/hyba-runtime-entrypoint.sh

RUN useradd --create-home --shell /usr/sbin/nologin hyba \
    && chown -R hyba:hyba /app /opt/hyba-venv
USER hyba

EXPOSE 3000 3001
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://127.0.0.1:3000/bridge/health || exit 1
ENTRYPOINT ["tini", "--", "/app/scripts/hyba-runtime-entrypoint.sh"]
