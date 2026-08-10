"""Finalize MG overlay schedule: dwell floors, diagram hold-after, collision trim.

Fixes the “list disappears too soon” failure mode where the last diagram step
was clamped to ``duration - 0.35`` and immediately faded out.
"""

from __future__ import annotations

from typing import Any

STRUCTURE = frozenset({"chapter", "diagram", "chip"})

DEFAULT_DWELL: dict[str, float] = {
    "chip_sec": 4.0,
    "chapter_sec": 5.5,
    "diagram_sec": 10.0,
    "emphasis_sec": 2.4,
    "callout_sec": 3.6,
    "min_sec": 1.8,
    "diagram_hold_after_last_sec": 2.6,
    "diagram_sec_per_step": 1.45,
    "diagram_search_pad_sec": 8.0,
    "exit_sec": 0.9,
}


def dwell_for(kind: str, dwell: dict[str, Any] | None = None) -> float:
    d = {**DEFAULT_DWELL, **(dwell or {})}
    return float(
        {
            "chip": d["chip_sec"],
            "chapter": d["chapter_sec"],
            "diagram": d["diagram_sec"],
            "emphasis": d["emphasis_sec"],
            "callout": d.get("callout_sec", d["emphasis_sec"]),
        }.get(kind, d["min_sec"])
    )


def diagram_floor(n_steps: int, dwell: dict[str, Any] | None = None) -> float:
    d = {**DEFAULT_DWELL, **(dwell or {})}
    base = float(d["diagram_sec"])
    per = float(d["diagram_sec_per_step"])
    hold = float(d["diagram_hold_after_last_sec"])
    # Title lead + paced steps + readable hold of the full list
    return max(base, 0.7 + per * max(1, n_steps) + hold)


def apply_diagram_hold(
    inst: dict[str, Any],
    *,
    timeline_dur: float,
    dwell: dict[str, Any] | None = None,
) -> None:
    """Ensure last step has readable on-screen time; set exitStartSec."""
    if inst.get("kind") != "diagram":
        return
    d = {**DEFAULT_DWELL, **(dwell or {})}
    hold = float(d["diagram_hold_after_last_sec"])
    exit_sec = float(d["exit_sec"])
    from_sec = float(inst["fromSec"])
    dur = float(inst["durationSec"])
    steps_at = list(inst.get("stepAtSec") or [])
    if not steps_at:
        # Still keep a gentler exit for title-only diagrams
        inst["exitStartSec"] = max(0.2, dur - exit_sec)
        return

    last = float(steps_at[-1])
    need = last + hold
    remaining = max(0.05, timeline_dur - from_sec)
    if need > dur:
        dur = min(need, remaining)
        inst["durationSec"] = dur

    # Keep steps inside the readable window (before hold/exit).
    max_step = max(0.2, dur - hold)
    clamped = [min(max(0.12, float(t)), max_step) for t in steps_at]
    for i in range(1, len(clamped)):
        if clamped[i] < clamped[i - 1] + 0.25:
            clamped[i] = min(max_step, clamped[i - 1] + 0.25)
    inst["stepAtSec"] = clamped
    last = float(clamped[-1])
    # Exit only after the list has been readable for most of the hold.
    inst["exitStartSec"] = min(dur - 0.35, max(last + hold * 0.55, dur - exit_sec))


def resolve_structure_collisions(
    instances: list[dict[str, Any]],
    *,
    dwell: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Trim earlier left-rail structure when it overlaps the next one.

    Emphasis may overlap diagrams (different safe zone). Structure kinds share
    the left third — keep one readable block at a time.
    """
    d = {**DEFAULT_DWELL, **(dwell or {})}
    min_sec = float(d["min_sec"])
    items = sorted(instances, key=lambda o: (float(o["fromSec"]), float(o["durationSec"])))
    struct = [o for o in items if o.get("kind") in STRUCTURE]
    for i in range(len(struct) - 1):
        a = struct[i]
        b = struct[i + 1]
        a0 = float(a["fromSec"])
        a1 = a0 + float(a["durationSec"])
        b0 = float(b["fromSec"])
        if a1 <= b0 + 0.05:
            continue
        # Prefer keeping the later structure's entrance; trim earlier end.
        new_end = max(a0 + min_sec, b0 - 0.12)
        if new_end < a1:
            a["durationSec"] = max(min_sec, new_end - a0)
            if a.get("kind") == "diagram":
                apply_diagram_hold(a, timeline_dur=a0 + float(a["durationSec"]) + 0.01, dwell=d)
                # If hold no longer fits, accept shorter hold rather than overlapping.
                steps_at = a.get("stepAtSec") or []
                if steps_at:
                    last = float(steps_at[-1])
                    a["exitStartSec"] = min(
                        float(a["durationSec"]) - 0.25,
                        max(last + 0.8, float(a["durationSec"]) - float(d["exit_sec"])),
                    )
    return items


def finalize_overlays(
    instances: list[dict[str, Any]],
    *,
    timeline_dur: float,
    dwell: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Apply diagram hold-after, then structure collision trims."""
    d = {**DEFAULT_DWELL, **(dwell or {})}
    for inst in instances:
        if inst.get("kind") == "diagram":
            apply_diagram_hold(inst, timeline_dur=timeline_dur, dwell=d)
        else:
            dur = float(inst["durationSec"])
            inst["exitStartSec"] = max(0.15, dur - float(d["exit_sec"]))
    return resolve_structure_collisions(instances, dwell=d)
