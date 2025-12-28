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
import faiss
from sentence_transformers import SentenceTransformer


def load_config():
    """Load configuration from config.yml"""
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class FAISSManager:
    def __init__(self, config):
        self.config = config
        self.dimension = config['faiss']['dimension']
        self.index_path = Path(config['faiss']['index_path'])
        
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
    
    def search(self, query_text, top_k=5):
        """Search for similar chunks"""
        query_embedding = self.embedding_model.encode([query_text], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if 0 <= idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['distance'] = float(distance)
                result['score'] = 1 / (1 + distance)
                results.append(result)
        
        return results

