#!/bin/bash
set -e

echo "🚀 Starting Document Ingestion..."

#Run the Python ingestion script with full path
python3 /app/src/ingest/ingest_docs.py || {
    echo "❌ Ingestion failed!"
    exit 1
}

echo "✅ Ingestion complete. Restarting ChromaDB service..."

# Restart the ChromaDB container (adjust name as needed)
docker compose restart unity-kb-chromadb

echo "🎉 All tasks completed successfully!"
