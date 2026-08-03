#!/usr/bin/env python3
"""Build social preview from the hand-designed card + current brand logo.

Source of truth (hand art): docs/assets/images/social-preview-hand.png
Brand mark overlay:         docs/assets/brand/logo-master-512.png
Outputs:
  docs/assets/images/social-preview-source.png
  docs/assets/images/social-preview.png           (1200x630)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
HAND = ROOT / "docs" / "assets" / "images" / "social-preview-hand.png"
# Fallback: Cursor attachment of the approved hand-designed card
HAND_FALLBACK = Path(
    r"C:\Users\snarayan\.cursor\projects\c-Users-snarayan-Desktop-timeseries-qc"
    r"\assets\c__Users_snarayan_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"2fd989603d45960af564b37ed8aa34c0_images_image-b38a807d-22ca-41d7-9e6a-aab23629b51e.png"
)
LOGO = ROOT / "docs" / "assets" / "brand" / "logo-master-512.png"
OUT_SRC = ROOT / "docs" / "assets" / "images" / "social-preview-source.png"
OUT = ROOT / "docs" / "assets" / "images" / "social-preview.png"
TARGET = (1200, 630)

# Full cover of old blue-bars mark + light border on the 1024x537 hand art
LOGO_ERASE_BOX_1024 = (26, 100, 112, 186)  # left, top, right, bottom
LOGO_PASTE_SIZE = 72  # square size of new mark inside the erased region


def cover_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def resolve_hand() -> Path:
    if HAND.exists():
        return HAND
    if HAND_FALLBACK.exists():
        return HAND_FALLBACK
    raise SystemExit(f"Missing hand-designed social card: {HAND}")


def paste_logo(base: Image.Image, logo: Image.Image, erase_box: tuple[int, int, int, int], paste_size: int) -> Image.Image:
    """Erase the old logo tile completely, then center the current brand mark."""
    out = base.convert("RGBA")
    left, top, right, bottom = erase_box
    w, h = right - left, bottom - top
    # Solid navy patch removes old mark + white border remnants
    bg = Image.new("RGBA", (w, h), (1, 8, 24, 255))
    out.paste(bg, (left, top))
    mark = logo.convert("RGBA").resize((paste_size, paste_size), Image.Resampling.LANCZOS)
    px = left + (w - paste_size) // 2
    py = top + (h - paste_size) // 2
    out.paste(mark, (px, py), mark)
    return out


def main() -> int:
    hand_path = resolve_hand()
    if not LOGO.exists():
        raise SystemExit(f"Missing brand logo: {LOGO}")

    hand = Image.open(hand_path).convert("RGBA")
    # Persist canonical hand source in-repo (without logo swap) once
    HAND.parent.mkdir(parents=True, exist_ok=True)
    if hand_path != HAND:
        hand.convert("RGB").save(HAND, "PNG", optimize=True)

    logo = Image.open(LOGO)
    scale = hand.width / 1024.0
    l, t, r, b = LOGO_ERASE_BOX_1024
    erase_box = (
        int(round(l * scale)),
        int(round(t * scale)),
        int(round(r * scale)),
        int(round(b * scale)),
    )
    paste_size = max(24, int(round(LOGO_PASTE_SIZE * scale)))
    composed = paste_logo(hand, logo, erase_box, paste_size)

    composed_rgb = composed.convert("RGB")
    OUT_SRC.parent.mkdir(parents=True, exist_ok=True)
    composed_rgb.save(OUT_SRC, "PNG", optimize=True)
    cover_resize(composed_rgb, TARGET).save(OUT, "PNG", optimize=True)
    print(f"Hand source: {HAND} ({hand.size[0]}x{hand.size[1]})")
    print(f"Wrote {OUT_SRC} ({composed_rgb.size[0]}x{composed_rgb.size[1]})")
    print(f"Wrote {OUT} ({TARGET[0]}x{TARGET[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
