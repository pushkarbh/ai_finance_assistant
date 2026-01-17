#!/usr/bin/env python3
"""
Download additional articles from custom URL list.
"""

import os
import re
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "src" / "data" / "knowledge_base" / "scraped"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
REQUEST_DELAY = 1.5  # Seconds between requests


def generate_filename(url: str, title: str, source: str) -> str:
    """Generate a unique filename for the article."""
    # Clean title for filename
    clean_title = re.sub(r'[^\w\s-]', '', title.lower())
    clean_title = re.sub(r'[-\s]+', '_', clean_title)
    clean_title = clean_title[:50]  # Limit length

    # Generate hash from URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # Clean source name
    source_clean = source.lower().replace(' ', '')

    return f"{source_clean}_{clean_title}_{url_hash}.md"


def extract_investopedia_content(soup: BeautifulSoup) -> tuple[str, str]:
    """Extract title and content from Investopedia article."""
    # Get title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Get main content
    content_parts = []

    # Try to find the article body
    article_body = soup.find('div', {'id': 'article-body_1-0'}) or \
                   soup.find('div', {'id': 'mntl-sc-page'}) or \
                   soup.find('div', class_=re.compile('article-body|mntl-sc-page'))

    if article_body:
        # Extract paragraphs
        for p in article_body.find_all(['p', 'h2', 'h3', 'li']):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Skip very short paragraphs
                content_parts.append(text)

    content = '\n\n'.join(content_parts)
    return title, content


def extract_nerdwallet_content(soup: BeautifulSoup) -> tuple[str, str]:
    """Extract title and content from NerdWallet article."""
    # Get title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Get main content
    content_parts = []

    # Try to find the article body
    article_body = soup.find('article') or \
                   soup.find('div', class_=re.compile('article|content'))

    if article_body:
        for p in article_body.find_all(['p', 'h2', 'h3', 'li']):
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                content_parts.append(text)

    content = '\n\n'.join(content_parts)
    return title, content


def scrape_article(url: str, source: str, category: str) -> dict:
    """Scrape a single article."""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract content based on source
        if 'investopedia.com' in url:
            title, content = extract_investopedia_content(soup)
        elif 'nerdwallet.com' in url:
            title, content = extract_nerdwallet_content(soup)
        else:
            # Generic extraction
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"

            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        return {
            'url': url,
            'title': title,
            'source': source,
            'category': category,
            'content': content,
            'date_scraped': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"  Error: {e}")
        return None


def save_article(article: dict, output_dir: Path) -> str:
    """Save article as markdown file with frontmatter."""
    filename = generate_filename(article['url'], article['title'], article['source'])
    filepath = output_dir / filename

    # Create markdown with YAML frontmatter
    markdown_content = f"""---
title: "{article['title']}"
source: "{article['source']}"
url: "{article['url']}"
category: "{article['category']}"
date_scraped: "{article['date_scraped']}"
---

# {article['title']}

{article['content']}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return filename


def main():
    """Download articles from custom URL list."""
    # Read URLs from JSON file
    import sys
    if len(sys.argv) > 1:
        urls_file = PROJECT_ROOT / "scripts" / sys.argv[1]
    else:
        urls_file = PROJECT_ROOT / "scripts" / "advanced_retirement_bonds_urls.json"

    with open(urls_file, 'r') as f:
        urls_data = json.load(f)

    print("=" * 60)
    print("DOWNLOADING ADVANCED RETIREMENT & BONDS ARTICLES")
    print("=" * 60)
    print(f"\nDownloading {len(urls_data)} articles to {KNOWLEDGE_BASE_PATH}")
    print("-" * 60)

    # Create output directory
    KNOWLEDGE_BASE_PATH.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_count = 0

    for idx, url_info in enumerate(urls_data, 1):
        url = url_info['url']
        source = url_info['source']
        category = url_info['category']

        print(f"[{idx}/{len(urls_data)}] Fetching: {url}")

        article = scrape_article(url, source, category)

        if article and article['content']:
            filename = save_article(article, KNOWLEDGE_BASE_PATH)
            print(f"  Saved: {filename}")
            success_count += 1
        else:
            print(f"  Failed to download or empty content")
            failed_count += 1

        # Be respectful - wait between requests
        if idx < len(urls_data):
            time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  Success: {success_count}")
    print(f"  Failed:  {failed_count}")
    print(f"  Output:  {KNOWLEDGE_BASE_PATH}")
    print("\nDone!")


if __name__ == "__main__":
    main()
