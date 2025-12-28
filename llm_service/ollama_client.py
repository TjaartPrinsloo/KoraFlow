#!/usr/bin/env python3
"""
Ollama Client
Client for interacting with Ollama API.
"""

import os
import requests
import yaml
from pathlib import Path


def load_config():
    """Load configuration from config.yml"""
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class OllamaClient:
    def __init__(self, config=None):
        if config is None:
            config = load_config()
        
        self.host = os.getenv('OLLAMA_HOST', config['ollama']['host'])
        self.port = os.getenv('OLLAMA_PORT', str(config['ollama']['port']))
        self.model = config['ollama']['model']
        self.base_url = f"http://{self.host}:{self.port}"
    
    def generate(self, prompt, context=None, temperature=None, max_tokens=None):
        """Generate text using Ollama"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False
        }
        
        if temperature is not None:
            payload['options'] = {'temperature': temperature}
        else:
            payload['options'] = {'temperature': 0.7}
        
        if max_tokens is not None:
            payload['options']['num_predict'] = max_tokens
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def chat(self, messages, temperature=None):
        """Chat with Ollama using messages format"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            'model': self.model,
            'messages': messages,
            'stream': False
        }
        
        if temperature is not None:
            payload['options'] = {'temperature': temperature}
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get('message', {}).get('content', '')
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def is_available(self):
        """Check if Ollama is available"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

