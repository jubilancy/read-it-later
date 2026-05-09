#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime


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

        summary = ""
        if article.summary:
            summary = article.summary[:300]
        elif article.text:
            summary = article.text[:300]

        keywords = article.keywords[:8] if article.keywords else []
        top_image = article.top_image or ""

        print(f"  Title   : {title[:80]}")
        print(f"  Author  : {author}")
        print(f"  Date    : {pub_date}")

        return {
            "url": url,
            "title": title,
            "author": author,
            "date": pub_date,
            "excerpt": summary,
            "top_image": top_image,
            "keywords": keywords,
            "saved_at": datetime.now().isoformat(),
        }

    except Exception as exc:
        print(f"⚠️  Extraction failed ({exc}), storing URL only")
        return {
            "url": url,
            "title": url,
            "author": "Unknown",
            "date": datetime.now().strftime("%B %d, %Y"),
            "excerpt": "",
            "top_image": "",
            "keywords": [],
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
    
    # repository_dispatch: new-url event
    client_payload = payload.get("client_payload")
    if isinstance(client_payload, dict) and "url" in client_payload:
        url = client_payload["url"]
    # Direct POST with url field
    elif "url" in payload:
        url = payload["url"]
    # workflow_call inputs
    else:
        inputs = payload.get("inputs")
        if isinstance(inputs, dict) and "url" in inputs:
            url = inputs["url"]
    
    # If triggered by push (not a real article request), skip processing
    if not url and payload.get("ref"):
        print("ℹ️  Push event detected, no URL to process — skipping extraction")
        print("   (Use repository_dispatch with a URL or run manually to add articles)")
        sys.exit(0)

    if not url:
        print("❌ No URL found in payload")
        print(f"   Payload keys: {list(payload.keys())}")
        print(f"   Event type: {payload.get('action', 'unknown')}")
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
        # Newest first
        articles.insert(0, article_data)
        print(f"✅ Saved: {article_data['title'][:80]}")

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"📚 Total articles: {len(articles)}")


if __name__ == "__main__":
    main()
