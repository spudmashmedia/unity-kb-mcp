# =============================================================================
# Dockerfile for Unity KB Ingest
# =============================================================================

FROM python:3.12-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    unzip \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /builder

# Copy dependency files first for better caching
COPY ./config ./config
COPY ./scripts ./scripts
COPY ./src ./src
COPY ./pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip wheel --wheel-dir=/builder/wheels .

# =============================================================================
# Production Stage (Multi-stage build)
# =============================================================================

FROM python:3.12-slim-bookworm AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:${PYTHONPATH}
# Install build dependencies
# 
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    vim \
    rsync \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /builder/wheels /app/wheels
RUN pip install --no-index --find-links=/app/wheels /app/wheels/*.whl && \
    rm -rf /app/wheels

# Copy Ingest Code
COPY --from=builder /builder/src/core/ ./src/core/
COPY --from=builder /builder/src/ingest/ ./src/ingest/
COPY --from=builder /builder/config/config_ingest.toml ./config/
COPY --from=builder /builder/scripts/get-docs-zip.sh ./scripts/
COPY --from=builder /builder/scripts/run-ingest.sh ./scripts/

RUN chmod +x ./scripts/get-docs-zip.sh
RUN chmod +x ./scripts/run-ingest.sh

# Entry point to run ingest runner
ENTRYPOINT ["/app/scripts/run-ingest.sh"]
