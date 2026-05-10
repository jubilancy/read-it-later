#!/usr/bin/env python3
import json
import os
import sys
import re
from datetime import datetime
from urllib.parse import urlparse

def slugify(text: str) -> str:
    """Convert a string into a URL-safe slug."""
    # Remove special characters, convert spaces to hyphens
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    # Limit length and remove trailing/leading hyphens
    return text[:80]

def extract_article(url: str) -> dict:
    """Download and parse an article using newspaper3k."""
    try:
        from newspaper import Article

        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

        title = article.title or url
        authors = article.authors or []
        author = ", ".join(authors) if authors else "Unknown"

        if article.publish_date:
            pub_date = article.publish_date.strftime("%B %d, %Y")
        else:
            pub_date = datetime.now().strftime("%B %d, %Y")

        summary = article.summary[:300] if article.summary else ""
        keywords = article.keywords[:8] if article.keywords else []
        top_image = article.top_image or ""

        # The full plain text – perfect for reading
        full_text = article.text if article.text else ""
        if not full_text:
            full_text = "No readable content could be extracted."

        # Generate a slug for the local article page
        base_slug = slugify(title)
        # Avoid collisions by adding a short hash of the URL
        url_hash = abs(hash(url)) % 10**6
        slug = f"{base_slug}-{url_hash}" if base_slug else f"article-{url_hash}"

        print(f"  Title   : {title[:80]}")
        print(f"  Author  : {author}")
        print(f"  Date    : {pub_date}")
        print(f"  Slug    : {slug}")

        return {
            "url": url,
            "title": title,
            "author": author,
            "date": pub_date,
            "excerpt": summary,
            "top_image": top_image,
            "keywords": keywords,
            "full_text": full_text,            # <-- stored full content
            "slug": slug,                      # <-- for local page
            "saved_at": datetime.now().isoformat(),
        }

    except Exception as exc:
        print(f"⚠️  Extraction failed ({exc}), storing only basic metadata")
        return {
            "url": url,
            "title": url,
            "author": "Unknown",
            "date": datetime.now().strftime("%B %d, %Y"),
            "excerpt": "",
            "top_image": "",
            "keywords": [],
            "full_text": f"<p>Could not extract content from {url}</p>",
            "slug": f"fallback-{abs(hash(url)) % 10**6}",
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
        print("   (Use repository_dispatch with a URL or run manually to add articles)")
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

    # Duplicate check (by URL)
    existing_urls = {a.get("url") for a in articles if isinstance(a, dict)}
    if url in existing_urls:
        print(f"⏭️  Duplicate — skipping: {url[:80]}")
    else:
        article_data = extract_article(url)
        # Newest first
        articles.insert(0, article_data)
        print(f"✅ Saved: {article_data['title'][:80]}")

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"📚 Total articles: {len(articles)}")

if __name__ == "__main__":
    main()