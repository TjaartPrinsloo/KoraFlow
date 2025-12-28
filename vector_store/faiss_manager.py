#!/usr/bin/env python3
"""
FAISS Vector Store Manager
Manages FAISS index for storing and retrieving embeddings.
"""

import os
import json
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


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
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        embedding_model = config['embeddings']['model']
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Update dimension based on actual model
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.dimension}")
        
        # Initialize or load FAISS index
        self.index = self._load_or_create_index()
        self.metadata = []
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        index_file = self.index_path.with_suffix('.index')
        metadata_file = self.index_path.with_suffix('.metadata.json')
        
        if index_file.exists() and metadata_file.exists():
            print(f"Loading existing index from {index_file}")
            index = faiss.read_index(str(index_file))
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
            return index
        else:
            print("Creating new FAISS index")
            # Use L2 distance (Euclidean)
            index = faiss.IndexFlatL2(self.dimension)
            return index
    
    def generate_embeddings(self, texts, batch_size=32):
        """Generate embeddings for texts"""
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings
    
    def add_chunks(self, chunks):
        """Add chunks to the index"""
        print(f"Adding {len(chunks)} chunks to index...")
        
        # Extract content from chunks
        texts = [chunk['content'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts, batch_size=self.config['embeddings']['batch_size'])
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store metadata
        for i, chunk in enumerate(chunks):
            self.metadata.append({
                'chunk_id': chunk['chunk_id'],
                'index_id': self.index.ntotal - len(chunks) + i,
                'source': chunk['source'],
                'repo': chunk['repo'],
                'path': chunk['path'],
                'commit': chunk['commit'],
                'type': chunk['type'],
                'headings': chunk.get('headings', []),
                'line_ranges': chunk.get('line_ranges', {}),
                'metadata': chunk.get('metadata', {})
            })
        
        print(f"Index now contains {self.index.ntotal} vectors")
    
    def search(self, query_text, top_k=5):
        """Search for similar chunks"""
        # Generate embedding for query
        query_embedding = self.embedding_model.encode([query_text], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Retrieve metadata
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['distance'] = float(distance)
                result['score'] = 1 / (1 + distance)  # Convert distance to similarity score
                results.append(result)
        
        return results
    
    def save(self):
        """Save index and metadata"""
        index_file = self.index_path.with_suffix('.index')
        metadata_file = self.index_path.with_suffix('.metadata.json')
        
        print(f"Saving index to {index_file}")
        faiss.write_index(self.index, str(index_file))
        
        with open(metadata_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_vectors': self.index.ntotal,
                'dimension': self.dimension,
                'metadata': self.metadata
            }, f, indent=2)
        
        print(f"Saved {self.index.ntotal} vectors")


def main():
    """Main function to build FAISS index from chunks"""
    config = load_config()
    chunks_dir = Path(config['paths']['chunks'])
    
    # Load chunk metadata
    metadata_path = chunks_dir / "chunk_metadata.json"
    if not metadata_path.exists():
        print("Error: chunk_metadata.json not found. Run chunk_documents.py first.")
        return
    
    with open(metadata_path, 'r') as f:
        chunk_metadata = json.load(f)
    
    # Load all chunks
    print("Loading chunks...")
    chunks = []
    for chunk_info in tqdm(chunk_metadata['chunks'], desc="Loading chunks"):
        chunk_file = chunks_dir / f"{chunk_info['chunk_id']}.json"
        if chunk_file.exists():
            with open(chunk_file, 'r') as f:
                chunks.append(json.load(f))
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Initialize FAISS manager
    manager = FAISSManager(config)
    
    # Add chunks to index
    manager.add_chunks(chunks)
    
    # Save index
    manager.save()
    
    print("\nFAISS index built successfully!")


if __name__ == "__main__":
    main()

