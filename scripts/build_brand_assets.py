#!/usr/bin/env python3
"""Build multi-format / multi-size brand assets from the approved logo master.

Source of truth (raster): docs/assets/brand/logo-master-512.png
Vector mark:             docs/assets/brand/logo.svg
Also syncs docs site logo/favicon under docs/assets/images/.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "docs" / "assets" / "brand"
IMAGES = ROOT / "docs" / "assets" / "images"
PUBLIC = ROOT / "public" / "brand"

# Cursor-generated approved mark (navy + white bars + green check badge)
CURSOR_SRC = Path(
    r"C:\Users\snarayan\.cursor\projects\c-Users-snarayan-Desktop-timeseries-qc"
    r"\assets\logo-e-var6-navy-green-badge.png"
)
MASTER_NAME = "logo-master-512.png"


def resolve_source() -> Path:
    """Prefer in-repo master; fall back to Cursor-approved source once."""
    master = BRAND / MASTER_NAME
    if master.exists():
        return master
    if CURSOR_SRC.exists():
        return CURSOR_SRC
    raise SystemExit(
        f"Missing brand master. Expected {master} or approved source {CURSOR_SRC}"
    )

SIZES = (16, 32, 48, 64, 96, 128, 180, 192, 256, 512)
ICO_SIZES = (16, 32, 48, 64, 128, 256)

# Squircle corner radius as fraction of side (matches ~rx=96 on 512 viewBox)
CORNER_RADIUS_RATIO = 96 / 512

NAVY = "#0B1120"
GREEN = "#16A34A"
WHITE = "#FFFFFF"

LOGO_SVG = f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="timeseries-qc">
  <!-- Transparent canvas; navy only inside the rounded tile -->
  <rect width="512" height="512" rx="96" fill="{NAVY}"/>
  <!-- ascending bars -->
  <rect x="118" y="268" width="68" height="132" rx="18" fill="{WHITE}"/>
  <rect x="222" y="188" width="68" height="212" rx="18" fill="{WHITE}"/>
  <rect x="326" y="108" width="68" height="292" rx="18" fill="{WHITE}"/>
  <!-- green check badge -->
  <circle cx="368" cy="368" r="92" fill="{GREEN}"/>
  <path d="M318 370 L352 404 L424 318" fill="none" stroke="{WHITE}"
        stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

FAVICON_SVG = LOGO_SVG  # same mark; square works as favicon


def cover_square(img: Image.Image, size: int) -> Image.Image:
    """Center-crop to square then resize."""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = img.crop((left, top, left + side, top + side))
    return cropped.resize((size, size), Image.Resampling.LANCZOS)


def apply_transparent_corners(img: Image.Image, radius_ratio: float = CORNER_RADIUS_RATIO) -> Image.Image:
    """Punch clear alpha outside the rounded tile so curved corners aren't black."""
    from PIL import ImageDraw

    rgba = img.convert("RGBA")
    w, h = rgba.size
    radius = max(1, int(round(min(w, h) * radius_ratio)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(rgba, mask=mask)
    # Keep original alpha inside the tile (intersect with existing alpha)
    src_a = rgba.split()[-1]
    tile_a = Image.new("L", (w, h), 0)
    tile_a.paste(src_a, mask=mask)
    out.putalpha(tile_a)
    return out


def write_raster(master: Image.Image, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rgba = master.convert("RGBA")
    for size in SIZES:
        icon = cover_square(rgba, size)
        # Re-apply mask after resize so downscales stay clean at corners
        icon = apply_transparent_corners(icon)
        stem = f"logo-{size}"
        icon.save(out_dir / f"{stem}.png", "PNG", optimize=True)
        # JPEG has no alpha — flatten onto white so corners stay "clear" on light UIs
        rgb = Image.new("RGB", icon.size, (255, 255, 255))
        rgb.paste(icon, mask=icon.split()[-1])
        rgb.save(out_dir / f"{stem}.jpg", "JPEG", quality=92, optimize=True)
        try:
            icon.save(out_dir / f"{stem}.webp", "WEBP", quality=90, method=6)
        except OSError:
            pass  # webp optional if encoder missing

    # Multi-resolution ICO (preserves transparency)
    ico_frames = [apply_transparent_corners(cover_square(rgba, s)) for s in ICO_SIZES]
    ico_frames[0].save(
        out_dir / "favicon.ico",
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_frames[1:],
    )


def sync_site_assets(master_512: Path) -> None:
    """Keep MkDocs theme paths working under docs/assets/images/."""
    IMAGES.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BRAND / "logo.svg", IMAGES / "logo.svg")
    shutil.copy2(BRAND / "logo.svg", IMAGES / "favicon.svg")
    shutil.copy2(master_512, IMAGES / "logo.png")
    shutil.copy2(BRAND / "sizes" / "logo-180.png", IMAGES / "apple-touch-icon.png")
    if (BRAND / "sizes" / "favicon.ico").exists():
        shutil.copy2(BRAND / "sizes" / "favicon.ico", IMAGES / "favicon.ico")


def main() -> int:
    src_path = resolve_source()

    BRAND.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)

    # Master raster (normalize to exact 512x512, transparent outside rounded tile)
    src = Image.open(src_path).convert("RGBA")
    master = apply_transparent_corners(cover_square(src, 512))
    master_path = BRAND / MASTER_NAME
    master.save(master_path, "PNG", optimize=True)

    # Vector mark
    (BRAND / "logo.svg").write_text(LOGO_SVG, encoding="utf-8")
    (BRAND / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")

    # Multi-size pack
    sizes_dir = BRAND / "sizes"
    write_raster(master, sizes_dir)

    # Mirror pack to public/brand for external consumers
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(BRAND, PUBLIC)

    sync_site_assets(master_path)

    # Packaged wheel assets (PyPI / importlib.resources)
    pkg = ROOT / "tsqc" / "assets"
    pkg.mkdir(parents=True, exist_ok=True)
    shutil.copy2(master_path, pkg / "logo.png")
    shutil.copy2(BRAND / "logo.svg", pkg / "logo.svg")
    shutil.copy2(sizes_dir / "logo-64.png", pkg / "logo-64.png")
    shutil.copy2(sizes_dir / "favicon.ico", pkg / "favicon.ico")

    print(f"Master: {master_path} ({master.size[0]}x{master.size[1]})")
    print(f"Brand pack: {BRAND}")
    print(f"Public pack: {PUBLIC}")
    print(f"Package assets: {pkg}")
    print(f"Site logo/favicon synced to: {IMAGES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
