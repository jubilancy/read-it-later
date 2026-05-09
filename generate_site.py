#!/usr/bin/env python3
"""
Generate the HTML site from metadata.json
Run as: python generate_site.py
"""

import json
import os
from datetime import datetime
from pathlib import Path

def load_articles():
    """Load articles from metadata.json"""
    if not os.path.exists('metadata.json'):
        return []
    
    with open('metadata.json', 'r') as f:
        data = json.load(f)
    
    # Handle different possible structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get('articles', [])
    return []

def generate_index_html(articles):
    """Generate the main index.html"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Reading List</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 My Reading List</h1>
            <p class="stats">{len(articles)} articles saved • Last updated: {datetime.now().strftime('%B %d, %Y')}</p>
        </header>
        
        <div class="articles-grid">
"""
    
    for article in articles:
        title = article.get('title', 'Untitled')
        url = article.get('url', '#')
        date = article.get('date', article.get('created', 'Unknown date'))
        excerpt = article.get('excerpt', article.get('description', 'No description available'))
        tags = article.get('tags', [])
        
        # Clean excerpt
        if excerpt and len(excerpt) > 200:
            excerpt = excerpt[:200] + '...'
        
        html += f"""
            <article class="article-card">
                <h2 class="article-title">
                    <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
                </h2>
                <div class="article-meta">📅 {date}</div>
                <p class="article-excerpt">{excerpt}</p>
                <div class="tags">
"""
        
        for tag in tags if isinstance(tags, list) else [tags]:
            if tag:
                html += f'                    <span class="tag">#{tag}</span>\n'
        
        html += """
                </div>
            </article>
"""
    
    html += f"""
        </div>
    </div>
    
    <script>
        // Simple search functionality
        document.addEventListener('DOMContentLoaded', function() {{
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = '🔍 Search articles...';
            searchInput.style.cssText = `
                width: 100%;
                padding: 12px;
                margin-bottom: 2rem;
                border: 1px solid var(--border);
                border-radius: 8px;
                font-size: 1rem;
            `;
            
            const header = document.querySelector('header');
            header.insertAdjacentElement('afterend', searchInput);
            
            searchInput.addEventListener('input', function(e) {{
                const query = e.target.value.toLowerCase();
                const cards = document.querySelectorAll('.article-card');
                
                cards.forEach(card => {{
                    const title = card.querySelector('.article-title').textContent.toLowerCase();
                    const excerpt = card.querySelector('.article-excerpt').textContent.toLowerCase();
                    const matches = title.includes(query) || excerpt.includes(query);
                    card.style.display = matches ? 'block' : 'none';
                }});
            }});
        }});
    </script>
</body>
</html>"""
    
    return html

def main():
    # Load articles
    articles = load_articles()
    
    # Generate site directory
    os.makedirs('site', exist_ok=True)
    
    # Generate main index
    index_html = generate_index_html(articles)
    with open('site/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Generate individual article files if needed
    os.makedirs('site/_articles', exist_ok=True)
    
    print(f"✅ Generated site with {len(articles)} articles")
    print(f"📁 Site directory: site/")
    print(f"📄 Main page: site/index.html")

if __name__ == "__main__":
    main()
