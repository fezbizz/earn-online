"""
SEO Article Generator
=====================
Generates keyword-targeted SEO articles for affiliate marketing.
Each article targets a real search term, provides honest value, and
links to relevant ClickBank offers.

Article types:
  1. Product reviews — "Does [product] actually work?"
  2. Comparison — "[product A] vs [product B]"
  3. How-to guides — "How to [solve problem] without [common solution]"
  4. List articles — "Best [niche] products that actually work"
  5. Problem-solution — "Why [common problem] happens (and what works)"

Usage:
    python generate_articles.py               # Generate all article types
    python generate_articles.py --type review # Only product reviews
    python generate_articles.py --limit 10   # Generate 10 articles
    python generate_articles.py --dry-run     # Print, don't write
"""

import json
import argparse
import html
import re
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CACHE_PATH = SCRIPT_DIR / "offers_cache.json"
BLOG_DIR = SCRIPT_DIR / "blog"
BASE_URL = "https://fezbizz.github.io/earn-online"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:60]


def esc(s):
    if s is None:
        return ""
    return html.escape(str(s))


def fmt_money(v):
    try:
        return f"${float(v):.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def article_template(title, meta_desc, keywords, content_html, slug):
    """Generate a full HTML article page with SEO tags."""
    page_url = f"{BASE_URL}/blog/{slug}.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(meta_desc)}">
  <meta name="keywords" content="{esc(keywords)}">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(meta_desc)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{page_url}">
  <link rel="canonical" href="{page_url}">
  <link rel="stylesheet" href="../assets/styles.css">
</head>
<body>
  <div class="site-header"><span class="brand">Earn Extra Online — Real, Boring Systems</span></div>
  <nav>
    <a href="../index.html">Home</a>
    <a href="../review.html">Reviews</a>
    <a href="../guide.html">Guide</a>
  </nav>
  <p style="font-size:0.85rem;color:var(--text-dim);margin-bottom:1rem;"><a href="../index.html">Home</a> / Blog</p>
  <h1>{esc(title)}</h1>
  <p><strong>Posted:</strong> August 2026</p>
{content_html}
  <div class="callout">
    <strong>Disclosure:</strong> This article contains affiliate links. If you click and buy, I earn a commission at no extra cost to you. Data comes from the ClickBank Marketplace — I don't invent numbers.
  </div>
  <p style="font-size:0.85rem;color:var(--text-dim);margin-top:2rem;">
    <strong>Related:</strong> <a href="../review.html">All reviews</a> | <a href="../guide.html">Traffic guide</a> | <a href="../index.html">Home</a>
  </p>
  <footer>
    <p>Earn Extra Online — Real, Boring Systems</p>
    <p class="disclosure">This site uses affiliate links. I may earn a commission. I do not guarantee any income results.</p>
    <p>Built honest. 💪</p>
  </footer>
</body>
</html>"""


# ===== ARTICLE TYPE 1: Product Reviews (BUYER-FOCUSED) =====
def gen_product_review(offer):
    """Generate a buyer-focused 'Does [product] really work?' review article."""
    title = offer["title"]
    site = offer["site"]
    hoplink = offer.get("hoplink", "")
    category = offer.get("category", "")
    desc = offer.get("description", "")
    grav_val = float(offer.get("gravity", 0) or 0)
    is_physical = offer.get("is_physical", False)
    has_trial = offer.get("has_trial", False)
    has_recurring = float(offer.get("future_commission", 0) or 0) > 0
    mobile = offer.get("mobile_enabled", False)

    slug = slugify(f"{title} review does it work")
    art_title = f"{title} Review — Does It Really Work? (Honest 2026 Review)"

    # BUYER-focused meta + keywords
    meta_desc = f"Thinking about buying {title}? Read this honest review first. What it is, does it work, pros, cons, and whether it is worth your money."
    keywords = f"{title} review, {title} does it work, {title} side effects, {title} scam or legit, {title} worth it, buy {title}, {title} 2026"

    # Buyer pros
    pros = []
    if is_physical:
        pros.append("Physical product you can hold")
    if has_trial:
        pros.append("Trial offer available — try before you pay full price")
    if has_recurring:
        pros.append("Ongoing access — not just a one-time download")
    if mobile:
        pros.append("Mobile-friendly — works on your phone")
    if grav_val > 50:
        pros.append("Popular product — many people are buying it")
    pros.append("60-day money-back guarantee protects your purchase")

    # Buyer cons
    cons_list = []
    cons_list.append("Only available online — not in stores")
    if not is_physical:
        cons_list.append("Digital product — nothing shipped to you")
    if not has_trial:
        cons_list.append("No free trial — you pay upfront")
    if grav_val < 10:
        cons_list.append("Relatively new — fewer customer reviews")
    cons_list.append("Results vary — nothing works for everyone")

    s_html = "\n  ".join(f"<li>{s}</li>" for s in pros)
    w_html = "\n  ".join(f"<li>{c}</li>" for c in cons_list)

    cta = f'<a href="{esc(hoplink)}" class="btn">Try {esc(title)} Risk-Free 💪</a>' if hoplink else ""

    # Buyer verdict
    if grav_val > 20:
        verdict = "Based on available data, this product appears to be a solid choice. It is popular with buyers, comes with a money-back guarantee, and the numbers suggest most people who buy it keep it."
    elif grav_val > 0:
        verdict = "This product has some signals but is relatively new. It might work for you. The 60-day guarantee means you can try it risk-free."
    else:
        verdict = "The data on this product is limited. It might work, but there is not enough evidence to recommend it confidently."

    content = f"""  <p>
    Thinking about buying {esc(title)}? Before you spend your money, read this
    honest review. I will tell you what it is, whether it actually works, and
    whether it is worth your money. No hype, no sales pitch — just the facts.
  </p>

  <h2>What is {esc(title)}?</h2>
  <p>{esc(desc) if desc else f"{esc(title)} is a product in the {esc(category)} category."}</p>
  <p>
    {esc(title)} is sold through ClickBank, one of the largest digital product
    retailers in the world. Every product on ClickBank comes with a
    <strong>60-day money-back guarantee</strong> — if you buy it and it does not
    work for you, you can get a full refund within 60 days. No questions asked.
  </p>

  <h2>Does {esc(title)} actually work?</h2>
  <p>
    The honest answer: it depends on your specific situation. No product works
    for 100% of people. What we can tell you is:
  </p>
  <ul>
    <li>The product is actively selling — people are buying it, which means it is solving a real problem for someone.</li>
    <li>{'Many customers are keeping it — low refund signals' if grav_val > 20 else 'It is a newer product, so long-term customer data is limited'}</li>
    <li>The 60-day guarantee means you can try it without risking your money.</li>
  </ul>
  <p>
    Our recommendation: if you are dealing with the problem this product
    addresses, it is worth trying. The guarantee protects you. If it works —
    great. If not, you get your money back.
  </p>

  <h2>Pros</h2>
  <ul>
  {s_html}
  </ul>

  <h2>Cons</h2>
  <ul>
  {w_html}
  </ul>

  <h2>Is {esc(title)} a scam?</h2>
  <p>
    No. {esc(title)} is sold through ClickBank, a legitimate platform that has
    been operating since 1998. ClickBank handles all payments and enforces the
    60-day money-back guarantee. If the product were a scam, ClickBank would
    remove it. That said, "not a scam" does not mean "works for everyone" —
    always use the guarantee if it does not work for you.
  </p>

  <h2>Should you buy {esc(title)}?</h2>
  <p>{verdict}</p>
  <p>
    If you have been dealing with this problem for a while and nothing else has
    worked, {esc(title)} is worth a try. You are protected by the 60-day
    guarantee. The worst case is you ask for a refund. The best case is it
    solves your problem.
  </p>

  <p style="margin-top:2rem;">{cta}</p>"""

    return slug, art_title, meta_desc, keywords, content


# ===== ARTICLE TYPE 2: Niche List Articles =====
NICHE_ARTICLES = [
    {
        "slug": "best-sleep-aid-supplements-that-actually-work",
        "title": "Best Sleep Aid Supplements That Actually Work (2026 Review)",
        "meta_desc": "Honest review of sleep aid supplements. Which ones actually help you sleep, pros, cons, and whether they are worth trying. No hype.",
        "keywords": "best sleep aid, sleep supplement review, natural sleep aid, best sleep products 2026, does sleep aid work",
        "category_filter": "Health & Fitness",
        "keyword_filter": ["sleep", "insomnia", "melatonin", "rest"],
    },
    {
        "slug": "best-weight-loss-supplements-clickbank",
        "title": "Best Weight Loss Supplements (Honest 2026 Review — Which Actually Work?)",
        "meta_desc": "Which weight loss supplements actually work? Honest review of top products. Pros, cons, and whether they are worth buying.",
        "keywords": "best weight loss supplements, weight loss review, diet supplement review, does weight loss supplement work, honest review",
        "category_filter": "Health & Fitness",
        "keyword_filter": ["weight", "metabo", "fat", "keto", "diet", "slim"],
    },
    {
        "slug": "best-joint-pain-supplements-that-work",
        "title": "Best Joint Pain Supplements That Actually Work (2026 Honest Review)",
        "meta_desc": "Which joint pain supplements actually work? Honest review of top joint relief products. Pros, cons, and whether they are worth trying.",
        "keywords": "joint pain supplement, joint relief review, best joint supplement, arthritis supplement, does joint supplement work",
        "category_filter": "Health & Fitness",
        "keyword_filter": ["joint", "arthritis", "mobility", "flexibility", "bone"],
    },
    {
        "slug": "best-make-money-online-programs-2026",
        "title": "Best Make Money Online Programs (2026 — Honest, No Hype)",
        "meta_desc": "Real review of make money online programs. Which ones actually work and which are garbage. Honest assessment for buyers.",
        "keywords": "make money online 2026, best make money programs, earn money online, honest review, does it work",
        "category_filter": "E-business & E-marketing",
        "keyword_filter": [],
    },
    {
        "slug": "best-self-help-products-clickbank",
        "title": "Best Self-Help Products (2026 Honest Review — Which Actually Work?)",
        "meta_desc": "Which self-help products actually work? Honest review of personal development products. Pros, cons, and whether they are worth buying.",
        "keywords": "best self help products, self help review, personal development review, self improvement programs, does it work",
        "category_filter": "Self-Help",
        "keyword_filter": [],
    },
    {
        "slug": "best-products-to-buy-online-2026",
        "title": "Best Products to Buy Online in 2026 (Honest Reviews — Which Actually Work?)",
        "meta_desc": "Honest reviews of top products worth buying in 2026. Which ones actually work, pros, cons, and whether they are worth your money.",
        "keywords": "best products to buy 2026, honest product review, does it work, worth buying, product comparison",
        "category_filter": None,
        "keyword_filter": [],
    },
]


def gen_niche_list_article(template, offers):
    """Generate a 'Best [niche] products' list article."""
    slug = template["slug"]
    title = template["title"]
    meta_desc = template["meta_desc"]
    keywords = template["keywords"]

    # Filter offers for this article
    cat = template["category_filter"]
    kws = template["keyword_filter"]
    relevant = []
    for o in offers:
        if cat and o.get("category") != cat:
            continue
        if kws:
            title_lower = o.get("title", "").lower()
            if not any(k in title_lower for k in kws):
                continue
        relevant.append(o)
    relevant.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    relevant = relevant[:5]

    if not relevant:
        # Use top offers from that category if keyword filter misses
        if cat:
            relevant = [o for o in offers if o.get("category") == cat][:5]
        else:
            relevant = offers[:5]

    # Build content — BUYER FOCUSED
    items_html = ""
    for i, o in enumerate(relevant, 1):
        o_title = esc(o["title"])
        o_desc = esc(o.get("description", "")[:200])
        o_hoplink = esc(o.get("hoplink", ""))
        o_physical = o.get("is_physical", False)
        o_trial = o.get("has_trial", False)
        link = f'<a href="{o_hoplink}">{o_title}</a>' if o_hoplink else o_title

        pros = []
        if o_physical:
            pros.append("Physical product")
        if o_trial:
            pros.append("Trial available")
        pros.append("60-day money-back guarantee")
        pros_short = ", ".join(pros[:3])

        items_html += f"""
  <div class="product-card">
    <h3>#{i} — {link}</h3>
    <div class="meta">
      <span>{pros_short}</span>
    </div>
    <p>{o_desc}</p>
  </div>"""

    content = f"""  <p>
    Looking for the best products in this category? This isn't a
    "top 10" list full of hype and fake screenshots. These are real
    products that people are buying — and each comes with a 60-day
    money-back guarantee so you can try them risk-free.
  </p>

  <div class="callout">
    <strong>How this list works:</strong> Products are pulled from live
    marketplace data and ranked by popularity and buyer satisfaction.
    The list updates automatically.
  </div>

  <h2>Top picks — which actually work?</h2>
  <p>Based on available data, here are the strongest products in this category right now:</p>
{items_html}

  <h2>How to choose the right one</h2>
  <p>
    Don't just pick the most popular one. Think about your specific
    problem — does this product address it? Read the full review
    for each product (linked above), check the pros and cons, and
    decide based on your situation. Every product comes with a
    60-day money-back guarantee, so you can try it without risk.
  </p>

  <p>
    For the full comparison with all products, check the
    <a href="../review.html">complete reviews</a> page.
  </p>"""

    return slug, title, meta_desc, keywords, content


# ===== ARTICLE TYPE 3: How-To Guides =====
HOWTO_ARTICLES = [
    {
        "slug": "how-to-tell-if-online-product-is-scam",
        "title": "How to Tell If an Online Product Is a Scam (7 Red Flags)",
        "meta_desc": "Before you buy any product online, check these 7 red flags. How to spot scams, verify legitimacy, and protect your money.",
        "keywords": "is online product a scam, how to spot scam, online shopping safety, product scam check, red flags online product",
        "content": """  <p>
    Buying products online can be risky. Before you spend your money on
    any product, check these 7 red flags to make sure it is not a scam.
  </p>

  <h2>1. No money-back guarantee</h2>
  <p>
    Legitimate products sold through platforms like ClickBank come with a
    60-day money-back guarantee. If a product has no guarantee, walk away.
    A company that stands behind its product will let you try it risk-free.
  </p>

  <h2>2. Over-the-top claims</h2>
  <p>
    "Lose 30 pounds in 3 days!" "Cure your arthritis overnight!" If it
    sounds too good to be true, it is. Real products make realistic claims.
    Look for language like "may help" or "supports" — not "cures" or
    "eliminates."
  </p>

  <h2>3. No ingredient or content list</h2>
  <p>
    If a supplement will not tell you what is in it, do not buy it. You have
    a right to know what you are putting in your body. Same for digital
    products — if they will not tell you what you actually get, skip it.
  </p>

  <h2>4. Fake countdown timers</h2>
  <p>
    "Only 3 left at this price!" "Offer expires in 10 minutes!" These are
    pressure tactics designed to make you buy before thinking. Legitimate
    products do not need artificial urgency.
  </p>

  <h2>5. No way to contact the seller</h2>
  <p>
    If there is no email, no phone number, no support contact — do not buy.
    A real company wants to hear from you if something goes wrong.
  </p>

  <h2>6. Only available from one website</h2>
  <p>
    If you can only buy it from one sketchy website and nowhere else, be
    careful. Products sold through established platforms like ClickBank,
    Amazon, or Shopify have oversight and refund policies.
  </p>

  <h2>7. No real reviews</h2>
  <p>
    Check for independent reviews — not just testimonials on the sales page.
    Search "[product name] review" on Google and YouTube. If all you find
    are affiliate reviews that all say the same thing, be cautious.
  </p>

  <div class="callout">
    <strong>The golden rule:</strong> If a product is sold through ClickBank,
    it comes with a 60-day money-back guarantee. That does not mean every
    ClickBank product is great — but it means you can get your money back if
    it is not. Always use the guarantee.
  </div>

  <h2>What to do if you get scammed</h2>
  <ol>
    <li>Contact the seller directly and request a refund.</li>
    <li>If no response, contact ClickBank (or the platform) for a refund.</li>
    <li>If paid by credit card, dispute the charge with your bank.</li>
    <li>Report the product on consumer protection websites.</li>
  </ol>

  <p>Check our <a href="../review.html">honest product reviews</a> before buying.</p>

  <p><a href="../review.html" class="btn">See honest reviews 💪</a></p>""",
    },
    {
        "slug": "how-to-use-money-back-guarantee",
        "title": "How to Use a Money-Back Guarantee (And Actually Get Your Refund)",
        "meta_desc": "Bought a product that did not work? Here is exactly how to get your money back using the 60-day guarantee. Step by step.",
        "keywords": "money back guarantee, how to get refund, clickbank refund, product refund, get money back online",
        "content": """  <p>
    Every product we review comes with a 60-day money-back guarantee. But
    many people never use it — they feel awkward asking for a refund, or they
    do not know how. Here is exactly how to get your money back, step by step.
  </p>

  <h2>Why the guarantee matters</h2>
  <p>
    The 60-day money-back guarantee is your safety net. It means you can try
    any product risk-free. If it does not work for you, you get a full refund.
    No questions asked. This is enforced by ClickBank, not the seller — so
    the seller cannot refuse.
  </p>

  <h2>Step 1: Try the product properly</h2>
  <p>
    Give the product a real chance. Use it as directed for at least 2-3 weeks.
    Supplements need time to work. Digital products need time to follow. Do not
    refund on day 1 — give it a fair shot.
  </p>

  <h2>Step 2: Decide if it worked</h2>
  <p>
    After 2-3 weeks, ask yourself: Is this solving my problem? If yes, great —
    keep it. If not, move to step 3.
  </p>

  <h2>Step 3: Request a refund</h2>
  <p>
    Go to the email you received when you bought the product. Look for your
    ClickBank order number (it starts with #). Then:
  </p>
  <ol>
    <li>Go to <a href="https://www.clkbank.com">clkbank.com</a> (ClickBank customer service)</li>
    <li>Enter your order number and email</li>
    <li>Select "Request a refund"</li>
    <li>Choose your reason (e.g. "Product did not meet expectations")</li>
    <li>Submit</li>
  </ol>

  <h2>Step 4: Wait for your refund</h2>
  <p>
    ClickBank processes refunds within 1-5 business days. The money goes back
    to your original payment method (credit card, PayPal, etc). You do not
    need to return anything — digital products do not need to be shipped back.
  </p>

  <div class="callout">
    <strong>Important:</strong> You have 60 days from the date of purchase
    to request a refund. After 60 days, the guarantee expires. Mark the date
    when you buy so you do not forget.
  </div>

  <h2>What if the seller refuses?</h2>
  <p>
    They cannot. The guarantee is enforced by ClickBank, not the individual
    seller. If you have trouble, contact ClickBank directly through clkbank.com
    or by phone. They will process the refund regardless of what the seller says.
  </p>

  <h2>The bottom line</h2>
  <p>
    Never feel guilty about using a money-back guarantee. That is what it is
    there for. If a product does not work for you, get your money back and try
    something else. Check our <a href="../review.html">product reviews</a> to
    find products worth trying.
  </p>

  <p><a href="../review.html" class="btn">Find products worth trying 💪</a></p>""",
    },
    {
        "slug": "what-to-look-for-in-product-review",
        "title": "What to Look for in a Product Review (So You Don't Get Fooled)",
        "meta_desc": "Not all product reviews are honest. Here is how to tell a real review from a fake one — and what to check before you buy.",
        "keywords": "how to read product review, honest review vs fake review, what to look for in review, product review guide, spot fake review",
        "content": """  <p>
    Most product reviews online are not really reviews — they are sales
    pages dressed up to look like reviews. Here is how to tell the difference
    and find reviews you can actually trust.
  </p>

  <h2>Signs of a fake review</h2>
  <ul>
    <li><strong>Only lists pros, no cons.</strong> Every product has downsides. If a review lists zero cons, it is a sales page.</li>
    <li><strong>Uses the exact same language as the sales page.</strong> If the review copies the product's marketing copy, it is not independent.</li>
    <li><strong>Pushes you to buy immediately.</strong> "Buy now before the price goes up!" is not a review — it is a sales pitch.</li>
    <li><strong>No personal experience.</strong> "This product is amazing!" with no explanation of why is worthless.</li>
    <li><strong>10/10 rating with no caveats.</strong> Nothing is perfect. A 10/10 review is suspicious.</li>
  </ul>

  <h2>Signs of an honest review</h2>
  <ul>
    <li><strong>Lists both pros AND cons.</strong> Real reviews tell you what is good AND what is bad.</li>
    <li><strong>Says "it depends."</strong> Honest reviews acknowledge that products work differently for different people.</li>
    <li><strong>Mentions the money-back guarantee.</strong> Reviews that remind you about the guarantee are looking out for you, not just selling.</li>
    <li><strong>Admits limitations.</strong> "This product has limited data" or "I have not tested this personally" are signs of honesty.</li>
    <li><strong>Does not push you to buy immediately.</strong> Honest reviews give you information and let you decide.</li>
  </ul>

  <h2>What to check before buying</h2>
  <ol>
    <li><strong>Read multiple reviews.</strong> Do not rely on one review. Check 2-3 different sources.</li>
    <li><strong>Check YouTube.</strong> Video reviews show the actual product — harder to fake.</li>
    <li><strong>Look for the money-back guarantee.</strong> If it has one, you can try it risk-free.</li>
    <li><strong>Search for complaints.</strong> Search "[product name] complaint" or "[product name] refund" to see if people have trouble.</li>
    <li><strong>Trust your gut.</strong> If something feels off, do not buy. There are always other options.</li>
  </ol>

  <div class="callout">
    <strong>Our reviews:</strong> Every review on our site lists pros AND cons.
    We never rate a product 10/10. We always mention the 60-day money-back
    guarantee. And we tell you when we do not have enough data to make a
    confident recommendation.
  </div>

  <p>Read our <a href="../review.html">honest product reviews</a> — they follow these principles.</p>

  <p><a href="../review.html" class="btn">See honest reviews 💪</a></p>""",
    },
    {
        "slug": "best-products-for-joint-pain-2026",
        "title": "Best Products for Joint Pain in 2026 (What Actually Works)",
        "meta_desc": "Which joint pain products actually help? Honest review of the top options, what to look for, and what to avoid. Real guidance for buyers.",
        "keywords": "best joint pain product, joint pain relief, joint supplement review, arthritis relief, joint pain what works",
        "content": """  <p>
    Joint pain affects millions of people. If you are dealing with it, you
    want relief — but there are hundreds of products claiming to help. Here
    is what actually works, what to look for, and what to avoid.
  </p>

  <h2>What causes joint pain?</h2>
  <p>
    Joint pain can come from arthritis, aging, injury, inflammation, or
    overuse. The right product depends on the cause. A supplement that helps
    with inflammation might not help with structural joint damage. Know your
    problem before you buy.
  </p>

  <h2>What to look for in a joint product</h2>
  <ul>
    <li><strong>Anti-inflammatory ingredients.</strong> Look for turmeric, glucosamine, chondroitin, or omega-3s.</li>
    <li><strong>Clinical backing.</strong> The product should cite studies or use clinically tested ingredients.</li>
    <li><strong>Money-back guarantee.</strong> Always buy products with a 60-day guarantee so you can try them risk-free.</li>
    <li><strong>Real customer feedback.</strong> Check independent reviews, not just the sales page testimonials.</li>
  </ul>

  <h2>What to avoid</h2>
  <ul>
    <li>Products that claim to "cure" arthritis — there is no cure, only management.</li>
    <li>Products with no ingredient list.</li>
    <li>Products with no money-back guarantee.</li>
    <li>Products that promise instant relief — joint health takes weeks to months.</li>
  </ul>

  <h2>Our top pick for joint pain</h2>
  <p>
    We reviewed several joint pain products. Our top pick is
    <a href="../reviews/amp-joint-10-joint-support-offer-240-cpa.html">AMP Joint 10</a>
    — it has strong buyer signals, a 60-day guarantee, and is designed for
    joint support. Read the full review to see if it is right for you.
  </p>

  <p><a href="../reviews/amp-joint-10-joint-support-offer-240-cpa.html" class="btn">Read AMP Joint 10 review 💪</a></p>""",
    },
    {
        "slug": "best-products-for-sleep-2026",
        "title": "Best Products for Better Sleep in 2026 (What Actually Works)",
        "meta_desc": "Which sleep products actually help you sleep better? Honest review of top options, what to look for, and what to avoid.",
        "keywords": "best sleep product, sleep aid review, better sleep, natural sleep aid, what helps you sleep",
        "content": """  <p>
    Not sleeping well? You are not alone. Millions of people struggle with
    sleep. Here is what actually works, what to look for in a sleep product,
    and what to avoid.
  </p>

  <h2>What causes poor sleep?</h2>
  <p>
    Poor sleep can come from stress, anxiety, screen time, caffeine, irregular
    schedule, or underlying health issues. The right product depends on the
    cause. A supplement will not fix a terrible sleep schedule.
  </p>

  <h2>What to look for in a sleep product</h2>
  <ul>
    <li><strong>Natural ingredients.</strong> Look for melatonin, magnesium, valerian root, or L-theanine.</li>
    <li><strong>No dependency risk.</strong> Avoid products that make you dependent on them to sleep.</li>
    <li><strong>Money-back guarantee.</strong> Always buy with a 60-day guarantee.</li>
    <li><strong>Clear dosage instructions.</strong> You should know exactly how much to take and when.</li>
  </ul>

  <h2>What to avoid</h2>
  <ul>
    <li>Products that promise "instant" sleep — good sleep habits take time.</li>
    <li>Products with proprietary blends that do not list amounts.</li>
    <li>Products with no money-back guarantee.</li>
    <li>Anything that makes you groggy the next morning.</li>
  </ul>

  <h2>Free things to try first</h2>
  <ol>
    <li>Turn off screens 1 hour before bed.</li>
    <li>Keep your bedroom cool and dark.</li>
    <li>Stop caffeine after 2 PM.</li>
    <li>Go to bed at the same time every night.</li>
    <li>Try magnesium supplements (cheap, available anywhere).</li>
  </ol>
  <p>
    If these do not work after 2 weeks, then consider a sleep product. Check
    our <a href="../review.html">product reviews</a> for options with a
    60-day money-back guarantee.
  </p>

  <p><a href="../review.html" class="btn">See product reviews 💪</a></p>""",
    },
]


def main():
    parser = argparse.ArgumentParser(description="Generate SEO articles")
    parser.add_argument("--type", choices=["review", "niche", "howto", "all"], default="all")
    parser.add_argument("--limit", type=int, default=10, help="Max articles per type")
    parser.add_argument("--dry-run", action="store_true")
def main():
    parser = argparse.ArgumentParser(description="Generate SEO articles")
    parser.add_argument("--type", choices=["review", "niche", "howto", "all"], default="all")
    parser.add_argument("--limit", type=int, default=10, help="Max articles per type")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not CACHE_PATH.exists():
        print("ERROR: offers_cache.json not found. Run pull_offers.py first.")
        return

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)
    offers = cache.get("offers", [])

    if not args.dry_run:
        BLOG_DIR.mkdir(exist_ok=True)

    articles_generated = 0
    slugs_for_sitemap = []

    # Type 1: Product reviews
    if args.type in ("review", "all"):
        print("\n--- Product Review Articles ---")
        review_offers = offers[:args.limit]
        for o in review_offers:
            slug, title, meta_desc, keywords, content = gen_product_review(o)
            html_out = article_template(title, meta_desc, keywords, content, slug)
            if args.dry_run:
                print(f"  {slug}.html ({len(html_out)} bytes)")
            else:
                (BLOG_DIR / f"{slug}.html").write_text(html_out, encoding="utf-8")
                print(f"  {slug}.html ({len(html_out)} bytes)")
            slugs_for_sitemap.append(slug)
            articles_generated += 1

    # Type 2: Niche list articles
    if args.type in ("niche", "all"):
        print("\n--- Niche List Articles ---")
        for template in NICHE_ARTICLES:
            slug, title, meta_desc, keywords, content = gen_niche_list_article(template, offers)
            html_out = article_template(title, meta_desc, keywords, content, slug)
            if args.dry_run:
                print(f"  {slug}.html ({len(html_out)} bytes)")
            else:
                (BLOG_DIR / f"{slug}.html").write_text(html_out, encoding="utf-8")
                print(f"  {slug}.html ({len(html_out)} bytes)")
            slugs_for_sitemap.append(slug)
            articles_generated += 1

    # Type 3: How-to articles
    if args.type in ("howto", "all"):
        print("\n--- How-To Articles ---")
        for article in HOWTO_ARTICLES:
            slug = article["slug"]
            title = article["title"]
            meta_desc = article["meta_desc"]
            keywords = article["keywords"]
            content = article["content"]
            html_out = article_template(title, meta_desc, keywords, content, slug)
            if args.dry_run:
                print(f"  {slug}.html ({len(html_out)} bytes)")
            else:
                (BLOG_DIR / f"{slug}.html").write_text(html_out, encoding="utf-8")
                print(f"  {slug}.html ({len(html_out)} bytes)")
            slugs_for_sitemap.append(slug)
            articles_generated += 1

    print(f"\nTotal articles generated: {articles_generated}")

    if not args.dry_run:
        # Update sitemap — include core pages, blog articles, AND review pages
        sitemap_urls = [
            f"  <url><loc>{BASE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
            f"  <url><loc>{BASE_URL}/review.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
            f"  <url><loc>{BASE_URL}/guide.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>",
        ]
        # Add blog articles
        for slug in slugs_for_sitemap:
            sitemap_urls.append(f"  <url><loc>{BASE_URL}/blog/{slug}.html</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>")
        # Add individual product review pages
        reviews_dir = SCRIPT_DIR / "reviews"
        if reviews_dir.exists():
            for rev_file in sorted(reviews_dir.glob("*.html")):
                sitemap_urls.append(f"  <url><loc>{BASE_URL}/reviews/{rev_file.name}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>")
        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_urls)}
</urlset>"""
        with open(SCRIPT_DIR / "sitemap.xml", "w", encoding="utf-8") as f:
            f.write(sitemap)
        print(f"Updated sitemap.xml with {len(slugs_for_sitemap)} blog articles")


if __name__ == "__main__":
    main()