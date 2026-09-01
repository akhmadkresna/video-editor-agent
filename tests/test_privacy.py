"""Tests for cover.privacy → timeline.privacy EDL remap."""

from __future__ import annotations

from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.remap import build_timeline_privacy


def test_build_timeline_privacy_basic_remap():
    edl = {
        "sources": {"cam": "../raw/cam.mkv"},
        "ranges": [
            {"source": "cam", "start": 10.0, "end": 20.0},
            {"source": "cam", "start": 30.0, "end": 40.0},
        ],
    }
    cover = {
        "privacy": [
            {
                "id": "secret-a",
                "start": 12.0,
                "end": 15.0,
                "rects": [{"x": 10, "y": 40, "w": 80, "h": 8}],
                "label": "CLIENT ID",
            },
            {
                # entirely in cut gap — dropped
                "id": "secret-gap",
                "start": 22.0,
                "end": 28.0,
                "rects": [{"x": 10, "y": 50, "w": 80, "h": 8}],
            },
            {
                # spans cut gap → two timeline entries (one per keep slice)
                "id": "secret-span",
                "start": 18.0,
                "end": 32.0,
                "rects": [
                    {"x": 10, "y": 40, "w": 80, "h": 6},
                    {"x": 10, "y": 50, "w": 80, "h": 6},
                ],
                "label": "SECRET",
            },
        ]
    }
    out = build_timeline_privacy(edl, cover)
    ids = [p["id"] for p in out]
    assert "secret-a" in ids
    assert "secret-gap" not in ids
    assert "secret-span-0" in ids
    assert "secret-span-1" in ids
    a = next(p for p in out if p["id"] == "secret-a")
    assert abs(a["fromSec"] - 2.0) < 1e-6
    assert abs(a["durationSec"] - 3.0) < 1e-6
    assert a["label"] == "CLIENT ID"
    assert a["mode"] == "bar"
    s0 = next(p for p in out if p["id"] == "secret-span-0")
    s1 = next(p for p in out if p["id"] == "secret-span-1")
    assert abs(s0["fromSec"] - 8.0) < 1e-6
    assert abs(s0["durationSec"] - 2.0) < 1e-6
    assert abs(s1["fromSec"] - 10.0) < 1e-6
    assert abs(s1["durationSec"] - 2.0) < 1e-6
    assert len(s1["rects"]) == 2


def test_timeline_includes_privacy():
    edl = {
        "sources": {"cam": "/tmp/cam.mp4"},
        "ranges": [{"source": "cam", "start": 0.0, "end": 20.0, "note": "hook"}],
    }
    cover = {
        "camera_play": {"snap_on_cuts": False, "home": "medium", "alt": "close"},
        "events": [],
        "privacy": [
            {
                "start": 5.0,
                "end": 9.0,
                "rects": [{"x": 5, "y": 35, "w": 90, "h": 12}],
                "label": "REDACTED",
            }
        ],
    }
    tl = build_timeline_from_edl_and_cover(edl, cover, fps=30, width=1920, height=1080)
    assert "privacy" in tl
    assert len(tl["privacy"]) == 1
    assert abs(tl["privacy"][0]["fromSec"] - 5.0) < 1e-6
    assert abs(tl["privacy"][0]["durationSec"] - 4.0) < 1e-6


def test_privacy_skips_empty_rects():
    edl = {"ranges": [{"source": "cam", "start": 0.0, "end": 10.0}]}
    cover = {
        "privacy": [
            {"start": 1.0, "end": 2.0, "rects": []},
            {"start": 3.0, "end": 4.0, "rects": [{"x": 0, "y": 0, "w": 0, "h": 10}]},
        ]
    }
    assert build_timeline_privacy(edl, cover) == []


def test_screen_blur_defaults_full_frame():
    edl = {
        "sources": {"cam": "../raw/cam.mkv"},
        "ranges": [{"source": "cam", "start": 0.0, "end": 120.0}],
    }
    cover = {
        "privacy": [
            {
                "id": "creds",
                "start": 10.0,
                "end": 20.0,
                "mode": "screen_blur",
                "label": "REDACTED",
            }
        ]
    }
    out = build_timeline_privacy(edl, cover)
    assert len(out) == 1
    assert out[0]["mode"] == "screen_blur"
    assert out[0]["rects"][0]["w"] == 100.0
