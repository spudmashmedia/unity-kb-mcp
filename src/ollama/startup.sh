#!/bin/sh
# =============================================================================
# Dockerfile for Unity KB - Ollama
# =============================================================================

set -e

# 1. Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &

SERVER_PID=$!

# 2. Wait for the server to accept connections
echo "Waiting for Ollama to initialize..."
until ollama list >/dev/null 2>&1; do
  sleep 1
done

# 3. Pull the required model
echo "Server ready! Pulling model..."
ollama pull qwen3-embedding:0.6b

# 4. Bring the background server process to the foreground
echo "Model pulled successfully. Keeping server running..."
wait "$SERVER_PID"
