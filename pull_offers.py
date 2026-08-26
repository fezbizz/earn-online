"""
ClickBank API Auto-Pull Script
==============================
Fetches ClickBank Marketplace offers via the ClickBank API, filters them by
category, sorts by commission/EPC, and saves the top offers to a JSON cache.

The script is designed to run standalone or be called by the review generator.

ClickBank API auth: HTTP Basic auth with the API key as username and a
colon-appended key. The key must NOT be a "Bearer" token — ClickBank uses
Basic auth with the developer key only.

Usage:
    python pull_offers.py                  # Pull all categories, top 20 per category
    python pull_offers.py --category "Health & Fitness"  # Pull specific category
    python pull_offers.py --limit 50       # Pull top 50 offers
    python pull_offers.py --dry-run        # Show what would be fetched without writing

Requirements:
    pip install requests
"""

import os
import sys
import json
import argparse
import base64
from datetime import datetime
from pathlib import Path

# --- Config ---
SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / ".env"
CACHE_PATH = SCRIPT_DIR / "offers_cache.json"

CLICKBANK_API_BASE = "https://api.clickbank.com/rest/1.3"


def load_env():
    """Load API key from .env file — never hardcode, never echo."""
    env = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    # Also check environment variables (override)
    for key in ["CLICKBANK_API_KEY", "CLICKBANK_NICKNAME", "CLICKBANK_CLERK_KEY"]:
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def make_auth_header(api_key):
    """
    ClickBank uses HTTP Basic auth.
    The format is: base64(api_key + ":")
    NOT "Bearer <key>" — that's what caused the 401 on the phone.
    """
    credentials = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json",
        "User-Agent": "EarnOnline/1.0",
    }


def fetch_category_list(api_key, headers):
    """Fetch all available ClickBank marketplace categories."""
    import requests
    url = f"{CLICKBANK_API_BASE}/marketplace/categories"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 401:
        print("ERROR 401: Auth failed. Check your API key in .env")
        print("ClickBank uses Basic auth with base64(key + ':'), NOT Bearer.")
        print("Also check: ClickBank may require IP allowlisting in account settings.")
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def fetch_marketplace_offers(api_key, headers, category=None, page=1, max_results=100):
    """
    Fetch marketplace offers from ClickBank API.
    Endpoint: /marketplace/search
    """
    import requests
    url = f"{CLICKBANK_API_BASE}/marketplace/search"
    params = {
        "pageNumber": page,
        "maxResults": max_results,
    }
    if category:
        params["category"] = category

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 401:
        print("ERROR 401: Auth failed. Check your API key in .env")
        print("ClickBank uses Basic auth with base64(key + ':'), NOT Bearer.")
        sys.exit(1)
    if resp.status_code == 403:
        print("ERROR 403: Forbidden. Your ClickBank account may need IP allowlisting.")
        print("Go to: accounts.clickbank.com > Settings > IP Scoping")
        print(f"Your current public IP needs to be allowlisted.")
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def normalize_offer(raw):
    """
    Extract the fields we care about from a ClickBank API response.
    Handles different API response shapes gracefully.
    """
    return {
        "title": raw.get("title", raw.get("site", "Unknown")),
        "site": raw.get("site", ""),
        "category": raw.get("category", raw.get("siteCategory", "Unknown")),
        "description": raw.get("description", ""),
        "commission": raw.get("commission", raw.get("affiliateCommission", 0)),
        "commission_percent": raw.get("commissionPercent", raw.get("affiliateCommissionPercentage", 0)),
        "epc": raw.get("epc", raw.get("averageEarningsPerClick", 0)),
        "gravity": raw.get("gravity", 0),
        "has_recurring": raw.get("hasRecurringProducts", raw.get("recurring", False)),
        "activation_fee": raw.get("activationFee", ""),
        "require_approval": raw.get("requireApproval", False),
        "total_rebill": raw.get("totalRebillAmmount", raw.get("totalRebillAmount", 0)),
        "initial_commission": raw.get("initialCommission", raw.get("commission", 0)),
        "future_commission": raw.get("futureCommission", raw.get("totalRebillAmmount", 0)),
        "vendor_url": raw.get("vendor", raw.get("vendorUrl", "")),
        "image_url": raw.get("image", raw.get("imageUrl", "")),
        "marketplace_url": raw.get("marketplaceAffiliateUrl", ""),
        "fetched_at": datetime.now().isoformat(),
    }


def score_offer(offer):
    """
    Score an offer by commission size, EPC, and gravity.
    Higher = better. This is a simple weighted score, not a sophisticated model.

    Weights:
        - Commission: 40% (bigger payouts = more income per sale)
        - EPC: 40% (proven conversion = less risk)
        - Gravity: 20% (more affiliates earning = offer converts)
    """
    commission = float(offer.get("commission", 0) or 0)
    epc = float(offer.get("epc", 0) or 0)
    gravity = float(offer.get("gravity", 0) or 0)

    # Normalize: commission on scale of $0-$200, EPC $0-$10, gravity 0-500
    comm_score = min(commission / 200.0, 1.0)
    epc_score = min(epc / 10.0, 1.0)
    grav_score = min(gravity / 500.0, 1.0)

    return (comm_score * 0.4) + (epc_score * 0.4) + (grav_score * 0.2)


def generate_hoplink(nickname, site):
    """Generate a ClickBank hoplink for a given product site."""
    if not nickname or not site:
        return ""
    return f"https://{nickname}.hop.clickbank.net/?vendor={site}"


def pull_offers(category=None, limit=20, dry_run=False):
    """Main pull function."""
    env = load_env()
    api_key = env.get("CLICKBANK_API_KEY", "")
    nickname = env.get("CLICKBANK_NICKNAME", "")

    if not api_key or "paste-your" in api_key.lower():
        print("ERROR: No ClickBank API key found.")
        print("Create a .env file with: CLICKBANK_API_KEY=your-key-here")
        print("Get your key from: https://accounts.clickbank.com/accounts/manageAPIKeys")
        sys.exit(1)

    if not nickname or "your-clickbank" in nickname.lower():
        print("WARNING: No ClickBank nickname set in .env.")
        print("Hoplinks will be empty until you set CLICKBANK_NICKNAME")
        nickname = ""

    headers = make_auth_header(api_key)
    print(f"Fetching ClickBank marketplace offers...")
    if category:
        print(f"  Category: {category}")
    print(f"  Limit: {limit}")

    try:
        import requests
    except ImportError:
        print("ERROR: 'requests' package not installed.")
        print("Install it: pip install requests")
        sys.exit(1)

    try:
        raw_data = fetch_marketplace_offers(api_key, headers, category=category, max_results=limit)
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to ClickBank API. Check your internet connection.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("ERROR: ClickBank API timed out. Try again.")
        sys.exit(1)

    # Parse response — ClickBank API returns different shapes
    offers_raw = []
    if isinstance(raw_data, dict):
        offers_raw = raw_data.get("offers", raw_data.get("results", raw_data.get("data", [])))
    elif isinstance(raw_data, list):
        offers_raw = raw_data

    if not offers_raw:
        print("No offers returned from ClickBank API.")
        print("This could mean:")
        print("  - The category name doesn't match ClickBank's internal names")
        print("  - Your account doesn't have marketplace access")
        print("  - API response format changed")
        print(f"\nRaw response keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data)}")
        sys.exit(0)

    # Normalize + score
    offers = [normalize_offer(o) for o in offers_raw]
    for o in offers:
        o["score"] = score_offer(o)
        o["hoplink"] = generate_hoplink(nickname, o.get("site", ""))

    # Sort by score descending
    offers.sort(key=lambda x: x["score"], reverse=True)

    print(f"\nFetched {len(offers)} offers. Top 5 by score:")
    for i, o in enumerate(offers[:5], 1):
        print(f"  {i}. {o['title']} — ${o['commission']} comm, ${o['epc']} EPC, score={o['score']:.2f}")

    if dry_run:
        print("\n--dry-run: Not writing cache file.")
        return offers

    # Save to cache
    cache = {
        "fetched_at": datetime.now().isoformat(),
        "category": category or "all",
        "count": len(offers),
        "offers": offers,
    }
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    print(f"\nSaved {len(offers)} offers to {CACHE_PATH}")

    return offers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull ClickBank marketplace offers")
    parser.add_argument("--category", type=str, default=None,
                        help="ClickBank category name (e.g. 'Health & Fitness')")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max offers to fetch (default: 20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show results without writing cache file")
    args = parser.parse_args()
    pull_offers(category=args.category, limit=args.limit, dry_run=args.dry_run)