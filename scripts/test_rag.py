#!/usr/bin/env python3
"""
RAG Pipeline Test Script
Tests the RAG pipeline with sample queries.
"""

import requests
import json
import sys
from typing import Dict, Any


def test_health(base_url: str = "http://localhost:8000"):
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Ollama available: {data.get('ollama_available')}")
            print(f"  Index size: {data.get('index_size')} vectors")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_query(base_url: str, query: str, top_k: int = 5):
    """Test a query"""
    print(f"\nQuery: {query}")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{base_url}/query",
            json={"query": query, "top_k": top_k},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data.get('answer', '')[:200]}...")
            print(f"\nCitations ({len(data.get('citations', []))}):")
            for i, citation in enumerate(data.get('citations', [])[:3], 1):
                print(f"  [{i}] {citation.get('source', '')}")
                print(f"      Score: {citation.get('score', 0):.3f}")
            return True
        else:
            print(f"✗ Query failed: {response.status_code}")
            print(f"  {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Query failed: {e}")
        return False


def main():
    """Run test queries"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("=" * 60)
    print("KoraFlow RAG Pipeline Test")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print()
    
    # Test health
    if not test_health(base_url):
        print("\n✗ Health check failed. Is the service running?")
        print("  Start with: docker-compose up llm_service")
        return 1
    
    # Test queries
    test_queries = [
        "How do I create a custom DocType in Frappe?",
        "What is the difference between DocType and Custom DocType?",
        "How do I create a custom report in ERPNext?",
    ]
    
    print("\n" + "=" * 60)
    print("Running Test Queries")
    print("=" * 60)
    
    results = []
    for query in test_queries:
        result = test_query(base_url, query)
        results.append(result)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

