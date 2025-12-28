# KoraFlow Setup Checklist

Use this checklist to ensure everything is set up correctly.

## Pre-Flight Checks

- [ ] Docker is installed and running
  ```bash
  docker --version
  docker info
  ```

- [ ] Python 3.10+ is installed
  ```bash
  python3 --version
  ```

- [ ] Git is installed
  ```bash
  git --version
  ```

- [ ] Ollama is installed
  ```bash
  ollama --version
  ```

## Ollama Setup

- [ ] Ollama server is running
  ```bash
  ollama serve
  # Keep this terminal open
  ```

- [ ] Required models are pulled
  ```bash
  ollama pull llama3
  ollama pull nomic-embed-text
  ```

- [ ] Verify models are available
  ```bash
  ollama list
  ```

## Project Setup

- [ ] All files are in place
  ```bash
  ls -la docker-compose.yml config.yml README.md
  ```

- [ ] Verify setup script
  ```bash
  python3 scripts/verify_setup.py
  ```

- [ ] Docker services can be built
  ```bash
  docker-compose build
  ```

## Ingestion Pipeline

- [ ] Clone repositories
  ```bash
  docker-compose run --rm ingestion python clone_repos.py
  ```
  Check: `ls repos/` should show cloned repos

- [ ] Scrape documentation
  ```bash
  docker-compose run --rm ingestion python scrape_docs.py
  ```
  Check: `ls docs/` should show JSON files

- [ ] Parse code files
  ```bash
  docker-compose run --rm ingestion python parse_code.py
  ```
  Check: `ls chunks/parsed_code.json` should exist

- [ ] Chunk documents
  ```bash
  docker-compose run --rm ingestion python chunk_documents.py
  ```
  Check: `ls chunks/*.json | wc -l` should show chunk files

## Vector Store

- [ ] Build FAISS index
  ```bash
  docker-compose run --rm vector_store python faiss_manager.py
  ```
  Check: `ls vector_store/indices/*.index` should exist

- [ ] Verify index metadata
  ```bash
  ls vector_store/indices/*.metadata.json
  ```

## RAG Service

- [ ] Start services
  ```bash
  docker-compose up -d
  ```

- [ ] Check service health
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] Test RAG pipeline
  ```bash
  python3 scripts/test_rag.py
  ```

## Frappe/Bench Setup

- [ ] Run bench setup
  ```bash
  ./bench_setup.sh
  ```

- [ ] Verify Bench installation
  ```bash
  cd bench
  bench version
  ```

- [ ] Verify site exists
  ```bash
  bench --site koraflow-site console
  # Should open Python console
  ```

- [ ] Verify apps are installed
  ```bash
  bench list-apps
  ```

## KoraFlow Core

- [ ] Install KoraFlow Core app
  ```bash
  cd bench
  bench get-app koraflow_core ../apps/koraflow_core
  bench --site koraflow-site install-app koraflow_core
  ```

- [ ] Build assets
  ```bash
  bench build
  ```

- [ ] Start development server
  ```bash
  bench start
  ```

- [ ] Access KoraFlow
  - Open: http://localhost:8000
  - Login with Administrator
  - Navigate to "KoraFlow Modules" workspace

## Verification Tests

- [ ] RAG pipeline responds to queries
  ```bash
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "top_k": 3}'
  ```

- [ ] Module registry API works
  ```bash
  # From Bench console or API
  curl http://localhost:8000/api/method/koraflow_core.koraflow_core.module_registry.get_all_modules_status
  ```

- [ ] Branding is applied
  - Check workspace labels show "KoraFlow" instead of "ERPNext"
  - Check app titles in UI

- [ ] Module activation works
  - Go to "KoraFlow Modules" DocType
  - Toggle a module on/off
  - Verify UI changes

## Troubleshooting

If any step fails:

1. Check logs:
   ```bash
   docker-compose logs [service_name]
   ```

2. Verify Ollama connection:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Check file permissions:
   ```bash
   ls -la repos/ docs/ chunks/
   ```

4. Rebuild if needed:
   ```bash
   docker-compose build --no-cache
   ```

5. Clean and restart:
   ```bash
   docker-compose down
   make clean  # Optional: removes generated data
   docker-compose up -d
   ```

## Success Criteria

✅ All services are running  
✅ RAG pipeline responds with citations  
✅ KoraFlow Core app is installed  
✅ Module management UI is accessible  
✅ Branding is applied in UI  
✅ No errors in logs  

## Next Steps After Setup

1. Customize branding in `apps/koraflow_core/koraflow_core/hooks.py`
2. Create custom workspaces via Desk UI
3. Configure module dependencies
4. Test with real queries
5. Extend RAG pipeline as needed

