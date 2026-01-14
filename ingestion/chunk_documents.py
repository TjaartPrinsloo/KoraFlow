#!/usr/bin/env python3
"""
Document Chunking Service
Chunks parsed code and documentation into normalized JSON format.
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
import hashlib
from tqdm import tqdm


def load_config():
    """Load configuration from config.yml"""
    # Try local path first, then Docker path
    local_config = Path(__file__).parent.parent / "config.yml"
    docker_config = Path("/app/config.yml")
    
    if local_config.exists():
        config_path = local_config
    elif docker_config.exists():
        config_path = docker_config
    else:
        raise FileNotFoundError(f"config.yml not found at {local_config} or {docker_config}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
        # Adjust paths for local execution
        project_docs = Path(__file__).parent.parent / "docs"
        project_chunks = Path(__file__).parent.parent / "chunks"
        if not Path(config['paths']['docs']).exists() and project_docs.exists():
            config['paths']['docs'] = str(project_docs)
        if not Path(config['paths']['chunks']).exists() and project_chunks.exists():
            config['paths']['chunks'] = str(project_chunks)
        
        return config


def create_chunk_id(source, path, line_start, line_end):
    """Create unique chunk ID"""
    content = f"{source}:{path}:{line_start}:{line_end}"
    return hashlib.md5(content.encode()).hexdigest()


def detect_task_metadata(file_path, content):
    """
    Detect task-specific metadata from file path and content
    
    Returns:
        dict with task_type, file_pattern, keywords
    """
    metadata = {
        'task_type': None,
        'file_pattern': None,
        'keywords': []
    }
    
    path_str = str(file_path).lower()
    content_lower = content.lower()
    
    # Detect task type from file path
    if 'hooks.py' in path_str:
        metadata['task_type'] = 'hook'
        metadata['file_pattern'] = '**/hooks.py'
        metadata['keywords'] = ['hook', 'doc_events', 'scheduler_events']
    elif 'patches' in path_str and path_str.endswith('.py'):
        metadata['task_type'] = 'patch'
        metadata['file_pattern'] = '**/patches/**/*.py'
        metadata['keywords'] = ['patch', 'execute', 'migrate']
    elif 'report' in path_str and path_str.endswith('.py'):
        metadata['task_type'] = 'report'
        metadata['file_pattern'] = '**/report/**/*.py'
        metadata['keywords'] = ['report', 'query', 'execute']
    elif 'api' in path_str and path_str.endswith('.py'):
        metadata['task_type'] = 'api'
        metadata['file_pattern'] = '**/api/**/*.py'
        metadata['keywords'] = ['@frappe.whitelist', 'api', 'endpoint']
    elif path_str.endswith('.js') or path_str.endswith('.vue'):
        metadata['task_type'] = 'ux'
        metadata['file_pattern'] = '**/*.js'
        metadata['keywords'] = ['frappe.ui.form', 'refresh', 'onload']
    elif 'doctype' in path_str and path_str.endswith('.json'):
        metadata['task_type'] = 'doctype'
        metadata['file_pattern'] = '**/*doctype*.json'
        metadata['keywords'] = ['doctype', 'docfield', 'field']
    
    # Detect from content if not detected from path
    if not metadata['task_type']:
        if 'has_permission' in content_lower or 'permission_query_conditions' in content_lower:
            metadata['task_type'] = 'permission'
            metadata['keywords'] = ['permission', 'has_permission', 'role']
        elif 'frappe.enqueue' in content_lower or 'background' in content_lower:
            metadata['task_type'] = 'job'
            metadata['keywords'] = ['frappe.enqueue', 'background', 'job']
        elif 'scheduler_events' in content_lower:
            metadata['task_type'] = 'scheduler'
            metadata['keywords'] = ['scheduler_events', 'daily', 'hourly']
        elif 'doctype' in content_lower and 'field' in content_lower:
            metadata['task_type'] = 'doctype'
            metadata['keywords'] = ['doctype', 'field']
    
    return metadata


def chunk_code_file(parsed_file, config):
    """Chunk a parsed code file"""
    chunks = []
    chunk_size = config['chunking']['chunk_size']
    overlap = config['chunking']['chunk_overlap']
    
    file_path = parsed_file['file_path']
    repo = parsed_file['repo']
    commit = parsed_file['commit']
    
    # Read original file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return chunks
    
    # Create chunks based on functions/classes
    if parsed_file['language'] == 'python':
        # Chunk by function/class
        for func in parsed_file.get('functions', []):
            line_start = func['line_start']
            line_end = func.get('line_end', line_start + 50)
            
            chunk_content = ''.join(lines[line_start-1:line_end])
            
            # Detect task metadata
            task_metadata = detect_task_metadata(file_path, chunk_content)
            
            chunk = {
                'chunk_id': create_chunk_id(repo, file_path, line_start, line_end),
                'source': f"{repo}/{file_path}",
                'repo': repo,
                'path': file_path,
                'commit': commit,
                'type': 'function',
                'headings': [{'level': 1, 'text': func['name']}],
                'line_ranges': {'start': line_start, 'end': line_end},
                'content': chunk_content,
                'metadata': {
                    'function_name': func['name'],
                    'docstring': func.get('docstring'),
                    'args': func.get('args', []),
                    **task_metadata
                },
                'chunk_timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        for cls in parsed_file.get('classes', []):
            line_start = cls['line_start']
            line_end = cls.get('line_end', line_start + 100)
            
            chunk_content = ''.join(lines[line_start-1:line_end])
            
            # Detect task metadata
            task_metadata = detect_task_metadata(file_path, chunk_content)
            
            chunk = {
                'chunk_id': create_chunk_id(repo, file_path, line_start, line_end),
                'source': f"{repo}/{file_path}",
                'repo': repo,
                'path': file_path,
                'commit': commit,
                'type': 'class',
                'headings': [{'level': 1, 'text': cls['name']}],
                'line_ranges': {'start': line_start, 'end': line_end},
                'content': chunk_content,
                'metadata': {
                    'class_name': cls['name'],
                    'docstring': cls.get('docstring'),
                    'bases': cls.get('bases', []),
                    **task_metadata
                },
                'chunk_timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
    
    # If no functions/classes, create sliding window chunks
    if not chunks:
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i+chunk_size]
            line_start = i + 1
            line_end = min(i + chunk_size, len(lines))
            
            chunk_content = ''.join(chunk_lines)
            
            # Detect task metadata
            task_metadata = detect_task_metadata(file_path, chunk_content)
            
            chunk = {
                'chunk_id': create_chunk_id(repo, file_path, line_start, line_end),
                'source': f"{repo}/{file_path}",
                'repo': repo,
                'path': file_path,
                'commit': commit,
                'type': 'code',
                'headings': [],
                'line_ranges': {'start': line_start, 'end': line_end},
                'content': chunk_content,
                'metadata': task_metadata,
                'chunk_timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
    
    return chunks


def chunk_documentation(doc_file, config):
    """Chunk a documentation file"""
    chunks = []
    chunk_size = config['chunking']['chunk_size']
    overlap = config['chunking']['chunk_overlap']
    
    try:
        with open(doc_file, 'r') as f:
            doc_data = json.load(f)
    except:
        return chunks
    
    if doc_data.get('status') != 'success':
        return chunks
    
    url = doc_data['url']
    headings = doc_data.get('headings', [])
    content = doc_data.get('content', '')
    
    # Split content into sentences/paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    current_chunk = []
    current_size = 0
    current_headings = []
    
    for para in paragraphs:
        para_size = len(para)
        
        if current_size + para_size > chunk_size and current_chunk:
            # Save current chunk
            chunk_content = '\n\n'.join(current_chunk)
            chunk_id = create_chunk_id('docs', url, 0, 0)
            
            # Detect task metadata for docs
            task_metadata = detect_task_metadata(url, chunk_content)
            
            chunk = {
                'chunk_id': chunk_id,
                'source': url,
                'repo': 'docs',
                'path': url,
                'commit': 'docs',
                'type': 'documentation',
                'headings': current_headings.copy(),
                'line_ranges': {'start': 0, 'end': 0},
                'content': chunk_content,
                'metadata': {
                    'title': doc_data.get('title', ''),
                    'url': url,
                    **task_metadata
                },
                'chunk_timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
            
            # Start new chunk with overlap
            overlap_text = '\n\n'.join(current_chunk[-overlap//100:]) if overlap else ''
            current_chunk = [overlap_text, para] if overlap_text else [para]
            current_size = len(chunk_content) - len(overlap_text) + para_size
        else:
            current_chunk.append(para)
            current_size += para_size
        
        # Update headings based on paragraph position
        # This is simplified - in production, you'd track heading hierarchy better
    
    # Save last chunk
    if current_chunk:
        chunk_content = '\n\n'.join(current_chunk)
        chunk_id = create_chunk_id('docs', url, 0, 0)
        
        chunk = {
            'chunk_id': chunk_id,
            'source': url,
            'repo': 'docs',
            'path': url,
            'commit': 'docs',
            'type': 'documentation',
            'headings': current_headings.copy(),
            'line_ranges': {'start': 0, 'end': 0},
            'content': chunk_content,
            'metadata': {
                'title': doc_data.get('title', ''),
                'url': url
            },
            'chunk_timestamp': datetime.now().isoformat()
        }
        chunks.append(chunk)
    
    return chunks


def main():
    """Main function to chunk all documents"""
    config = load_config()
    chunks_dir = Path(config['paths']['chunks'])
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    
    # Chunk parsed code files
    parsed_code_path = chunks_dir / "parsed_code.json"
    if parsed_code_path.exists():
        print("Chunking code files...")
        with open(parsed_code_path, 'r') as f:
            parsed_data = json.load(f)
        
        for parsed_file in tqdm(parsed_data['parsed_files'], desc="Chunking code"):
            if parsed_file.get('status') == 'success':
                file_chunks = chunk_code_file(parsed_file, config)
                all_chunks.extend(file_chunks)
    
    # Chunk documentation files
    docs_dir = Path(config['paths']['docs'])
    if not docs_dir.exists():
        # Try to create or use project-relative path
        project_docs = Path(__file__).parent.parent / "docs"
        if project_docs.exists():
            docs_dir = project_docs
    
    if docs_dir.exists():
        print("Chunking documentation files...")
        doc_files = list(docs_dir.glob("*.json"))
        doc_files = [f for f in doc_files if f.name != 'docs_metadata.json']
        
        for doc_file in tqdm(doc_files, desc="Chunking docs"):
            doc_chunks = chunk_documentation(doc_file, config)
            all_chunks.extend(doc_chunks)
    
    # Save individual chunk files
    for chunk in all_chunks:
        chunk_file = chunks_dir / f"{chunk['chunk_id']}.json"
        with open(chunk_file, 'w') as f:
            json.dump(chunk, f, indent=2)
    
    # Save chunk metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_chunks': len(all_chunks),
        'chunks': [{
            'chunk_id': c['chunk_id'],
            'source': c['source'],
            'type': c['type']
        } for c in all_chunks]
    }
    
    metadata_path = chunks_dir / "chunk_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nCreated {len(all_chunks)} chunks")
    print(f"Chunks saved to {chunks_dir}")
    print(f"Metadata saved to {metadata_path}")


if __name__ == "__main__":
    main()

