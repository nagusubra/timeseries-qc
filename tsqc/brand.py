"""Brand asset accessors shipped with the tsqc package."""

from __future__ import annotations

from importlib.resources import files


def logo_bytes(name: str = "logo.png") -> bytes:
    """Return packaged brand asset bytes.

    Available names: ``logo.png`` (512), ``logo-64.png``, ``logo.svg``, ``favicon.ico``.
    """
    return (files("tsqc") / "assets" / name).read_bytes()


def logo_svg() -> str:
    """Return the vector brand mark as an SVG string."""
    return logo_bytes("logo.svg").decode("utf-8")
