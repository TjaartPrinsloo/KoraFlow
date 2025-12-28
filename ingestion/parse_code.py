#!/usr/bin/env python3
"""
Code Parsing Service
Parses Python and JavaScript files, extracting structure and metadata.
"""

import os
import json
import ast
import yaml
from pathlib import Path
from datetime import datetime
import re
from tqdm import tqdm


def load_config():
    """Load configuration from config.yml"""
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def parse_python_file(file_path, repo_name, commit_sha):
    """Parse a Python file and extract structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        functions = []
        classes = []
        imports = []
        docstrings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_doc = ast.get_docstring(node)
                functions.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    'docstring': func_doc,
                    'args': [arg.arg for arg in node.args.args]
                })
            
            elif isinstance(node, ast.ClassDef):
                class_doc = ast.get_docstring(node)
                classes.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    'docstring': class_doc,
                    'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) for base in node.bases]
                })
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.append({
                        'type': 'import',
                        'modules': [alias.name for alias in node.names]
                    })
                else:
                    imports.append({
                        'type': 'from',
                        'module': node.module,
                        'names': [alias.name for alias in node.names]
                    })
        
        # Extract module-level docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            docstrings.append({
                'type': 'module',
                'content': module_doc,
                'line_start': 1
            })
        
        return {
            'file_path': str(file_path),
            'repo': repo_name,
            'commit': commit_sha,
            'language': 'python',
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'docstrings': docstrings,
            'line_count': len(content.splitlines()),
            'parse_timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        return {
            'file_path': str(file_path),
            'repo': repo_name,
            'commit': commit_sha,
            'language': 'python',
            'status': 'error',
            'error': str(e),
            'parse_timestamp': datetime.now().isoformat()
        }


def parse_javascript_file(file_path, repo_name, commit_sha):
    """Parse a JavaScript file and extract structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = []
        classes = []
        
        # Extract function definitions
        func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>)'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            line_num = content[:match.start()].count('\n') + 1
            functions.append({
                'name': func_name,
                'line_start': line_num
            })
        
        # Extract class definitions
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            classes.append({
                'name': class_name,
                'line_start': line_num
            })
        
        # Check for Frappe-specific patterns (DocType definitions, etc.)
        frappe_patterns = []
        if 'frappe' in content.lower():
            # Look for DocType definitions
            doctype_pattern = r'frappe\.get_doc\(["\']([^"\']+)["\']'
            for match in re.finditer(doctype_pattern, content):
                frappe_patterns.append({
                    'type': 'doctype',
                    'name': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return {
            'file_path': str(file_path),
            'repo': repo_name,
            'commit': commit_sha,
            'language': 'javascript',
            'functions': functions,
            'classes': classes,
            'frappe_patterns': frappe_patterns,
            'line_count': len(content.splitlines()),
            'parse_timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        return {
            'file_path': str(file_path),
            'repo': repo_name,
            'commit': commit_sha,
            'language': 'javascript',
            'status': 'error',
            'error': str(e),
            'parse_timestamp': datetime.now().isoformat()
        }


def find_code_files(repos_dir, repo_name):
    """Find all Python and JavaScript files in a repository"""
    repo_path = repos_dir / repo_name
    code_files = []
    
    for ext in ['*.py', '*.js']:
        code_files.extend(repo_path.rglob(ext))
    
    # Filter out common exclusions
    excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env'}
    code_files = [f for f in code_files if not any(excluded in f.parts for excluded in excluded_dirs)]
    
    return code_files


def main():
    """Main function to parse all code files"""
    config = load_config()
    repos_dir = Path(config['paths']['repos'])
    
    # Load repo metadata to get commit SHAs
    metadata_path = Path("/app/repo_metadata.json")
    if not metadata_path.exists():
        print("Error: repo_metadata.json not found. Run clone_repos.py first.")
        return
    
    with open(metadata_path, 'r') as f:
        repo_metadata = json.load(f)
    
    # Create mapping of repo name to commit SHA
    repo_commits = {r['name']: r.get('commit_sha', 'unknown') for r in repo_metadata['repositories']}
    
    all_parsed = []
    
    for repo_config in config['repositories']:
        repo_name = repo_config['name']
        commit_sha = repo_commits.get(repo_name, 'unknown')
        
        print(f"Parsing code in {repo_name}...")
        code_files = find_code_files(repos_dir, repo_name)
        
        for file_path in tqdm(code_files, desc=f"Parsing {repo_name}"):
            if file_path.suffix == '.py':
                parsed = parse_python_file(file_path, repo_name, commit_sha)
            elif file_path.suffix == '.js':
                parsed = parse_javascript_file(file_path, repo_name, commit_sha)
            else:
                continue
            
            all_parsed.append(parsed)
    
    # Save parsed data
    output_path = Path("/app/chunks/parsed_code.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'parsed_files': all_parsed
        }, f, indent=2)
    
    print(f"\nParsed {len([p for p in all_parsed if p['status'] == 'success'])} files")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()

