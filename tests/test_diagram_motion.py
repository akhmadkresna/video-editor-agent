"""Speech-synced diagram list step timing."""

from __future__ import annotations

from agentic_editor.cover.diagram_motion import (
    align_diagram_step_source_times,
    even_step_at_sec,
    step_keywords,
)
from agentic_editor.cover.remap import build_timeline_overlays


def test_step_keywords_filters_stopwords():
    kws = step_keywords("1 Master data produk & stock")
    assert "master" in kws
    assert "produk" in kws
    assert "stock" in kws or "data" in kws
    assert "dan" not in kws


def test_align_steps_to_spoken_phrases():
    # Simulated cam transcript mentioning checklist ideas in order.
    words = []
    script = [
        (10.0, "oke"),
        (10.3, "dari"),
        (10.6, "supplier"),
        (11.2, "kita"),
        (11.5, "beli"),
        (11.8, "masuk"),
        (12.1, "gudang"),
        (13.0, "harga"),
        (13.4, "grosir"),
        (14.2, "lalu"),
        (14.5, "penjualan"),
        (15.0, "di"),
        (15.2, "counter"),
        (16.0, "surat"),
        (16.3, "jalan"),
        (17.0, "dan"),
        (17.2, "piutang"),
    ]
    t = 10.0
    for start, text in script:
        words.append({"text": text, "start": start, "end": start + 0.25, "score": 1.0})
        t = start

    steps = ["Supplier", "Beli → Gudang", "Harga bertingkat", "Penjualan", "Surat jalan", "Piutang"]
    times = align_diagram_step_source_times(
        steps,
        words,
        overlay_start=10.0,
        overlay_end=18.0,
        lead_in_sec=0.4,
        min_gap_sec=0.4,
        min_score=0.2,
    )
    assert len(times) == len(steps)
    assert times == sorted(times)
    # Supplier should land near first mention (~10.6), not all at t0
    assert times[0] >= 10.3
    assert times[-1] > times[0] + 1.5


def test_even_fallback_monotonic():
    times = even_step_at_sec(4, 8.0)
    assert len(times) == 4
    assert times == sorted(times)
    assert times[0] >= 0.2
    assert times[-1] <= 8.0


def test_build_timeline_overlays_attaches_step_at_sec():
    edl = {
        "ranges": [{"source": "cam", "start": 0.0, "end": 30.0}],
    }
    cover = {
        "overlays": [
            {
                "id": "d1",
                "kind": "diagram",
                "start": 10.0,
                "end": 18.0,
                "kicker": "Checklist",
                "title": "Alur",
                "steps": ["Supplier", "Gudang", "Penjualan"],
            }
        ]
    }
    words = [
        {"text": "supplier", "start": 10.8, "end": 11.1, "score": 1.0},
        {"text": "masuk", "start": 12.0, "end": 12.2, "score": 1.0},
        {"text": "gudang", "start": 12.3, "end": 12.6, "score": 1.0},
        {"text": "untuk", "start": 14.0, "end": 14.2, "score": 1.0},
        {"text": "penjualan", "start": 14.5, "end": 14.9, "score": 1.0},
    ]
    ov = build_timeline_overlays(edl, cover, words=words)
    assert len(ov) == 1
    assert ov[0]["kind"] == "diagram"
    assert ov[0]["stepMotion"] == "speech"
    assert len(ov[0]["stepAtSec"]) == 3
    assert ov[0]["stepAtSec"] == sorted(ov[0]["stepAtSec"])
