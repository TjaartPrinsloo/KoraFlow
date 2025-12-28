#!/bin/bash
# KoraFlow Ingestion Pipeline Runner
# Runs the complete ingestion pipeline in sequence

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=========================================="
echo "KoraFlow Ingestion Pipeline"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Step 1: Clone repositories
echo "[1/4] Cloning repositories..."
docker-compose run --rm ingestion python clone_repos.py
echo "✓ Repositories cloned"
echo ""

# Step 2: Scrape documentation
echo "[2/4] Scraping documentation..."
docker-compose run --rm ingestion python scrape_docs.py
echo "✓ Documentation scraped"
echo ""

# Step 3: Parse code files
echo "[3/4] Parsing code files..."
docker-compose run --rm ingestion python parse_code.py
echo "✓ Code files parsed"
echo ""

# Step 4: Chunk documents
echo "[4/4] Chunking documents..."
docker-compose run --rm ingestion python chunk_documents.py
echo "✓ Documents chunked"
echo ""

echo "=========================================="
echo "Ingestion pipeline complete!"
echo "=========================================="
echo ""
echo "Next step: Build FAISS index"
echo "  docker-compose run --rm vector_store python faiss_manager.py"
echo ""

