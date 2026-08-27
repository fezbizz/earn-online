"""
Automated Video Generator
==========================
Generates complete faceless YouTube review videos as MP4 files.

Pipeline:
  1. Read YouTube script JSON (from generate_youtube.py)
  2. Generate slide images with Pillow (dark background, white/gold text)
  3. Combine slides + voiceover MP3 into an MP4 using FFmpeg

Output: youtube/<slug>_video.mp4

Usage:
    python generate_video.py --script ampjoint_script.json
    python generate_video.py --all              # Generate videos for all scripts with audio
    python generate_video.py --all --dry-run    # Show what would be generated

Requirements:
    - Pillow (installed)
    - FFmpeg (installed)
    - Voiceover MP3s from generate_youtube.py --tts
"""

import json
import argparse
import subprocess
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).parent
YOUTUBE_DIR = SCRIPT_DIR / "youtube"

# Video dimensions (1080p)
WIDTH, HEIGHT = 1920, 1080

# Colors (match site theme)
BG_COLOR = (14, 17, 22)          # #0e1116
TEXT_COLOR = (240, 246, 252)     # #f0f6fc
ACCENT_COLOR = (201, 162, 39)    # #c9a227 gold
DIM_COLOR = (139, 150, 165)      # #8b96a5


def get_font(size, bold=False):
    """Get a system font, fall back to default if needed."""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_text(text, font, draw, max_width):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def render_slide(scene, slide_index, total_slides, output_path):
    """Render a single slide as a PNG image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    slide_text = scene.get("slide_text", "")
    subtitle = scene.get("subtitle", "")

    # Split slide_text into lines (it may contain \n)
    text_lines = slide_text.split("\n")

    # Determine font size based on text length
    max_line_length = max(len(line) for line in text_lines) if text_lines else 0
    if max_line_length > 60:
        font_size = 48
    elif max_line_length > 40:
        font_size = 60
    elif max_line_length > 20:
        font_size = 72
    else:
        font_size = 84

    main_font = get_font(font_size, bold=True)
    sub_font = get_font(36, bold=False)

    # Calculate total height for vertical centering
    line_heights = []
    for line in text_lines:
        wrapped = wrap_text(line, main_font, draw, WIDTH - 200)
        for w in wrapped:
            bbox = draw.textbbox((0, 0), w, font=main_font)
            line_heights.append(bbox[3] - bbox[1] + 10)

    main_total_height = sum(line_heights) + 20 * (len(line_heights) - 1)
    sub_height = 60 if subtitle else 0
    total_height = main_total_height + sub_height + 40

    # Start Y for vertical centering
    y = (HEIGHT - total_height) // 2

    # Draw main text (centered)
    for line in text_lines:
        wrapped = wrap_text(line, main_font, draw, WIDTH - 200)
        for w in wrapped:
            bbox = draw.textbbox((0, 0), w, font=main_font)
            w_width = bbox[2] - bbox[0]
            x = (WIDTH - w_width) // 2
            draw.text((x, y), w, fill=TEXT_COLOR, font=main_font)
            y += bbox[3] - bbox[1] + 10
        y += 20

    # Draw subtitle (smaller, dimmed, centered)
    if subtitle:
        y += 20
        sub_wrapped = wrap_text(subtitle, sub_font, draw, WIDTH - 300)
        for w in sub_wrapped:
            bbox = draw.textbbox((0, 0), w, font=sub_font)
            w_width = bbox[2] - bbox[0]
            x = (WIDTH - w_width) // 2
            draw.text((x, y), w, fill=ACCENT_COLOR, font=sub_font)
            y += bbox[3] - bbox[1] + 8

    # Draw slide number (bottom right)
    num_font = get_font(24)
    num_text = f"{slide_index} / {total_slides}"
    bbox = draw.textbbox((0, 0), num_text, font=num_font)
    draw.text((WIDTH - bbox[2] - 40, HEIGHT - bbox[3] - 30), num_text, fill=DIM_COLOR, font=num_font)

    # Draw brand text (bottom left)
    brand_font = get_font(24)
    brand = "Earn Extra Online"
    draw.text((40, HEIGHT - 50), brand, fill=DIM_COLOR, font=brand_font)

    img.save(output_path, "PNG")
    return str(output_path)


def get_audio_duration(audio_path):
    """Get duration of audio file in seconds using FFprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, timeout=10
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, TypeError):
        return 101  # fallback to script total_duration


def generate_video(script_path, audio_path, output_path):
    """Generate an MP4 video from a script + audio using FFmpeg."""
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    scenes = script.get("scenes", [])
    total_slides = len(scenes)

    if not scenes:
        print("  ERROR: No scenes in script")
        return False

    # Generate slide images
    slide_paths = []
    temp_dir = tempfile.mkdtemp(prefix="earn_video_")

    for i, scene in enumerate(scenes, 1):
        slide_path = os.path.join(temp_dir, f"slide_{i:03d}.png")
        render_slide(scene, i, total_slides, slide_path)
        slide_paths.append(slide_path)
        print(f"  Slide {i}/{total_slides} rendered")

    # Get audio duration and calculate per-slide duration
    audio_duration = get_audio_duration(audio_path)
    # Distribute duration across slides proportionally
    script_total = sum(s.get("duration", 12) for s in scenes)
    slide_durations = []
    for scene in scenes:
        proportion = scene.get("duration", 12) / script_total
        slide_durations.append(max(1, audio_duration * proportion))

    # Create FFmpeg concat file
    concat_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_path, "w") as f:
        for i, (slide_path, duration) in enumerate(zip(slide_paths, slide_durations)):
            f.write(f"file '{slide_path}'\n")
            f.write(f"duration {duration:.2f}\n")
        # FFmpeg requires the last file repeated without duration
        f.write(f"file '{slide_paths[-1]}'\n")

    # Build FFmpeg command: slides + audio = MP4
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-i", str(audio_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-r", "30",
        str(output_path)
    ]

    print(f"  Stitching video with FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    # Cleanup temp files
    for sp in slide_paths:
        try:
            os.remove(sp)
        except OSError:
            pass
    try:
        os.remove(concat_path)
    except OSError:
        pass
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-300:]}")
        return False

    # Check output file exists and has size
    if not os.path.exists(output_path) or os.path.getsize(output_path) < 10000:
        print(f"  Output file too small or missing")
        return False

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Video saved: {Path(output_path).name} ({size_mb:.1f} MB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate MP4 videos from YouTube scripts")
    parser.add_argument("--script", type=str, help="Specific script JSON file to use")
    parser.add_argument("--all", action="store_true", help="Generate videos for all scripts with audio")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    if not args.script and not args.all:
        print("Specify --script <file> or --all")
        return

    # Find script + audio pairs
    if args.script:
        script_path = YOUTUBE_DIR / args.script
        slug = args.script.replace("_script.json", "")
        audio_path = YOUTUBE_DIR / f"{slug}_voiceover.mp3"
        output_path = YOUTUBE_DIR / f"{slug}_video.mp4"

        if not script_path.exists():
            print(f"ERROR: {script_path} not found")
            return
        if not audio_path.exists():
            print(f"ERROR: {audio_path} not found. Run generate_youtube.py --tts first.")
            return

        if args.dry_run:
            print(f"Would generate: {output_path.name}")
            return

        print(f"\nGenerating video: {output_path.name}")
        success = generate_video(script_path, audio_path, output_path)
        if success:
            print(f"\nDone! Upload {output_path} to YouTube.")
    else:
        scripts = sorted(YOUTUBE_DIR.glob("*_script.json"))
        generated = 0
        for sp in scripts:
            slug = sp.name.replace("_script.json", "")
            audio_path = YOUTUBE_DIR / f"{slug}_voiceover.mp3"
            output_path = YOUTUBE_DIR / f"{slug}_video.mp4"

            if not audio_path.exists():
                print(f"  SKIP {slug}: no audio file")
                continue

            if args.dry_run:
                print(f"  Would generate: {output_path.name}")
                continue

            print(f"\n[{generated+1}] Generating: {output_path.name}")
            success = generate_video(sp, audio_path, output_path)
            if success:
                generated += 1

        print(f"\nDone! {generated} videos generated in youtube/")
        print("Upload them to YouTube with the title/description from the .txt scripts.")


if __name__ == "__main__":
    main()