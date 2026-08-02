#!/usr/bin/env python3
"""Resize the approved social preview source to GitHub's 1200x630 spec.

Source of truth: docs/assets/images/social-preview-source.png
Output:          docs/assets/images/social-preview.png
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "assets" / "images" / "social-preview-source.png"
OUT = ROOT / "docs" / "assets" / "images" / "social-preview.png"
TARGET = (1200, 630)


def cover_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"Missing source image: {SRC}")
    img = Image.open(SRC).convert("RGB")
    img = cover_resize(img, TARGET)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({img.size[0]}x{img.size[1]}, {OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
