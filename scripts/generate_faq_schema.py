#!/usr/bin/env python3
"""Parse docs/faq.md ### questions into docs/_data/faq.json for FAQPage JSON-LD."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAQ_MD = ROOT / "docs" / "faq.md"
OUT = ROOT / "docs" / "_data" / "faq.json"

HEADING_RE = re.compile(r"^### (.+)$", re.MULTILINE)


def _strip_md(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_#]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_faq(md: str) -> list[dict[str, str]]:
    matches = list(HEADING_RE.finditer(md))
    items: list[dict[str, str]] = []
    for i, match in enumerate(matches):
        question = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        # Stop at next ## section if it appears before next ###
        section = md[start:end]
        section = re.split(r"^## ", section, maxsplit=1, flags=re.MULTILINE)[0]
        answer = _strip_md(section)
        if question and answer:
            items.append({"question": question, "answer": answer})
    return items


def main() -> int:
    md = FAQ_MD.read_text(encoding="utf-8")
    items = parse_faq(md)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} FAQ items to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
