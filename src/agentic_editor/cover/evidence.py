"""Evidence stills — real website/YouTube captures for style: evidence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

EVIDENCE_TYPES = frozenset({"evidence", "evidence_with_cam"})
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

_SAFE_KEY = re.compile(r"[^a-zA-Z0-9_]+")


def evidence_source_key(src: str) -> str:
    """Stable timeline source key for an evidence filename/path."""
    stem = Path(str(src)).stem
    safe = _SAFE_KEY.sub("_", stem).strip("_").lower() or "still"
    return f"evidence_{safe}"


def resolve_evidence_path(episode: Path, src: str) -> Path:
    """Resolve evidence asset under raw/evidence or edit/evidence."""
    raw = str(src or "").strip().replace("\\", "/")
    if not raw:
        raise FileNotFoundError("evidence event missing src")
    p = Path(raw)
    if p.is_absolute():
        if not p.is_file():
            raise FileNotFoundError(f"evidence file missing: {p}")
        return p.resolve()
    candidates = [
        episode / "raw" / "evidence" / raw,
        episode / "edit" / "evidence" / raw,
        episode / raw,
        episode / "raw" / "evidence" / Path(raw).name,
        episode / "edit" / "evidence" / Path(raw).name,
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise FileNotFoundError(
        f"evidence file not found for {src!r} "
        f"(tried raw/evidence and edit/evidence under {episode})"
    )


def collect_evidence_sources_from_cover(
    episode: Path, cover: dict[str, Any] | None
) -> dict[str, str]:
    """Map evidence_* keys → absolute paths from cover.events[]."""
    if not cover:
        return {}
    out: dict[str, str] = {}
    for ev in cover.get("events") or []:
        if not isinstance(ev, dict):
            continue
        kind = str(ev.get("type") or "").lower()
        if kind not in EVIDENCE_TYPES:
            continue
        src = str(ev.get("src") or ev.get("source") or "").strip()
        if not src or src in ("cam", "screen"):
            continue
        key = evidence_source_key(src)
        if key in out:
            continue
        out[key] = str(resolve_evidence_path(episode, src))
    return out


def is_image_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_SUFFIXES
