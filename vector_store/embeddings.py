#!/usr/bin/env python3
"""
Embedding Generation Service
Generates embeddings using Ollama or sentence-transformers.
"""

import os
import json
import yaml
import requests
from pathlib import Path
from sentence_transformers import SentenceTransformer


def load_config():
    """Load configuration from config.yml"""
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def generate_embeddings_ollama(texts, config):
    """Generate embeddings using Ollama API"""
    ollama_host = config['ollama']['host']
    ollama_port = config['ollama']['port']
    embedding_model = config['ollama']['embedding_model']
    
    url = f"http://{ollama_host}:{ollama_port}/api/embeddings"
    
    embeddings = []
    for text in texts:
        payload = {
            'model': embedding_model,
            'prompt': text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            embeddings.append(result['embedding'])
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Fallback to zero vector
            embeddings.append([0.0] * 768)
    
    return embeddings


def generate_embeddings_local(texts, config):
    """Generate embeddings using local sentence-transformers"""
    model_name = config['embeddings']['model']
    model = SentenceTransformer(model_name)
    
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def generate_embeddings(texts, config, use_ollama=False):
    """Generate embeddings using specified method"""
    if use_ollama:
        return generate_embeddings_ollama(texts, config)
    else:
        return generate_embeddings_local(texts, config)

