.PHONY: help setup clone parse chunk index start stop clean test

help:
	@echo "KoraFlow Makefile Commands:"
	@echo "  make setup      - Initial setup (clone repos, parse, chunk, index)"
	@echo "  make clone      - Clone all repositories"
	@echo "  make parse      - Parse code files"
	@echo "  make chunk      - Chunk documents"
	@echo "  make index      - Build FAISS index"
	@echo "  make start      - Start all Docker services"
	@echo "  make stop       - Stop all Docker services"
	@echo "  make clean      - Clean generated files"
	@echo "  make test       - Run tests"

setup: clone parse chunk index
	@echo "Setup complete!"

clone:
	docker-compose run --rm ingestion python clone_repos.py

parse:
	docker-compose run --rm ingestion python parse_code.py

chunk:
	docker-compose run --rm ingestion python chunk_documents.py

index:
	docker-compose run --rm vector_store python faiss_manager.py

start:
	docker-compose up -d

stop:
	docker-compose down

clean:
	rm -rf repos/* docs/* chunks/* vector_store/indices/*

test:
	curl http://localhost:8000/health

