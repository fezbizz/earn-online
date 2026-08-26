"""
ClickBank Marketplace Auto-Pull Script
========================================
Fetches ClickBank Marketplace offers via the public GraphQL endpoint
(no API key required — this is the same endpoint the ClickBank marketplace
UI uses at accounts.clickbank.com/marketplace.htm).

Pulls all offers, filters by category (optional), sorts by a weighted score
(commission + EPC + gravity), and saves the top offers to a JSON cache.

Usage:
    python pull_offers.py                  # Pull all offers, top 20
    python pull_offers.py --category "Health & Fitness"
    python pull_offers.py --limit 50
    python pull_offers.py --dry-run         # Show results without writing cache

Requirements:
    pip install requests
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / ".env"
CACHE_PATH = SCRIPT_DIR / "offers_cache.json"
GRAPHQL_URL = "https://accounts.clickbank.com/graphql"

GRAPHQL_QUERY = """
query ($parameters: MarketplaceSearchParameters!) {
  marketplaceSearch(parameters: $parameters) {
    totalHits
    offset
    hits {
      site
      title
      description
      url
      urlTitle
      urlDescription
      marketplaceStats {
        activateDate
        category
        subCategory
        initialDollarsPerSale
        averageDollarsPerSale
        gravity
        totalRebill
        de
        en
        es
        fr
        it
        pt
        standard
        physical
        rebill
        upsell
        standardUrlPresent
        mobileEnabled
        whitelistVendor
        cpaVisible
        dollarTrial
        hasAdditionalSiteHoplinks
        directTracking
        expectedReturnRate
        returnRateSource
        initialEPC
        futureEPC
        averageEPC
        conversionRate
        netEPC
        biGravity
        score
        rank
        sellerVolume
      }
      affiliateToolsUrl
      affiliateSupportEmail
      offerImageUrl
    }
  }
}
"""


def load_env():
    """Load config from .env file."""
    env = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    for key in ["CLICKBANK_API_KEY", "CLICKBANK_NICKNAME"]:
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def generate_hoplink(nickname, site):
    """Generate a ClickBank hoplink for a given product site."""
    if not nickname or not site:
        return ""
    return f"https://{nickname}.hop.clickbank.net/?vendor={site}"


def fetch_offers(category=None):
    """Fetch offers from ClickBank public GraphQL endpoint."""
    import requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://accounts.clickbank.com",
        "Referer": "https://accounts.clickbank.com/marketplace.htm",
    }

    parameters = {}
    if category:
        parameters["category"] = category

    resp = requests.post(
        GRAPHQL_URL,
        json={"query": GRAPHQL_QUERY, "variables": {"parameters": parameters}},
        headers=headers,
        timeout=45,
    )

    if resp.status_code != 200:
        print(f"ERROR: HTTP {resp.status_code} from ClickBank GraphQL")
        print(f"  Body: {resp.text[:300]}")
        sys.exit(1)

    data = resp.json()
    if "errors" in data:
        print("ERROR: GraphQL returned errors:")
        for e in data["errors"]:
            print(f"  {e.get('message', e)}")
        sys.exit(1)

    search_results = data["data"]["marketplaceSearch"]
    return search_results


def normalize_offer(raw):
    """Extract the fields we care about from a GraphQL response hit."""
    stats = raw.get("marketplaceStats", {})
    return {
        "title": raw.get("title", "Unknown"),
        "site": raw.get("site", ""),
        "category": stats.get("category", "Unknown"),
        "sub_category": stats.get("subCategory", ""),
        "description": raw.get("description", ""),
        "url": raw.get("url", ""),
        "commission": float(stats.get("averageDollarsPerSale", 0) or 0),
        "initial_commission": float(stats.get("initialDollarsPerSale", 0) or 0),
        "future_commission": float(stats.get("totalRebill", 0) or 0),
        "average_dollars_per_sale": float(stats.get("averageDollarsPerSale", 0) or 0),
        "epc": float(stats.get("averageEPC", 0) or 0),
        "initial_epc": float(stats.get("initialEPC", 0) or 0),
        "future_epc": float(stats.get("futureEPC", 0) or 0),
        "net_epc": float(stats.get("netEPC", 0) or 0),
        "gravity": float(stats.get("gravity", 0) or 0),
        "bi_gravity": float(stats.get("biGravity", 0) or 0),
        "conversion_rate": float(stats.get("conversionRate", 0) or 0),
        "has_recurring": float(stats.get("totalRebill", 0) or 0) > 0,
        "has_upsell": bool(stats.get("upsell", False)),
        "is_physical": bool(stats.get("physical", False)),
        "whitelist_vendor": bool(stats.get("whitelistVendor", False)),
        "cpa_visible": bool(stats.get("cpaVisible", False)),
        "has_trial": bool(stats.get("dollarTrial", False)),
        "mobile_enabled": bool(stats.get("mobileEnabled", False)),
        "seller_volume": float(stats.get("sellerVolume", 0) or 0),
        "rank": int(stats.get("rank", 0) or 0),
        "score_raw": float(stats.get("score", 0) or 0),
        "affiliate_tools_url": raw.get("affiliateToolsUrl", ""),
        "offer_image_url": raw.get("offerImageUrl", ""),
        "fetched_at": datetime.now().isoformat(),
    }


def score_offer(offer):
    """
    Score an offer: commission (40%), EPC (40%), gravity (20%).
    Higher = better.
    """
    commission = offer.get("commission", 0)
    epc = offer.get("epc", 0)
    gravity = offer.get("gravity", 0)

    comm_score = min(commission / 200.0, 1.0)
    epc_score = min(epc / 250.0, 1.0)
    grav_score = min(gravity / 500.0, 1.0)

    return (comm_score * 0.4) + (epc_score * 0.4) + (grav_score * 0.2)


QUALITY_CATEGORIES = {
    "Health & Fitness",
    "Self-Help",
    "E-business & E-marketing",
    "Spirituality, New Age & Alternative Beliefs",
    "Green Products",
}

# Blacklist keywords in product titles — hype, novelty, political, or low-quality
TITLE_BLACKLIST = [
    "trump", "badge", "pin", "lapel", "golden badge",
    "pharaoh", "nectar", "ormus", "gold ormus",
    "pineal", "activation",
]


def is_quality_offer(offer):
    """Filter out junk offers — keep only quality niches with real data."""
    cat = offer.get("category", "")
    if cat not in QUALITY_CATEGORIES:
        return False
    title = offer.get("title", "").lower()
    for bad in TITLE_BLACKLIST:
        if bad in title:
            return False
    # Must have some commission data
    if float(offer.get("commission", 0) or 0) < 10:
        return False
    return True


def pull_offers(category=None, limit=20, dry_run=False):
    """Main pull function."""
    env = load_env()
    nickname = env.get("CLICKBANK_NICKNAME", "")

    if not nickname or "your-clickbank" in nickname.lower():
        print("WARNING: No ClickBank nickname set in .env.")
        print("Hoplinks will be empty until you set CLICKBANK_NICKNAME")
        nickname = ""

    print("Fetching ClickBank marketplace offers...")
    if category:
        print(f"  Category filter: {category}")

    try:
        results = fetch_offers(category=category)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    total_hits = results.get("totalHits", 0)
    raw_hits = results.get("hits", [])
    print(f"  Total offers available: {total_hits}")
    print(f"  Offers fetched: {len(raw_hits)}")

    if not raw_hits:
        print("No offers returned.")
        sys.exit(0)

    offers = [normalize_offer(h) for h in raw_hits]

    # Filter to quality offers only
    pre_count = len(offers)
    offers = [o for o in offers if is_quality_offer(o)]
    print(f"  Filtered: {pre_count} → {len(offers)} quality offers (removed {pre_count - len(offers)} junk)")

    for o in offers:
        o["score"] = score_offer(o)
        o["hoplink"] = generate_hoplink(nickname, o.get("site", ""))

    offers.sort(key=lambda x: x["score"], reverse=True)

    top = offers[:limit]
    print(f"\nTop {len(top)} offers by score:")
    for i, o in enumerate(top[:10], 1):
        print(f"  {i}. {o['title'][:50]}")
        print(f"     ${o['commission']:.2f} comm, ${o['epc']:.2f} EPC, grav={o['gravity']:.1f}, score={o['score']:.3f}")

    if dry_run:
        print(f"\n--dry-run: Not writing cache file.")
        return top

    cache = {
        "fetched_at": datetime.now().isoformat(),
        "category": category or "all",
        "total_available": total_hits,
        "count": len(top),
        "offers": top,
    }
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    print(f"\nSaved {len(top)} offers to {CACHE_PATH}")
    return top


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull ClickBank marketplace offers")
    parser.add_argument("--category", type=str, default=None,
                        help="ClickBank category (e.g. 'Health & Fitness')")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max offers to save to cache (default: 20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show results without writing cache")
    args = parser.parse_args()
    pull_offers(category=args.category, limit=args.limit, dry_run=args.dry_run)