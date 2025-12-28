# KoraFlow Quick Start Guide

This guide will help you get KoraFlow up and running quickly.

## Prerequisites Check

First, verify your setup:

```bash
python3 scripts/verify_setup.py
```

This will check:
- Python 3.10+
- Docker and Docker Compose
- Ollama installation and models
- Project structure

## Step 1: Start Ollama

If Ollama is not already running:

```bash
# Start Ollama server
ollama serve

# In another terminal, pull required models
ollama pull llama3
ollama pull nomic-embed-text
```

## Step 2: Run Ingestion Pipeline

Clone repositories, scrape docs, parse code, and chunk documents:

```bash
# Option 1: Use the script
./scripts/run_pipeline.sh

# Option 2: Use Makefile
make setup

# Option 3: Manual steps
docker-compose run --rm ingestion python clone_repos.py
docker-compose run --rm ingestion python scrape_docs.py
docker-compose run --rm ingestion python parse_code.py
docker-compose run --rm ingestion python chunk_documents.py
```

**Note**: This may take a while depending on repository sizes and documentation pages.

## Step 3: Build FAISS Index

Generate embeddings and build the vector store:

```bash
docker-compose run --rm vector_store python faiss_manager.py
```

**Note**: This will take time depending on the number of chunks. The embedding model will process all chunks.

## Step 4: Start Services

Start all Docker services:

```bash
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f llm_service
```

## Step 5: Test RAG Pipeline

Test the RAG service:

```bash
# Health check
curl http://localhost:8000/health

# Run test queries
python3 scripts/test_rag.py

# Or manually test
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I create a custom DocType?", "top_k": 5}'
```

## Step 6: Setup Frappe/Bench

Install Frappe Framework and modules:

```bash
# Run setup script
./bench_setup.sh

# Or manually (if script fails)
bench init --frappe-branch version-14 bench
cd bench
bench new-site koraflow-site
bench get-app erpnext --branch version-14
bench --site koraflow-site install-app erpnext
# ... install other modules
```

## Step 7: Install KoraFlow Core

Add KoraFlow Core app to your Bench installation:

```bash
cd bench

# Get the app (adjust path as needed)
bench get-app koraflow_core ../apps/koraflow_core

# Install the app
bench --site koraflow-site install-app koraflow_core

# Build assets
bench build

# Start development server
bench start
```

## Step 8: Access KoraFlow

1. Open browser: http://localhost:8000
2. Login with Administrator credentials
3. Navigate to "KoraFlow Modules" workspace
4. Manage module activation/deactivation

## Troubleshooting

### Ollama Connection Issues

If the RAG service can't connect to Ollama:

1. Check Ollama is running: `ollama list`
2. Update `OLLAMA_HOST` in `docker-compose.yml` if needed
3. For macOS, `host.docker.internal` should work
4. For Linux, you may need to use `172.17.0.1` or your host IP

### FAISS Index Not Found

If you get errors about missing index:

1. Verify chunks exist: `ls -la chunks/`
2. Rebuild index: `docker-compose run --rm vector_store python faiss_manager.py`
3. Check index file: `ls -la vector_store/indices/`

### Module Not Showing

If modules don't appear in UI:

1. Check module is installed: `bench list-apps`
2. Verify module is enabled in "KoraFlow Modules" DocType
3. Clear cache: `bench clear-cache`
4. Rebuild assets: `bench build`

## Next Steps

- Customize branding in `apps/koraflow_core/koraflow_core/hooks.py`
- Add custom workspaces via Desk UI
- Configure module dependencies
- Extend RAG pipeline with custom retrieval logic

## Useful Commands

```bash
# View service logs
docker-compose logs -f [service_name]

# Stop all services
docker-compose down

# Rebuild services
docker-compose build

# Clean generated data
make clean

# Run tests
make test
```

## Getting Help

- Check `README.md` for detailed documentation
- Review Frappe docs: https://docs.frappe.io
- Query the RAG system for code-specific questions

