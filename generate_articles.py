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


# ===== ARTICLE TYPE 1: Product Reviews =====
def gen_product_review(offer):
    """Generate a 'Does [product] actually work?' review article."""
    title = offer["title"]
    site = offer["site"]
    hoplink = offer.get("hoplink", "")
    category = offer.get("category", "")
    comm = fmt_money(offer.get("commission", 0))
    epc = fmt_money(offer.get("epc", 0))
    gravity = offer.get("gravity", 0)
    future = float(offer.get("future_commission", 0) or 0)
    desc = offer.get("description", "")

    slug = slugify(f"{title} review does it work")
    art_title = f"{title} Review — Does It Actually Work? (Real Data)"

    # Extract niche keyword from category
    niche = category.replace(" & ", " ").replace("E-business & E-marketing", "make money online").lower()

    meta_desc = f"Honest {title} review. Real ClickBank data: {comm} commission, {epc} EPC, gravity {gravity:.0f}. Does it work? Read before you buy."
    keywords = f"{title} review, {title} does it work, {title} scam, {title} legit, {title} clickbank, {niche} product review"

    # Build honest content
    strengths = []
    weaknesses = []
    comm_val = float(offer.get("commission", 0) or 0)
    epc_val = float(offer.get("epc", 0) or 0)
    grav_val = float(offer.get("gravity", 0) or 0)

    if comm_val >= 100:
        strengths.append(f"High commission ({comm} per sale) — above average for ClickBank.")
    elif comm_val >= 50:
        strengths.append(f"Decent commission at {comm} per sale.")
    else:
        weaknesses.append(f"Lower commission ({comm}) — needs high volume.")

    if epc_val >= 3:
        strengths.append(f"EPC of {epc} — affiliates are actively earning per click.")
    elif epc_val > 0:
        strengths.append(f"EPC of {epc} — positive but modest.")
    else:
        weaknesses.append("No EPC data — conversion is unproven.")

    if grav_val > 100:
        strengths.append(f"High gravity ({grav_val:.0f}) — many affiliates earning.")
    elif grav_val > 20:
        strengths.append(f"Moderate gravity ({grav_val:.0f}) — solid traction.")
    elif grav_val > 0:
        weaknesses.append(f"Low gravity ({grav_val:.0f}) — fewer affiliates earning.")
    else:
        weaknesses.append("Zero gravity — unproven offer.")

    if future > 0:
        strengths.append(f"Recurring revenue ({fmt_money(future)} future commission).")
    else:
        weaknesses.append("One-time payout — no recurring income.")

    s_html = "\n  ".join(f"<li>{s}</li>" for s in strengths)
    w_html = "\n  ".join(f"<li>{w}</li>" for w in weaknesses)

    cta = f'<a href="{esc(hoplink)}" class="btn">Visit {esc(title)} 💪</a>' if hoplink else ""

    does_it_work = "Yes, the numbers support it. The EPC shows affiliates are earning, and the gravity confirms it." if epc_val > 0 and grav_val > 20 else ("The data is mixed. The EPC is there but gravity is low — few affiliates are testing it. It could work, but it is a gamble." if epc_val > 0 else "Unclear. No EPC data means conversion is unproven. Test with a small amount of traffic before committing.")
    verdict_numbers = "strong numbers" if epc_val > 3 and grav_val > 20 else ("decent but mixed numbers" if epc_val > 0 else "unproven numbers")

    content = f"""  <p>
    Looking for an honest {esc(title)} review? This isn't a sales pitch.
    I pulled the real ClickBank Marketplace data — commission, EPC, gravity —
    and I'll tell you straight: whether it's worth promoting, and whether
    the numbers justify the hype.
  </p>

  <h2>What is {esc(title)}?</h2>
  <p>{esc(desc) if desc else f"A product in the {esc(category)} category on ClickBank."}</p>

  <h2>The real numbers</h2>
  <table>
    <tr><th>Commission</th><td>{comm}</td></tr>
    <tr><th>EPC</th><td>{epc}</td></tr>
    <tr><th>Gravity</th><td>{gravity:.1f}</td></tr>
    <tr><th>Recurring</th><td>{'Yes' if future > 0 else 'No'}</td></tr>
  </table>

  <h2>Strengths</h2>
  <ul>
  {s_html}
  </ul>

  <h2>Weaknesses</h2>
  <ul>
  {w_html}
  </ul>

  <h2>Does it actually work?</h2>
  <p>
    Based on the data: {does_it_work}
  </p>
  <p>
    The honest answer: I haven't personally driven traffic to this offer yet.
    The numbers above are from ClickBank's marketplace data — real, but
    aggregated across all affiliates. Your results depend on your traffic
    quality and audience fit.
  </p>

  <h2>How to promote it</h2>
  <p>
    If you decide to promote {esc(title)}, here's the boring, honest method:
  </p>
  <ol>
    <li>Write a review article (like this one) targeting "{esc(title.lower())} review" as the keyword.</li>
    <li>Create a YouTube video showing the product and sharing your honest opinion.</li>
    <li>Pin it on Pinterest with a clear, simple image and headline.</li>
    <li>Do this consistently for 3 months before judging results.</li>
  </ol>
  <p>Read the full <a href="../guide.html">traffic guide</a> for details.</p>

  <h2>The verdict</h2>
  <p>
    {esc(title)} has {verdict_numbers}. If you're in the {esc(category)} niche, it's worth testing — but don't bet everything on one offer. Test 2-3 in the same niche and compare.
  </p>

  <p style="margin-top:2rem;">{cta}</p>"""

    return slug, art_title, meta_desc, keywords, content


# ===== ARTICLE TYPE 2: Niche List Articles =====
NICHE_ARTICLES = [
    {
        "slug": "best-sleep-aid-supplements-that-actually-work",
        "title": "Best Sleep Aid Supplements That Actually Work (2026 Review)",
        "meta_desc": "Honest review of the best sleep aid supplements on ClickBank. Real EPC, commission, and gravity data. No hype — just what works.",
        "keywords": "best sleep aid, sleep supplement review, natural sleep aid, clickbank sleep products, best sleep products 2026",
        "category_filter": "Health & Fitness",
        "keyword_filter": ["sleep", "insomnia", "melatonin", "rest"],
    },
    {
        "slug": "best-weight-loss-supplements-clickbank",
        "title": "Best Weight Loss Supplements on ClickBank (Honest 2026 Review)",
        "meta_desc": "Real review of weight loss offers on ClickBank. Commission, EPC, gravity data. Which ones convert and which to avoid.",
        "keywords": "best weight loss supplements, weight loss affiliate programs, clickbank weight loss, diet supplement review",
        "category_filter": "Health & Fitness",
        "keyword_filter": ["weight", "metabo", "fat", "keto", "diet", "slim"],
    },
    {
        "slug": "best-joint-pain-supplements-that-work",
        "title": "Best Joint Pain Supplements That Actually Work (2026)",
        "meta_desc": "Honest review of joint pain relief supplements on ClickBank. Real EPC and commission data. Which ones are worth promoting.",
        "keywords": "joint pain supplement, joint relief review, best joint supplement, clickbank joint pain, arthritis supplement",
        "category_filter": "Health & Fitness",
        "keyword_filter": ["joint", "arthritis", "mobility", "flexibility", "bone"],
    },
    {
        "slug": "best-make-money-online-programs-2026",
        "title": "Best Make Money Online Programs (2026 — Honest, No Hype)",
        "meta_desc": "Real review of make money online programs on ClickBank. Commission, EPC, gravity. Which ones work and which are garbage.",
        "keywords": "make money online 2026, best make money programs, affiliate marketing programs, clickbank make money, earn money online",
        "category_filter": "E-business & E-marketing",
        "keyword_filter": [],
    },
    {
        "slug": "best-self-help-products-clickbank",
        "title": "Best Self-Help Products on ClickBank (2026 Honest Review)",
        "meta_desc": "Real review of self-help and personal development products. Commission, EPC, gravity data. Which ones are worth your traffic.",
        "keywords": "best self help products, self help review, personal development affiliate, clickbank self help, self improvement programs",
        "category_filter": "Self-Help",
        "keyword_filter": [],
    },
    {
        "slug": "highest-paying-clickbank-offers-beginners",
        "title": "Highest Paying ClickBank Offers for Beginners (2026 Real Data)",
        "meta_desc": "Top ClickBank offers ranked by commission and EPC. Which high-paying offers actually convert. Honest data for beginners.",
        "keywords": "highest paying clickbank offers, best clickbank offers for beginners, high commission affiliate, top EPC clickbank",
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

    # Build content
    items_html = ""
    for i, o in enumerate(relevant, 1):
        o_title = esc(o["title"])
        o_comm = fmt_money(o.get("commission", 0))
        o_epc = fmt_money(o.get("epc", 0))
        o_grav = o.get("gravity", 0)
        o_hoplink = esc(o.get("hoplink", ""))
        o_desc = esc(o.get("description", "")[:200])
        link = f'<a href="{o_hoplink}">{o_title}</a>' if o_hoplink else o_title

        items_html += f"""
  <div class="product-card">
    <h3>#{i} — {link}</h3>
    <div class="meta">
      <span>Commission: {o_comm}</span>
      <span>EPC: {o_epc}</span>
      <span>Gravity: {o_grav:.1f}</span>
    </div>
    <p>{o_desc}</p>
  </div>"""

    content = f"""  <p>
    This isn't another "top 10" list full of hype and fake screenshots.
    These are real ClickBank offers with real data — commission, EPC, and
    gravity — pulled directly from the ClickBank Marketplace. I tell you
    what's worth promoting and what to skip.
  </p>

  <div class="callout">
    <strong>How this list works:</strong> Offers are pulled from ClickBank's
    live marketplace data and ranked by a weighted score (commission 40%,
    EPC 40%, gravity 20%). The data updates automatically.
  </div>

  <h2>The top picks</h2>
  <p>Based on live data, here are the strongest offers in this category right now:</p>
{items_html}

  <h2>How to choose the right one</h2>
  <p>
    Don't pick the one with the biggest commission number. Pick the one with
    the highest EPC — that's the number that tells you the offer actually
    converts. A $50 commission with $5 EPC beats a $500 commission with $0 EPC
    every time.
  </p>

  <h2>How to promote them</h2>
  <p>
    Pick ONE offer. Write an honest review (like the ones on our
    <a href="../review.html">reviews page</a>). Get traffic using the free
    methods in the <a href="../guide.html">traffic guide</a>. Do it for
    3 months. That's it.
  </p>

  <p>
    For the full comparison with all data, check the
    <a href="../review.html">complete offer reviews</a> page.
  </p>"""

    return slug, title, meta_desc, keywords, content


# ===== ARTICLE TYPE 3: How-To Guides =====
HOWTO_ARTICLES = [
    {
        "slug": "how-to-earn-5-dollars-per-day-online",
        "title": "How to Earn $5 Per Day Online (Realistic, No Hype)",
        "meta_desc": "Step-by-step plan to earn $5/day online with affiliate marketing. Free traffic, real timeline, no get-rich-quick garbage.",
        "keywords": "earn 5 dollars a day online, make 5 dollars per day, affiliate marketing $5 day, earn money online realistic, small income online",
        "content": """  <p>
    $5 per day. That's $150/month, $1,825/year. Not life-changing — but real,
    achievable, and the foundation for everything bigger. This is the honest
    plan for getting there.
  </p>

  <div class="callout">
    <strong>Reality check:</strong> This takes 3-6 months of consistent work.
    If you need $5 today, sell something on eBay. If you want to build a
    system that pays $5/day passively, read on.
  </div>

  <h2>The math of $5/day</h2>
  <p>
    $5/day with affiliate marketing means:
  </p>
  <ul>
    <li>One $50 commission every 10 days (1 sale per 10 days)</li>
    <li>Or one $15 commission every 3 days</li>
    <li>At a 2% conversion rate, you need ~250 visitors/day to your affiliate link</li>
    <li>At a 5% click-through rate, you need ~5,000 page views/month</li>
  </ul>
  <p>
    5,000 monthly page views is achievable with 20-30 SEO articles in a single
    niche. Not easy, not fast, but doable.
  </p>

  <h2>Step 1: Pick a niche with products that pay $50+ per sale</h2>
  <p>
    Health & Fitness is the easiest starting point. ClickBank has dozens of
    offers paying $50-$200+ per sale. Check the
    <a href="../review.html">reviews page</a> for real EPC data.
  </p>

  <h2>Step 2: Build a free site</h2>
  <p>
    Use GitHub Pages (like this site), Blogger, or Medium. Write 20-30 articles
    answering real questions in your niche. Each article targets one search term.
  </p>
  <p>
    Article ideas:
  </p>
  <ul>
    <li>"Does [product name] actually work?" — product reviews</li>
    <li>"Best [niche] products that actually work" — list articles</li>
    <li>"Why [problem] happens and what to do about it" — problem-solution</li>
    <li>"[product A] vs [product B]" — comparisons</li>
  </ul>

  <h2>Step 3: Get free traffic</h2>
  <p>
    Read the full <a href="../guide.html">traffic guide</a>, but the short version:
  </p>
  <ol>
    <li>Publish 2-3 articles per week (consistency beats quality)</li>
    <li>Create 1 YouTube video per week (screen recording + honest review)</li>
    <li>Pin each article on Pinterest (3-5 pins per day)</li>
    <li>Answer questions in 2-3 niche forums (link only when relevant)</li>
  </ol>

  <h2>Step 4: The 6-month timeline</h2>
  <table>
    <tr><th>Month 1-2</th><td>Write 15 articles. Traffic: near zero. No sales. Normal.</td></tr>
    <tr><th>Month 3-4</th><td>Google indexes your site. 10-30 visitors/day. Maybe first sale.</td></tr>
    <tr><th>Month 5-6</th><td>30-80 visitors/day. 1-2 sales/week. ~$5/day average.</td></tr>
    <tr><th>Month 7-12</th><td>Compounding. $5-20/day if you stayed consistent.</td></tr>
  </table>

  <h2>What kills $5/day</h2>
  <ul>
    <li><strong>Quitting in month 2.</strong> The graph is flat, then it curves. Most people quit before the curve.</li>
    <li><strong>Switching niches.</strong> Every switch resets the clock to month 1.</li>
    <li><strong>Picking bad offers.</strong> High commission + zero EPC = no sales. Always check EPC.</li>
    <li><strong>Expecting passive immediately.</strong> Month 1-4 is active work. Passive comes after.</li>
  </ul>

  <h2>The boring truth</h2>
  <p>
    $5/day is not exciting. It's not a "laptop lifestyle" Instagram post. It's
    boring, slow, and unglamorous. But it's real, it compounds, and it's the
    foundation for $10/day, $20/day, and beyond. Start here.
  </p>

  <p><a href="../review.html" class="btn">Find offers to promote 💪</a></p>""",
    },
    {
        "slug": "how-to-get-free-traffic-for-affiliate-links",
        "title": "How to Get Free Traffic for Affiliate Links (9 Methods That Work)",
        "meta_desc": "9 free traffic methods for affiliate marketing. No paid ads. SEO, YouTube, Pinterest, forums, and more. Real timelines and effort required.",
        "keywords": "free traffic affiliate links, affiliate marketing traffic free, get clicks affiliate, free traffic methods, SEO traffic affiliate",
        "content": """  <p>
    You have affiliate links. Nobody's clicking them. Here are 9 free methods
    to get real eyes on your links — no paid ads, no shortcuts, no garbage.
  </p>

  <h2>1. SEO blog content (the main path)</h2>
  <p>
    Write articles answering questions people search for. Google sends free
    traffic to pages that answer questions better than the competition. This
    is what this entire site does. 2-3 articles per week for 6 months.
  </p>

  <h2>2. YouTube review videos</h2>
  <p>
    A 5-minute honest review ranks faster than a blog post because YouTube has
    less competition in most niches. Screen-record the product, talk honestly,
    put your link in the description. 1 video per week.
  </p>

  <h2>3. Pinterest pins</h2>
  <p>
    Pinterest is a search engine, not social media. Pins live for months. Create
    simple pins in Canva (free), link to your review page, pin 3-5 per day.
    Works best for health, fitness, and lifestyle niches.
  </p>

  <h2>4. Reddit (carefully)</h2>
  <p>
    Find subreddits in your niche. Answer questions honestly for 2-3 weeks
    without linking anything. After you build trust, link your reviews when
    genuinely relevant. Never spam — Reddit bans fast.
  </p>

  <h2>5. Quora answers</h2>
  <p>
    Answer questions in your niche on Quora. Link to your review when it's
    genuinely the answer. Quora answers rank on Google and drive traffic for
    years. 1-2 answers per week.
  </p>

  <h2>6. Forum participation</h2>
  <p>
    Find 2-3 active forums in your niche. Be helpful. After 2-3 weeks, link your
    reviews when relevant. Old forums still get search traffic.
  </p>

  <h2>7. Email newsletter</h2>
  <p>
    Collect emails on your site (free with Substack or ConvertKit free tier).
    Send a weekly email with your latest review or article. Email traffic
    converts 3-5x better than search traffic.
  </p>

  <h2>8. Guest posting</h2>
  <p>
    Write articles for other blogs in your niche. Include one link back to your
    site. Free backlink + free traffic. Reach out to small/medium blogs — they
    usually say yes to free content.
  </p>

  <h2>9. Repurpose content</h2>
  <p>
    Turn one article into: a YouTube video script, a Pinterest pin, a Twitter
    thread, a Quora answer, and an email. One piece of content, 5 channels.
    Don't create more — repurpose more.
  </p>

  <div class="callout">
    <strong>The rule:</strong> Pick ONE method. Do it consistently for 3 months.
    Don't add a second method until the first one produces traffic. Focus
    beats variety every single time.
  </div>

  <p>For the full version, read the <a href="../guide.html">complete traffic guide</a>.</p>

  <p><a href="../review.html" class="btn">Find offers to promote 💪</a></p>""",
    },
    {
        "slug": "affiliate-marketing-mistakes-beginners-make",
        "title": "7 Affiliate Marketing Mistakes Beginners Make (And How to Avoid Them)",
        "meta_desc": "The real mistakes that kill affiliate marketing beginners. No hype — just what goes wrong and how to fix it. Learn from others' failures.",
        "keywords": "affiliate marketing mistakes, beginner affiliate mistakes, affiliate marketing tips, what not to do affiliate, affiliate marketing failure",
        "content": """  <p>
    Most people who try affiliate marketing fail. Not because it doesn't work —
    because they make the same 7 mistakes. Here they are, and here's how to
    avoid each one.
  </p>

  <h2>1. Promoting products with zero EPC data</h2>
  <p>
    EPC (Earnings Per Click) tells you if the offer converts. If EPC is $0 or
    unreported, you're gambling. Always check EPC before promoting. Our
    <a href="../review.html">reviews page</a> shows EPC for every offer.
  </p>

  <h2>2. Trying 5 niches at once</h2>
  <p>
    Pick one niche. Stick with it for 6 months. Niche authority compounds —
    Google ranks sites that cover one topic deeply, not sites that cover
    everything shallowly.
  </p>

  <h2>3. Writing sales pages, not reviews</h2>
  <p>
    People search "[product] review" because they want honesty, not a sales
    pitch. Write the real strengths AND weaknesses. Honest reviews convert
    better than hype — and they don't get penalized by Google.
  </p>

  <h2>4. Expecting results in month 1</h2>
  <p>
    SEO takes 3-6 months. If you quit in month 2 because there's no traffic,
    you've wasted all your work. The traffic graph is flat for months, then
    it curves upward. You need to survive the flat part.
  </p>

  <h2>5. Spamming links</h2>
  <p>
    Posting your affiliate link in forums, comments, DMs, and Facebook groups
    gets you banned and destroys trust. Write honest content, link naturally,
    and let the traffic come to you.
  </p>

  <h2>6. Paying for ads before free traffic works</h2>
  <p>
    Paid ads burn money if you don't know what converts. Get free traffic first
    — prove the offer converts with real visitors — then consider ads. 90% of
    beginners should never run ads.
  </p>

  <h2>7. Ignoring the product quality</h2>
  <p>
    If you promote garbage, people refund. Refunds claw back your commission.
    Check the product yourself or read real reviews before promoting. Your
    reputation is worth more than one commission.
  </p>

  <h2>The fix</h2>
  <p>
    Pick one niche. Pick 2-3 offers with proven EPC. Write honest reviews. Get
    free traffic. Be patient for 6 months. That's it. The system is boring
    because it works — the exciting "shortcuts" are the ones that fail.
  </p>

  <p><a href="../review.html" class="btn">Find quality offers 💪</a></p>""",
    },
    {
        "slug": "clickbank-vs-other-affiliate-networks",
        "title": "ClickBank vs Other Affiliate Networks (Which Is Best for Beginners?)",
        "meta_desc": "Honest comparison of ClickBank, Amazon Associates, ShareASale, and CJ. Commission rates, ease of use, and which is best for beginners.",
        "keywords": "clickbank vs amazon associates, best affiliate network, clickbank vs shareasale, affiliate network comparison, clickbank vs cj",
        "content": """  <p>
    ClickBank isn't the only affiliate network. Here's how it compares to the
    others — and which one beginners should start with.
  </p>

  <h2>ClickBank</h2>
  <table>
    <tr><th>Commission</th><td>40-75% (often $50-$200+ per sale)</td></tr>
    <tr><th>Products</th><td>Mostly digital (ebooks, courses, supplements)</td></tr>
    <tr><th>Approval</th><td>Most offers instant, some require vendor approval</td></tr>
    <tr><th>Best for</th><td>Digital products, health supplements, self-help</td></tr>
  </table>
  <p>
    <strong>Verdict:</strong> Best for beginners. High commissions, easy signup,
    lots of data (EPC, gravity) to pick good offers. Check our
    <a href="../review.html">reviews</a> for top picks.
  </p>

  <h2>Amazon Associates</h2>
  <table>
    <tr><th>Commission</th><td>1-10% (usually $1-$10 per sale)</td></tr>
    <tr><th>Products</th><td>Physical products (everything Amazon sells)</td></tr>
    <tr><th>Approval</th><td>Easy signup, but strict rules</td></tr>
    <tr><th>Best for</th><td>Product review sites, gadget blogs</td></tr>
  </table>
  <p>
    <strong>Verdict:</strong> Low commissions but huge product range. Good if
    you already review physical products. Not the best for earning $5/day
    quickly — you need massive volume.
  </p>

  <h2>ShareASale</h2>
  <table>
    <tr><th>Commission</th><td>Varies by merchant ($5-$100+ per sale)</td></tr>
    <tr><th>Products</th><td>Mix of physical and digital, established brands</td></tr>
    <tr><th>Approval</th><td>Each merchant approves separately</td></tr>
    <tr><th>Best for</th><td>Fashion, home, lifestyle niches</td></tr>
  </table>
  <p>
    <strong>Verdict:</strong> Good for physical product niches. More approval
    friction than ClickBank but often higher quality merchants.
  </p>

  <h2>CJ Affiliate (Commission Junction)</h2>
  <table>
    <tr><th>Commission</th><td>Varies by advertiser</td></tr>
    <tr><th>Products</th><td>Big brands (Gap, Lowe's, etc.)</td></tr>
    <tr><th>Approval</th><td>Strict — each advertiser approves separately</td></tr>
    <tr><th>Best for</th><td>Established sites with existing traffic</td></tr>
  </table>
  <p>
    <strong>Verdict:</strong> Not for beginners. Need existing traffic to get
    approved by good advertisers. Come back to this after you have 1,000+
    monthly visitors.
  </p>

  <h2>Which should you start with?</h2>
  <p>
    <strong>ClickBank.</strong> It's the easiest to start, has the highest
    commissions for beginners, and gives you data (EPC, gravity) to pick offers
    that actually convert. Once you have traffic, add Amazon Associates or
    ShareASale for complementary products.
  </p>

  <p>Start with our <a href="../review.html">ClickBank offer reviews</a> and the <a href="../guide.html">traffic guide</a>.</p>

  <p><a href="../review.html" class="btn">See top ClickBank offers 💪</a></p>""",
    },
    {
        "slug": "what-is-epc-and-why-it-matters-affiliate",
        "title": "What Is EPC in Affiliate Marketing? (And Why It's the Only Number That Matters)",
        "meta_desc": "EPC explained simply. What it means, how to use it, and why it's more important than commission rate. Real ClickBank examples.",
        "keywords": "what is epc affiliate, epc meaning, earnings per click, affiliate epc explained, clickbank epc, epc vs commission",
        "content": """  <p>
    If you only learn one metric in affiliate marketing, make it EPC. Here's
    what it means, why it matters more than commission, and how to use it.
  </p>

  <h2>What is EPC?</h2>
  <p>
    EPC = Earnings Per Click. It's the average amount affiliates earn every time
    someone clicks their affiliate link. If EPC is $5, that means for every 100
    clicks, affiliates earn $500 on average.
  </p>

  <h2>Why EPC beats commission</h2>
  <p>
    Two offers on ClickBank:
  </p>
  <ul>
    <li>Offer A: $500 commission, $0.50 EPC</li>
    <li>Offer B: $50 commission, $5 EPC</li>
  </ul>
  <p>
    Offer A sounds better ($500!), but the EPC tells the truth. At $0.50 EPC,
    you need 1,000 clicks to make $500. At $5 EPC, you need 100 clicks to make
    $500. Offer B is 10x better despite paying 10x less per sale.
  </p>
  <p>
    EPC accounts for conversion rate. High commission + bad conversion = low EPC.
    Low commission + great conversion = high EPC. Always follow the EPC.
  </p>

  <h2>How to use EPC</h2>
  <ol>
    <li>Filter ClickBank offers by EPC (our <a href="../review.html">reviews page</a> shows EPC for every offer).</li>
    <li>Pick offers with EPC above $3 — these are proven to convert.</li>
    <li>Be cautious of offers with $0 EPC — they're unproven or don't convert.</li>
    <li>Compare EPC across offers in the same niche to find the best one.</li>
  </ol>

  <h2>What's a good EPC?</h2>
  <table>
    <tr><th>EPC Range</th><th>What It Means</th></tr>
    <tr><td>$0 or unreported</td><td>Unproven. Don't promote unless you have a specific reason.</td></tr>
    <tr><td>$0.01 - $1</td><td>Low conversion. Might work with highly targeted traffic.</td></tr>
    <tr><td>$1 - $3</td><td>Decent. Worth testing.</td></tr>
    <tr><td>$3 - $10</td><td>Good. Proven conversion. Safe to promote.</td></tr>
    <tr><td>$10+</td><td>Excellent. High-converting offer with strong commission.</td></tr>
  </table>

  <div class="callout">
    <strong>Important:</strong> EPC is an average across all affiliates. Your
    EPC depends on your traffic quality. Someone with a targeted email list
    will have higher EPC than someone with random social media traffic. The
    marketplace EPC is a baseline, not a guarantee.
  </div>

  <h2>EPC is your traffic ROI</h2>
  <p>
    If you send 1,000 visitors to an offer with $5 EPC, you expect ~$5,000 in
    affiliate earnings. That's your return on 1,000 visitors. Use EPC to decide
    which offers deserve your traffic.
  </p>

  <p>
    Check the <a href="../review.html">reviews page</a> for live EPC data on
    every top ClickBank offer.
  </p>

  <p><a href="../review.html" class="btn">Compare EPC data 💪</a></p>""",
    },
]


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