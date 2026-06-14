#!/bin/bash
# =============================================================================
# init_ingest.sh - Environment Setup for Unity KB Ingest Pipeline
# =============================================================================

set -e

# Calculate PROJECT_ROOT (parent of scripts/ folder where docker-compose.yml lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../" && pwd)"

echo "🔧 Initializing Unity KB Ingest Environment..."
echo "   Project Root: ${ROOT_DIR}"
echo ""

mkdir -p "${ROOT_DIR}/data/raw"
mkdir -p "${ROOT_DIR}/data/vectors"
mkdir -p "${ROOT_DIR}/data/archive/raw"

echo "✅ Created directories:"
echo "   ├─ ${ROOT_DIR}/data/"
echo "   ├─ ${ROOT_DIR}/data/raw/"
echo "   ├─ ${ROOT_DIR}/data/vectors/"
echo "   └─ ${ROOT_DIR}/data/archive/raw/"
echo ""

chmod -R 755 "${ROOT_DIR}/data"

echo "📝 Directory structure ready!"
echo ""
echo "💡 Next steps:"
echo "   1. Place your source documents in: ${ROOT_DIR}/data/raw/"
echo "   2. Run 'docker compose up -d' to start services"
echo "   3. Monitor logs with: docker compose logs -f unity-kb-ingest"
echo ""

if command -v tree &> /dev/null; then
    echo "📁 Directory Tree:"
    tree "${ROOT_DIR}/data/"
else
    echo "📁 Directory Structure:"
    find "${ROOT_DIR}/data" -type d | head -20
fi

echo ""
echo "✅ Environment initialization complete!"
