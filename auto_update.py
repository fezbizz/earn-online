"""
Auto-Update Pipeline — One Command Does Everything
===================================================
Runs the full pipeline:
  1. Pull offers from ClickBank API  → offers_cache.json
  2. Generate review.html from cache  → review.html
  3. Git commit + (optionally) push

Usage:
    python auto_update.py                    # Pull + generate + git commit
    python auto_update.py --push             # Pull + generate + git commit + push to GitHub
    python auto_update.py --category "Health & Fitness"  # Pull specific category
    python auto_update.py --limit 50         # Pull 50 offers per category
    python auto_update.py --dry-run          # Pull + generate, no git changes

This is the script you run to refresh the site with fresh ClickBank data.
    python auto_update.py --push
"""

import subprocess
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run(cmd, label):
    """Run a command and print output."""
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print(f"FAILED (exit {result.returncode})")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Full auto-update pipeline")
    parser.add_argument("--push", action="store_true",
                        help="Also git push to remote after commit")
    parser.add_argument("--category", type=str, default=None,
                        help="ClickBank category filter")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max offers to fetch per category (default: 20)")
    parser.add_argument("--top", type=int, default=3,
                        help="Top offers to feature with full cards (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't commit or push, just pull + generate")
    args = parser.parse_args()

    py = sys.executable or "python"

    # Step 1: Pull offers
    pull_cmd = [py, "pull_offers.py", "--limit", str(args.limit)]
    if args.category:
        pull_cmd += ["--category", args.category]
    if not run(pull_cmd, "STEP 1: Pull ClickBank offers"):
        sys.exit(1)

    # Step 2: Generate review.html
    gen_cmd = [py, "generate_reviews.py", "--top", str(args.top)]
    if not run(gen_cmd, "STEP 2: Generate review.html"):
        sys.exit(1)

    if args.dry_run:
        print("\n--dry-run: Skipping git commit.")
        print("Done. review.html has been regenerated.")
        return

    # Step 3: Git commit
    print(f"\n{'='*50}")
    print(f"  STEP 3: Git commit")
    print(f"{'='*50}")
    subprocess.run(["git", "add", "-A"], cwd=SCRIPT_DIR)
    commit_msg = f"Auto-update: {('Category: ' + args.category) if args.category else 'All categories'} — {args.limit} offers pulled"
    result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=SCRIPT_DIR,
                            capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Step 4: Push (optional)
    if args.push:
        print(f"\n{'='*50}")
        print(f"  STEP 4: Git push")
        print(f"{'='*50}")
        result = subprocess.run(["git", "push"], cwd=SCRIPT_DIR,
                                capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode != 0:
            print("Push failed. Make sure you've set up the remote:")
            print("  git remote add origin https://github.com/fezbizz/earn-online.git")
            sys.exit(1)

    print("\n" + "="*50)
    print("  DONE.")
    print("="*50)
    print("  Offers pulled → review.html regenerated → committed")
    if args.push:
        print("  Pushed to GitHub → live on GitHub Pages")
    print("="*50)


if __name__ == "__main__":
    main()