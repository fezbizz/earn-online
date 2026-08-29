"""
Blog Publishing Scheduler
==========================
Staggers blog article publication — 1 per day.
Currently all 42 articles are already live on GitHub Pages.
This script manages a "featured" schedule and generates a blog index
that highlights the current day's article while keeping all articles
accessible.

Approach: Since GitHub Pages serves all files (can't truly "unpublish"
without removing files), we use a different strategy:
  - All articles stay live (Google can index them)
  - The homepage/blog index shows a "Today's Article" featured slot
  - A blog.html index page auto-updates daily via the cron job
  - This creates the appearance of daily publishing for returning visitors

The cron job runs this script every day at 9 AM to update the featured article.

Usage:
    python schedule_blog.py                # Generate blog index + update featured
    python schedule_blog.py --status       # Show schedule status
    python schedule_blog.py --dry-run      # Print what would be featured
"""

import json
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BLOG_DIR = SCRIPT_DIR / "blog"
SCHEDULE_PATH = SCRIPT_DIR / "blog_schedule.json"
BASE_URL = "https://fezbizz.github.io/earn-online"


def extract_title_from_html(html_text):
    match = re.search(r"<title>(.*?)</title>", html_text, re.I | re.DOTALL)
    if match:
        title = match.group(1).strip()
        for suffix in [" | Earn Extra Online", " — Real, Boring Systems"]:
            if title.endswith(suffix):
                title = title[:-len(suffix)]
        return title
    return "Untitled"


def extract_desc_from_html(html_text):
    match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html_text, re.I)
    if match:
        return match.group(1)
    return ""


def load_schedule():
    if SCHEDULE_PATH.exists():
        with open(SCHEDULE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_schedule(schedule):
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2)


def build_schedule():
    """Build a daily schedule from all blog articles — buyer reviews first, tutorials last."""
    if not BLOG_DIR.exists():
        print("ERROR: blog/ directory not found")
        return None

    buyer_reviews = []
    buyer_lists = []
    tutorials = []

    for f in BLOG_DIR.glob("*.html"):
        html_text = f.read_text(encoding="utf-8")
        title = extract_title_from_html(html_text)
        desc = extract_desc_from_html(html_text)
        entry = {
            "slug": f.name,
            "title": title,
            "description": desc,
            "url": f"{BASE_URL}/blog/{f.name}",
        }
        name_lower = f.name.lower()
        if "really work" in title.lower() or ("review" in name_lower and "does-it-work" in name_lower):
            buyer_reviews.append(entry)
        elif name_lower.startswith("best-") and "clickbank" not in name_lower and "affiliate" not in name_lower:
            buyer_lists.append(entry)
        else:
            tutorials.append(entry)

    # Order: buyer reviews first, then buyer lists, then tutorials last
    buyer_reviews.sort(key=lambda x: x["title"])
    buyer_lists.sort(key=lambda x: x["title"])
    tutorials.sort(key=lambda x: x["title"])
    articles = buyer_reviews + buyer_lists + tutorials

    # Assign each article to a day, starting today
    today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    schedule = {
        "start_date": today.isoformat(),
        "cadence": "1x/day",
        "total_articles": len(articles),
        "articles": [],
    }

    for i, article in enumerate(articles):
        publish_date = today + timedelta(days=i)
        article["publish_date"] = publish_date.isoformat()
        article["day_number"] = i + 1
        article["status"] = "published" if publish_date <= datetime.now() else "scheduled"
        schedule["articles"].append(article)

    save_schedule(schedule)
    return schedule


def get_today_article(schedule):
    """Get the article scheduled for today."""
    today = datetime.now().date()
    for article in schedule["articles"]:
        pub_date = datetime.fromisoformat(article["publish_date"]).date()
        if pub_date == today:
            return article
    # If past the last article, cycle back to the first
    return schedule["articles"][0] if schedule["articles"] else None


def generate_blog_index(schedule):
    """Generate a blog.html index page with today's featured article + all articles."""
    today_article = get_today_article(schedule)

    # Build article cards for all articles
    cards = []
    for article in schedule["articles"]:
        title = article["title"]
        desc = article["description"][:120]
        url = article["url"]
        day = article["day_number"]
        pub_date = datetime.fromisoformat(article["publish_date"]).strftime("%b %d")

        is_today = today_article and article["slug"] == today_article["slug"]
        featured_class = "product-card" if is_today else ""
        today_badge = '<span class="tag tag-green">TODAY</span>' if is_today else f'<span class="tag">Day {day} · {pub_date}</span>'

        cards.append(f"""    <div class="{featured_class}">
      <h3><a href="blog/{article['slug']}">{title}</a></h3>
      <div class="meta">{today_badge}</div>
      <p>{desc}...</p>
    </div>""")

    cards_html = "\n".join(cards)

    today_html = ""
    if today_article:
        today_html = f"""  <div class="callout">
    <strong>Today's article (Day {today_article['day_number']}):</strong>
    <a href="blog/{today_article['slug']}">{today_article['title']}</a>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — All Articles | Earn Extra Online</title>
  <meta name="description" content="All affiliate marketing articles — honest reviews, guides, and tutorials. Published daily.">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="Blog — Earn Extra Online">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{BASE_URL}/blog.html">
  <link rel="canonical" href="{BASE_URL}/blog.html">
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>

  <div class="site-header"><span class="brand">Earn Extra Online — Real, Boring Systems</span></div>

  <nav>
    <a href="index.html">Home</a>
    <a href="review.html">Reviews</a>
    <a href="guide.html">Guide</a>
    <a href="blog.html" class="active">Blog</a>
  </nav>

  <h1>Blog — All Articles</h1>

  <p>
    Honest affiliate marketing articles — reviews, guides, and tutorials.
    One new article featured every day. {len(schedule['articles'])} articles total.
  </p>

{today_html}

  <h2>All Articles</h2>

{cards_html}

  <footer>
    <p>Earn Extra Online — Real, Boring Systems</p>
    <p class="disclosure">This site uses affiliate links. I may earn a commission. I do not guarantee any income results.</p>
    <p>Built honest. 💪</p>
  </footer>

</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Schedule blog posts 1x/day")
    parser.add_argument("--status", action="store_true", help="Show schedule status")
    parser.add_argument("--dry-run", action="store_true", help="Print, don't write")
    args = parser.parse_args()

    # Build or load schedule
    schedule = build_schedule()

    if not schedule:
        return

    today_article = get_today_article(schedule)

    if args.status:
        print(f"\nBlog Schedule: {schedule['cadence']}")
        print(f"Total articles: {schedule['total_articles']}")
        print(f"Start date: {schedule['start_date'][:10]}")
        print(f"\nToday's featured: {today_article['title'] if today_article else 'None'}")
        print(f"  Day {today_article['day_number'] if today_article else '?'}")
        print(f"  URL: {today_article['url'] if today_article else '?'}")
        # Show next 5
        print(f"\nNext 5 articles:")
        today_idx = schedule["articles"].index(today_article) if today_article else 0
        for article in schedule["articles"][today_idx:today_idx+5]:
            pub = article["publish_date"][:10]
            print(f"  Day {article['day_number']} ({pub}): {article['title'][:60]}")
        return

    if args.dry_run:
        print(f"Today's featured: {today_article['title'] if today_article else 'None'}")
        print(f"Would generate blog.html with {len(schedule['articles'])} articles")
        return

    # Generate blog.html
    blog_html = generate_blog_index(schedule)
    blog_path = SCRIPT_DIR / "blog.html"
    with open(blog_path, "w", encoding="utf-8") as f:
        f.write(blog_html)

    print(f"Generated blog.html ({len(blog_html)} bytes)")
    print(f"Featured today: {today_article['title'] if today_article else 'None'}")
    print(f"Total articles: {len(schedule['articles'])}")

    # Update sitemap with blog.html
    sitemap_path = SCRIPT_DIR / "sitemap.xml"
    if sitemap_path.exists():
        smap = sitemap_path.read_text(encoding="utf-8")
        if "blog.html" not in smap:
            # Insert blog.html after the guide.html entry
            smap = smap.replace(
                '<url><loc>{BASE_URL}/guide.html'.format(BASE_URL=BASE_URL),
                '<url><loc>{BASE_URL}/blog.html</loc><changefreq>daily</changefreq><priority>0.8</priority></url>\n  <url><loc>{BASE_URL}/guide.html'.format(BASE_URL=BASE_URL)
            )
            with open(sitemap_path, "w", encoding="utf-8") as f:
                f.write(smap)
            print("Added blog.html to sitemap.xml")


if __name__ == "__main__":
    main()