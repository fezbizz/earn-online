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
    """Generate a standalone SEO review page for a single offer."""
    title = offer.get("title", "Unknown")
    site = offer.get("site", "")
    slug = slugify(title)
    hoplink = offer.get("hoplink", "")
    category = offer.get("category", "Unknown")
    sub_cat = offer.get("sub_category", "")
    comm = fmt_money(offer.get("commission", 0))
    initial_comm = fmt_money(offer.get("initial_commission", 0))
    future_comm = fmt_money(offer.get("future_commission", 0))
    epc = fmt_money(offer.get("epc", 0))
    gravity = offer.get("gravity", 0)
    desc = esc(offer.get("description", "No description available."))
    has_recurring = float(offer.get("future_commission", 0) or 0) > 0
    is_physical = offer.get("is_physical", False)
    has_trial = offer.get("has_trial", False)
    mobile = offer.get("mobile_enabled", False)
    conversion_rate = offer.get("conversion_rate", 0)

    # SEO title: "Product Name Review — Worth It? (Commission, EPC, Gravity)"
    seo_title = f"{esc(title)} Review — Worth It? Real Commission & EPC Data"

    # Meta description
    meta_desc = f"Honest {esc(title)} review. Real ClickBank data: {comm} commission, {epc} EPC, gravity {gravity:.0f}. Is it worth promoting? Read before you click."

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
        "author": {"@type": "Organization", "name": "Earn Extra Online"},
        "publisher": {"@type": "Organization", "name": "Earn Extra Online"},
    }

    # Build the review content
    strengths = []
    weaknesses = []

    comm_val = float(offer.get("commission", 0) or 0)
    epc_val = float(offer.get("epc", 0) or 0)
    gravity_val = float(offer.get("gravity", 0) or 0)
    future_val = float(offer.get("future_commission", 0) or 0)

    if comm_val >= 100:
        strengths.append(f"Strong commission at {comm} per sale — above average for ClickBank.")
    elif comm_val >= 50:
        strengths.append(f"Decent commission at {comm} per sale.")
    else:
        weaknesses.append(f"Low commission at {comm} per sale — needs high traffic volume.")

    if epc_val >= 3:
        strengths.append(f"EPC of {epc} — proven conversion. Affiliates are earning per click.")
    elif epc_val > 0:
        strengths.append(f"EPC of {epc} — modest but positive.")
    else:
        weaknesses.append("EPC not reported — conversion is unproven.")

    if future_val > 0:
        strengths.append(f"Recurring revenue ({future_comm} future commission) — income compounds over time.")
    else:
        weaknesses.append("One-time payout only — no recurring income. Needs constant new traffic.")

    if gravity_val > 100:
        strengths.append(f"High gravity ({gravity_val:.0f}) — many affiliates are actively earning.")
    elif gravity_val > 20:
        strengths.append(f"Moderate gravity ({gravity_val:.0f}) — solid affiliate traction.")
    elif gravity_val > 0:
        weaknesses.append(f"Low gravity ({gravity_val:.0f}) — fewer affiliates earning, higher risk.")
    else:
        weaknesses.append("Zero gravity — no affiliate traction data. High risk.")

    if is_physical:
        strengths.append("Physical product — tangible value, lower refund rates typically.")
    if has_trial:
        strengths.append("Trial available — lower barrier to entry for buyers.")
    if mobile:
        strengths.append("Mobile-optimized — captures mobile traffic.")
    if conversion_rate and float(conversion_rate) > 0:
        strengths.append(f"Conversion rate of {float(conversion_rate):.1f}% — buyers are converting.")

    # Verdict
    score = float(offer.get("score", 0))
    if score >= 0.6:
        verdict = "Strong pick. This offer has the numbers to back it up — high commission, proven EPC, and solid gravity. Worth getting approval for if needed. Promote it."
        rating_text = "4-5 / 5"
    elif score >= 0.4:
        verdict = "Decent offer. The numbers are positive but not exceptional. Test it with a small amount of traffic before going all in."
        rating_text = "3-4 / 5"
    else:
        verdict = "Weak offer. The numbers don't justify the effort unless you have highly targeted traffic that fits this specific product."
        rating_text = "2 / 5"

    strengths_html = "\n    ".join(f"<li>{s}</li>" for s in strengths) if strengths else "<li>No notable strengths.</li>"
    weaknesses_html = "\n    ".join(f"<li>{w}</li>" for w in weaknesses) if weaknesses else "<li>No notable weaknesses.</li>"

    # Breadcrumb
    cat_slug = slugify(category)
    breadcrumb = f'<p style="font-size:0.85rem; color:var(--text-dim); margin-bottom:1rem;"><a href="../index.html">Home</a> / <a href="../review.html">Reviews</a> / {esc(category)}</p>'

    cta = f'<a href="{esc(hoplink)}" class="btn">Visit {esc(title)} 💪</a>' if hoplink else '<span style="color:var(--text-dim);">No affiliate link yet</span>'

    page_url = f"{BASE_URL}/reviews/{slug}.html"

    return slug, f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{seo_title}</title>
  <meta name="description" content="{meta_desc}">
  <meta name="keywords" content="{esc(title)} review, {esc(title)} clickbank, {esc(title)} affiliate, {esc(title)} worth it, {esc(title)} commission, {esc(category).lower()} affiliate offer">
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

  <div class="site-header"><span class="brand">Earn Extra Online — Real, Boring Systems</span></div>

  <nav>
    <a href="../index.html">Home</a>
    <a href="../review.html">Reviews</a>
    <a href="../guide.html">Guide</a>
  </nav>

  {breadcrumb}

  <h1>{esc(title)} Review</h1>

  <div class="callout">
    <strong>Quick verdict:</strong> {verdict}
    <br><strong>Rating:</strong> {rating_text}
  </div>

  <h2>The Numbers</h2>
  <table>
    <tr><th>Avg Commission</th><td>{comm}</td></tr>
    <tr><th>Initial Commission</th><td>{initial_comm}</td></tr>
    <tr><th>Future / Rebill</th><td>{future_comm}</td></tr>
    <tr><th>EPC (Earnings Per Click)</th><td>{epc}</td></tr>
    <tr><th>Gravity</th><td>{gravity:.1f}</td></tr>
    <tr><th>Category</th><td>{esc(category)}{(' — ' + esc(sub_cat)) if sub_cat else ''}</td></tr>
    <tr><th>Recurring</th><td>{'Yes' if has_recurring else 'No (one-time payout)'}</td></tr>
    <tr><th>Physical Product</th><td>{'Yes' if is_physical else 'No (digital)'}</td></tr>
    <tr><th>Trial Available</th><td>{'Yes' if has_trial else 'No'}</td></tr>
    <tr><th>Mobile Optimized</th><td>{'Yes' if mobile else 'No'}</td></tr>
  </table>

  <h2>What It Is</h2>
  <p>{desc}</p>

  <h2>Strengths</h2>
  <ul>
    {strengths_html}
  </ul>

  <h2>Weaknesses</h2>
  <ul>
    {weaknesses_html}
  </ul>

  <h2>Should You Promote It?</h2>
  <p>{verdict}</p>
  <p>
    If you have traffic in the {esc(category)} niche, this offer is worth testing.
    Start with a small amount of traffic — a blog post, a YouTube video, or a
    Pinterest pin — and see if your audience clicks and converts. Don't bet
    everything on one offer; test 2-3 and compare.
  </p>
  <p>Read the <a href="../guide.html">traffic guide</a> for free methods to get eyes on this offer.</p>

  <p style="margin-top:2rem;">{cta}</p>

  <div class="callout">
    <strong>Disclosure:</strong> This review contains affiliate links. If you
    click and purchase, I earn a commission at no extra cost to you. The data
    on this page comes directly from the ClickBank Marketplace — I don't
    invent numbers. If something is untested, I say so.
  </div>

  <p style="font-size:0.85rem; color:var(--text-dim); margin-top:2rem;">
    <strong>Related:</strong>
    <a href="../review.html">All offer reviews</a> |
    <a href="../guide.html">How to get traffic</a> |
    <a href="../index.html">Home</a>
  </p>

  <footer>
    <p>Earn Extra Online — Real, Boring Systems</p>
    <p class="disclosure">
      This site uses affiliate links. I may earn a commission if you click
      a link and purchase a product. This never affects the price you pay.
      I do not guarantee any income results.
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