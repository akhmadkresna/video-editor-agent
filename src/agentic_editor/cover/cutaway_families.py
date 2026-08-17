"""Cutaway family ids — labels for Sequence names / QA, not renderers.

Every brief renders through one Remotion engine (`InterfaceStage`). Board
layout is inferred from the data (catalog / ledger / access / shot). Family
ids stay so suggest can rotate names and contact sheets can group shots.

New VOs become VisualBrief data. Do not add a React component per topic.
"""

from __future__ import annotations

from typing import Any

DEFAULT_CUTAWAY_STYLE = "press"
DEFAULT_CUTAWAY_BACKDROP: dict[str, Any] = {
    "kind": "cam_blur",
    "blurPx": 34,
    "dim": 0.22,
}

# Canonical family ids (timeline naming + suggest rotation + quality gates).
CUTAWAY_FAMILIES = frozenset(
    {
        "document",
        "flow",
        "kinetic_type",
        "comparison",
        "sequence",
        "system_map",
        "evidence",
        "minimal",
    }
)

# Experimental / legacy scene ids → family (authoring aliases).
SCENE_TO_FAMILY: dict[str, str] = {
    "ledger_flow": "flow",
    "receipt_tape": "document",
    "kinetic_figures": "kinetic_type",
    "blueprint_nodes": "system_map",
    # Direct family ids also accepted as "scene" during migration.
    "document": "document",
    "flow": "flow",
    "kinetic_type": "kinetic_type",
    "comparison": "comparison",
    "sequence": "sequence",
    "system_map": "system_map",
    "evidence": "evidence",
    "minimal": "minimal",
}

# Remotion still keys components by scene for dissolve naming; prefer family.
FAMILY_TO_SCENE: dict[str, str] = {
    "document": "receipt_tape",
    "flow": "ledger_flow",
    "kinetic_type": "kinetic_figures",
    "system_map": "blueprint_nodes",
    "comparison": "kinetic_figures",
    "sequence": "ledger_flow",
    "evidence": "evidence",
    "minimal": "minimal",
}

# One engine: every family id shares the same capability envelope.
ENGINE_CAPABILITIES: dict[str, Any] = {
    "supportsValues": True,
    "supportsProof": True,
    "maxEntities": 8,
    "preferredIntents": [
        "explain",
        "compare",
        "accumulate",
        "transform",
        "sequence",
        "prove",
        "warn",
        "summarize",
    ],
    "minDurationSec": 3.0,
    "maxCopyChars": 72,
}
FAMILY_CAPABILITIES: dict[str, dict[str, Any]] = {
    fam: dict(ENGINE_CAPABILITIES) for fam in CUTAWAY_FAMILIES
}

# Generic beat names ↔ legacy cue keys (cover source time → timeline *Sec).
BEAT_ALIASES: dict[str, str] = {
    # generic → legacy out key
    "open": "ledgerInSec",
    "classify": "inOutSec",
    "total": "balanceSec",
    "lock": "lockSec",
    "stamp": "stampSec",
    "reject": "attemptSec",
    # legacy source keys → out
    "ledgerIn": "ledgerInSec",
    "inOut": "inOutSec",
    "balance": "balanceSec",
    "attempts": "attemptSec",
}

LEGACY_CUE_TO_BEAT: dict[str, str] = {
    "ledgerIn": "open",
    "inOut": "classify",
    "balance": "total",
    "lock": "lock",
    "stamp": "stamp",
    "attempts": "reject",
}

# Picture takeover ends after the last real beat — not the VO window.
# Matches CutawayLayer dissolve (10 frames @ 30fps) + InterfaceStage hitMotion.
CUTAWAY_FADE_SEC = 10 / 30
CUTAWAY_MOTION_SETTLE_SEC = 0.5
CUTAWAY_HOLD_AFTER_LAST_SEC = 0.45
CUTAWAY_MAX_IDLE_TO_RESOLVE_SEC = 3.5
CUTAWAY_RESOLVE_AFTER_ACTION_SEC = 0.85
CUTAWAY_MIN_PLAY_SEC = 2.4

_RESOLVE_CUE_KEYS = frozenset(
    {"stamp", "stampSec", "resolve", "resolveSec"}
)
_ACTION_CUE_KEYS = frozenset(
    {
        "open",
        "openSec",
        "ledgerIn",
        "ledgerInSec",
        "classify",
        "classifySec",
        "inOut",
        "inOutSec",
        "total",
        "totalSec",
        "balance",
        "balanceSec",
        "lock",
        "lockSec",
        "reject",
        "rejectSec",
        "attempts",
        "attemptSec",
    }
)


def _collect_seconds(value: Any) -> list[float]:
    if isinstance(value, list):
        out: list[float] = []
        for item in value:
            out.extend(_collect_seconds(item))
        return out
    try:
        return [float(value)]
    except (TypeError, ValueError):
        return []


def cutaway_action_times(cut: dict[str, Any]) -> tuple[list[float], list[float]]:
    """Return (action seconds, resolve/stamp seconds) in the cut's time base."""
    action: list[float] = []
    resolve: list[float] = []
    for row in list(cut.get("feeds") or []) + list(cut.get("entities") or []):
        if not isinstance(row, dict):
            continue
        action.extend(_collect_seconds(row.get("atSec", row.get("at"))))
    for beat in cut.get("beats") or []:
        if not isinstance(beat, dict):
            continue
        kind = str(beat.get("kind") or "")
        secs = _collect_seconds(beat.get("atSec", beat.get("at")))
        if kind in ("stamp", "resolve"):
            resolve.extend(secs)
        else:
            action.extend(secs)
    cues = cut.get("cues") or {}
    if isinstance(cues, dict):
        for key, val in cues.items():
            secs = _collect_seconds(val)
            if key in _RESOLVE_CUE_KEYS:
                resolve.extend(secs)
            elif key in _ACTION_CUE_KEYS:
                action.extend(secs)
    return action, resolve


def tighten_cutaway_motion(cut: dict[str, Any]) -> dict[str, Any]:
    """Trim picture takeover to last motion; pull a parked end-stamp forward.

    cover.start/end (or timeline fromSec/durationSec) is the *allowed* window.
    After the last feed/lock/reject, do not hold a still graphic until VO ends.
    """
    duration = float(cut.get("durationSec") or 0.0)
    if duration <= 0 and "start" in cut and "end" in cut:
        duration = float(cut["end"]) - float(cut["start"])
    action, resolve = cutaway_action_times(cut)
    last_action = max(action) if action else 0.0
    last_resolve = max(resolve) if resolve else None
    used_resolve = last_resolve
    if last_resolve is not None and last_resolve - last_action > CUTAWAY_MAX_IDLE_TO_RESOLVE_SEC:
        used_resolve = round(last_action + CUTAWAY_RESOLVE_AFTER_ACTION_SEC, 3)
        cues = dict(cut.get("cues") or {})
        for key in ("stampSec", "resolveSec", "stamp", "resolve"):
            if key in cues and not isinstance(cues.get(key), list):
                cues[key] = used_resolve
        cut["cues"] = cues
    last_motion = last_action
    if used_resolve is not None:
        last_motion = max(last_motion, used_resolve)
    play = max(
        last_motion
        + CUTAWAY_MOTION_SETTLE_SEC
        + CUTAWAY_HOLD_AFTER_LAST_SEC
        + CUTAWAY_FADE_SEC,
        CUTAWAY_MIN_PLAY_SEC,
    )
    if duration > 0:
        play = min(duration, play)
        cut["durationSec"] = round(play, 3)
        if "start" in cut and "end" in cut:
            cut["end"] = round(float(cut["start"]) + play, 3)
    return cut


def apply_cutaway_defaults(entry: dict[str, Any]) -> dict[str, Any]:
    """Fill production defaults: press ink + live cam blur through the field."""
    if not str(entry.get("style") or "").strip() and not str(
        entry.get("look") or ""
    ).strip():
        entry["style"] = DEFAULT_CUTAWAY_STYLE
    bd = entry.get("backdrop")
    if not isinstance(bd, dict) or not bd.get("kind"):
        entry["backdrop"] = dict(DEFAULT_CUTAWAY_BACKDROP)
        return entry
    patched = dict(bd)
    if patched.get("kind") == "cam_blur" and patched.get("blurPx") is None:
        patched["blurPx"] = DEFAULT_CUTAWAY_BACKDROP["blurPx"]
    if patched.get("dim") is None:
        patched["dim"] = DEFAULT_CUTAWAY_BACKDROP["dim"]
    entry["backdrop"] = patched
    return entry


def resolve_family(item: dict[str, Any]) -> str | None:
    """Return canonical family id from family or legacy scene field."""
    fam = str(item.get("family") or "").lower().strip()
    if fam in CUTAWAY_FAMILIES:
        return fam
    scene = str(item.get("scene") or "").lower().strip()
    return SCENE_TO_FAMILY.get(scene)


def family_capabilities(family: str) -> dict[str, Any]:
    return dict(FAMILY_CAPABILITIES.get(family) or FAMILY_CAPABILITIES["minimal"])


def validate_brief_against_family(
    family: str,
    *,
    entity_count: int = 0,
    has_values: bool = False,
    has_proof: bool = False,
    copy_chars: int = 0,
    duration_sec: float = 0.0,
    intent: str | None = None,
) -> list[str]:
    """Return soft/hard issues; empty means the brief fits the family."""
    caps = family_capabilities(family)
    issues: list[str] = []
    max_ent = int(caps.get("maxEntities") or 99)
    if entity_count > max_ent:
        issues.append(f"{family} maxEntities={max_ent}, got {entity_count}")
    if has_values and not caps.get("supportsValues"):
        issues.append(f"{family} does not supportValues")
    if has_proof and not caps.get("supportsProof"):
        issues.append(f"{family} does not supportProof")
    max_copy = int(caps.get("maxCopyChars") or 999)
    if copy_chars > max_copy:
        issues.append(f"{family} maxCopyChars={max_copy}, got {copy_chars}")
    min_dur = float(caps.get("minDurationSec") or 0)
    if duration_sec and duration_sec < min_dur:
        issues.append(f"{family} minDurationSec={min_dur}, got {duration_sec:.1f}")
    preferred = caps.get("preferredIntents") or []
    if intent and preferred and intent not in preferred and family != "minimal":
        issues.append(f"{family} prefers {preferred}, got intent={intent}")
    return issues
