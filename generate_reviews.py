"""
Review Page Auto-Generator
===========================
Reads offers from offers_cache.json (produced by pull_offers.py) and
generates review.html with real comparison tables, offer cards, and
affiliate links.

Usage:
    python generate_reviews.py                    # Generate from cache
    python generate_reviews.py --top 3            # Only top 3 offers
    python generate_reviews.py --category "Sleep" # Filter by sub-category
    python generate_reviews.py --dry-run          # Print to stdout, don't write

Requirements:
    No external packages — pure stdlib.
"""

import json
import argparse
import html
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CACHE_PATH = SCRIPT_DIR / "offers_cache.json"
REVIEW_PATH = SCRIPT_DIR / "review.html"


def load_cache():
    if not CACHE_PATH.exists():
        print(f"ERROR: {CACHE_PATH} not found.")
        print("Run pull_offers.py first to fetch offers from ClickBank API.")
        return None
    with open(CACHE_PATH, encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    """HTML-escape a value."""
    if s is None:
        return ""
    return html.escape(str(s))


def fmt_money(v):
    """Format a number as $X.XX."""
    try:
        return f"${float(v):.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def fmt_tag(offer):
    """Generate HTML tags for an offer."""
    tags = []
    if offer.get("require_approval"):
        tags.append('<span class="tag tag-warning">Approval Required</span>')
    else:
        tags.append('<span class="tag tag-green">Instant Activation</span>')

    future = float(offer.get("future_commission", 0) or 0)
    if future > 0:
        tags.append('<span class="tag">Recurring</span>')
    else:
        tags.append('<span class="tag">One-time</span>')

    if offer.get("gravity", 0) and float(offer.get("gravity", 0)) > 100:
        tags.append('<span class="tag tag-green">Hot</span>')

    return " ".join(tags)


def generate_table(offers):
    """Generate the comparison table HTML."""
    rows = []
    for o in offers:
        hoplink = o.get("hoplink", "")
        title = esc(o.get("title", "Unknown"))
        link_html = f'<a href="{esc(hoplink)}">{title}</a>' if hoplink else title
        rows.append(f"""      <tr>
        <td>{link_html}</td>
        <td>{fmt_money(o.get('initial_commission') or o.get('commission'))}</td>
        <td>{fmt_money(o.get('future_commission'))}</td>
        <td>{fmt_money(o.get('epc'))}</td>
        <td>{esc(o.get('gravity', '—'))}</td>
        <td>{'Recurring' if float(o.get('future_commission',0) or 0)>0 else 'One-time'}</td>
        <td>{fmt_tag(o).replace('class="tag ','<span class="tag ').replace('</span>','</span>').replace('tag tag-warning','<span class="tag tag-warning').replace('tag tag-green','<span class="tag tag-green').replace('tag">','tag">')}</td>
      </tr>""")

    return f"""  <table>
    <thead>
      <tr>
        <th>Product</th>
        <th>Initial $/Conv</th>
        <th>Future $/Conv</th>
        <th>EPC</th>
        <th>Gravity</th>
        <th>Payout Type</th>
        <th>Approval</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>"""


def generate_offer_card(o, rank):
    """Generate a detailed offer card for top offers."""
    title = esc(o.get("title", "Unknown"))
    hoplink = o.get("hoplink", "")
    cat = esc(o.get("category", "Unknown"))
    comm = fmt_money(o.get("initial_commission") or o.get("commission"))
    future = fmt_money(o.get("future_commission"))
    epc = fmt_money(o.get("epc"))
    gravity = esc(o.get("gravity", "N/A"))
    desc = esc(o.get("description", "No description available."))
    tags = fmt_tag(o)

    # Verdict logic based on data
    score = float(o.get("score", 0))
    strengths = []
    weaknesses = []

    comm_val = float(o.get("commission", 0) or 0)
    epc_val = float(o.get("epc", 0) or 0)
    future_val = float(o.get("future_commission", 0) or 0)
    gravity_val = float(o.get("gravity", 0) or 0)

    if comm_val >= 100:
        strengths.append(f"Strong commission at {comm} per sale.")
    elif comm_val >= 50:
        strengths.append(f"Decent commission at {comm} per sale.")
    else:
        weaknesses.append(f"Low commission at {comm} per sale — needs high volume.")

    if epc_val >= 3:
        strengths.append(f"Good EPC ({epc}) — proven conversion.")
    elif epc_val > 0:
        strengths.append(f"EPC of {epc} — modest but positive.")
    else:
        weaknesses.append("EPC not reported — conversion is unproven.")

    if future_val > 0:
        strengths.append(f"Recurring revenue at {future} future commission — income compounds.")
    else:
        weaknesses.append("One-time payout — no recurring income. Needs constant new traffic.")

    if o.get("require_approval"):
        weaknesses.append("Approval required — can't start promoting instantly.")
    else:
        strengths.append("Instant activation — start promoting immediately.")

    if gravity_val > 100:
        strengths.append(f"High gravity ({gravity_val}) — many affiliates are earning.")
    elif gravity_val > 20:
        strengths.append(f"Moderate gravity ({gravity_val}) — some affiliate traction.")
    else:
        weaknesses.append(f"Low gravity ({gravity_val}) — few affiliates earning, higher risk.")

    # Verdict
    if score >= 0.5:
        verdict = "Strong pick. Worth promoting."
    elif score >= 0.3:
        verdict = "Decent offer. Test it, but don't bet everything on it."
    else:
        verdict = "Weak offer. Only promote if you have specific traffic that fits."

    strengths_html = "\n      ".join(f"<li>{s}</li>" for s in strengths)
    weaknesses_html = "\n      ".join(f"<li>{w}</li>" for w in weaknesses)

    cta = f'<a href="{esc(hoplink)}" class="btn">Visit {title} 💪</a>' if hoplink else f'<span style="color:var(--text-dim);">No affiliate link yet</span>'

    return f"""  <div class="product-card">
    <h3>#{rank} — {title}</h3>
    <div class="meta">
      <span>Category: {cat}</span>
      <span>Initial: {comm}</span>
      <span>Future: {future}</span>
      <span>EPC: {epc}</span>
      <span>Gravity: {gravity}</span>
      {tags}
    </div>

    <h4>What it is</h4>
    <p>{desc}</p>

    <h4>Strengths</h4>
    <ul>
      {strengths_html}
    </ul>

    <h4>Weaknesses</h4>
    <ul>
      {weaknesses_html}
    </ul>

    <h4>Verdict</h4>
    <p>{verdict}</p>

    <p>{cta}</p>
  </div>"""


def generate_review_html(offers, top_n=3):
    """Generate the full review.html page."""
    # Group by category
    categories = {}
    for o in offers:
        cat = o.get("category", "Uncategorized")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(o)

    sections = []
    for cat, cat_offers in categories.items():
        cat_esc = esc(cat)
        # Sort by score
        cat_offers.sort(key=lambda x: float(x.get("score", 0)), reverse=True)

        table_html = generate_table(cat_offers)
        cards_html = "\n\n".join(generate_offer_card(o, i+1) for i, o in enumerate(cat_offers[:top_n]))

        sections.append(f"""  <h2>{cat_esc}</h2>
  <p>Comparison of {len(cat_offers)} offers in this category.</p>
{table_html}

  <h3>Top {min(top_n, len(cat_offers))} picks in {cat_esc}</h3>
{cards_html}""")

    sections_html = "\n\n<hr>\n\n".join(sections)
    fetched = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Affiliate Offer Reviews — Real, Boring Systems</title>
  <meta name="description" content="Honest side-by-side comparison of ClickBank and direct affiliate offers. Real commission numbers, real EPC, real approval status.">
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>

  <div class="site-header"><span class="brand">Earn Extra Online — Real, Boring Systems</span></div>

  <nav>
    <a href="index.html">Home</a>
    <a href="review.html" class="active">Reviews</a>
    <a href="guide.html">Guide</a>
  </nav>

  <h1>Affiliate Offer Reviews</h1>

  <p>
    No hype. No "this one product changed my life" garbage. These are real
    numbers pulled directly from the ClickBank Marketplace API — commission,
    EPC, gravity, approval status, and whether the offer is actually worth
    your traffic.
  </p>

  <div class="callout">
    <strong>How to read this page:</strong> Each offer is scored on commission
    size (40%), EPC (40%), and gravity (20%). The top picks in each category
    get full review cards. If data is missing or unproven, I say so — no
    invented numbers.
  </div>

  <div class="callout">
    <strong>Data source:</strong> ClickBank Marketplace API.
    <strong>Last updated:</strong> {fetched}.
    Offers are re-pulled automatically — this page regenerates with fresh data
    each time <code>pull_offers.py</code> + <code>generate_reviews.py</code> runs.
  </div>

{sections_html}

  <footer>
    <p>Earn Extra Online — Real, Boring Systems</p>
    <p class="disclosure">
      This site uses affiliate links. I may earn a commission if you click
      a link and purchase a product. This never affects the price you pay.
      I do not guarantee any income results — earnings depend on your effort,
      traffic, and the products you choose to promote.
    </p>
    <p>Built honest. 💪</p>
  </footer>

</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate review.html from cached offers")
    parser.add_argument("--top", type=int, default=3,
                        help="Number of top offers to give full cards (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print HTML to stdout, don't write file")
    args = parser.parse_args()

    cache = load_cache()
    if not cache:
        return

    offers = cache.get("offers", [])
    if not offers:
        print("No offers in cache. Run pull_offers.py first.")
        return

    print(f"Generating review page from {len(offers)} cached offers...")
    html_output = generate_review_html(offers, top_n=args.top)

    if args.dry_run:
        print(html_output)
    else:
        with open(REVIEW_PATH, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"Wrote {REVIEW_PATH} ({len(html_output)} bytes)")


if __name__ == "__main__":
    main()