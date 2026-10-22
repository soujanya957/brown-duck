"""Render the Open Duck Mini left-leg assembly walkthrough.

Requires ImageMagick (`magick`) and FFmpeg (`ffmpeg`). Source CAD stills are
from Open_Duck_Mini/docs/assembly_guide.md (apirrone/Open_Duck_Mini).
Run from the repository root: python docs/render_leg_assembly_video.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "videos" / "leg-assembly.mp4"
POSTER = ROOT / "docs" / "images" / "leg-assembly-poster.png"
SOURCE = "https://github.com/user-attachments/assets/"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
if not Path(FONT).exists():
    FONT = "DejaVu-Sans"
    BOLD = "DejaVu-Sans-Bold"

# Each still is a CAD view used in the upstream guide, in assembly order.
SLIDES = [
    ("BUILD ONE LEFT LEG", "Foot / shin / thigh / hip", "Start with servo IDs 20-24 set one at a time.", "368a85ad-1c58-4db2-bdd0-812334b6c784"),
    ("1  BUILD THE FOOT", "TPU sole + PLA base", "Add inserts; join sole and base with two M3x6 screws.", "6749a5ba-cea9-4b0a-ac32-f32e130fd057"),
    ("2  FIT THE ANKLE", "Foot top and servo", "Center the unloaded servo before fitting the horn.", "197cd9b7-05a6-46ed-9af5-d2def37970c8"),
    ("3  ROUTE THE CABLE", "Through the shin sheet", "Plug in the ankle cable before closing the shin.", "a1432505-6b6c-4765-aea6-0a7a0b8b220b"),
    ("4  CLOSE THE SHIN", "Sheets + spacers", "Check that the cable is clear of moving links.", "54615217-fec9-46dd-8b40-e21a4f527b55"),
    ("5  BUILD THE THIGH", "Hip pitch orientation", "Match the guide's zero-position orientation.", "951157a4-26dc-41bb-b97f-18dbbb0c1cd3"),
    ("6  ASSEMBLE THE HIP", "Left bracket + yaw/roll", "Use the mirrored LEFT roll-to-pitch part.", "368a85ad-1c58-4db2-bdd0-812334b6c784"),
    ("7  CONNECT THE CHAIN", "Waveshare bus adapter", "Power OFF to cable. Match every servo's voltage rating.", "diagram"),
    ("8  CHECK THE LEG", "Supported bench motion", "Secure the hip. Check status, then try a 5-degree sweep.", "368a85ad-1c58-4db2-bdd0-812334b6c784"),
]


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def add_text(card, value, x, y, size, color, font, tmp):
    layer = tmp / "text.png"
    run("magick", "-background", "none", "-fill", color, "-font", font,
        "-pointsize", str(size), f"label:{value}", str(layer))
    next_card = tmp / "next.png"
    run("magick", str(card), str(layer), "-geometry", f"+{x}+{y}",
        "-composite", str(next_card))
    next_card.replace(card)


def chain_diagram(photo, tmp):
    drawings = [
        "roundrectangle 40,35 330,125 16,16",
        "roundrectangle 470,35 765,125 16,16",
    ]
    for x in (33, 183, 333, 483, 633):
        drawings.append(f"roundrectangle {x},270 {x+135},365 12,12")
    run("magick", "-size", "805x545", "xc:white", "-fill", "#e9f3fb",
        "-stroke", "#3a627e", "-strokewidth", "3",
        "-draw", " ".join(drawings), "-stroke", "#f0a72e", "-strokewidth", "5",
        "-draw", "line 332,80 464,80 line 560,128 560,230 line 560,230 100,230 "
        "line 100,230 100,265 line 168,317 183,317 line 318,317 333,317 "
        "line 468,317 483,317 line 618,317 633,317", str(photo))
    labels = [
        ("External servo supply", 60, 62, 24),
        ("Waveshare bus adapter", 487, 62, 22),
        ("USB to laptop", 590, 164, 20),
        ("20  HIP YAW", 43, 300, 18),
        ("21  HIP ROLL", 193, 300, 18),
        ("22  HIP PITCH", 338, 300, 18),
        ("23  KNEE", 507, 300, 18),
        ("24  ANKLE", 649, 300, 18),
        ("Power OFF while plugging servos in", 175, 435, 24),
    ]
    for value, x, y, size in labels:
        add_text(photo, value, x, y, size, "#173047", BOLD, tmp)


def render_slide(slide, number, tmp):
    title, subtitle, note, asset_id = slide
    photo = tmp / "photo.png"
    if asset_id == "diagram":
        chain_diagram(photo, tmp)
    else:
        source = tmp / "source.png"
        urllib.request.urlretrieve(SOURCE + asset_id, source)
        run("magick", str(source), "-resize", "780x520", "-background", "white",
            "-alpha", "remove", "-gravity", "center", "-extent", "805x545", str(photo))
    card = tmp / f"slide-{number:02}.png"
    run("magick", "-size", "1280x720", "xc:#101c2b", "-fill", "#f8b73a",
        "-draw", "rectangle 0,0 1280,8", "-fill", "#2d4155",
        "-draw", "rectangle 34,91 849,646", str(card))
    composed = tmp / "composed.png"
    run("magick", str(card), str(photo), "-geometry", "+39+96", "-composite", str(composed))
    composed.replace(card)
    add_text(card, "OPEN DUCK MINI  /  LEFT LEG", 38, 32, 23, "#f8b73a", BOLD, tmp)
    add_text(card, f"{number + 1:02} / {len(SLIDES):02}", 1165, 34, 18, "#9db3c7", FONT, tmp)
    add_text(card, title, 885, 153, 27, "white", BOLD, tmp)
    add_text(card, subtitle, 885, 230, 23, "#f8b73a", BOLD, tmp)
    words = note.split()
    lines, line = [], []
    for word in words:
        if len(" ".join(line + [word])) > 27:
            lines.append(" ".join(line))
            line = []
        line.append(word)
    if line:
        lines.append(" ".join(line))
    for i, text in enumerate(lines):
        add_text(card, text, 885, 303 + 37 * i, 20, "#e8eef5", FONT, tmp)
    add_text(card, "Follow the full assembly guide for screws and horn alignment.",
             38, 668, 16, "#9db3c7", FONT, tmp)
    return card


def main():
    for program in ("magick", "ffmpeg"):
        if not shutil.which(program):
            raise SystemExit(f"Install {program} to render the video")
    with TemporaryDirectory(prefix="brown-duck-video-") as folder:
        tmp = Path(folder)
        slides = [render_slide(slide, i, tmp) for i, slide in enumerate(SLIDES)]
        shutil.copy2(slides[0], POSTER)
        concat = tmp / "slides.txt"
        concat.write_text("".join(f"file '{slide}'\nduration 3.5\n" for slide in slides)
                          + f"file '{slides[-1]}'\nduration 0.04\n")
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-safe", "0",
            "-f", "concat", "-i", str(concat), "-t", str(len(slides) * 3.5),
            "-vf", "fps=24,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-movflags", "+faststart", str(OUTPUT))
    print(f"Wrote {OUTPUT} and {POSTER}")


if __name__ == "__main__":
    main()
