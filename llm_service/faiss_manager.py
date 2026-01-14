#!/usr/bin/env python3
"""
FAISS Manager for LLM Service
Simplified FAISS manager for the RAG pipeline.
"""

import os
import json
import yaml
import numpy as np
from pathlib import Path
from typing import Optional, Dict
import faiss
from sentence_transformers import SentenceTransformer


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
        return yaml.safe_load(f)


class FAISSManager:
    def __init__(self, config):
        self.config = config
        self.dimension = config['faiss']['dimension']
        
        # Handle both local and Docker paths
        index_path_str = config['faiss']['index_path']
        # Check if Docker path - try local equivalent first
        if '/app/' in index_path_str or index_path_str.startswith('/app'):
            # Docker path - try local equivalent
            # Get project root (go up from llm_service/faiss_manager.py to project root)
            script_dir = Path(__file__).resolve().parent  # llm_service/
            project_root = script_dir.parent  # KoraFlow/
            local_index = project_root / "vector_store" / "indices" / "koraflow_index"
            
            if local_index.with_suffix('.index').exists():
                self.index_path = local_index
            else:
                self.index_path = Path(index_path_str)
        else:
            self.index_path = Path(index_path_str)
        
        # Load embedding model
        embedding_model = config['embeddings']['model']
        self.embedding_model = SentenceTransformer(embedding_model)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Load index and metadata
        self.index = self._load_index()
        self.metadata = self._load_metadata()
    
    def _load_index(self):
        """Load FAISS index"""
        index_file = self.index_path.with_suffix('.index')
        if index_file.exists():
            return faiss.read_index(str(index_file))
        else:
            # Create empty index
            return faiss.IndexFlatL2(self.dimension)
    
    def _load_metadata(self):
        """Load metadata"""
        metadata_file = self.index_path.with_suffix('.metadata.json')
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                return data.get('metadata', [])
        return []
    
    def search(self, query_text, top_k=5, filters: Optional[Dict] = None):
        """
        Search for similar chunks with optional filtering
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            filters: Optional dict with:
                - task_type: Filter by task type (doctype, hook, patch, etc.)
                - file_pattern: Filter by file path pattern (e.g., '**/hooks.py')
                - keywords: List of keywords that must be present in metadata
                - repo: Filter by repository name
        """
        query_embedding = self.embedding_model.encode([query_text], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        
        # Search more results if filtering is applied
        search_k = top_k * 3 if filters else top_k
        distances, indices = self.index.search(query_embedding, search_k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if 0 <= idx < len(self.metadata):
                result = self.metadata[idx].copy()
                
                # Apply filters
                if filters and not self._matches_filters(result, filters):
                    continue
                
                result['distance'] = float(distance)
                result['score'] = 1 / (1 + distance)
                results.append(result)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches all filters"""
        import fnmatch
        
        # Filter by task_type
        if 'task_type' in filters:
            metadata_task_type = metadata.get('metadata', {}).get('task_type')
            if metadata_task_type != filters['task_type']:
                return False
        
        # Filter by file_pattern
        if 'file_pattern' in filters:
            path = metadata.get('path', '')
            pattern = filters['file_pattern']
            if not fnmatch.fnmatch(path, pattern) and pattern not in path:
                return False
        
        # Filter by keywords
        if 'keywords' in filters:
            keywords = filters['keywords']
            content = metadata.get('content', '').lower()
            metadata_keywords = metadata.get('metadata', {}).get('keywords', [])
            
            # Check if any keyword matches
            found = False
            for keyword in keywords:
                if keyword.lower() in content or keyword.lower() in str(metadata_keywords).lower():
                    found = True
                    break
            
            if not found:
                return False
        
        # Filter by repo
        if 'repo' in filters:
            if metadata.get('repo') != filters['repo']:
                return False
        
        return True
    
    def filter_by_type(self, task_type: str, query_text: str, top_k: int = 5):
        """Search filtered by task type"""
        return self.search(query_text, top_k, filters={'task_type': task_type})
    
    def filter_by_path(self, file_pattern: str, query_text: str, top_k: int = 5):
        """Search filtered by file path pattern"""
        return self.search(query_text, top_k, filters={'file_pattern': file_pattern})
    
    def filter_by_keywords(self, keywords: list, query_text: str, top_k: int = 5):
        """Search filtered by keywords"""
        return self.search(query_text, top_k, filters={'keywords': keywords})

