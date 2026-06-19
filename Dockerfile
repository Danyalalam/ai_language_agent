# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

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
FROM python:3.12-slim AS runtime

# Install ffmpeg (required for audio conversion) and other runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment and source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Make sure the venv binaries are on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
