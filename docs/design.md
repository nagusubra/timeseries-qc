---
title: Design System — Brand, Color, Typography & Assets
description: >-
  Official design system for timeseries-qc — logo, color tokens, typography,
  quality colors, asset locations, and rules for docs, reports, social cards,
  and package branding. Follow this when changing UI or marketing surfaces.
og_title: "timeseries-qc Design System"
og_description: "Brand logo, colors, typography, and asset conventions for consistent docs, reports, and package identity."
---

# Design System

This document is the source of truth for **visual identity** across the
timeseries-qc library: documentation site, social / OG cards, HTML reports,
README, and packaged brand assets.

When changing UI or marketing surfaces, follow this guide. Prefer updating
assets via the build scripts rather than hand-editing copies.

---

## Brand mark

**Concept:** Navy tile + three ascending white bars (time series) + green
check badge (quality validated).

| Property | Value |
|----------|--------|
| Shape | Squircle (rounded square), corner radius ≈ 18.75% of side (`rx=96` on 512) |
| Background | `#0B1120` (navy) |
| Bars | `#FFFFFF`, ascending left → right |
| Badge | Circle `#16A34A` with white checkmark |
| Raster alpha | **Transparent** outside the rounded tile (PNG / WebP / ICO / SVG) |
| JPEG | No alpha — corners flattened onto white |

Do **not** revive the old “QC” text tile or the blue-gradient bars + pale
checkmark from earlier social art.

---

## Color tokens

| Token | Hex | Use |
|-------|-----|-----|
| Logo navy | `#0B1120` | Logo fill, `theme-color`, social card chrome |
| Logo green | `#16A34A` | Check badge; docs `--qc-good` / `--tsqc-green` |
| Docs primary | Material **indigo** (`#2563EB` adjacent) | Links, buttons, accents on light docs |
| Docs good | `#16A34A` | `--qc-good` in `assets/stylesheets/extra.css` |
| Docs suspect | `#CA8A04` | `--qc-sus` |
| Docs bad | `#DC2626` | `--qc-bad` |
| Plotly good | `#008000` | Chart segments — **do not change** without an intentional release note |
| Plotly sus | `#FFFF00` | Chart segments |
| Plotly bad | `#FF0000` | Chart segments |

**Theme posture**

- **Docs site:** light, airy Material (Roboto) + indigo accents.
- **Logo / social preview:** dark navy industrial card with the brand mark.
- **HTML reports:** light SaaS chrome (`#f8fafc` background, navy headings,
  green brand subtitle) with the inline SVG mark.

---

## Typography

| Surface | Font |
|---------|------|
| MkDocs Material docs | Roboto (theme default) — keep |
| Code / install chips | Material code font |
| HTML `export_report` | Roboto, then system UI stack |
| Logo wordmark in social art | Bold sans (hand card); do not invent a custom display face |

Do not introduce Inter / IBM Plex / other brand fonts unless this document
is updated first.

---

## Asset locations

| Path | Role |
|------|------|
| `docs/assets/brand/` | Canonical brand pack (master PNG, SVG, sizes) |
| `docs/assets/images/` | MkDocs copies: favicon, apple-touch, social preview |
| `public/brand/` | Mirror of the brand pack for external consumers |
| `tsqc/assets/` | Packaged wheel assets (`logo.png`, `logo-64.png`, `logo.svg`, `favicon.ico`) |

**Canonical URLs (docs site)**

- Logo: `https://nagusubra.github.io/timeseries-qc/assets/brand/logo-master-512.png`
- Social / OG: `https://nagusubra.github.io/timeseries-qc/assets/images/social-preview.png` (1200×630)

---

## Rebuild commands

```bash
# Raster + SVG sizes, sync docs/images + public/brand
python scripts/build_brand_assets.py

# Hand-designed card + current logo overlay → social-preview.png
python scripts/generate_social_preview.py
```

Sources:

- Raster master: `docs/assets/brand/logo-master-512.png`
- Hand social art (no logo swap): `docs/assets/images/social-preview-hand.png`

After regenerating the social card, **re-upload**
`docs/assets/images/social-preview.png` in GitHub → Settings → Social preview
(manual step; in-repo file does not update GitHub’s CDN automatically).

---

## Python API

```python
import tsqc

png = tsqc.logo_bytes()           # 512×512 PNG
svg = tsqc.logo_svg()             # vector mark
ico = tsqc.logo_bytes("favicon.ico")
```

Reports (`QCResult.export_report`) embed an inline SVG of the same mark so
exported HTML stays self-contained.

---

## SEO / share cards

- Default OG / Twitter image: `social-preview.png` (1200×630) with
  `og:image:width` / `height` / `alt` set in `docs/overrides/main.html`.
- Organization + SoftwareApplication JSON-LD use an `ImageObject` for the
  512×512 logo.
- Prefer the branded social card for page `og_image` unless a page needs a
  specific product screenshot.

---

## Do / don’t

**Do**

- Keep Material indigo for docs chrome.
- Keep Plotly chart colors unless shipping a documented visual change.
- Run both brand scripts after changing the master logo.
- Sync packaged `tsqc/assets/` when the master changes
  (`build_brand_assets.py` + copy into `tsqc/assets/`, or extend the script).

**Don’t**

- Mix alternate logos (QC letters, blue-gradient bars) on public surfaces.
- Commit opaque black corners on PNG/WebP masters.
- Point schema `Organization.logo` at a non-square or low-res file.
- Change social preview layout without updating
  `social-preview-hand.png` and regenerating via the script.

---

## Related

- [Contributing](contributing.md) — PR process
- [Architecture](architecture.md) — library internals
- [AI Citation Tracking](project/ai-citation-tracking.md) — AEO scorecard
- Brand pack notes: `docs/assets/brand/README.md` (repo path; not a docs nav page)
