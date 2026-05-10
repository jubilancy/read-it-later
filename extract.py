#!/usr/bin/env python3
import json
import os
import sys
import re
import requests
from datetime import datetime
from urllib.parse import urlparse
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    def handle_data(self, d):
        self.text.append(d)
    def get_data(self):
        return ''.join(self.text)

def strip_tags(html):
    """Remove HTML tags from string"""
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def slugify(text: str) -> str:
    """Convert a string into a URL-safe slug."""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text[:80] if text else "article"

def extract_with_readability(url: str):
    """Fallback: use readability-lxml directly"""
    try:
        from readability import Document
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=15)
        response.raise_for_status()
        doc = Document(response.text)
        title = doc.title()
        content = doc.summary()
        return title, content
    except Exception as e:
        print(f"  Readability failed: {e}")
        return None, None

def extract_with_newspaper(url: str):
    """Primary: use newspaper3k"""
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        return article
    except Exception as e:
        print(f"  Newspaper failed: {e}")
        return None

def extract_article(url: str) -> dict:
    """Download and parse an article using multiple methods."""
    
    title = url
    full_text = f"<p>Could not extract content from {url}</p>"
    author = "Unknown"
    pub_date = datetime.now().strftime("%B %d, %Y")
    summary = ""
    keywords = []
    top_image = ""
    
    # Method 1: Try newspaper3k
    print(f"  Trying newspaper3k...")
    article = extract_with_newspaper(url)
    
    if article and article.text:
        print(f"  ✓ Newspaper3k succeeded")
        title = article.title or url
        authors = article.authors or []
        author = ", ".join(authors) if authors else "Unknown"
        
        if article.publish_date:
            pub_date = article.publish_date.strftime("%B %d, %Y")
        
        summary = article.summary[:300] if article.summary else ""
        keywords = article.keywords[:8] if article.keywords else []
        top_image = article.top_image or ""
        
        # Get full text as HTML paragraphs
        text_content = article.text
        paragraphs = text_content.split('\n\n')
        full_text = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
    
    # Method 2: Try readability if newspaper failed
    if not article or not article.text:
        print(f"  Trying readability-lxml...")
        read_title, read_content = extract_with_readability(url)
        
        if read_title and read_content:
            print(f"  ✓ Readability succeeded")
            title = read_title or url
            # Extract plain text from HTML content
            plain_text = strip_tags(read_content)
            paragraphs = plain_text.split('\n\n')
            full_text = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
            summary = plain_text[:300]
    
    # Generate slug
    slug = slugify(title)
    # Add hash to avoid collisions
    url_hash = abs(hash(url)) % 10000
    slug = f"{slug}-{url_hash}" if slug != "article" else f"article-{url_hash}"
    
    print(f"  Title   : {title[:80]}")
    print(f"  Author  : {author}")
    print(f"  Slug    : {slug}")
    print(f"  Content length: {len(full_text)} chars")
    
    return {
        "url": url,
        "title": title,
        "author": author,
        "date": pub_date,
        "excerpt": summary,
        "top_image": top_image,
        "keywords": keywords,
        "full_text": full_text,
        "slug": slug,
        "saved_at": datetime.now().isoformat(),
    }

def main():
    payload_file = "payload.json"
    if not os.path.exists(payload_file):
        print("❌ No payload.json found")
        sys.exit(1)

    with open(payload_file, "r") as f:
        payload = json.load(f)

    # Extract URL from various trigger types
    url = None
    client_payload = payload.get("client_payload")
    if isinstance(client_payload, dict) and "url" in client_payload:
        url = client_payload["url"]
    elif "url" in payload:
        url = payload["url"]
    else:
        inputs = payload.get("inputs")
        if isinstance(inputs, dict) and "url" in inputs:
            url = inputs["url"]

    # If triggered by push (not a real article request), skip
    if not url and payload.get("ref"):
        print("ℹ️  Push event detected, no URL to process — skipping extraction")
        sys.exit(0)

    if not url:
        print("❌ No URL found in payload")
        print(f"   Payload keys: {list(payload.keys())}")
        sys.exit(1)

    print(f"🔗 Processing: {url}")

    # Load existing metadata
    metadata_file = "metadata.json"
    articles = []
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                articles = data if isinstance(data, list) else []
            except json.JSONDecodeError:
                articles = []

    # Duplicate check
    existing_urls = {a.get("url") for a in articles if isinstance(a, dict)}
    if url in existing_urls:
        print(f"⏭️  Duplicate — skipping: {url[:80]}")
    else:
        article_data = extract_article(url)
        articles.insert(0, article_data)
        print(f"✅ Saved: {article_data['title'][:80]}")

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"📚 Total articles: {len(articles)}")

if __name__ == "__main__":
    main()