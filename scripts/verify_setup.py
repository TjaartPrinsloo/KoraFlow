#!/usr/bin/env python3
"""
Setup Verification Script
Verifies that all prerequisites are met before running the pipeline.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path


def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker installed: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker not found")
            return False
    except FileNotFoundError:
        print("✗ Docker not found")
        return False


def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker Compose available: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker Compose not found")
            return False
    except FileNotFoundError:
        print("✗ Docker Compose not found")
        return False


def check_ollama():
    """Check if Ollama is running and accessible"""
    try:
        # Try localhost first
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running on localhost:11434")
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            print(f"  Available models: {', '.join(model_names) if model_names else 'None'}")
            return True
    except requests.exceptions.RequestException:
        pass
    
    try:
        # Try host.docker.internal (Docker context)
        response = requests.get('http://host.docker.internal:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is accessible from Docker at host.docker.internal:11434")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print("✗ Ollama is not running or not accessible")
    print("  Please start Ollama: ollama serve")
    print("  And pull required models: ollama pull llama3 && ollama pull nomic-embed-text")
    return False


def check_required_models():
    """Check if required Ollama models are available"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '').split(':')[0] for m in models]
            
            required = ['llama3', 'nomic-embed-text']
            missing = [m for m in required if m not in model_names]
            
            if not missing:
                print("✓ All required models are available")
                return True
            else:
                print(f"✗ Missing models: {', '.join(missing)}")
                print(f"  Install with: ollama pull {' && ollama pull '.join(missing)}")
                return False
    except:
        return False


def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python 3.10+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_config():
    """Check if config.yml exists"""
    config_path = Path(__file__).parent.parent / 'config.yml'
    if config_path.exists():
        print("✓ config.yml exists")
        return True
    else:
        print("✗ config.yml not found")
        return False


def check_directories():
    """Check if required directories exist"""
    base = Path(__file__).parent.parent
    required_dirs = ['ingestion', 'vector_store', 'llm_service', 'apps/koraflow_core']
    all_exist = True
    
    for dir_path in required_dirs:
        full_path = base / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}/ exists")
        else:
            print(f"✗ {dir_path}/ not found")
            all_exist = False
    
    return all_exist


def main():
    """Run all checks"""
    print("=" * 60)
    print("KoraFlow Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Configuration", check_config),
        ("Project Structure", check_directories),
        ("Ollama Service", check_ollama),
        ("Required Models", check_required_models),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    if all_passed:
        print("\n✓ All checks passed! You're ready to proceed.")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

