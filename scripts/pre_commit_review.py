#!/usr/bin/env python3
"""
Pre-commit hook for code review
Reviews staged files against Frappe standards.
"""

import sys
import subprocess
from pathlib import Path


def get_staged_files():
    """Get list of staged files"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return files
    except subprocess.CalledProcessError:
        return []


def filter_reviewable_files(files):
    """Filter files that can be reviewed"""
    reviewable_extensions = {'.py', '.js', '.vue', '.scss'}
    reviewable = []
    
    for file in files:
        file_path = Path(file)
        if file_path.suffix in reviewable_extensions:
            reviewable.append(file)
    
    return reviewable


def main():
    """Main pre-commit hook"""
    staged_files = get_staged_files()
    reviewable_files = filter_reviewable_files(staged_files)
    
    if not reviewable_files:
        print("No reviewable files staged")
        return 0
    
    print(f"Reviewing {len(reviewable_files)} file(s)...")
    
    # Import review function
    script_dir = Path(__file__).parent
    review_script = script_dir / 'review_code.py'
    
    # Review each file
    failed_files = []
    for file in reviewable_files:
        print(f"\n{'='*80}")
        print(f"Reviewing: {file}")
        print('='*80)
        
        try:
            result = subprocess.run(
                [sys.executable, str(review_script), file, '-f', 'text'],
                cwd=script_dir.parent,
                check=False
            )
            
            if result.returncode != 0:
                failed_files.append(file)
        except Exception as e:
            print(f"Error reviewing {file}: {e}", file=sys.stderr)
            failed_files.append(file)
    
    if failed_files:
        print("\n" + "="*80)
        print("REVIEW FAILED")
        print("="*80)
        print("The following files have issues:")
        for file in failed_files:
            print(f"  - {file}")
        print("\nPlease fix the issues before committing.")
        return 1
    
    print("\n✓ All files passed review!")
    return 0


if __name__ == '__main__':
    sys.exit(main())

