"""
YouTube Script + Voiceover Generator
=====================================
Generates faceless YouTube video scripts from ClickBank offers.
Each script includes:
  - Title (SEO-optimized)
  - Description (with affiliate link)
  - Tags
  - Scene-by-scene script with text overlays
  - ElevenLabs TTS audio generation

The videos are designed to be made with simple slideshow tools:
  - Each "scene" = one slide (text on dark background)
  - Voiceover from ElevenLabs
  - Free editing: Clipchamp (Windows) or DaVinci Resolve (free)

Usage:
    python generate_youtube.py                    # Generate scripts for top 5 offers
    python generate_youtube.py --top 10           # Generate for top 10
    python generate_youtube.py --tts              # Also generate ElevenLabs audio
    python generate_youtube.py --dry-run          # Print scripts, don't write

Requirements for TTS:
    pip install requests
    Set ELEVENLABS_API_KEY in .env
"""

import json
import argparse
import html
import os
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CACHE_PATH = SCRIPT_DIR / "offers_cache.json"
YOUTUBE_DIR = SCRIPT_DIR / "youtube"
BASE_URL = "https://fezbizz.github.io/earn-online"


def esc(s):
    if s is None:
        return ""
    return html.escape(str(s))


def fmt_money(v):
    try:
        return f"${float(v):.2f}"
    except (ValueError, TypeError):
        return "$0"


def generate_script(offer):
    """Generate a complete YouTube video script for a faceless review video."""
    title = offer["title"]
    site = offer["site"]
    hoplink = offer.get("hoplink", "")
    category = offer.get("category", "")
    comm = fmt_money(offer.get("commission", 0))
    initial_comm = fmt_money(offer.get("initial_commission", 0))
    epc = fmt_money(offer.get("epc", 0))
    gravity = offer.get("gravity", 0)
    future = float(offer.get("future_commission", 0) or 0)
    has_recurring = future > 0
    desc_text = offer.get("description", "")

    epc_val = float(offer.get("epc", 0) or 0)
    grav_val = float(offer.get("gravity", 0) or 0)
    comm_val = float(offer.get("commission", 0) or 0)

    # Video title (SEO-optimized for YouTube search)
    video_title = f"{title} Review — Does It Actually Work? (Real Data)"

    # Build scene-by-scene script
    # Each scene = one slide + voiceover text

    scenes = []

    # Scene 1: Hook
    scenes.append({
        "slide_text": f"{title}\nReview — Does It Actually Work?",
        "subtitle": "Real ClickBank Data. No Hype.",
        "voiceover": f"Is {title} worth your money? In this video, I break down the real data — commission, EPC, and gravity — so you can decide before you click. No hype, no sales pitch, just the numbers.",
        "duration": 10,
    })

    # Scene 2: What is it
    short_desc = desc_text[:150] if desc_text else f"A product in the {category} category on ClickBank."
    scenes.append({
        "slide_text": f"What Is {title}?",
        "subtitle": category,
        "voiceover": f"{title} is a product in the {category} category on ClickBank. {short_desc}",
        "duration": 15,
    })

    # Scene 3: The numbers
    scenes.append({
        "slide_text": f"The Numbers\nCommission: {comm}\nEPC: {epc}\nGravity: {gravity:.0f}",
        "subtitle": "Data from ClickBank Marketplace",
        "voiceover": f"Here are the real numbers from the ClickBank Marketplace. The commission is {comm} per sale. The EPC — earnings per click — is {epc}. And the gravity score is {gravity:.0f}, which means this many affiliates are actively earning from this offer.",
        "duration": 15,
    })

    # Scene 4: What the numbers mean
    if epc_val >= 3 and grav_val > 20:
        verdict_voice = "These numbers are strong. The EPC shows affiliates are earning, and the gravity confirms it. This offer converts."
        verdict_text = "VERDICT: Strong pick"
    elif epc_val > 0:
        verdict_voice = f"The EPC is positive at {epc}, which means the offer does convert. But the gravity is {gravity:.0f}, which means fewer affiliates are testing it. It could work, but it's more of a gamble."
        verdict_text = "VERDICT: Decent but mixed"
    else:
        verdict_voice = "The EPC is not reported, which means conversion is unproven. I would test this carefully with a small amount of traffic before committing."
        verdict_text = "VERDICT: Unproven"
    scenes.append({
        "slide_text": verdict_text,
        "subtitle": "Based on EPC + Gravity",
        "voiceover": verdict_voice,
        "duration": 12,
    })

    # Scene 5: Strengths
    strengths = []
    if comm_val >= 100:
        strengths.append(f"High commission at {comm} per sale")
    elif comm_val >= 50:
        strengths.append(f"Decent commission at {comm} per sale")
    if epc_val >= 3:
        strengths.append(f"EPC of {epc} — proven conversion")
    if grav_val > 100:
        strengths.append(f"High gravity ({gravity:.0f}) — many affiliates earning")
    elif grav_val > 20:
        strengths.append(f"Moderate gravity ({gravity:.0f}) — solid traction")
    if has_recurring:
        strengths.append(f"Recurring revenue — income compounds")
    strengths_text = "\n".join(f"✓ {s}" for s in strengths) if strengths else "✓ Positive EPC"
    scenes.append({
        "slide_text": f"Strengths\n\n{strengths_text}",
        "subtitle": "Why it might work",
        "voiceover": "Here are the strengths. " + ". ".join(strengths) + ".",
        "duration": 12,
    })

    # Scene 6: Weaknesses
    weaknesses = []
    if comm_val < 50:
        weaknesses.append(f"Lower commission at {comm}")
    if epc_val == 0:
        weaknesses.append("No EPC data — conversion unproven")
    if grav_val < 10 and grav_val > 0:
        weaknesses.append(f"Low gravity ({gravity:.0f}) — few affiliates earning")
    if not has_recurring:
        weaknesses.append("One-time payout — no recurring income")
    weaknesses_text = "\n".join(f"✗ {w}" for w in weaknesses) if weaknesses else "✗ Limited data available"
    scenes.append({
        "slide_text": f"Weaknesses\n\n{weaknesses_text}",
        "subtitle": "What to watch out for",
        "voiceover": "Here are the weaknesses. " + ". ".join(weaknesses) + ".",
        "duration": 12,
    })

    # Scene 7: How to promote
    scenes.append({
        "slide_text": "How to Promote It\n\n1. Write an honest review\n2. Make a YouTube video\n3. Pin on Pinterest\n4. Be consistent for 3 months",
        "subtitle": "Free traffic methods",
        "voiceover": "If you decide to promote this offer, here is the boring method that works. Write an honest review article. Make a YouTube video about it. Pin it on Pinterest. Do this consistently for three months before judging results. There are no shortcuts.",
        "duration": 15,
    })

    # Scene 8: CTA
    scenes.append({
        "slide_text": f"Try {title}\nLink in description",
        "subtitle": "Affiliate link below",
        "voiceover": f"If this review was helpful, the link is in the description below. Check out the full written review on our site for more details. Thanks for watching, and remember — the boring system works. Stick with it.",
        "duration": 10,
    })

    # Full voiceover script (for ElevenLabs)
    full_voiceover = " ".join(s["voiceover"] for s in scenes)

    # YouTube description
    yt_description = f"""{title} Review — Does It Actually Work?

Real ClickBank data: {comm} commission, {epc} EPC, {gravity:.0f} gravity. No hype — just the numbers.

Full written review: {BASE_URL}/reviews/

Try {title}: {hoplink}

Disclosure: This video contains affiliate links. If you click and buy, I earn a commission at no extra cost to you. I don't guarantee any income results.

Timestamps:
0:00 - Introduction
0:10 - What is {title}?
0:25 - The real numbers
0:40 - What the numbers mean
0:52 - Strengths
1:04 - Weaknesses
1:16 - How to promote it
1:31 - Final verdict

#clickbank #affiliatemarketing #{site.lower()} #review"""

    # Tags
    tags = [
        title.lower(), site.lower(), "clickbank", "affiliate marketing",
        "clickbank review", "does it work", category.lower().replace(" & ", ""),
        "affiliate offer", "earn money online", "passive income",
    ]

    return {
        "video_title": video_title,
        "description": yt_description,
        "tags": tags,
        "scenes": scenes,
        "full_voiceover": full_voiceover,
        "hoplink": hoplink,
        "total_duration": sum(s["duration"] for s in scenes),
    }


def generate_elevenlabs_audio(text, api_key, voice_id=None, output_path=None):
    """Generate voiceover audio using ElevenLabs API."""
    import requests

    # Default voice — you can change this to your preferred voice
    if not voice_id:
        voice_id = "JBFqnCBsd6RMkjVDRZzb"  # George — warm, captivating storyteller (premade, free tier)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    resp = requests.post(url, json=data, headers=headers, timeout=60)

    if resp.status_code == 200:
        if output_path:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return str(output_path)
        return resp.content
    else:
        print(f"  ElevenLabs error {resp.status_code}: {resp.text[:200]}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube scripts for faceless review videos")
    parser.add_argument("--top", type=int, default=5, help="Number of top offers (default: 5)")
    parser.add_argument("--tts", action="store_true", help="Generate ElevenLabs audio")
    parser.add_argument("--dry-run", action="store_true", help="Print scripts, don't write files")
    args = parser.parse_args()

    if not CACHE_PATH.exists():
        print("ERROR: offers_cache.json not found. Run pull_offers.py first.")
        return

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)

    offers = cache.get("offers", [])[:args.top]

    if not args.dry_run:
        YOUTUBE_DIR.mkdir(exist_ok=True)

    # Load ElevenLabs key if TTS requested
    elevenlabs_key = None
    if args.tts:
        env_path = SCRIPT_DIR / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    elevenlabs_key = line.split("=", 1)[1].strip()
        if not elevenlabs_key or "your-" in elevenlabs_key.lower():
            print("WARNING: No ElevenLabs API key found in .env.")
            print("Add: ELEVENLABS_API_KEY=your-key-here")
            print("Generating scripts only (no audio).")
            args.tts = False

    print(f"\nGenerating YouTube scripts for {len(offers)} offers...\n")

    for i, offer in enumerate(offers, 1):
        script = generate_script(offer)
        slug = offer["site"].lower().replace(" ", "-")

        if args.dry_run:
            print(f"--- Video {i}: {script['video_title']} ---")
            print(f"  Duration: {script['total_duration']}s")
            print(f"  Scenes: {len(script['scenes'])}")
            print(f"  Tags: {', '.join(script['tags'][:5])}")
            print()
            continue

        # Save script as JSON (structured, for automation)
        script_path = YOUTUBE_DIR / f"{slug}_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2)

        # Save readable script as text
        txt_path = YOUTUBE_DIR / f"{slug}_script.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"YOUTUBE VIDEO SCRIPT\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"TITLE: {script['video_title']}\n\n")
            f.write(f"DURATION: ~{script['total_duration']} seconds\n\n")
            f.write(f"DESCRIPTION:\n{script['description']}\n\n")
            f.write(f"TAGS: {', '.join(script['tags'])}\n\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"SCENE-BY-SCENE SCRIPT\n")
            f.write(f"{'=' * 60}\n\n")
            for j, scene in enumerate(script["scenes"], 1):
                f.write(f"SCENE {j} ({scene['duration']}s)\n")
                f.write(f"  Slide text: {scene['slide_text']}\n")
                f.write(f"  Subtitle: {scene['subtitle']}\n")
                f.write(f"  Voiceover: {scene['voiceover']}\n\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"FULL VOICEOVER (for ElevenLabs):\n\n")
            f.write(script["full_voiceover"])
            f.write(f"\n\n{'=' * 60}\n")

        print(f"  {i}. {slug}_script.txt + {slug}_script.json ({script['total_duration']}s)")

        # Generate ElevenLabs audio if requested
        if args.tts and elevenlabs_key:
            audio_path = YOUTUBE_DIR / f"{slug}_voiceover.mp3"
            print(f"     Generating ElevenLabs audio...")
            result = generate_elevenlabs_audio(
                script["full_voiceover"],
                elevenlabs_key,
                output_path=str(audio_path)
            )
            if result:
                print(f"     Audio saved: {slug}_voiceover.mp3")
            else:
                print(f"     Audio generation failed (check API key)")

    if not args.dry_run:
        print(f"\nDone! {len(offers)} scripts in youtube/")
        print(f"  Read the .txt files for the full scene-by-scene script")
        print(f"  Use the .json files for automation")
        if args.tts:
            print(f"  Audio files ready for video editing")
        print(f"\nTo make the video:")
        print(f"  1. Create slides in Clipchamp (free on Windows) or Canva")
        print(f"  2. Use the slide text from each scene")
        print(f"  3. Add the voiceover audio")
        print(f"  4. Export as MP4 and upload to YouTube")


if __name__ == "__main__":
    main()