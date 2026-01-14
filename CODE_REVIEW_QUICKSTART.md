# Code Review Quick Start

Quick guide to get started with Ollama-based code review for Frappe standards.

## Quick Setup

1. **Ensure Ollama is running**
   ```bash
   ollama serve
   # In another terminal, verify:
   curl http://localhost:11434/api/tags
   ```

2. **Review a file**
   ```bash
   python scripts/review_code.py path/to/your/file.py
   ```

3. **Review a directory**
   ```bash
   python scripts/review_code.py path/to/directory/
   ```

## Example

```bash
# Review a Python API file
python scripts/review_code.py bench/apps/koraflow_core/koraflow_core/api/patient_signup.py

# Review with JSON output
python scripts/review_code.py bench/apps/koraflow_core/koraflow_core/api/patient_signup.py -f json -o review.json
```

## Pre-commit Hook

To automatically review code before committing:

```bash
# Option 1: Use pre-commit framework
cp .pre-commit-config.example.yaml .pre-commit-config.yaml
# Edit to enable frappe-code-review hook
pre-commit install

# Option 2: Direct git hook
cp scripts/pre_commit_review.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## What It Checks

- ✅ PEP 8 compliance (Python)
- ✅ Frappe coding conventions
- ✅ Proper use of Frappe APIs
- ✅ Documentation standards
- ✅ Security best practices
- ✅ Error handling patterns
- ✅ ESLint/Prettier compliance (JS/Vue)

## Troubleshooting

**Ollama not running?**
```bash
ollama serve
```

**No context found?**
- Ensure FAISS index is built (see RAG_OPTIMIZATION_GUIDE.md)
- Check that vector_store/indices/ contains index files

**Import errors?**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

For detailed documentation, see `CODE_REVIEW_GUIDE.md`.

