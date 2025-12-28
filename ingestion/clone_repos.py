#!/usr/bin/env python3
"""
Repository Cloning Service
Clones all specified GitHub repositories and records metadata.
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
import git
from tqdm import tqdm


def load_config():
    """Load configuration from config.yml"""
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def clone_repository(repo_config, repos_dir):
    """Clone a single repository and return metadata"""
    repo_name = repo_config['name']
    repo_url = repo_config['url']
    branch = repo_config.get('branch', 'main')
    
    repo_path = repos_dir / repo_name
    
    print(f"Cloning {repo_name}...")
    
    try:
        if repo_path.exists():
            # Update existing repo
            repo = git.Repo(repo_path)
            repo.remotes.origin.fetch()
            repo.git.checkout(branch)
            repo.remotes.origin.pull()
        else:
            # Clone new repo
            repo = git.Repo.clone_from(repo_url, repo_path, branch=branch)
        
        commit_sha = repo.head.commit.hexsha
        commit_date = repo.head.commit.committed_datetime.isoformat()
        
        return {
            'name': repo_name,
            'url': repo_url,
            'path': str(repo_path),
            'branch': branch,
            'commit_sha': commit_sha,
            'commit_date': commit_date,
            'clone_timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        print(f"Error cloning {repo_name}: {str(e)}")
        return {
            'name': repo_name,
            'url': repo_url,
            'path': str(repo_path),
            'branch': branch,
            'status': 'error',
            'error': str(e),
            'clone_timestamp': datetime.now().isoformat()
        }


def main():
    """Main function to clone all repositories"""
    config = load_config()
    repos_dir = Path(config['paths']['repos'])
    repos_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'repositories': []
    }
    
    for repo_config in tqdm(config['repositories'], desc="Cloning repositories"):
        repo_metadata = clone_repository(repo_config, repos_dir)
        metadata['repositories'].append(repo_metadata)
    
    # Save metadata
    metadata_path = Path("/app/repo_metadata.json")
    # Ensure it's a file, not a directory
    if metadata_path.is_dir():
        metadata_path = metadata_path / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nCloned {len([r for r in metadata['repositories'] if r['status'] == 'success'])} repositories")
    print(f"Metadata saved to {metadata_path}")


if __name__ == "__main__":
    main()

