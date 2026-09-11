# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock .python-version ./

# Install dependencies into a virtual environment (no project code yet)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the source code
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Install ffmpeg (required for audio conversion) and other runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# One COPY, not two: /app in the builder already contains .venv, so copying the
# venv separately first would ship the entire virtualenv twice — once in each
# layer — roughly doubling the stored/pushed image size for no benefit.
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Documentation only; the actual port comes from $PORT at runtime.
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health')"

# Shell form so ${PORT} is expanded at runtime: Azure App Service, DigitalOcean
# App Platform and Cloud Run all inject the port they expect the app to bind to,
# and a hardcoded 8000 fails their health checks. `exec` keeps uvicorn as PID 1
# so SIGTERM reaches it and shutdown stays graceful.
# --proxy-headers makes uvicorn honour X-Forwarded-Proto/For from the platform's
# load balancer, so request.url and client IP are correct behind TLS termination.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
