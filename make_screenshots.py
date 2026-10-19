"""Render real program output as terminal-style PNG screenshots for the slides and report.

    python make_screenshots.py

Runs the commands below, captures exactly what they print (colours included)
and draws it in a terminal window. Output: docs/screenshots/*.png
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "screenshots"
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
SIZE, LINE = 26, 36
BG, BAR, FG = (24, 28, 36), (44, 49, 60), (222, 226, 232)
COLOURS = {"32": (110, 210, 120), "34": (110, 170, 255), "2": (130, 138, 150)}
ANSI = re.compile(r"\033\[([0-9;]*)m")

SHOTS = {
    "tests": (["-m", "pytest", "-v", "--color=yes", "-p", "no:cacheprovider"], "pytest -v", None),
    "tests_summary": (["-m", "pytest", "-q", "--color=yes", "-p", "no:cacheprovider"], "pytest -q", None),
    "demo_textbook": (["demo.py"], "python demo.py", ("1. Is the simulator", "2. Why the classical")),
    "demo_prediction": (["demo.py"], "python demo.py", ("2. Why the classical", "3. All 11")),
    "demo_comparison": (["demo.py"], "python demo.py", ("3. All 11", None)),
    "train": (["train_models.py"], "python train_models.py", None),
}


def capture(args, section):
    text = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout
    lines = text.rstrip("\n").split("\n")
    if section:
        start, end = section
        plain = [ANSI.sub("", l) for l in lines]
        i = next(k for k, l in enumerate(plain) if l.startswith(start)) - 1   # include the ==== rule
        j = next((k for k, l in enumerate(plain) if end and l.startswith(end)), len(lines)) - 1
        lines = lines[i:j]
        while lines and not ANSI.sub("", lines[-1]).strip("= "):
            lines.pop()
    return lines


def render(lines, command, path):
    regular = ImageFont.truetype(FONT_PATH, SIZE, index=0)
    bold = ImageFont.truetype(FONT_PATH, SIZE, index=1)
    lines = [f"\033[32m$\033[0m {command}"] + lines
    cols = max(len(ANSI.sub("", l)) for l in lines)
    char_w = regular.getlength("M")
    width = int(cols * char_w) + 80
    height = len(lines) * LINE + 60 + 50
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, 50], fill=BAR)
    for k, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([20 + k * 30, 17, 36 + k * 30, 33], fill=c)
    d.text((width / 2, 25), "ai_cpu_scheduler — zsh", fill=(170, 176, 186), font=regular, anchor="mm")
    y = 80
    for line in lines:
        x, colour, font = 40.0, FG, regular
        pieces = ANSI.split(line)
        for idx, piece in enumerate(pieces):
            if idx % 2 == 1:   # an escape code
                for code in piece.split(";") or ["0"]:
                    if code in ("", "0"):
                        colour, font = FG, regular
                    elif code == "1":
                        font = bold
                    else:
                        colour = COLOURS.get(code, colour)
                continue
            d.text((x, y), piece, fill=colour, font=font)
            x += font.getlength(piece)
        y += LINE
    img.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (args, command, section) in SHOTS.items():
        render(capture(args, section), command, OUT / f"{name}.png")
        print(f"wrote docs/screenshots/{name}.png")


if __name__ == "__main__":
    main()
