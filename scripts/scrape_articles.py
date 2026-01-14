#!/usr/bin/env python3
"""
Financial Article Scraper for AI Finance Assistant.

Scrapes educational articles from Investopedia, NerdWallet, and other financial
education sites to build a comprehensive knowledge base for RAG.

Usage:
    python scripts/scrape_articles.py --discover    # Find and save URLs
    python scripts/scrape_articles.py --download    # Download articles from saved URLs
    python scripts/scrape_articles.py --all         # Both discover and download
"""

import os
import re
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "src" / "data" / "knowledge_base" / "scraped"
URLS_FILE = PROJECT_ROOT / "scripts" / "article_urls.json"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
REQUEST_DELAY = 1.5  # Seconds between requests to be respectful


@dataclass
class Article:
    """Represents a scraped article."""
    url: str
    title: str
    source: str
    category: str
    content: str
    author: Optional[str] = None
    date_published: Optional[str] = None
    date_scraped: str = ""

    def __post_init__(self):
        if not self.date_scraped:
            self.date_scraped = datetime.now().isoformat()


# =============================================================================
# IMPORTANT FINANCIAL EDUCATION URLS
# =============================================================================

CURATED_URLS = [
    # ---------------------------------------------------------------------
    # INVESTOPEDIA - Investing Basics
    # ---------------------------------------------------------------------
    {
        "url": "https://www.investopedia.com/terms/s/stock.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/b/bond.asp",
        "category": "fixed_income",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/e/etf.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/m/mutualfund.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/i/indexfund.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/d/diversification.asp",
        "category": "portfolio_management",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/a/assetallocation.asp",
        "category": "portfolio_management",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/d/dollarcostaveraging.asp",
        "category": "investing_strategies",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/c/compoundinterest.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/r/riskmanagement.asp",
        "category": "risk_management",
        "source": "Investopedia"
    },

    # ---------------------------------------------------------------------
    # INVESTOPEDIA - Retirement
    # ---------------------------------------------------------------------
    {
        "url": "https://www.investopedia.com/terms/1/401kplan.asp",
        "category": "retirement",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/i/ira.asp",
        "category": "retirement",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/r/rothira.asp",
        "category": "retirement",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/t/traditionalira.asp",
        "category": "retirement",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/r/rsu.asp",
        "category": "equity_compensation",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/e/espp.asp",
        "category": "equity_compensation",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/s/stockoption.asp",
        "category": "equity_compensation",
        "source": "Investopedia"
    },

    # ---------------------------------------------------------------------
    # INVESTOPEDIA - Taxes
    # ---------------------------------------------------------------------
    {
        "url": "https://www.investopedia.com/terms/c/capital_gains_tax.asp",
        "category": "taxes",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/t/taxlossharvesting.asp",
        "category": "taxes",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/d/dividend.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/q/qualifieddividend.asp",
        "category": "taxes",
        "source": "Investopedia"
    },

    # ---------------------------------------------------------------------
    # INVESTOPEDIA - Analysis & Metrics
    # ---------------------------------------------------------------------
    {
        "url": "https://www.investopedia.com/terms/p/price-earningsratio.asp",
        "category": "analysis",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/m/marketcapitalization.asp",
        "category": "analysis",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/e/expenseratio.asp",
        "category": "investing_basics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/b/beta.asp",
        "category": "risk_management",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/s/sharperatio.asp",
        "category": "analysis",
        "source": "Investopedia"
    },

    # ---------------------------------------------------------------------
    # INVESTOPEDIA - Market & Economy
    # ---------------------------------------------------------------------
    {
        "url": "https://www.investopedia.com/terms/b/bullmarket.asp",
        "category": "market_concepts",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/b/bearmarket.asp",
        "category": "market_concepts",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/i/inflation.asp",
        "category": "economics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/r/recession.asp",
        "category": "economics",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/f/federalreservebank.asp",
        "category": "economics",
        "source": "Investopedia"
    },

    # ---------------------------------------------------------------------
    # INVESTOPEDIA - Real Estate & Alternatives
    # ---------------------------------------------------------------------
    {
        "url": "https://www.investopedia.com/terms/r/reit.asp",
        "category": "real_estate",
        "source": "Investopedia"
    },
    {
        "url": "https://www.investopedia.com/terms/r/realestate.asp",
        "category": "real_estate",
        "source": "Investopedia"
    },

    # ---------------------------------------------------------------------
    # NERDWALLET - Personal Finance
    # ---------------------------------------------------------------------
    {
        "url": "https://www.nerdwallet.com/article/investing/how-to-start-investing",
        "category": "investing_basics",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/what-is-a-brokerage-account",
        "category": "investing_basics",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/roth-ira-vs-traditional-ira",
        "category": "retirement",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/finance/emergency-fund",
        "category": "personal_finance",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/finance/how-to-budget",
        "category": "personal_finance",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/asset-allocation",
        "category": "portfolio_management",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/index-funds-vs-mutual-funds",
        "category": "investing_basics",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/what-is-a-stock",
        "category": "investing_basics",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/what-is-an-etf",
        "category": "investing_basics",
        "source": "NerdWallet"
    },
    {
        "url": "https://www.nerdwallet.com/article/investing/retirement-planning",
        "category": "retirement",
        "source": "NerdWallet"
    },

    # ---------------------------------------------------------------------
    # THE BALANCE / BANKRATE - Additional Topics
    # ---------------------------------------------------------------------
    {
        "url": "https://www.bankrate.com/investing/what-is-diversification/",
        "category": "portfolio_management",
        "source": "Bankrate"
    },
    {
        "url": "https://www.bankrate.com/investing/what-is-compound-interest/",
        "category": "investing_basics",
        "source": "Bankrate"
    },
    {
        "url": "https://www.bankrate.com/retirement/what-is-a-401k/",
        "category": "retirement",
        "source": "Bankrate"
    },
    {
        "url": "https://www.bankrate.com/investing/what-are-bonds/",
        "category": "fixed_income",
        "source": "Bankrate"
    },
    {
        "url": "https://www.bankrate.com/taxes/capital-gains-tax/",
        "category": "taxes",
        "source": "Bankrate"
    },

    # ---------------------------------------------------------------------
    # FIDELITY - Educational Content
    # ---------------------------------------------------------------------
    {
        "url": "https://www.fidelity.com/learning-center/investment-products/etf/what-are-etfs",
        "category": "investing_basics",
        "source": "Fidelity"
    },
    {
        "url": "https://www.fidelity.com/learning-center/investment-products/mutual-funds/what-are-mutual-funds",
        "category": "investing_basics",
        "source": "Fidelity"
    },
]


def get_session() -> requests.Session:
    """Create a requests session with proper headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return session


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """Fetch a page and return BeautifulSoup object."""
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return text.strip()


def extract_investopedia_content(soup: BeautifulSoup, url: str) -> Optional[Article]:
    """Extract content from Investopedia article."""
    try:
        # Title
        title_elem = soup.find("h1", class_="article-heading") or soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Author
        author_elem = soup.find("span", class_="mntl-attribution__item-name")
        author = author_elem.get_text(strip=True) if author_elem else None

        # Date
        date_elem = soup.find("span", class_="mntl-attribution__item-date")
        date_published = date_elem.get_text(strip=True) if date_elem else None

        # Content - try multiple selectors
        content_elem = (
            soup.find("article", class_="article-content") or
            soup.find("div", class_="article-body") or
            soup.find("div", id="article-body") or
            soup.find("article")
        )

        if not content_elem:
            print(f"  Could not find content element for {url}")
            return None

        # Extract paragraphs and headers
        content_parts = []
        for elem in content_elem.find_all(["p", "h2", "h3", "li"]):
            text = clean_text(elem.get_text())
            if text and len(text) > 20:  # Skip very short snippets
                if elem.name in ["h2", "h3"]:
                    content_parts.append(f"\n## {text}\n")
                elif elem.name == "li":
                    content_parts.append(f"- {text}")
                else:
                    content_parts.append(text)

        content = "\n\n".join(content_parts)

        if len(content) < 200:
            print(f"  Content too short for {url}")
            return None

        return Article(
            url=url,
            title=title,
            source="Investopedia",
            category="",  # Will be set from CURATED_URLS
            content=content,
            author=author,
            date_published=date_published
        )

    except Exception as e:
        print(f"  Error extracting Investopedia content: {e}")
        return None


def extract_nerdwallet_content(soup: BeautifulSoup, url: str) -> Optional[Article]:
    """Extract content from NerdWallet article."""
    try:
        # Title
        title_elem = soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Author
        author_elem = soup.find("a", class_="author-link") or soup.find("span", class_="author")
        author = author_elem.get_text(strip=True) if author_elem else None

        # Content
        content_elem = (
            soup.find("div", class_="article-body") or
            soup.find("article") or
            soup.find("main")
        )

        if not content_elem:
            return None

        content_parts = []
        for elem in content_elem.find_all(["p", "h2", "h3", "li"]):
            text = clean_text(elem.get_text())
            if text and len(text) > 20:
                if elem.name in ["h2", "h3"]:
                    content_parts.append(f"\n## {text}\n")
                elif elem.name == "li":
                    content_parts.append(f"- {text}")
                else:
                    content_parts.append(text)

        content = "\n\n".join(content_parts)

        if len(content) < 200:
            return None

        return Article(
            url=url,
            title=title,
            source="NerdWallet",
            category="",
            content=content,
            author=author
        )

    except Exception as e:
        print(f"  Error extracting NerdWallet content: {e}")
        return None


def extract_generic_content(soup: BeautifulSoup, url: str, source: str) -> Optional[Article]:
    """Generic content extraction for other sites."""
    try:
        # Title
        title_elem = soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Content - try common selectors
        content_elem = (
            soup.find("article") or
            soup.find("div", class_=re.compile(r"(article|content|post|entry)", re.I)) or
            soup.find("main")
        )

        if not content_elem:
            return None

        content_parts = []
        for elem in content_elem.find_all(["p", "h2", "h3", "li"]):
            text = clean_text(elem.get_text())
            if text and len(text) > 20:
                if elem.name in ["h2", "h3"]:
                    content_parts.append(f"\n## {text}\n")
                elif elem.name == "li":
                    content_parts.append(f"- {text}")
                else:
                    content_parts.append(text)

        content = "\n\n".join(content_parts)

        if len(content) < 200:
            return None

        return Article(
            url=url,
            title=title,
            source=source,
            category="",
            content=content
        )

    except Exception as e:
        print(f"  Error extracting content: {e}")
        return None


def extract_content(soup: BeautifulSoup, url: str, source: str) -> Optional[Article]:
    """Extract content based on source."""
    if "investopedia.com" in url:
        return extract_investopedia_content(soup, url)
    elif "nerdwallet.com" in url:
        return extract_nerdwallet_content(soup, url)
    else:
        return extract_generic_content(soup, url, source)


def generate_filename(article: Article) -> str:
    """Generate a unique filename for the article."""
    # Create slug from title
    slug = re.sub(r'[^a-z0-9]+', '_', article.title.lower())
    slug = slug[:50]  # Limit length

    # Add hash for uniqueness
    url_hash = hashlib.md5(article.url.encode()).hexdigest()[:8]

    return f"{article.source.lower()}_{slug}_{url_hash}.md"


def save_article(article: Article, output_dir: Path) -> bool:
    """Save article as markdown file with metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = generate_filename(article)
    filepath = output_dir / filename

    # Format as markdown with YAML frontmatter
    content = f"""---
title: "{article.title}"
source: "{article.source}"
url: "{article.url}"
category: "{article.category}"
author: "{article.author or 'Unknown'}"
date_published: "{article.date_published or 'Unknown'}"
date_scraped: "{article.date_scraped}"
---

# {article.title}

*Source: [{article.source}]({article.url})*

{article.content}

---

*This content was scraped from {article.source} for educational purposes. Please visit the original source for the most up-to-date information.*
"""

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Saved: {filename}")
        return True
    except Exception as e:
        print(f"  Error saving {filename}: {e}")
        return False


def discover_urls() -> list[dict]:
    """Return the curated list of URLs."""
    return CURATED_URLS


def save_urls(urls: list[dict], filepath: Path):
    """Save URLs to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(urls, f, indent=2)
    print(f"Saved {len(urls)} URLs to {filepath}")


def load_urls(filepath: Path) -> list[dict]:
    """Load URLs from JSON file."""
    if not filepath.exists():
        return []
    with open(filepath, "r") as f:
        return json.load(f)


def download_articles(urls: list[dict], output_dir: Path) -> tuple[int, int]:
    """Download articles from URLs."""
    session = get_session()
    success_count = 0
    fail_count = 0

    for i, url_info in enumerate(urls, 1):
        url = url_info["url"]
        category = url_info.get("category", "general")
        source = url_info.get("source", "Unknown")

        print(f"[{i}/{len(urls)}] Fetching: {url}")

        # Be respectful with rate limiting
        time.sleep(REQUEST_DELAY)

        soup = fetch_page(url, session)
        if not soup:
            fail_count += 1
            continue

        article = extract_content(soup, url, source)
        if not article:
            print(f"  Could not extract content")
            fail_count += 1
            continue

        # Set category from URL info
        article.category = category

        if save_article(article, output_dir):
            success_count += 1
        else:
            fail_count += 1

    return success_count, fail_count


def print_summary(urls: list[dict]):
    """Print summary of URLs by source and category."""
    from collections import Counter

    sources = Counter(u["source"] for u in urls)
    categories = Counter(u["category"] for u in urls)

    print("\n" + "=" * 60)
    print("URL SUMMARY")
    print("=" * 60)

    print(f"\nTotal URLs: {len(urls)}")

    print("\nBy Source:")
    for source, count in sources.most_common():
        print(f"  {source}: {count}")

    print("\nBy Category:")
    for category, count in categories.most_common():
        print(f"  {category}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape financial education articles for RAG knowledge base"
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover and save URLs to JSON file"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download articles from saved URLs"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Both discover URLs and download articles"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=KNOWLEDGE_BASE_PATH,
        help="Output directory for downloaded articles"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of articles to download"
    )

    args = parser.parse_args()

    # Default to --all if no action specified
    if not any([args.discover, args.download, args.all]):
        args.all = True

    print("=" * 60)
    print("FINANCIAL ARTICLE SCRAPER")
    print("=" * 60)

    if args.discover or args.all:
        print("\n[1] Discovering URLs...")
        urls = discover_urls()
        print_summary(urls)
        save_urls(urls, URLS_FILE)

    if args.download or args.all:
        print("\n[2] Downloading articles...")
        urls = load_urls(URLS_FILE)

        if not urls:
            print("No URLs found. Run with --discover first.")
            return

        # Limit number of articles
        urls = urls[:args.limit]

        print(f"Downloading {len(urls)} articles to {args.output}")
        print("-" * 60)

        success, fail = download_articles(urls, args.output)

        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)
        print(f"  Success: {success}")
        print(f"  Failed:  {fail}")
        print(f"  Output:  {args.output}")

    print("\nDone!")


if __name__ == "__main__":
    main()
