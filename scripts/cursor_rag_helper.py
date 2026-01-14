#!/usr/bin/env python3
"""
Cursor RAG Helper
CLI tool for Cursor to call the local RAG pipeline.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def query_rag(query: str, base_url: str = "http://localhost:8001", top_k: int = 5) -> dict:
    """
    Query the RAG pipeline
    
    Args:
        query: User query
        base_url: RAG service base URL
        top_k: Number of results to retrieve
        
    Returns:
        Response dict with answer and citations
    """
    try:
        response = requests.post(
            f"{base_url}/query",
            json={"query": query, "top_k": top_k},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Error: RAG service not running. Start it with: docker-compose up llm_service")
        sys.exit(1)
    except Exception as e:
        print(f"Error querying RAG: {e}")
        sys.exit(1)


def check_health(base_url: str = "http://localhost:8001") -> bool:
    """Check if RAG service is healthy"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python cursor_rag_helper.py '<query>' [top_k]")
        print("\nExample:")
        print("  python cursor_rag_helper.py 'create a DocType for Patient'")
        sys.exit(1)
    
    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Check health first
    if not check_health():
        print("Warning: RAG service may not be running or healthy")
        print("Start with: docker-compose up llm_service")
    
    # Query RAG
    result = query_rag(query, top_k=top_k)
    
    # Output result
    print("=" * 60)
    print("RAG Response")
    print("=" * 60)
    print(f"\nAnswer:\n{result.get('answer', '')}")
    
    if result.get('citations'):
        print(f"\nCitations ({len(result['citations'])}):")
        for i, citation in enumerate(result['citations'][:5], 1):
            print(f"  [{i}] {citation.get('source', 'unknown')}")
    
    print(f"\nRetrieved chunks: {result.get('retrieved_chunks', 0)}")
    
    # Return JSON for programmatic use
    if os.getenv('CURSOR_RAG_JSON'):
        print("\n" + json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

