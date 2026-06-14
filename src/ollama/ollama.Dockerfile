# =============================================================================
# Dockerfile for Unity KB - Ollama
# =============================================================================

FROM ollama/ollama:latest
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY ./src/ollama/startup.sh ./
RUN chmod +x ./startup.sh

ENTRYPOINT ["./startup.sh"]
