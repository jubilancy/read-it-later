#!/usr/bin/env python3
"""
Extract article metadata from URL
"""

import json
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

try:
    from newspaper import Article
except ImportError:
    print("⚠️ newspaper3k not installed, using basic extraction")
    Article = None

def extract_article(url):
    """Extract article metadata"""
    result = {
        'url': url,
        'title': url,
        'excerpt': '',
        'date': datetime.now().isoformat(),
        'tags': [],
        'saved_at': datetime.now().isoformat()
    }
    
    if Article:
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            result['title'] = article.title or url
            result['excerpt'] = article.meta_description or article.text[:200] if article.text else ''
            
            if article.publish_date:
                result['date'] = article.publish_date.isoformat()
                
        except Exception as e:
            print(f"⚠️ Newspaper extraction failed: {e}")
    
    return result

def main():
    # Load the event payload
    payload_file = 'payload.json'
    if not os.path.exists(payload_file):
        print("❌ No payload.json found")
        sys.exit(1)
    
    with open(payload_file, 'r') as f:
        payload = json.load(f)
    
    # Extract URL from the dispatch event
    url = None
    if 'client_payload' in payload and 'url' in payload['client_payload']:
        url = payload['client_payload']['url']
    elif 'inputs' in payload and 'url' in payload['inputs']:
        url = payload['inputs']['url']
    
    if not url:
        print("❌ No URL found in payload")
        sys.exit(1)
    
    print(f"📖 Extracting: {url}")
    
    # Extract article
    article_data = extract_article(url)
    
    # Load existing metadata.json
    metadata_file = 'metadata.json'
    existing_articles = []
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            existing_articles = json.load(f)
            if not isinstance(existing_articles, list):
                existing_articles = [existing_articles] if existing_articles else []
    
    # Check for duplicates
    urls_existing = [a.get('url') for a in existing_articles if isinstance(a, dict)]
    if article_data['url'] not in urls_existing:
        existing_articles.append(article_data)
        print(f"✅ Added new article: {article_data['title']}")
    else:
        print(f"⏭️  Article already exists: {article_data['title']}")
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(existing_articles, f, indent=2)
    
    print(f"📊 Total articles: {len(existing_articles)}")

if __name__ == "__main__":
    main()
