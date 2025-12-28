#!/usr/bin/env python3
"""
Documentation Scraping Service
Scrapes Frappe documentation and preserves structure.
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
    config_path = Path("/app/config.yml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def scrape_page(url, base_url):
    """Scrape a single documentation page"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else ""
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        # Extract headings hierarchy
        headings = []
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            text = heading.get_text().strip()
            headings.append({
                'level': level,
                'text': text,
                'id': heading.get('id', '')
            })
        
        # Extract text content
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        content = main_content.get_text(separator='\n', strip=True)
        
        # Extract code blocks
        code_blocks = []
        for code in main_content.find_all('code'):
            code_blocks.append({
                'language': code.get('class', [''])[0] if code.get('class') else '',
                'content': code.get_text()
            })
        
        # Extract links
        links = []
        for link in main_content.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            links.append({
                'text': link.get_text().strip(),
                'href': absolute_url
            })
        
        return {
            'url': url,
            'title': title_text,
            'headings': headings,
            'content': content,
            'code_blocks': code_blocks,
            'links': links,
            'scrape_timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
    except Exception as e:
        return {
            'url': url,
            'status': 'error',
            'error': str(e),
            'scrape_timestamp': datetime.now().isoformat()
        }


def get_doc_urls(base_url, max_pages=1000):
    """Get list of documentation URLs to scrape"""
    # This is a simplified version - in production, you'd want to crawl the sitemap
    # or use the documentation API if available
    urls = []
    
    # Start with main documentation pages
    start_urls = [
        f"{base_url}/docs",
        f"{base_url}/docs/user",
        f"{base_url}/docs/developer",
        f"{base_url}/docs/api",
    ]
    
    visited = set()
    to_visit = start_urls.copy()
    
    while to_visit and len(urls) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        
        visited.add(url)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                urls.append(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find links to other documentation pages
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    if base_url in absolute_url and absolute_url not in visited:
                        to_visit.append(absolute_url)
        except:
            pass
        
        time.sleep(0.5)  # Be respectful
    
    return urls


def main():
    """Main function to scrape all documentation"""
    config = load_config()
    docs_dir = Path(config['paths']['docs'])
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'documents': []
    }
    
    for doc_config in config['documentation']:
        base_url = doc_config['url']
        print(f"Scraping documentation from {base_url}...")
        
        # Get URLs to scrape
        urls = get_doc_urls(base_url, max_pages=500)
        
        for url in tqdm(urls, desc=f"Scraping {base_url}"):
            doc_data = scrape_page(url, base_url)
            
            if doc_data['status'] == 'success':
                # Save individual document
                url_path = urlparse(url).path.strip('/').replace('/', '_')
                if not url_path:
                    url_path = 'index'
                
                doc_file = docs_dir / f"{url_path}.json"
                with open(doc_file, 'w') as f:
                    json.dump(doc_data, f, indent=2)
            
            metadata['documents'].append(doc_data)
            time.sleep(0.5)  # Be respectful
    
    # Save metadata
    metadata_path = docs_dir / "docs_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nScraped {len([d for d in metadata['documents'] if d['status'] == 'success'])} documents")
    print(f"Metadata saved to {metadata_path}")


if __name__ == "__main__":
    main()

