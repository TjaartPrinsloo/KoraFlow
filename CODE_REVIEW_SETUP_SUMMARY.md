# Code Review Setup Summary

## What Was Created

A complete code review system using Ollama LLM and RAG (Retrieval-Augmented Generation) to review code against Frappe Framework standards.

### Core Components

1. **Code Review Handler** (`llm_service/handlers/code_review_handler.py`)
   - Integrates with existing RAG pipeline
   - Retrieves relevant Frappe standards from FAISS index
   - Uses Ollama to analyze code against standards
   - Returns structured review results

2. **CLI Review Tool** (`scripts/review_code.py`)
   - Command-line interface for reviewing files/directories
   - Supports text and JSON output formats
   - Can review single files or entire directories
   - Exit codes for CI/CD integration

3. **Pre-commit Hook** (`scripts/pre_commit_review.py`)
   - Git pre-commit hook integration
   - Automatically reviews staged files
   - Prevents commits with code quality issues

4. **Configuration Updates**
   - Added `code_review` task to `config.yml`
   - Integrated handler into RAG pipeline
   - Updated handlers module exports

5. **Documentation**
   - `CODE_REVIEW_GUIDE.md` - Comprehensive guide
   - `CODE_REVIEW_QUICKSTART.md` - Quick start guide
   - `.pre-commit-config.example.yaml` - Example pre-commit config

## Features

✅ **Intelligent Code Review**
   - Uses RAG to retrieve relevant Frappe standards
   - Context-aware analysis based on file type
   - Provides citations to standards/examples

✅ **Multi-language Support**
   - Python (PEP 8, Frappe conventions)
   - JavaScript (ESLint, Prettier)
   - Vue.js (Vue best practices)
   - SCSS (Design system compliance)

✅ **Structured Output**
   - Text format for human reading
   - JSON format for automation
   - Severity levels (error/warning/info)
   - Line-by-line issue reporting

✅ **Integration Ready**
   - Pre-commit hooks
   - CI/CD compatible
   - Exit codes for automation

## Usage Examples

### Review Single File
```bash
python scripts/review_code.py path/to/file.py
```

### Review Directory
```bash
python scripts/review_code.py path/to/directory/
```

### JSON Output
```bash
python scripts/review_code.py file.py -f json -o review.json
```

### Pre-commit Hook
```bash
# Install pre-commit hook
cp scripts/pre_commit_review.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Requirements

1. **Ollama running** (default: http://localhost:11434)
   ```bash
   ollama serve
   ollama pull llama3  # or your preferred model
   ```

2. **FAISS Index built** with Frappe/ERPNext code
   - See `RAG_OPTIMIZATION_GUIDE.md` for setup
   - Index should be at `vector_store/indices/koraflow_index`

3. **Python Dependencies**
   ```bash
   pip install -r llm_service/requirements.txt
   ```

## Configuration

Edit `config.yml` to customize:

```yaml
task_routing:
  tasks:
    code_review:
      top_k: 5                    # Context chunks to retrieve
      max_context_chars: 1000     # Max chars per chunk
      temperature: 0.3            # LLM temperature
```

## Integration Points

### RAG Pipeline
- Handler registered in `RAGPipeline.handlers['code_review']`
- Uses existing FAISS manager and Ollama client
- Leverages task routing infrastructure

### Pre-commit Framework
- Compatible with pre-commit framework
- Can be added to `.pre-commit-config.yaml`
- Works standalone as git hook

### CI/CD
- Exit codes: 0 = pass, 1 = fail
- JSON output for parsing
- Can be integrated into GitHub Actions, GitLab CI, etc.

## Next Steps

1. **Build FAISS Index** (if not already done)
   ```bash
   # Follow RAG_OPTIMIZATION_GUIDE.md
   ```

2. **Test Review Tool**
   ```bash
   python scripts/review_code.py scripts/review_code.py
   ```

3. **Set Up Pre-commit Hook** (optional)
   ```bash
   cp scripts/pre_commit_review.py .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

4. **Customize Configuration**
   - Adjust `config.yml` settings
   - Modify review prompts if needed
   - Add custom standards to FAISS index

## Files Created/Modified

### New Files
- `llm_service/handlers/code_review_handler.py`
- `scripts/review_code.py`
- `scripts/pre_commit_review.py`
- `CODE_REVIEW_GUIDE.md`
- `CODE_REVIEW_QUICKSTART.md`
- `CODE_REVIEW_SETUP_SUMMARY.md`
- `.pre-commit-config.example.yaml`
- `.pre-commit-hooks.yaml`

### Modified Files
- `llm_service/handlers/__init__.py` - Added CodeReviewHandler
- `llm_service/rag_pipeline.py` - Integrated code review handler
- `config.yml` - Added code_review task configuration

## Troubleshooting

See `CODE_REVIEW_GUIDE.md` for detailed troubleshooting.

Common issues:
- **Ollama not running**: `ollama serve`
- **No context found**: Build FAISS index
- **Import errors**: Check PYTHONPATH

## Support

For issues or questions:
1. Check `CODE_REVIEW_GUIDE.md`
2. Verify Ollama is running
3. Check FAISS index exists
4. Review error messages for specific issues

