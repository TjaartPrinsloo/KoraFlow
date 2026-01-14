#!/usr/bin/env python3
"""
Caching Layer
In-memory cache for RAG query results to reduce token usage.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from threading import Lock


class QueryCache:
    """Thread-safe in-memory cache for RAG queries"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def _make_key(self, task_type: str, query: str, top_k: Optional[int] = None) -> str:
        """Create cache key from query parameters"""
        key_data = {
            'task_type': task_type,
            'query': query.lower().strip(),
            'top_k': top_k
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, task_type: str, query: str, top_k: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached result
        
        Returns:
            Cached result dict or None if not found/expired
        """
        key = self._make_key(task_type, query, top_k)
        
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if datetime.now() > entry['expires_at']:
                del self.cache[key]
                return None
            
            return entry['data']
    
    def set(self, task_type: str, query: str, data: Dict[str, Any], 
            ttl: Optional[int] = None, top_k: Optional[int] = None):
        """
        Cache a result
        
        Args:
            task_type: Task type
            query: Query string
            data: Data to cache
            ttl: Time-to-live in seconds (uses default if None)
            top_k: Top-K parameter
        """
        key = self._make_key(task_type, query, top_k)
        ttl = ttl or self.default_ttl
        
        with self.lock:
            self.cache[key] = {
                'data': data,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now(),
                'task_type': task_type
            }
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            now = datetime.now()
            total = len(self.cache)
            expired = sum(1 for entry in self.cache.values() if now > entry['expires_at'])
            active = total - expired
            
            return {
                'total_entries': total,
                'active_entries': active,
                'expired_entries': expired,
                'default_ttl': self.default_ttl
            }

