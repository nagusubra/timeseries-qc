#!/usr/bin/env python3
"""Fail if agent/doc files disagree with pyproject.toml version."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)

# Files that must mention the current package version (as vX.Y.Z or X.Y.Z).
VERSIONED_FILES = [
    "CLAUDE.md",
    "CLINE.md",
    ".cursor/rules/timeseries-qc.mdc",
    ".github/copilot-instructions.md",
    ".opencode/skills/timeseries-qc.md",
    "docs/timeseries-qc.md",
    "docs/llms-context.md",
    "docs/llms.txt",
    "docs/llms-full.txt",
    "docs/index.md",
    "README.md",
]

# Stale reason-string prefix that must not appear as current docs.
STALE_REASON = "external_quality_value:"
REASON_CHECK_FILES = [
    ".cursor/rules/timeseries-qc.mdc",
    ".opencode/skills/timeseries-qc.md",
    "docs/timeseries-qc.md",
    "docs/llms-full.txt",
    "docs/llms-context.md",
    "CLAUDE.md",
    "CLINE.md",
    "README.md",
]


def read_package_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = VERSION_RE.search(text)
    if not match:
        raise SystemExit("Could not find version in pyproject.toml")
    return match.group(1)


def main() -> int:
    version = read_package_version()
    patterns = [
        re.compile(rf"\bv{re.escape(version)}\b"),
        re.compile(rf"\b{re.escape(version)}\b"),
    ]
    errors: list[str] = []

    for rel in VERSIONED_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if not any(p.search(text) for p in patterns):
            errors.append(f"{rel}: does not mention version {version}")

    for rel in REASON_CHECK_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Allow changelog/history mentions of the old prefix.
        if STALE_REASON in text and "Renamed" not in text and "renamed" not in text:
            # Still allow if it's clearly historical ("from X to Y").
            if f"from `{STALE_REASON}`" not in text and f"from {STALE_REASON}" not in text:
                errors.append(
                    f"{rel}: still documents stale reason prefix {STALE_REASON!r}; "
                    f"use 'source_data_quality:'"
                )

    if errors:
        print("Version consistency check FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"Version consistency OK (package version {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
