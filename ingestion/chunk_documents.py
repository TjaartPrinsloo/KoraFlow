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
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_chunk_id(source, path, line_start, line_end):
    """Create unique chunk ID"""
    content = f"{source}:{path}:{line_start}:{line_end}"
    return hashlib.md5(content.encode()).hexdigest()


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
                    'args': func.get('args', [])
                },
                'chunk_timestamp': datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        for cls in parsed_file.get('classes', []):
            line_start = cls['line_start']
            line_end = cls.get('line_end', line_start + 100)
            
            chunk_content = ''.join(lines[line_start-1:line_end])
            
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
                    'bases': cls.get('bases', [])
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
                'metadata': {},
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

