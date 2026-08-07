"""Tests for modern-tech SFX suggest + remap (no whoosh)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_editor.cover.remap import build_timeline_sfx
from agentic_editor.cover.sfx_suggest import (
    FORBIDDEN,
    merge_sfx_into_cover,
    resolve_sfx_file,
    suggest_sfx,
)


def _write_episode(tmp: Path) -> Path:
    ep = tmp / "ep"
    (ep / "edit" / "transcripts").mkdir(parents=True)
    (ep / "raw").mkdir(parents=True)
    (ep / "project.yaml").write_text(
        "id: sfx-test\nsources:\n  cam: raw/cam.mp4\n  screen: raw/screen.mp4\nstyle: tutorial\n",
        encoding="utf-8",
    )
    edl = {
        "sources": {"cam": "../raw/cam.mp4", "screen": "../raw/screen.mp4"},
        "ranges": [
            {"source": "cam", "start": 0.0, "end": 20.0, "note": "a"},
            {"source": "cam", "start": 40.0, "end": 80.0, "note": "b"},
        ],
    }
    (ep / "edit" / "edl.json").write_text(json.dumps(edl), encoding="utf-8")
    cover = {
        "camera_play": {"snap_on_cuts": True, "home": "medium", "alt": "close"},
        "events": [
            {"type": "punch_in", "start": 5.0, "end": 6.2, "scale": 1.2},
            {
                "type": "screen_with_cam",
                "start": 42.0,
                "end": 70.0,
                "note": "demo",
            },
            {
                "type": "framing",
                "start": 10.0,
                "end": 14.0,
                "framing": "close",
                "motion": "snap",
            },
        ],
        "overlays": [
            {
                "kind": "diagram",
                "start": 45.0,
                "end": 55.0,
                "title": "Flow",
                "steps": ["a", "b"],
            }
        ],
        "sfx": [],
    }
    (ep / "edit" / "cover.json").write_text(json.dumps(cover), encoding="utf-8")
    words = {
        "language": "id",
        "backend": "test",
        "model": "tiny",
        "words": [
            {"text": "klik", "start": 43.0, "end": 43.3},
            {"text": "code", "start": 50.0, "end": 50.4},
            {"text": "seed", "start": 51.0, "end": 51.3},
        ],
    }
    (ep / "edit" / "transcripts" / "cam.json").write_text(
        json.dumps(words), encoding="utf-8"
    )
    return ep


def test_resolve_forbids_whoosh():
    with pytest.raises(ValueError):
        resolve_sfx_file("click", explicit="whoosh_big.mp3")


def test_forbidden_set_has_whoosh():
    assert "whoosh" in FORBIDDEN


def test_suggest_couples_punch_screen_typing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ep = _write_episode(tmp_path)
    monkeypatch.setenv("AGENTIC_EDITOR_HOME", str(Path(__file__).resolve().parents[1]))
    from agentic_editor import paths

    monkeypatch.setattr(paths, "framework_home", lambda: Path(__file__).resolve().parents[1])

    suggestion = suggest_sfx(ep)
    kinds = {s["kind"] for s in suggestion["sfx"]}
    assert "shutter" in kinds
    assert "click" in kinds
    assert "typing" in kinds
    assert suggestion["_meta"]["no_whoosh"] is True
    notes = " ".join(str(s.get("note")) for s in suggestion["sfx"])
    assert "punch" in notes or "cut_snap" in notes or "framing_snap" in notes
    assert "screen_enter" in notes or "deixis" in notes


def test_remap_sfx_through_edl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ep = _write_episode(tmp_path)
    monkeypatch.setattr(
        "agentic_editor.cover.style_load.framework_home",
        lambda: Path(__file__).resolve().parents[1],
    )
    cover = json.loads((ep / "edit" / "cover.json").read_text(encoding="utf-8"))
    cover["sfx"] = [
        {
            "id": "sfx-shutter-0",
            "kind": "shutter",
            "start": 5.0,
            "end": 5.2,
            "src": "shutter.mp3",
            "volume": 0.4,
            "note": "suggest:punch",
        },
        {
            "id": "sfx-typing-0",
            "kind": "typing",
            "start": 42.0,
            "end": 70.0,
            "src": "typing-thock.mp3",
            "volume": 0.38,
            "note": "suggest:screen_demo",
        },
    ]
    edl = json.loads((ep / "edit" / "edl.json").read_text(encoding="utf-8"))
    tl = build_timeline_sfx(edl, cover, style_name="tutorial")
    assert tl
    assert all(s["src"].startswith("ae-media/sfx/") for s in tl)
    shutter = next(s for s in tl if s["kind"] == "shutter")
    assert abs(shutter["fromSec"] - 5.0) < 0.05
    typing = next(s for s in tl if s["kind"] == "typing")
    # keep [40,80) starts at output 20s; typing starts at source 42 → fromSec 22
    assert abs(typing["fromSec"] - 22.0) < 0.05
    assert typing.get("tile") is True


def test_merge_keeps_hand_authored():
    cover = {
        "sfx": [
            {"kind": "click", "start": 1.0, "end": 1.2, "note": "hand"},
            {"kind": "shutter", "start": 2.0, "end": 2.2, "note": "suggest:old"},
        ]
    }
    merged = merge_sfx_into_cover(
        cover,
        [{"kind": "click", "start": 9.0, "end": 9.2, "note": "suggest:new"}],
    )
    notes = [str(s.get("note")) for s in merged]
    assert "hand" in notes
    assert "suggest:old" not in notes
    assert "suggest:new" in notes
