# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (better layer caching)
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# VITE_API_BASE_URL is injected at build time via --build-arg. Vite's loadEnv
# picks up VITE_-prefixed vars from the process environment, and .env* files are
# excluded via .dockerignore so the committed .env.production (used by the Vercel
# build) can't silently override this one.
# Default is a same-origin relative path: the browser then talks to nginx below,
# which proxies /api to the backend. Pass an absolute URL instead when the API
# lives on a different host.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# ── Stage 2: Serve with Nginx ─────────────────────────────────────────────────
FROM nginx:alpine AS runtime

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Templates in this directory are rendered with envsubst by the image's
# entrypoint before nginx starts, which is how ${PORT} and ${BACKEND_ORIGIN}
# become runtime-configurable. Writing default.conf.template also replaces the
# image's stock default.conf, avoiding a duplicate default server on the port.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

ENV PORT=80 \
    BACKEND_ORIGIN=http://backend:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1

# Documentation only; the actual port comes from $PORT at runtime.
EXPOSE 80

# 127.0.0.1, not localhost: in this image `localhost` resolves to ::1 only,
# while nginx `listen ${PORT}` binds IPv4 — so a localhost probe gets
# ECONNREFUSED and the container never reports healthy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- "http://127.0.0.1:${PORT}/" >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
