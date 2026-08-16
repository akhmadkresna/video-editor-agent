"""Render a 3-frame contact sheet stills for cutaway QA (opening / dense / payoff)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def pick_cutaway_qa_frames(
    cutaway: dict[str, Any],
    *,
    fps: int = 30,
) -> dict[str, int]:
    """Return frame indices (scene-local) for opening, densest, payoff."""
    dur = float(cutaway.get("durationSec") or 6.0)
    cues = cutaway.get("cues") or {}
    feeds = cutaway.get("feeds") or cutaway.get("entities") or []
    open_sec = float(
        cues.get("openSec")
        or cues.get("ledgerInSec")
        or 0.2
    )
    # Densest: middle feed arrival or 45% through.
    if isinstance(feeds, list) and feeds:
        mid = feeds[len(feeds) // 2]
        dense_sec = float(mid.get("atSec") or mid.get("at") or dur * 0.45) + 0.6
    else:
        dense_sec = dur * 0.45
    payoff_sec = float(
        cues.get("stampSec")
        or cues.get("resolveSec")
        or cues.get("lockSec")
        or cues.get("totalSec")
        or cues.get("balanceSec")
        or max(dur - 0.8, open_sec + 1.0)
    )
    clamp = lambda s: max(0, min(int(round(s * fps)), max(0, int(dur * fps) - 1)))
    return {
        "opening": clamp(open_sec + 0.35),
        "dense": clamp(dense_sec),
        "payoff": clamp(payoff_sec),
    }


def write_cutaway_contact_plan(
    episode: Path,
    timeline: dict[str, Any],
) -> Path | None:
    """Write edit/cutaway_contact_plan.json describing frames to still-render."""
    cuts = [c for c in (timeline.get("cutaways") or []) if isinstance(c, dict)]
    if not cuts:
        return None
    fps = int(timeline.get("fps") or 30)
    plan = {
        "fps": fps,
        "cutaways": [
            {
                "id": c.get("id"),
                "family": c.get("family"),
                "scene": c.get("scene"),
                "fromSec": c.get("fromSec"),
                "durationSec": c.get("durationSec"),
                "frames": pick_cutaway_qa_frames(c, fps=fps),
            }
            for c in cuts
        ],
    }
    out = episode / "edit" / "cutaway_contact_plan.json"
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return out
