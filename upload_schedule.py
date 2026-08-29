"""
YouTube Upload Schedule
========================
Manages a 3-videos-per-week upload schedule.

Current state: 15 videos already uploaded (all public).
Strategy going forward:
  - Keep the 15 already-uploaded videos as-is (they're live, can't unschedule)
  - Generate NEW videos and schedule them 3x per week
  - Track schedule in youtube/schedule.json

Schedule: Monday, Wednesday, Friday at 15:00 (3 PM) — catches afternoon viewers

This script:
  1. Shows the current upload schedule
  2. Calculates the next upload date
  3. Can be used by auto_update.py to schedule new videos

Usage:
    python upload_schedule.py                # Show current schedule
    python upload_schedule.py --next         # Show next upload date
    python upload_schedule.py --add <slug>   # Add a video to the schedule
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
YOUTUBE_DIR = SCRIPT_DIR / "youtube"
SCHEDULE_PATH = YOUTUBE_DIR / "schedule.json"

# Upload days: Monday=0, Wednesday=2, Friday=4
UPLOAD_DAYS = [0, 2, 4]
UPLOAD_TIME = "15:00"  # 3 PM


def load_schedule():
    if SCHEDULE_PATH.exists():
        with open(SCHEDULE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"uploaded": [], "scheduled": [], "cadence": "3x/week", "days": ["Mon", "Wed", "Fri"], "time": UPLOAD_TIME}


def save_schedule(schedule):
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2)


def get_next_upload_date(from_date=None):
    """Get the next upload date (Mon, Wed, or Fri)."""
    if from_date is None:
        from_date = datetime.now()
    else:
        from_date = datetime.fromisoformat(from_date)

    # If today is an upload day and we haven't uploaded yet, use today
    if from_date.weekday() in UPLOAD_DAYS and from_date.hour < 15:
        return from_date.replace(hour=15, minute=0, second=0, microsecond=0)

    # Find next upload day
    for i in range(1, 8):
        check_date = from_date + timedelta(days=i)
        if check_date.weekday() in UPLOAD_DAYS:
            return check_date.replace(hour=15, minute=0, second=0, microsecond=0)
    return from_date


def get_upload_dates(count, start_from=None):
    """Get a list of upcoming upload dates."""
    dates = []
    current = get_next_upload_date(start_from)
    dates.append(current)
    while len(dates) < count:
        current = get_next_upload_date(current.isoformat())
        dates.append(current)
    return dates


def main():
    parser = argparse.ArgumentParser(description="Manage YouTube upload schedule")
    parser.add_argument("--next", action="store_true", help="Show next upload date")
    parser.add_argument("--add", type=str, help="Add a video slug to schedule")
    parser.add_argument("--plan", type=int, help="Show upload plan for next N videos")
    args = parser.parse_args()

    schedule = load_schedule()

    if args.next:
        next_date = get_next_upload_date()
        print(f"Next upload: {next_date.strftime('%A, %B %d at %H:%M')}")
        return

    if args.add:
        slug = args.add
        next_date = get_next_upload_date()
        schedule["scheduled"].append({
            "slug": slug,
            "date": next_date.isoformat(),
            "status": "pending"
        })
        save_schedule(schedule)
        print(f"Scheduled {slug} for {next_date.strftime('%A, %B %d at %H:%M')}")
        return

    if args.plan:
        dates = get_upload_dates(args.plan)
        print(f"\nUpload plan — next {args.plan} videos:")
        print(f"Schedule: Monday, Wednesday, Friday at 3:00 PM")
        print()
        for i, date in enumerate(dates, 1):
            print(f"  {i}. {date.strftime('%A, %B %d at %H:%M')}")
        return

    # Default: show current state
    print(f"\nYouTube Upload Schedule")
    print(f"{'='*50}")
    print(f"Cadence: {schedule.get('cadence', '3x/week')}")
    print(f"Days: {', '.join(schedule.get('days', ['Mon', 'Wed', 'Fri']))}")
    print(f"Time: {schedule.get('time', '15:00')}")
    print(f"\nUploaded videos: {len(schedule.get('uploaded', []))}")
    print(f"Scheduled (pending): {len(schedule.get('scheduled', []))}")

    # List uploaded videos
    if schedule.get("uploaded"):
        print(f"\nUploaded:")
        for v in schedule["uploaded"]:
            print(f"  {v['slug']} — {v.get('date', '?')} — {v.get('url', '?')}")

    # Show next 5 upload dates
    dates = get_upload_dates(5)
    print(f"\nNext 5 upload slots:")
    for i, date in enumerate(dates, 1):
        print(f"  {i}. {date.strftime('%A, %B %d at 3:00 PM')}")

    # Check which slugs have scripts but aren't uploaded yet
    all_scripts = set()
    for f in YOUTUBE_DIR.glob("*_script.json"):
        all_scripts.add(f.name.replace("_script.json", ""))
    uploaded_slugs = set(v["slug"] for v in schedule.get("uploaded", []))
    scheduled_slugs = set(v["slug"] for v in schedule.get("scheduled", []))
    available = all_scripts - uploaded_slugs - scheduled_slugs

    if available:
        print(f"\nVideos with scripts ready to schedule: {len(available)}")
        dates = get_upload_dates(len(available))
        for slug, date in zip(sorted(available), dates):
            print(f"  {slug} → {date.strftime('%A, %B %d')}")
    else:
        print(f"\nAll scripts have been uploaded or scheduled.")


if __name__ == "__main__":
    main()