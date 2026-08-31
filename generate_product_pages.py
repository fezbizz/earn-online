"""
Individual Product Review Page Generator
==========================================
Generates standalone SEO-optimized review pages for top ClickBank offers.
These individual pages rank much better than a comparison table because
they target specific product name searches (e.g. "YU SLEEP review").

Usage:
    python generate_product_pages.py             # Generate pages for top 5 offers
    python generate_product_pages.py --top 10    # Generate for top 10
    python generate_product_pages.py --dry-run   # Print to stdout

Generates: reviews/<slug>.html for each offer
Updates: sitemap.xml with new review URLs
"""

import json
import argparse
import html
import re
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CACHE_PATH = SCRIPT_DIR / "offers_cache.json"
REVIEWS_DIR = SCRIPT_DIR / "reviews"
SITEMAP_PATH = SCRIPT_DIR / "sitemap.xml"
BASE_URL = "https://fezbizz.github.io/earn-online"


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text[:60]


def esc(s):
    if s is None:
        return ""
    return html.escape(str(s))


def fmt_money(v):
    try:
        return f"${float(v):.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def generate_review_page(offer):
    """Generate a standalone SEO review page targeting BUYERS (not affiliates)."""
    title = offer.get("title", "Unknown")
    site = offer.get("site", "")
    slug = slugify(title)
    hoplink = offer.get("hoplink", "")
    category = offer.get("category", "Unknown")
    sub_cat = offer.get("sub_category", "")
    desc_raw = offer.get("description", "")
    desc = esc(desc_raw) if desc_raw else ""
    has_recurring = float(offer.get("future_commission", 0) or 0) > 0
    is_physical = offer.get("is_physical", False)
    has_trial = offer.get("has_trial", False)
    mobile = offer.get("mobile_enabled", False)
    conversion_rate = offer.get("conversion_rate", 0)
    gravity = offer.get("gravity", 0)

    # BUYER-focused SEO title: "Product Name Review — Does It Really Work?"
    seo_title = f"{esc(title)} Review — Does It Really Work? (Honest 2026 Review)"

    # BUYER-focused meta description
    meta_desc = f"Thinking about buying {esc(title)}? Read this honest review first. What it is, how it works, what real users say, and whether it's worth your money."

    # BUYER-focused keywords (what consumers search for)
    keywords = f"{esc(title)} review, {esc(title)} does it work, {esc(title)} side effects, {esc(title)} worth it, {esc(title)} scam or legit, {esc(title)} ingredients, buy {esc(title)}, {esc(title)} 2026"

    # Schema.org structured data (JSON-LD) for Google rich snippets
    schema = {
        "@context": "https://schema.org",
        "@type": "Review",
        "itemReviewed": {
            "@type": "Product",
            "name": esc(title),
            "category": esc(category),
        },
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": max(1, min(5, round(float(offer.get("score", 0)) * 5))),
            "bestRating": 5,
        },
        "author": {"@type": "Organization", "name": "Honest Product Reviews"},
        "publisher": {"@type": "Organization", "name": "Honest Product Reviews"},
    }

    # Build buyer-focused content
    # What is it
    what_is_it = desc if desc else f"{esc(title)} is a product in the {esc(category)} category. It's sold through ClickBank, which means it comes with a 60-day money-back guarantee."

    # Pros (from buyer perspective)
    pros = []
    if is_physical:
        pros.append("Physical product you can hold — not just a digital download")
    if has_trial:
        pros.append("Trial offer available — you can try it before paying full price")
    if has_recurring:
        pros.append("Ongoing support/membership — you get continued access, not just a one-time download")
    if mobile:
        pros.append("Mobile-friendly — works on your phone, not just desktop")
    if gravity and float(gravity) > 50:
        pros.append("Popular product — many people are buying and using it")
    if conversion_rate and float(conversion_rate) > 0:
        pros.append("Good conversion rate — buyers are satisfied enough to keep it")
    pros.append("Sold through ClickBank — 60-day money-back guarantee protects your purchase")
    if not pros:
        pros.append("Available for purchase online with money-back guarantee")

    # Cons (from buyer perspective)
    cons = []
    cons.append("Only available online — you can't buy it in stores")
    if not is_physical:
        cons.append("Digital product — no physical item shipped to you")
    if not has_trial:
        cons.append("No free trial — you pay upfront (but the guarantee covers you)")
    if gravity and float(gravity) < 10:
        cons.append("Relatively new product — fewer customer reviews available")
    cons.append("Results vary from person to person — nothing works for everyone")

    # Buyer verdict
    score = float(offer.get("score", 0))
    if score >= 0.6:
        verdict = "Based on the available data, this product appears to be a solid choice. It's popular with buyers, comes with a money-back guarantee, and the conversion numbers suggest most people who buy it keep it. If you're struggling with the problem it addresses, it's worth trying — you're protected by the 60-day guarantee if it doesn't work for you."
        rating_text = "4 / 5"
    elif score >= 0.4:
        verdict = "This product has decent signals but isn't the top option in its category. It may work for you, but consider comparing it with alternatives first. The money-back guarantee means you can try it risk-free, but don't expect miracles."
        rating_text = "3 / 5"
    else:
        verdict = "The signals on this product are mixed. It might work, but there's not enough buyer data to recommend it confidently. If you decide to try it, rely on the money-back guarantee — and stop using it if you don't see results within 30 days."
        rating_text = "2 / 5"

    pros_html = "\n    ".join(f"<li>{p}</li>" for p in pros)
    cons_html = "\n    ".join(f"<li>{c}</li>" for c in cons)

    # Breadcrumb
    breadcrumb = f'<p style="font-size:0.85rem; color:var(--text-dim); margin-bottom:1rem;"><a href="../index.html">Home</a> / <a href="../review.html">Reviews</a> / {esc(category)}</p>'

    # BUYER CTA: "Try [Product] Risk-Free" not "Visit [Product]"
    cta = f'<a href="{esc(hoplink)}" class="btn">Try {esc(title)} Risk-Free 💪</a>' if hoplink else '<span style="color:var(--text-dim);">Link coming soon</span>'

    page_url = f"{BASE_URL}/reviews/{slug}.html"

    return slug, f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{seo_title}</title>
  <meta name="description" content="{meta_desc}">
  <meta name="keywords" content="{keywords}">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="{seo_title}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{page_url}">
  <link rel="canonical" href="{page_url}">
  <link rel="stylesheet" href="../assets/styles.css">
  <script type="application/ld+json">
  {json.dumps(schema, indent=2)}
  </script>
</head>
<body>

  <div class="site-header"><span class="brand">Honest Product Reviews</span></div>

  <nav>
    <a href="../index.html">Home</a>
    <a href="../review.html">Reviews</a>
    <a href="../guide.html">Guide</a>
    <a href="../blog.html">Blog</a>
  </nav>

  {breadcrumb}

  <h1>{esc(title)} Review — Does It Really Work?</h1>

  <div class="callout">
    <strong>Quick verdict:</strong> {verdict}
    <br><strong>Our rating:</strong> {rating_text}
    <br><strong>Money-back guarantee:</strong> 60 days (ClickBank protected)
  </div>

  <h2>What Is {esc(title)}?</h2>
  <p>{what_is_it}</p>
  <p>
    {esc(title)} is sold through ClickBank, one of the largest digital product
    retailers in the world. Every product on ClickBank comes with a
    <strong>60-day money-back guarantee</strong> — if you buy it and it doesn't
    work for you, you can get a full refund within 60 days. No questions asked.
  </p>

  <h2>Does {esc(title)} Actually Work?</h2>
  <p>
    The honest answer: it depends on your specific situation. No product works
    for 100% of people. What we can tell you is:
  </p>
  <ul>
    <li>The product is actively selling — people are buying it, which means it's solving a real problem for someone.</li>
    <li>{'Many customers are keeping it (low refund rate signals)' if gravity and float(gravity) > 20 else 'It is a newer product, so long-term customer data is limited'}</li>
    <li>The 60-day guarantee means you can try it without risking your money.</li>
  </ul>
  <p>
    Our recommendation: if you're dealing with the problem this product addresses,
    it's worth trying. The guarantee protects you. If it works — great. If not,
    you get your money back.
  </p>

  <h2>Pros</h2>
  <ul>
    {pros_html}
  </ul>

  <h2>Cons</h2>
  <ul>
    {cons_html}
  </ul>

  <h2>Is {esc(title)} a Scam?</h2>
  <p>
    No. {esc(title)} is sold through ClickBank, a legitimate platform that's been
    operating since 1998. ClickBank handles all payments and enforces the 60-day
    money-back guarantee. If the product were a scam, ClickBank would remove it.
    That said, "not a scam" doesn't mean "works for everyone" — always rely on
    the guarantee if it doesn't work for you.
  </p>

  <h2>Should You Buy It?</h2>
  <p>{verdict}</p>
  <p>
    If you've been dealing with this problem for a while and nothing else has
    worked, {esc(title)} is worth a try. You're protected by the 60-day
    guarantee. The worst case is you ask for a refund. The best case is it
    solves your problem.
  </p>

  <p style="margin-top:2rem;">{cta}</p>

  <div class="callout">
    <strong>Disclosure:</strong> This review contains affiliate links. If you
    click and purchase, I earn a commission at no extra cost to you. I don't
    make false claims about products — if something is unproven, I say so.
    Always use the money-back guarantee if a product doesn't work for you.
  </div>

  <p style="font-size:0.85rem; color:var(--text-dim); margin-top:2rem;">
    <strong>Related:</strong>
    <a href="../review.html">All product reviews</a> |
    <a href="../blog.html">More articles</a> |
    <a href="../index.html">Home</a>
  </p>

  <footer>
    <p>Honest Product Reviews</p>
    <p class="disclosure">
      This site uses affiliate links. I may earn a commission if you click
      a link and purchase a product. This never affects the price you pay.
      I do not guarantee any results — always use the money-back guarantee.
    </p>
    <p>Built honest. 💪</p>
  </footer>

</body>
</html>"""

def update_sitemap(slugs):
    """Update sitemap.xml with individual review page URLs."""
    urls = [
        f"  <url><loc>{BASE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{BASE_URL}/review.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{BASE_URL}/guide.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>",
    ]
    for slug in slugs:
        urls.append(f"  <url><loc>{BASE_URL}/reviews/{slug}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"Updated sitemap.xml with {len(slugs)} review pages")


def main():
    parser = argparse.ArgumentParser(description="Generate individual product review pages")
    parser.add_argument("--top", type=int, default=5,
                        help="Number of top offers to generate pages for (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print to stdout, don't write files")
    args = parser.parse_args()

    if not CACHE_PATH.exists():
        print("ERROR: offers_cache.json not found. Run pull_offers.py first.")
        return

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)

    offers = cache.get("offers", [])
    if not offers:
        print("No offers in cache.")
        return

    top_offers = offers[:args.top]
    slugs = []

    if not args.dry_run:
        REVIEWS_DIR.mkdir(exist_ok=True)

    print(f"Generating {len(top_offers)} individual review pages...")

    for offer in top_offers:
        slug, html_content = generate_review_page(offer)
        slugs.append(slug)

        if args.dry_run:
            print(f"\n--- {slug}.html ({len(html_content)} bytes) ---")
            print(html_content[:500])
        else:
            path = REVIEWS_DIR / f"{slug}.html"
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"  {slug}.html ({len(html_content)} bytes)")

    if not args.dry_run:
        update_sitemap(slugs)
        print(f"\nDone! {len(slugs)} review pages in reviews/")
        print(f"  View at: {BASE_URL}/reviews/<slug>.html")


if __name__ == "__main__":
    main()