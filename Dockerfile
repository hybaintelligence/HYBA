FROM node:22.15.0-bookworm-slim AS node-deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:22.15.0-bookworm-slim AS frontend-build
WORKDIR /app
COPY --from=node-deps /app/node_modules ./node_modules
COPY package*.json ./
COPY . .
RUN npm run build

FROM python:3.11-slim-bookworm AS runtime
ENV NODE_ENV=production \
    HYBA_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/python_backend \
    PORT=3000 \
    PULVINI_BACKEND_URL=http://127.0.0.1:3001

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm tini \
    && rm -rf /var/lib/apt/lists/*

COPY python_backend/hyba_genesis_api/requirements.txt /app/python_backend/hyba_genesis_api/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/python_backend/hyba_genesis_api/requirements.txt

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=frontend-build /app/dist ./dist
COPY python_backend ./python_backend
COPY scripts ./scripts
COPY server.ts ./server.ts
COPY deploy ./deploy

RUN useradd --create-home --shell /usr/sbin/nologin hyba \
    && chown -R hyba:hyba /app
USER hyba

EXPOSE 3000 3001
ENTRYPOINT ["tini", "--"]
CMD ["/app/deploy/entrypoint.sh"]
