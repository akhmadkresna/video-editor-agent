"""Cutaway motion families — visual engines, not VO topics.

New VOs become data (VisualBrief). A new family is only justified when a
genuinely new motion language is needed.
"""

from __future__ import annotations

from typing import Any

# Canonical family ids (Remotion registry + suggest + quality gates).
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

FAMILY_CAPABILITIES: dict[str, dict[str, Any]] = {
    "document": {
        "supportsValues": True,
        "supportsProof": True,
        "maxEntities": 6,
        "preferredIntents": ["prove", "accumulate", "warn", "summarize"],
        "minDurationSec": 8.0,
        "maxCopyChars": 48,
    },
    "flow": {
        "supportsValues": True,
        "supportsProof": True,
        "maxEntities": 5,
        "preferredIntents": ["transform", "explain", "accumulate", "sequence"],
        "minDurationSec": 8.0,
        "maxCopyChars": 42,
    },
    "kinetic_type": {
        "supportsValues": True,
        "supportsProof": True,
        "maxEntities": 4,
        "preferredIntents": ["summarize", "compare", "explain", "warn"],
        "minDurationSec": 5.0,
        "maxCopyChars": 36,
    },
    "comparison": {
        "supportsValues": True,
        "supportsProof": False,
        "maxEntities": 4,
        "preferredIntents": ["compare"],
        "minDurationSec": 6.0,
        "maxCopyChars": 40,
    },
    "sequence": {
        "supportsValues": False,
        "supportsProof": False,
        "maxEntities": 6,
        "preferredIntents": ["sequence", "explain"],
        "minDurationSec": 7.0,
        "maxCopyChars": 40,
    },
    "system_map": {
        "supportsValues": True,
        "supportsProof": True,
        "maxEntities": 6,
        "preferredIntents": ["explain", "transform", "sequence"],
        "minDurationSec": 8.0,
        "maxCopyChars": 42,
    },
    "evidence": {
        "supportsValues": False,
        "supportsProof": True,
        "maxEntities": 3,
        "preferredIntents": ["prove", "explain"],
        "minDurationSec": 4.0,
        "maxCopyChars": 48,
    },
    "minimal": {
        "supportsValues": False,
        "supportsProof": False,
        "maxEntities": 2,
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
        "maxCopyChars": 56,
    },
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
