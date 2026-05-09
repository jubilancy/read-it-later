#!/usr/bin/env python3
"""Generate the static HTML site from metadata.json."""

import json
import os
from datetime import datetime
from pathlib import Path

CSS = """
:root {
  --primary: #3b82f6;
  --primary-dark: #2563eb;
  --bg: #f9fafb;
  --card-bg: #ffffff;
  --text: #111827;
  --text-light: #6b7280;
  --border: #e5e7eb;
  --radius: 12px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 2rem 1rem;
}

.container { max-width: 1100px; margin: 0 auto; }

/* ── Header ── */
header {
  text-align: center;
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid var(--border);
}

h1 {
  font-size: 2.25rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary), #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.stats { color: var(--text-light); font-size: 0.875rem; }

/* ── Search ── */
#search {
  display: block;
  width: 100%;
  max-width: 560px;
  margin: 0 auto 2.5rem;
  padding: 0.75rem 1.25rem;
  font-size: 1rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card-bg);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

#search:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

/* ── Grid ── */
.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

/* ── Card ── */
.article-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.article-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px -6px rgba(0,0,0,0.1);
}

.article-card img.thumb {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
}

.article-title {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.4;
}

.article-title a { color: var(--text); text-decoration: none; }
.article-title a:hover { color: var(--primary); }

.article-meta {
  font-size: 0.8rem;
  color: var(--text-light);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.article-excerpt {
  font-size: 0.875rem;
  color: var(--text-light);
  line-height: 1.55;
  flex-grow: 1;
}

.tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: auto; }

.tag {
  background: #eff6ff;
  color: var(--primary-dark);
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 500;
}

.empty {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--text-light);
  padding: 4rem 0;
  font-size: 1.1rem;
}

@media (max-width: 640px) {
  body { padding: 1rem; }
  h1 { font-size: 1.6rem; }
  .articles-grid { grid-template-columns: 1fr; }
}
"""

SEARCH_JS = """
const input = document.getElementById('search');
const cards = document.querySelectorAll('.article-card');

input.addEventListener('input', () => {
  const q = input.value.trim().toLowerCase();
  let visible = 0;
  cards.forEach(card => {
    const text = card.textContent.toLowerCase();
    const show = !q || text.includes(q);
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  });

  // Show/hide empty state
  let empty = document.querySelector('.empty');
  if (!empty) {
    empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = 'No articles match your search.';
    document.querySelector('.articles-grid').appendChild(empty);
  }
  empty.style.display = (!q || visible) ? 'none' : '';
});
"""


def escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_articles() -> list:
    if not os.path.exists("metadata.json"):
        return []
    with open("metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("articles", [])


def card_html(article: dict) -> str:
    title = escape(article.get("title") or "Untitled")
    url = escape(article.get("url", "#"))
    author = escape(article.get("author") or "")
    date = escape(article.get("date") or "")
    excerpt = escape((article.get("excerpt") or "")[:260])
    top_image = article.get("top_image") or ""
    keywords = article.get("keywords") or []

    thumb = ""
    if top_image:
        thumb = f'<img class="thumb" src="{escape(top_image)}" alt="" loading="lazy" onerror="this.style.display=\'none\'">\n'

    meta_parts = []
    if author and author != "Unknown":
        meta_parts.append(f"✍️ {author}")
    if date:
        meta_parts.append(f"📅 {date}")
    meta_html = "  ".join(meta_parts)

    tags_html = ""
    for kw in keywords[:6]:
        if kw:
            tags_html += f'<span class="tag">{escape(kw)}</span>'

    return f"""
    <article class="article-card">
      {thumb}
      <h2 class="article-title">
        <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
      </h2>
      <div class="article-meta">{meta_html}</div>
      <p class="article-excerpt">{excerpt}</p>
      <div class="tags">{tags_html}</div>
    </article>"""


def generate_index(articles: list) -> str:
    now = datetime.now().strftime("%B %d, %Y")
    count = len(articles)
    cards = "\n".join(card_html(a) for a in articles) if articles else '<p class="empty">No articles saved yet. Send a URL to get started!</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Reading List</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1>📚 My Reading List</h1>
      <p class="stats">{count} article{"s" if count != 1 else ""} saved &mdash; last updated {now}</p>
    </header>

    <input id="search" type="search" placeholder="🔍 Search articles…" autocomplete="off">

    <div class="articles-grid">
      {cards}
    </div>
  </div>

  <script>{SEARCH_JS}</script>
</body>
</html>"""


def main():
    articles = load_articles()

    Path("site/css").mkdir(parents=True, exist_ok=True)
    Path("site/_articles").mkdir(parents=True, exist_ok=True)

    # Write CSS
    with open("site/css/style.css", "w", encoding="utf-8") as f:
        f.write(CSS)

    # Write index
    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(generate_index(articles))

    # .nojekyll so GitHub Pages serves _articles without stripping it
    Path("site/.nojekyll").touch()

    print(f"✅ Site generated with {len(articles)} articles → site/")


if __name__ == "__main__":
    main()