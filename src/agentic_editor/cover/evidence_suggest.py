"""Suggest evidence still holds from transcript deixis (confirm before apply)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentic_editor.cover.evidence import EVIDENCE_TYPES
from agentic_editor.cover.style_load import _load_style_yaml
from agentic_editor.cover.suggest import load_cam_words
from agentic_editor.project import load_project

DEFAULT_EVIDENCE_PHRASES = [
    "socialcounts",
    "social counts",
    "vidiq",
    "socialblade",
    "estimasi",
    "estimate",
    "earnings",
    "rpm",
    "cpm",
    "subscriber",
    "subscribers",
    "views",
    "pendapatan",
    "juta",
    "screenshot",
    "website",
    "dashboard",
]


def list_evidence_files(episode: Path) -> list[Path]:
    roots = [episode / "raw" / "evidence", episode / "edit" / "evidence"]
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.iterdir()):
            if p.is_file() and p.suffix.lower() in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".gif",
            }:
                files.append(p)
    return files


def _cover_cfg(style_name: str) -> dict[str, Any]:
    parsed = _load_style_yaml(style_name)
    cover = parsed.get("cover") if isinstance(parsed, dict) else None
    return cover if isinstance(cover, dict) else {}


def _phrases(style_name: str) -> list[str]:
    cfg = _cover_cfg(style_name)
    raw = cfg.get("prefer_evidence_when") or DEFAULT_EVIDENCE_PHRASES
    out = [str(p).strip().lower() for p in raw if str(p).strip()]
    return out or list(DEFAULT_EVIDENCE_PHRASES)


def _word_hits(
    words: list[dict[str, Any]], phrases: list[str]
) -> list[tuple[float, float, str]]:
    """Return (start, end, phrase) for transcript hits."""
    if not words:
        return []
    texts = [str(w.get("text") or w.get("word") or "").lower() for w in words]
    starts = [float(w.get("start") or 0) for w in words]
    ends = [float(w.get("end") or w.get("start") or 0) for w in words]
    joined = " ".join(texts)
    # Build char→word index for approximate mapping
    hits: list[tuple[float, float, str]] = []
    for phrase in phrases:
        if " " in phrase:
            if phrase not in joined:
                continue
            # Find first word that starts the phrase
            for i, t in enumerate(texts):
                window = " ".join(texts[i : i + len(phrase.split())])
                if window.startswith(phrase) or phrase in window:
                    j = min(len(texts) - 1, i + len(phrase.split()) - 1)
                    hits.append((starts[i], ends[j], phrase))
                    break
        else:
            for i, t in enumerate(texts):
                if phrase in t or t == phrase:
                    hits.append((starts[i], ends[i], phrase))
                    break
    hits.sort(key=lambda x: x[0])
    return hits


def suggest_evidence_events(
    episode: Path,
    *,
    style_name: str | None = None,
) -> dict[str, Any]:
    """Build evidence event suggestions from files + transcript deixis."""
    cfg = load_project(episode)
    style = style_name or str(cfg.get("style") or "tutorial")
    cover_cfg = _cover_cfg(style)
    ev_cfg = cover_cfg.get("evidence") if isinstance(cover_cfg.get("evidence"), dict) else {}
    min_hold = float(ev_cfg.get("min_hold_sec") or cover_cfg.get("min_hold_sec") or 2.5)
    layout = str(ev_cfg.get("default_layout") or "float")
    with_pip = bool(ev_cfg.get("default_pip", True))
    event_type = "evidence_with_cam" if with_pip else "evidence"

    files = list_evidence_files(episode)
    words = load_cam_words(episode / "edit")
    phrases = _phrases(style)
    hits = _word_hits(words, phrases)

    events: list[dict[str, Any]] = []
    used_files: list[str] = []
    for i, f in enumerate(files):
        if i < len(hits):
            start = float(hits[i][0])
            phrase = hits[i][2]
        else:
            # Spread leftover stills after last hit or from 8s
            base = hits[-1][0] + 8.0 if hits else 8.0 + i * 10.0
            start = base
            phrase = "evidence-file"
        end = start + min_hold
        events.append(
            {
                "type": event_type,
                "start": round(start, 3),
                "end": round(end, 3),
                "src": f.name,
                "layout": layout if layout in ("float", "full") else "float",
                "note": f"evidence still ({phrase})",
            }
        )
        used_files.append(f.name)

    return {
        "style": style,
        "evidence_dir": "raw/evidence",
        "files": used_files,
        "hit_phrases": [h[2] for h in hits],
        "events": events,
        "rule": "Real captures only — no AI-generated dashboards. Confirm before --apply.",
    }


def apply_evidence_events(
    episode: Path,
    suggestion: dict[str, Any],
    *,
    replace: bool = True,
) -> Path:
    """Merge suggestion events into edit/cover.json."""
    edit = episode / "edit"
    edit.mkdir(parents=True, exist_ok=True)
    cover_path = edit / "cover.json"
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
    else:
        from agentic_editor.cover import example_cover

        cover = example_cover()
    existing = list(cover.get("events") or [])
    if replace:
        existing = [
            e
            for e in existing
            if str(e.get("type") or "").lower() not in EVIDENCE_TYPES
        ]
    existing.extend(list(suggestion.get("events") or []))
    cover["events"] = existing
    cover_path.write_text(json.dumps(cover, indent=2) + "\n", encoding="utf-8")
    return cover_path
