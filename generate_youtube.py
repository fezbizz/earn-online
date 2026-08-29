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

    # Video title (BUYER-focused, max 100 chars)
    raw_title = f"{title} Review — Does It Really Work? (Honest 2026)"
    video_title = raw_title[:95] + "..." if len(raw_title) > 100 else raw_title

    # Build scene-by-scene script — BUYER FOCUSED
    scenes = []

    # Scene 1: Hook (buyer question)
    scenes.append({
        "slide_text": f"{title}\nReview — Does It Really Work?",
        "subtitle": "Honest Review. No Hype.",
        "voiceover": f"Thinking about buying {title}? Before you spend your money, watch this honest review. I will tell you what it is, how it works, and whether it is actually worth it. No hype, no sales pitch — just the facts.",
        "duration": 10,
    })

    # Scene 2: What is it
    short_desc = desc_text[:150] if desc_text else f"A product in the {category} category."
    scenes.append({
        "slide_text": f"What Is {title}?",
        "subtitle": category,
        "voiceover": f"{title} is a product in the {category} category. {short_desc} It is sold through ClickBank, which means it comes with a 60-day money-back guarantee.",
        "duration": 15,
    })

    # Scene 3: Does it work? (buyer perspective)
    scenes.append({
        "slide_text": f"Does {title} Work?",
        "subtitle": "What the data says",
        "voiceover": f"Does it actually work? The honest answer is — it depends on your situation. No product works for 100 percent of people. But here is what we know: the product is actively selling, which means it is solving a real problem for buyers. And the 60-day money-back guarantee means you can try it without risk.",
        "duration": 15,
    })

    # Scene 4: Pros
    pros = []
    if is_physical if 'is_physical' in dir() else offer.get("is_physical", False):
        pros.append("Physical product you can hold")
    if offer.get("has_trial", False):
        pros.append("Trial offer available — try before you pay full price")
    if has_recurring:
        pros.append("Ongoing access — not just a one-time download")
    if offer.get("mobile_enabled", False):
        pros.append("Works on your phone")
    if grav_val > 50:
        pros.append("Popular product — many people are buying it")
    pros.append("60-day money-back guarantee protects your purchase")
    pros_text = "\n".join(f"+ {p}" for p in pros[:5])
    scenes.append({
        "slide_text": f"Pros\n\n{pros_text}",
        "subtitle": "Why it might be worth trying",
        "voiceover": "Here are the pros. " + ". ".join(pros[:5]) + ".",
        "duration": 12,
    })

    # Scene 5: Cons
    cons = []
    cons.append("Only available online — not in stores")
    if not offer.get("is_physical", False):
        cons.append("Digital product — nothing shipped to you")
    if not offer.get("has_trial", False):
        cons.append("No free trial — you pay upfront")
    if grav_val < 10:
        cons.append("Relatively new — fewer customer reviews")
    cons.append("Results vary — nothing works for everyone")
    cons_text = "\n".join(f"- {c}" for c in cons[:4])
    scenes.append({
        "slide_text": f"Cons\n\n{cons_text}",
        "subtitle": "What to consider before buying",
        "voiceover": "Here are the cons. " + ". ".join(cons[:4]) + ".",
        "duration": 12,
    })

    # Scene 6: Is it a scam?
    scenes.append({
        "slide_text": f"Is {title} a Scam?",
        "subtitle": "No — but here is the catch",
        "voiceover": f"Is {title} a scam? No. It is sold through ClickBank, a legitimate platform that has been around since 1998. ClickBank enforces the 60-day money-back guarantee. If it were a scam, ClickBank would remove it. But not being a scam does not mean it works for everyone — always use the guarantee if it does not work for you.",
        "duration": 15,
    })

    # Scene 7: Should you buy it?
    if grav_val > 20:
        verdict = "If you are dealing with the problem this product addresses, it is worth trying. You are protected by the 60-day guarantee. The worst case is you ask for a refund."
    elif grav_val > 0:
        verdict = "This product has some signals but is relatively new. It might work for you. The 60-day guarantee means you can try it risk-free."
    else:
        verdict = "The data on this product is limited. It might work, but there is not enough evidence to recommend it confidently. Try it only if you are willing to use the guarantee."
    scenes.append({
        "slide_text": f"Should You Buy {title}?",
        "subtitle": "The honest verdict",
        "voiceover": verdict + " If it works, great. If not, you get your money back. That is the beauty of the ClickBank guarantee.",
        "duration": 12,
    })

    # Scene 8: CTA (buyer-focused)
    scenes.append({
        "slide_text": f"Try {title}\nRisk-Free",
        "subtitle": "60-day money-back guarantee",
        "voiceover": f"If this review was helpful and you want to try {title}, the link is in the description below. You are protected by the 60-day money-back guarantee. Thanks for watching, and remember — if a product does not work for you, always ask for a refund.",
        "duration": 10,
    })

    # Full voiceover script (for ElevenLabs)
    full_voiceover = " ".join(s["voiceover"] for s in scenes)

    # YouTube description (BUYER-focused)
    yt_description = f"""{title} Review — Does It Really Work?

Thinking about buying {title}? Watch this honest review first. What it is, does it work, pros and cons, and whether it's worth your money.

Full written review: {BASE_URL}/reviews/

Try {title} risk-free (60-day guarantee): {hoplink}

Disclosure: This video contains affiliate links. If you click and buy, I earn a commission at no extra cost to you. I don't make false claims — always use the 60-day money-back guarantee if a product doesn't work for you.

Timestamps:
0:00 - Introduction
0:10 - What is {title}?
0:25 - Does it actually work?
0:40 - Pros
0:52 - Cons
1:04 - Is it a scam?
1:19 - Should you buy it?
1:31 - Try it risk-free

#{site.lower()} #review #doesitwork #honestreview #{category.lower().replace(' & ', '').replace(' ', '')}"""

    # Tags (BUYER-focused)
    tags = [
        title.lower(), site.lower(), "review", "does it work",
        "honest review", "is it worth it", "scam or legit",
        category.lower().replace(" & ", ""), "product review",
        "should i buy", "real review",
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
    """Generate voiceover audio using ElevenLabs API (primary) or edge-tts (free fallback)."""
    import requests

    # Try ElevenLabs first
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

    try:
        resp = requests.post(url, json=data, headers=headers, timeout=60)
        if resp.status_code == 200:
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return str(output_path)
            return resp.content
        else:
            error_msg = resp.text[:200]
            if "quota" in error_msg.lower() or "401" in str(resp.status_code):
                print(f"  ElevenLabs quota exceeded — falling back to edge-tts (free)")
                return generate_edge_tts(text, output_path)
            print(f"  ElevenLabs error {resp.status_code}: {error_msg}")
            return None
    except Exception as e:
        print(f"  ElevenLabs error: {e} — falling back to edge-tts (free)")
        return generate_edge_tts(text, output_path)


def generate_edge_tts(text, output_path):
    """Generate voiceover using edge-tts (free, unlimited, Microsoft Edge Neural voices)."""
    import asyncio
    import edge_tts

    async def _generate():
        voice = "en-US-AndrewMultilingualNeural"  # Warm, confident, authentic, honest
        communicate = edge_tts.Communicate(text, voice, rate="-5%")
        await communicate.save(output_path)

    try:
        asyncio.run(_generate())
        if output_path and Path(output_path).exists() and Path(output_path).stat().st_size > 5000:
            print(f"  edge-tts audio saved")
            return str(output_path)
        else:
            print(f"  edge-tts generated empty file")
            return None
    except Exception as e:
        print(f"  edge-tts error: {e}")
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