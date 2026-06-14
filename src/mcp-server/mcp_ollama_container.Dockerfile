# =============================================================================
# Dockerfile for Unity KB MCP Server
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
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /builder

# Copy dependency files first for better caching
COPY ./src ./src
COPY ./scripts ./scripts
COPY ./config ./config
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

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /builder/wheels /app/wheels
RUN pip install --no-index --find-links=/app/wheels /app/wheels/*.whl && \
    rm -rf /app/wheels

# Copy MCP Server Code
COPY --from=builder /builder/src/core/ ./src/core/
COPY --from=builder /builder/src/mcp-server/ ./src/mcp-server/
COPY --from=builder /builder/config/config_mcp_ollama_container.toml ./config/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/src/mcp-server/server.py

USER appuser

# Expose the MCP server port (default 8000)
EXPOSE 8000

# Health check (optional, requires curl)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    # CMD curl -f http://ollama:${MCP_SERVER_PORT}/health || exit 1

# Entry point to run the MCP server
CMD ["python", "-m", "src.mcp-server.server"]

