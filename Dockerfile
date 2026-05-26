# Koii OS (AIOS) - Main Application Dockerfile
# Production-grade multi-architecture support

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    KOII_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    gcc \
    g++ \
    # Network tools
    curl \
    wget \
    netcat-openbsd \
    # Database clients
    sqlite3 \
    postgresql-client \
    # Utilities
    ca-certificates \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt

# Copy application code
COPY . /app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config /app/.koii-configs && \
    chmod 755 /app/data /app/logs /app/config /app/.koii-configs

# Create non-root user for security
RUN groupadd -r koii && useradd -r -g koii koii && \
    chown -R koii:koii /app

USER koii

# Expose ports
EXPOSE 8000 8222 27017 27018 27019 27020 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python3", "-m", "src.main"]
