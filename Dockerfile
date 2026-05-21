# Multi-stage Dockerfile for Koii OS (AIOS)
# Supports all platforms via Docker

# Stage 1: Base image with Python and system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Install Playwright and browser dependencies
FROM base as playwright

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Stage 3: Application build
FROM playwright as builder

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Stage 4: Final runtime image
FROM playwright as runtime

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash koii && \
    mkdir -p /app /data /config && \
    chown -R koii:koii /app /data /config

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/ms-playwright /home/koii/.cache/ms-playwright

# Copy application code
COPY --chown=koii:koii . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R koii:koii /app

# Switch to non-root user
USER koii

# Expose ports
# 8000: Web UI / API Server
# 43210: Min Browser (Electron) API
# 4222: NATS messaging (if used)
EXPOSE 8000 43210 4222

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command: Run the web UI
CMD ["python", "-m", "uvicorn", "src.koii_os.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

# Made with Bob
