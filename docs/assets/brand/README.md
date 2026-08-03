# Brand assets — timeseries-qc

Canonical brand mark: navy tile + white ascending bars + green check badge.

PNG / WebP / ICO / SVG use a **transparent** canvas outside the rounded tile
(no black corner boxes). JPEG flattens those corners onto white.

## Tokens

| Token | Hex | Use |
|-------|-----|-----|
| Navy | `#0B1120` | Logo background |
| Green | `#16A34A` | Check badge / docs `--qc-good` |
| White | `#FFFFFF` | Bars + check |
| Brand blue | `#2563EB` | Docs Material indigo-adjacent accents |

Plotly timeline colors stay `#008000` / `#FFFF00` / `#FF0000` (not changed).

## Layout

```
docs/assets/brand/
  logo-master-512.png   # approved raster master
  logo.svg              # vector mark
  favicon.svg
  sizes/                # logo-{16..512}.{png,jpg,webp}, favicon.ico

docs/assets/images/     # MkDocs site copies (logo.svg, favicon.svg, logo.png, …)
public/brand/           # mirrored pack for external use
```

Rebuild after changing the master:

```bash
python scripts/build_brand_assets.py
python scripts/generate_social_preview.py   # hand card + logo overlay → 1200x630
```

Hand-designed social art (logo replaced in script): `docs/assets/images/social-preview-hand.png`

Packaged for PyPI (`import tsqc.brand`): `tsqc/assets/logo.png`, `logo-64.png`, `logo.svg`, `favicon.ico`.
