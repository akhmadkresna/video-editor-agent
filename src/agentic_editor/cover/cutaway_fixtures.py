"""Canonical cutaway VisualBrief fixtures (episode-agnostic).

New VO → new brief data. New family only when a new motion language is needed.
"""

from __future__ import annotations

FIXTURES: dict[str, dict] = {
    "proof_ledger": {
        "family": "document",
        "intent": "prove",
        "tone": "tactile",
        "start": 0.0,
        "end": 18.0,
        "copy": {
            "kicker": "Record",
            "title": "Locked automatically",
            "totalLabel": "Running total",
            "lockLabel": "Read only",
            "stampLabel": "VALIDATED",
        },
        "openingBalance": 1000,
        "entities": [
            {"label": "In", "value": 5000, "at": 4.0, "icon": "cart"},
            {"label": "Out", "value": -2000, "at": 6.0, "icon": "bag"},
        ],
        "cues": {"open": 0.2, "total": 9.0, "lock": 12.0, "stamp": 15.0},
    },
    "process_flow": {
        "family": "flow",
        "intent": "transform",
        "tone": "technical",
        "start": 0.0,
        "end": 14.0,
        "copy": {"kicker": "Flow", "title": "Source to ledger"},
        "entities": [
            {"label": "Event A", "value": 1, "at": 3.0},
            {"label": "Event B", "value": 1, "at": 5.0},
            {"label": "Event C", "value": 1, "at": 7.0},
        ],
        "cues": {"open": 0.2, "total": 10.0},
    },
    "compare_kinetic": {
        "family": "kinetic_type",
        "intent": "compare",
        "tone": "editorial",
        "start": 0.0,
        "end": 10.0,
        "copy": {"kicker": "Compare", "title": "Before vs after"},
        "entities": [
            {"label": "Before", "value": -100, "at": 2.0},
            {"label": "After", "value": 400, "at": 4.5},
        ],
        "cues": {"open": 0.15, "total": 7.0},
    },
    "sequence_steps": {
        "family": "sequence",
        "intent": "sequence",
        "tone": "technical",
        "start": 0.0,
        "end": 12.0,
        "copy": {"kicker": "Steps", "title": "Three moves"},
        "entities": [
            {"label": "One", "at": 2.0},
            {"label": "Two", "at": 4.0},
            {"label": "Three", "at": 6.0},
        ],
        "cues": {"open": 0.2},
    },
    "system_map": {
        "family": "system_map",
        "intent": "explain",
        "tone": "technical",
        "start": 0.0,
        "end": 14.0,
        "copy": {"kicker": "Architecture", "title": "How it connects"},
        "entities": [
            {"label": "Node A", "value": 10, "at": 3.0},
            {"label": "Node B", "value": -4, "at": 5.0},
        ],
        "cues": {"open": 0.2, "lock": 10.0},
    },
    "evidence_hero": {
        "family": "evidence",
        "intent": "prove",
        "tone": "serious",
        "start": 0.0,
        "end": 8.0,
        "copy": {"kicker": "Evidence", "title": "From the form", "stampLabel": "CHECKED"},
        "cues": {"open": 0.2, "stamp": 5.5},
    },
    "warn_minimal": {
        "family": "minimal",
        "intent": "warn",
        "tone": "serious",
        "start": 0.0,
        "end": 5.0,
        "copy": {"kicker": "Warning", "title": "Do not edit the ledger"},
        "cues": {"open": 0.15},
    },
}
