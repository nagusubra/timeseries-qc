"""MkDocs hooks for timeseries-qc documentation site."""

from __future__ import annotations

import json
from pathlib import Path


def on_config(config):
    """Ensure FAQ schema JSON exists before build."""
    docs_dir = Path(config["docs_dir"])
    faq_json = docs_dir / "_data" / "faq.json"
    faq_md = docs_dir / "faq.md"
    if not faq_json.exists() and faq_md.exists():
        # Generate on the fly if missing (CI safety net).
        import sys

        root = docs_dir.parent
        sys.path.insert(0, str(root / "scripts"))
        from generate_faq_schema import main as generate

        generate()
    return config


def on_page_context(context, page, config, **kwargs):
    """Inject FAQ schema data for the FAQ page template."""
    if page.file.src_uri == "faq.md":
        faq_path = Path(config["docs_dir"]) / "_data" / "faq.json"
        if faq_path.exists():
            context["faq_items"] = json.loads(faq_path.read_text(encoding="utf-8"))
        else:
            context["faq_items"] = []
    return context
