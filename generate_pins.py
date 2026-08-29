"""
Pinterest Pin Generator
=======================
Generates pin images + descriptions for each review article and blog post.
Pinterest is a visual search engine — pins drive steady traffic for months.

Output:
  pinterest/pins.json  — structured pin data (title, description, link, image path)
  pinterest/*.png      — pin images (1000x1500px, Pinterest's recommended size)

Usage:
    python generate_pins.py               # Generate pins for all articles
    python generate_pins.py --limit 10    # Generate 10 pins
    python generate_pins.py --dry-run     # Print, don't write files

To use on Pinterest:
    1. Create a free Pinterest business account
    2. Create a board called "Affiliate Marketing Reviews" or "Earn Extra Online"
    3. Upload each pin image with its title + description + link
    4. Pin 3-5 per day for steady traffic
"""

import json
import argparse
import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).parent
BLOG_DIR = SCRIPT_DIR / "blog"
REVIEWS_DIR = SCRIPT_DIR / "reviews"
PINTEREST_DIR = SCRIPT_DIR / "pinterest"
BASE_URL = "https://fezbizz.github.io/earn-online"

# Pinterest recommended pin size
PIN_WIDTH, PIN_HEIGHT = 1000, 1500

# Colors (match site theme)
BG_COLOR = (14, 17, 22)
TEXT_COLOR = (240, 246, 252)
ACCENT_COLOR = (201, 162, 39)
DIM_COLOR = (139, 150, 165)


def get_font(size, bold=True):
    paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:50]


def extract_title_from_html(html_text):
    """Extract the <title> from an HTML file."""
    match = re.search(r"<title>(.*?)</title>", html_text, re.I | re.DOTALL)
    if match:
        title = match.group(1).strip()
        # Clean up common suffixes
        for suffix in [" | Earn Extra Online", " — Real, Boring Systems"]:
            if title.endswith(suffix):
                title = title[:-len(suffix)]
        return title
    return "Untitled"


def extract_desc_from_html(html_text):
    """Extract meta description from HTML."""
    match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html_text, re.I)
    if match:
        return match.group(1)
    return ""


def generate_pin_image(title, subtitle, output_path):
    """Generate a Pinterest pin image (1000x1500px)."""
    img = Image.new("RGB", (PIN_WIDTH, PIN_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([0, 0, PIN_WIDTH, 8], fill=ACCENT_COLOR)

    # Brand text at top
    brand_font = get_font(28, bold=True)
    draw.text((50, 40), "EARN EXTRA ONLINE", fill=ACCENT_COLOR, font=brand_font)
    sub_brand_font = get_font(24, bold=False)
    draw.text((50, 75), "Real, Boring Systems", fill=DIM_COLOR, font=sub_brand_font)

    # Main title — wrapped and centered
    title_font = get_font(56, bold=True)
    words = title.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        bbox = draw.textbbox((0, 0), test, font=title_font)
        if bbox[2] - bbox[0] <= PIN_WIDTH - 100:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))

    # Draw title centered vertically
    line_height = 65
    total_h = len(lines) * line_height
    y = (PIN_HEIGHT - total_h) // 2 - 50

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (PIN_WIDTH - w) // 2
        draw.text((x, y), line, fill=TEXT_COLOR, font=title_font)
        y += line_height

    # Subtitle below title
    if subtitle:
        sub_font = get_font(32, bold=False)
        y += 30
        sub_words = subtitle.split()
        sub_lines = []
        sub_current = []
        for w in sub_words:
            test = " ".join(sub_current + [w])
            bbox = draw.textbbox((0, 0), test, font=sub_font)
            if bbox[2] - bbox[0] <= PIN_WIDTH - 150:
                sub_current.append(w)
            else:
                if sub_current:
                    sub_lines.append(" ".join(sub_current))
                sub_current = [w]
        if sub_current:
            sub_lines.append(" ".join(sub_current))

        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            w = bbox[2] - bbox[0]
            x = (PIN_WIDTH - w) // 2
            draw.text((x, y), line, fill=DIM_COLOR, font=sub_font)
            y += 40

    # CTA at bottom
    cta_font = get_font(36, bold=True)
    cta_text = "Full review — link in description"
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    w = bbox[2] - bbox[0]
    x = (PIN_WIDTH - w) // 2
    draw.text((x, PIN_HEIGHT - 100), cta_text, fill=ACCENT_COLOR, font=cta_font)

    # Bottom accent bar
    draw.rectangle([0, PIN_HEIGHT - 8, PIN_WIDTH, PIN_HEIGHT], fill=ACCENT_COLOR)

    img.save(output_path, "PNG")
    return str(output_path)


def generate_pin_data(html_file, url_path):
    """Generate pin metadata from an HTML file."""
    html_text = html_file.read_text(encoding="utf-8")
    title = extract_title_from_html(html_text)
    description = extract_desc_from_html(html_text)

    # Pinterest description (with hashtags)
    pin_desc = f"{description}\n\n#affiliatemarketing #clickbank #earnmoneyonline #passiveincome #review"

    return {
        "title": title[:100],  # Pinterest title limit
        "description": pin_desc[:500],  # Pinterest description limit
        "link": f"{BASE_URL}/{url_path}",
        "slug": slugify(title),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest pins")
    parser.add_argument("--limit", type=int, default=50, help="Max pins to generate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.dry_run:
        PINTEREST_DIR.mkdir(exist_ok=True)

    # Collect all pages to create pins for
    pages = []

    # Blog articles
    if BLOG_DIR.exists():
        for f in sorted(BLOG_DIR.glob("*.html")):
            pages.append((f, f"blog/{f.name}"))

    # Product review pages
    if REVIEWS_DIR.exists():
        for f in sorted(REVIEWS_DIR.glob("*.html")):
            pages.append((f, f"reviews/{f.name}"))

    # Core pages
    for name in ["review.html", "guide.html"]:
        p = SCRIPT_DIR / name
        if p.exists():
            pages.append((p, name))

    pages = pages[:args.limit]
    print(f"\nGenerating {len(pages)} Pinterest pins...\n")

    all_pins = []

    for html_file, url_path in pages:
        pin = generate_pin_data(html_file, url_path)
        all_pins.append(pin)

        if args.dry_run:
            print(f"  {pin['slug']} → {pin['link']}")
            continue

        # Generate pin image
        img_path = PINTEREST_DIR / f"{pin['slug']}.png"
        generate_pin_image(pin["title"], "Honest review with real data", str(img_path))

        print(f"  {pin['slug']}.png — {pin['title'][:50]}")

    if not args.dry_run:
        # Save pin data as JSON
        pins_json = PINTEREST_DIR / "pins.json"
        with open(pins_json, "w", encoding="utf-8") as f:
            json.dump(all_pins, f, indent=2)

        print(f"\nDone! {len(all_pins)} pins in pinterest/")
        print(f"  Pin images: {PINTEREST_DIR}/*.png")
        print(f"  Pin data: pinterest/pins.json")
        print(f"\nTo use on Pinterest:")
        print(f"  1. Create a free Pinterest business account")
        print(f"  2. Create a board: 'Affiliate Marketing Reviews'")
        print(f"  3. Upload each pin with title + description from pins.json")
        print(f"  4. Pin 3-5 per day for steady traffic")


if __name__ == "__main__":
    main()