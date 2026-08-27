"""
YouTube Auto-Upload Script
============================
Uploads generated faceless review videos to YouTube automatically.
Reads the video MP4 + script JSON (for title, description, tags) and
uploads via the YouTube Data API v3.

One-time OAuth setup:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or use existing)
  3. Enable "YouTube Data API v3"
  4. Create OAuth 2.0 credentials (Desktop app)
  5. Download the client_secret.json file
  6. Save it as youtube/client_secret.json

First run opens a browser for Google login. After that, token is cached.

Usage:
    python upload_youtube.py --video ampjoint    # Upload one video
    python upload_youtube.py --all               # Upload all videos
    python upload_youtube.py --all --dry-run     # Show what would upload

Requirements:
    pip install google-auth google-auth-oauthlib google-api-python-client
"""

import json
import argparse
import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
YOUTUBE_DIR = SCRIPT_DIR / "youtube"
CLIENT_SECRET = YOUTUBE_DIR / "client_secret.json"
TOKEN_PATH = YOUTUBE_DIR / "youtube_token.json"

# Upload scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    """Authenticate and return YouTube service object."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request

    if not CLIENT_SECRET.exists():
        print("ERROR: client_secret.json not found in youtube/ directory.")
        print()
        print("One-time setup:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project (or use existing)")
        print("  3. Search for 'YouTube Data API v3' and ENABLE it")
        print("  4. Go to Credentials → Create Credentials → OAuth client ID")
        print("  5. Choose 'Desktop app'")
        print("  6. Download the JSON file")
        print(f"  7. Save it as: {CLIENT_SECRET}")
        print()
        print("Then run this script again.")
        sys.exit(1)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, video_path, script_path):
    """Upload a single video to YouTube."""
    from googleapiclient.http import MediaFileUpload

    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    title = script.get("video_title", "Untitled Review")
    description = script.get("description", "")
    tags = script.get("tags", [])

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
    )

    print(f"  Uploading: {title[:60]}...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"    Progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"    Uploaded! URL: {video_url}")
    return video_url


def main():
    parser = argparse.ArgumentParser(description="Upload videos to YouTube")
    parser.add_argument("--video", type=str, help="Video slug (e.g. 'ampjoint')")
    parser.add_argument("--all", action="store_true", help="Upload all videos")
    parser.add_argument("--dry-run", action="store_true", help="Show what would upload")
    args = parser.parse_args()

    if not args.video and not args.all:
        print("Specify --video <slug> or --all")
        return

    # Find video + script pairs
    videos = []
    if args.video:
        mp4 = YOUTUBE_DIR / f"{args.video}_video.mp4"
        script = YOUTUBE_DIR / f"{args.video}_script.json"
        if not mp4.exists():
            print(f"ERROR: {mp4} not found")
            return
        if not script.exists():
            print(f"ERROR: {script} not found")
            return
        videos.append((mp4, script))
    else:
        for mp4 in sorted(YOUTUBE_DIR.glob("*_video.mp4")):
            slug = mp4.name.replace("_video.mp4", "")
            script = YOUTUBE_DIR / f"{slug}_script.json"
            if script.exists():
                videos.append((mp4, script))

    if not videos:
        print("No videos found to upload.")
        return

    print(f"\nFound {len(videos)} videos to upload:\n")
    for mp4, script in videos:
        with open(script, encoding="utf-8") as f:
            s = json.load(f)
        size_mb = mp4.stat().st_size / (1024 * 1024)
        print(f"  {mp4.name} ({size_mb:.1f} MB)")
        print(f"    Title: {s.get('video_title', '?')[:70]}")
        print()

    if args.dry_run:
        print("--dry-run: Not uploading.")
        return

    if not CLIENT_SECRET.exists():
        print("ERROR: YouTube OAuth not set up yet.")
        print("Follow the setup instructions in the script docstring.")
        return

    youtube = get_youtube_service()
    print(f"\nAuthenticated. Starting uploads...\n")

    uploaded = []
    for mp4, script in videos:
        try:
            url = upload_video(youtube, mp4, script)
            uploaded.append(url)
            # Rate limit: wait between uploads
            if len(videos) > 1:
                print("  Waiting 10s before next upload...")
                time.sleep(10)
        except Exception as e:
            print(f"  FAILED: {e}")

    print(f"\n{'='*50}")
    print(f"  Uploaded {len(uploaded)}/{len(videos)} videos")
    print(f"{'='*50}")
    for url in uploaded:
        print(f"  {url}")


if __name__ == "__main__":
    main()