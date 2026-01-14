#!/usr/bin/env python3
"""
Scrape Courier Guy API Documentation
Specialized scraper for The Courier Guy API documentation
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import time


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
        raise FileNotFoundError(f"config.yml not found")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def scrape_courier_guy_api_docs(base_url="https://thecourierguy.co.za/api-docs"):
    """Scrape Courier Guy API documentation"""
    config = load_config()
    
    # Use local paths when running outside Docker
    docs_path = config['paths']['docs']
    if docs_path.startswith('/app'):
        # Running locally, use project-relative path
        project_root = Path(__file__).parent.parent
        docs_dir = project_root / "docs"
    else:
        docs_dir = Path(docs_path)
    
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Scraping Courier Guy API documentation from {base_url}...")
    
    # Headers to help with Cloudflare
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        # Scrape main API docs page
        print(f"Fetching {base_url}...")
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "Courier Guy API Documentation"
        
        # Find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        # Extract headings hierarchy
        headings = []
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            text = heading.get_text().strip()
            if text:
                headings.append({
                    'level': level,
                    'text': text,
                    'id': heading.get('id', '')
                })
        
        # Remove script, style, nav, footer, header
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Extract text content
        content = main_content.get_text(separator='\n', strip=True)
        
        # Extract code blocks (API examples, request/response formats)
        code_blocks = []
        for code in main_content.find_all(['code', 'pre']):
            code_text = code.get_text().strip()
            if code_text:
                language = ''
                if code.get('class'):
                    classes = code.get('class', [])
                    for cls in classes:
                        if 'language-' in cls or 'lang-' in cls:
                            language = cls.replace('language-', '').replace('lang-', '')
                code_blocks.append({
                    'language': language,
                    'content': code_text
                })
        
        # Extract API endpoint information
        api_endpoints = []
        # Look for common API documentation patterns
        for section in main_content.find_all(['section', 'div'], class_=lambda x: x and ('api' in str(x).lower() or 'endpoint' in str(x).lower())):
            endpoint_text = section.get_text().strip()
            if endpoint_text:
                api_endpoints.append(endpoint_text)
        
        # Extract links to other API docs pages
        links = []
        for link in main_content.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            if 'api-docs' in absolute_url or 'api' in absolute_url.lower():
                links.append({
                    'text': link.get_text().strip(),
                    'href': absolute_url
                })
        
        # Create document data
        doc_data = {
            'url': base_url,
            'title': title_text,
            'headings': headings,
            'content': content,
            'code_blocks': code_blocks,
            'api_endpoints': api_endpoints,
            'links': links,
            'scrape_timestamp': datetime.now().isoformat(),
            'status': 'success',
            'source': 'courier_guy_api'
        }
        
        # Save document
        doc_file = docs_dir / "courier_guy_api_docs.json"
        with open(doc_file, 'w') as f:
            json.dump(doc_data, f, indent=2)
        
        print(f"✓ Scraped Courier Guy API documentation")
        print(f"  - Title: {title_text}")
        print(f"  - Headings: {len(headings)}")
        print(f"  - Code blocks: {len(code_blocks)}")
        print(f"  - Content length: {len(content)} characters")
        print(f"  - Saved to: {doc_file}")
        
        # Also try to find and scrape additional API documentation pages
        additional_urls = []
        for link in links[:10]:  # Limit to first 10 links
            href = link['href']
            if href not in [base_url] and 'api-docs' in href:
                additional_urls.append(href)
        
        if additional_urls:
            print(f"\nFound {len(additional_urls)} additional API documentation pages")
            for url in tqdm(additional_urls[:5], desc="Scraping additional pages"):  # Limit to 5 pages
                try:
                    time.sleep(1)  # Be respectful
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        main_content = soup.find('main') or soup.find('article') or soup.find('body')
                        
                        # Extract content
                        for element in soup(["script", "style", "nav", "footer", "header"]):
                            element.decompose()
                        
                        content = main_content.get_text(separator='\n', strip=True) if main_content else ""
                        title = soup.find('title')
                        title_text = title.get_text() if title else url
                        
                        # Save additional page
                        url_path = urlparse(url).path.strip('/').replace('/', '_')
                        if not url_path:
                            url_path = 'index'
                        
                        additional_doc = {
                            'url': url,
                            'title': title_text,
                            'content': content,
                            'scrape_timestamp': datetime.now().isoformat(),
                            'status': 'success',
                            'source': 'courier_guy_api'
                        }
                        
                        doc_file = docs_dir / f"courier_guy_api_{url_path}.json"
                        with open(doc_file, 'w') as f:
                            json.dump(additional_doc, f, indent=2)
                except Exception as e:
                    print(f"  ⚠ Failed to scrape {url}: {e}")
        
        return doc_data
        
    except Exception as e:
        print(f"Error scraping Courier Guy API docs: {e}")
        return {
            'url': base_url,
            'status': 'error',
            'error': str(e),
            'scrape_timestamp': datetime.now().isoformat()
        }


def main():
    """Main function"""
    result = scrape_courier_guy_api_docs()
    
    if result.get('status') == 'success':
        print("\n✅ Courier Guy API documentation scraped successfully!")
        print("\nNext steps:")
        print("1. Run chunk_documents.py to chunk the documentation")
        print("2. Run faiss_manager.py to build the index")
    else:
        print(f"\n❌ Failed to scrape documentation: {result.get('error')}")


if __name__ == "__main__":
    main()

