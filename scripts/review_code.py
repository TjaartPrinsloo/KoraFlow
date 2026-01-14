#!/usr/bin/env python3
"""
Code Review Script
Review code files against Frappe standards using Ollama and RAG.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path to import llm_service modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_service.rag_pipeline import RAGPipeline, load_config
from llm_service.ollama_client import OllamaClient


def format_review_output(review: dict, output_format: str = 'text'):
    """Format review output"""
    if output_format == 'json':
        return json.dumps(review, indent=2)
    
    # Text format
    output = []
    output.append("=" * 80)
    output.append("CODE REVIEW RESULTS")
    output.append("=" * 80)
    output.append("")
    
    if 'review' in review:
        review_data = review['review']
    else:
        review_data = review
    
    # Summary
    if 'summary' in review_data:
        output.append("SUMMARY:")
        output.append("-" * 80)
        output.append(review_data['summary'])
        output.append("")
    
    # Score
    if 'score' in review_data and review_data['score'] is not None:
        output.append(f"SCORE: {review_data['score']}/100")
        output.append("")
    
    # Issues
    if 'issues' in review_data and review_data['issues']:
        output.append("ISSUES:")
        output.append("-" * 80)
        for issue in review_data['issues']:
            severity = issue.get('severity', 'info').upper()
            line = issue.get('line', '?')
            rule = issue.get('rule', 'Unknown')
            message = issue.get('message', '')
            suggestion = issue.get('suggestion', '')
            
            output.append(f"[{severity}] Line {line} - {rule}")
            output.append(f"  {message}")
            if suggestion:
                output.append(f"  Suggestion: {suggestion}")
            output.append("")
    
    # Suggestions
    if 'suggestions' in review_data and review_data['suggestions']:
        output.append("SUGGESTIONS:")
        output.append("-" * 80)
        for i, suggestion in enumerate(review_data['suggestions'], 1):
            output.append(f"{i}. {suggestion}")
        output.append("")
    
    # Positive feedback
    if 'positive_feedback' in review_data and review_data['positive_feedback']:
        output.append("POSITIVE FEEDBACK:")
        output.append("-" * 80)
        for feedback in review_data['positive_feedback']:
            output.append(f"✓ {feedback}")
        output.append("")
    
    # Citations
    if 'citations' in review_data and review_data['citations']:
        output.append("REFERENCES:")
        output.append("-" * 80)
        for citation in review_data['citations']:
            output.append(f"  - {citation}")
        output.append("")
    
    return "\n".join(output)


def review_file(file_path: str, output_format: str = 'text', output_file: str = None):
    """Review a single file"""
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    # Read file
    try:
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    # Detect file type
    if file_path.endswith('.py'):
        file_type = 'python'
    elif file_path.endswith('.js'):
        file_type = 'javascript'
    elif file_path.endswith('.vue'):
        file_type = 'vue'
    elif file_path.endswith('.scss'):
        file_type = 'scss'
    else:
        file_type = 'unknown'
    
    # Load config and initialize pipeline
    try:
        config = load_config()
        pipeline = RAGPipeline(config)
    except Exception as e:
        print(f"Error initializing RAG pipeline: {e}", file=sys.stderr)
        return 1
    
    # Check if code review handler is available
    if 'code_review' not in pipeline.handlers:
        print("Error: Code review handler not available", file=sys.stderr)
        return 1
    
    # Perform review
    try:
        print(f"Reviewing {file_path}...", file=sys.stderr)
        handler = pipeline.handlers['code_review']
        review = handler.review_code(code, str(file_path_obj), file_type)
        
        # Format output
        output = format_review_output({'review': review}, output_format)
        
        # Write output
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Review saved to {output_file}", file=sys.stderr)
        else:
            print(output)
        
        # Return exit code based on issues
        if 'issues' in review:
            errors = [i for i in review['issues'] if i.get('severity') == 'error']
            if errors:
                return 1
        
        return 0
        
    except Exception as e:
        print(f"Error during review: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def review_directory(directory: str, output_format: str = 'text', 
                     file_extensions: list = None, output_dir: str = None):
    """Review all files in a directory"""
    if file_extensions is None:
        file_extensions = ['.py', '.js', '.vue', '.scss']
    
    directory_path = Path(directory)
    if not directory_path.exists():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        return 1
    
    # Find all files
    files = []
    for ext in file_extensions:
        files.extend(directory_path.rglob(f'*{ext}'))
    
    if not files:
        print(f"No files found in {directory}", file=sys.stderr)
        return 0
    
    print(f"Found {len(files)} files to review", file=sys.stderr)
    
    # Review each file
    results = []
    for file_path in files:
        rel_path = file_path.relative_to(directory_path)
        print(f"\nReviewing {rel_path}...", file=sys.stderr)
        
        output_file = None
        if output_dir:
            output_path = Path(output_dir) / f"{rel_path}.review.{output_format}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_file = str(output_path)
        
        exit_code = review_file(str(file_path), output_format, output_file)
        results.append((str(rel_path), exit_code))
    
    # Summary
    print("\n" + "=" * 80, file=sys.stderr)
    print("REVIEW SUMMARY", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    passed = sum(1 for _, code in results if code == 0)
    failed = len(results) - passed
    print(f"Total files: {len(results)}", file=sys.stderr)
    print(f"Passed: {passed}", file=sys.stderr)
    print(f"Failed: {failed}", file=sys.stderr)
    
    return 1 if failed > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description='Review code against Frappe standards using Ollama and RAG'
    )
    parser.add_argument(
        'path',
        help='File or directory to review'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file (for single file) or directory (for directory review)'
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.py', '.js', '.vue', '.scss'],
        help='File extensions to review (default: .py .js .vue .scss)'
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        exit_code = review_file(str(path), args.format, args.output)
    elif path.is_dir():
        exit_code = review_directory(str(path), args.format, args.extensions, args.output)
    else:
        print(f"Error: Path not found: {path}", file=sys.stderr)
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

