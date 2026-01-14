# Code Review with Ollama RAG

This guide explains how to use the Ollama-based code review tool that checks your code against Frappe Framework standards using RAG (Retrieval-Augmented Generation).

## Overview

The code review tool uses:
- **Ollama** for LLM-based code analysis
- **RAG Pipeline** to retrieve relevant Frappe standards and examples from the codebase
- **FAISS** vector store for efficient similarity search

## Prerequisites

1. **Ollama installed and running**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the model (default: llama3)
   ollama pull llama3
   
   # Verify Ollama is running
   curl http://localhost:11434/api/tags
   ```

2. **RAG Pipeline initialized**
   - The FAISS index should be built with Frappe/ERPNext code
   - See `RAG_OPTIMIZATION_GUIDE.md` for setup instructions

3. **Python dependencies**
   ```bash
   pip install -r llm_service/requirements.txt
   ```

## Usage

### Review a Single File

```bash
python scripts/review_code.py path/to/file.py
```

### Review a Directory

```bash
python scripts/review_code.py path/to/directory/
```

### Options

- `-f, --format`: Output format (`text` or `json`)
- `-o, --output`: Output file (for single file) or directory (for directory review)
- `--extensions`: File extensions to review (default: `.py .js .vue .scss`)

### Examples

```bash
# Review a Python file
python scripts/review_code.py bench/apps/koraflow_core/koraflow_core/api/patient_signup.py

# Review with JSON output
python scripts/review_code.py path/to/file.py -f json -o review.json

# Review all Python files in a directory
python scripts/review_code.py bench/apps/koraflow_core/ --extensions .py

# Review and save results
python scripts/review_code.py bench/apps/koraflow_core/ -o reviews/
```

## Pre-commit Hook Integration

### Option 1: Using pre-commit framework

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: frappe-code-review
        name: Frappe Code Review (Ollama RAG)
        entry: python scripts/pre_commit_review.py
        language: system
        types: [python, javascript]
        pass_filenames: false
```

Then install:
```bash
pre-commit install
```

### Option 2: Git hook directly

```bash
# Copy the pre-commit hook
cp scripts/pre_commit_review.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Review Output Format

### Text Format

```
================================================================================
CODE REVIEW RESULTS
================================================================================

SUMMARY:
--------------------------------------------------------------------------------
Overall assessment of the code...

SCORE: 85/100

ISSUES:
--------------------------------------------------------------------------------
[ERROR] Line 42 - PEP 8
  Missing docstring for function
  Suggestion: Add a docstring describing the function's purpose

[WARNING] Line 67 - Frappe Convention
  Direct database query instead of using frappe.db.get_value
  Suggestion: Use frappe.db.get_value() for better maintainability

SUGGESTIONS:
--------------------------------------------------------------------------------
1. Consider adding type hints for better code clarity
2. Extract magic numbers into named constants

POSITIVE FEEDBACK:
--------------------------------------------------------------------------------
✓ Good use of error handling
✓ Proper use of Frappe permissions API
✓ Clean code structure

REFERENCES:
--------------------------------------------------------------------------------
  - frappe/frappe/database/database.py
  - erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py
```

### JSON Format

```json
{
  "summary": "Overall assessment...",
  "score": 85,
  "issues": [
    {
      "severity": "error",
      "line": 42,
      "rule": "PEP 8",
      "message": "Missing docstring",
      "suggestion": "Add docstring"
    }
  ],
  "suggestions": ["Consider type hints"],
  "positive_feedback": ["Good error handling"],
  "citations": ["frappe/frappe/database/database.py"]
}
```

## What Gets Reviewed

The tool checks for:

1. **Python Code**
   - PEP 8 compliance
   - Frappe-specific patterns
   - Proper use of Frappe APIs
   - Docstring conventions
   - Import organization
   - Error handling patterns

2. **JavaScript/Vue Code**
   - ESLint compliance
   - Prettier formatting
   - Frappe UI patterns
   - Vue.js best practices
   - Frappe client-side API usage

3. **SCSS Code**
   - Prettier formatting
   - Frappe design system compliance
   - CSS best practices

## Configuration

Edit `config.yml` to customize:

```yaml
task_routing:
  tasks:
    code_review:
      top_k: 5                    # Number of context chunks to retrieve
      max_context_chars: 1000     # Max characters per chunk
      use_template: false         # Use template-based prompts
      temperature: 0.3            # LLM temperature (lower = more focused)
```

## Troubleshooting

### Ollama not available

```
Error: Ollama API error: Connection refused
```

**Solution**: Make sure Ollama is running:
```bash
ollama serve
```

### No relevant context found

```
Error: No relevant context found for code_review task
```

**Solution**: 
1. Ensure FAISS index is built with Frappe code
2. Check that `vector_store/indices/` contains the index files
3. Verify `config.yml` paths are correct

### Import errors

```
ModuleNotFoundError: No module named 'llm_service'
```

**Solution**: Run from project root or add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r llm_service/requirements.txt
      - name: Setup Ollama
        run: |
          curl -fsSL https://ollama.ai/install.sh | sh
          ollama pull llama3
          ollama serve &
      - name: Review code
        run: |
          python scripts/review_code.py . --extensions .py .js .vue
```

## Best Practices

1. **Review before committing**: Use pre-commit hooks
2. **Fix issues incrementally**: Address high-severity issues first
3. **Learn from feedback**: Use citations to understand Frappe patterns
4. **Regular reviews**: Review code regularly, not just before commits
5. **Team alignment**: Share review results with team for consistency

## Limitations

- Requires Ollama to be running locally or accessible
- FAISS index must be built and up-to-date
- Review quality depends on the quality of indexed code
- May not catch all issues; use alongside traditional linters

## Support

For issues or questions:
1. Check `RAG_OPTIMIZATION_GUIDE.md` for RAG setup
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check FAISS index: `ls vector_store/indices/`

