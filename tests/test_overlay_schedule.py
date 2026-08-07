"""Diagram hold-after + structure collision schedule."""

from __future__ import annotations

from agentic_editor.cover.overlay_schedule import (
    apply_diagram_hold,
    diagram_floor,
    finalize_overlays,
)
from agentic_editor.cover.remap import build_timeline_overlays


def test_diagram_floor_grows_with_steps():
    assert diagram_floor(1) >= 10.0
    assert diagram_floor(6) > diagram_floor(3)


def test_apply_diagram_hold_extends_duration():
    inst = {
        "kind": "diagram",
        "fromSec": 10.0,
        "durationSec": 7.5,
        "stepAtSec": [0.5, 2.0, 4.0, 7.0],
        "steps": ["a", "b", "c", "d"],
    }
    apply_diagram_hold(inst, timeline_dur=120.0)
    assert inst["durationSec"] >= 7.0 + 2.5  # last + hold
    last = inst["stepAtSec"][-1]
    assert inst["durationSec"] - last >= 2.4
    assert inst["exitStartSec"] > last


def test_finalize_trims_overlapping_structure():
    items = [
        {
            "id": "d1",
            "kind": "diagram",
            "fromSec": 0.0,
            "durationSec": 12.0,
            "stepAtSec": [1.0, 3.0, 5.0],
            "steps": ["a", "b", "c"],
            "title": "A",
        },
        {
            "id": "c1",
            "kind": "chapter",
            "fromSec": 8.0,
            "durationSec": 5.0,
            "text": "Next",
        },
    ]
    out = finalize_overlays(items, timeline_dur=60.0)
    by_id = {o["id"]: o for o in out}
    # Diagram must end before chapter entrance
    assert by_id["d1"]["fromSec"] + by_id["d1"]["durationSec"] <= 8.05


def test_build_timeline_diagram_has_readable_hold():
    edl = {"ranges": [{"source": "cam", "start": 0.0, "end": 60.0}]}
    cover = {
        "overlays": [
            {
                "id": "d1",
                "kind": "diagram",
                "start": 10.0,
                "end": 17.5,  # short cover window (old bug)
                "title": "Alur",
                "steps": ["Supplier", "Gudang", "Penjualan", "Piutang"],
            }
        ]
    }
    words = [
        {"text": "supplier", "start": 10.8, "end": 11.1, "score": 1.0},
        {"text": "gudang", "start": 13.0, "end": 13.3, "score": 1.0},
        {"text": "penjualan", "start": 15.0, "end": 15.4, "score": 1.0},
        {"text": "piutang", "start": 18.5, "end": 18.9, "score": 1.0},
    ]
    ov = build_timeline_overlays(edl, cover, words=words)
    assert len(ov) == 1
    d = ov[0]
    assert d["durationSec"] >= 10.0
    last = d["stepAtSec"][-1]
    assert d["durationSec"] - last >= 2.4
    assert d.get("exitStartSec", 0) > last
