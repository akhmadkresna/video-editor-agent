"""Tests for evidence stills production path (style: evidence)."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_editor.cover import build_timeline_from_edl_and_cover, partition_range_by_cover
from agentic_editor.cover.evidence import (
    collect_evidence_sources_from_cover,
    evidence_source_key,
)
from agentic_editor.cover.evidence_suggest import apply_evidence_events, suggest_evidence_events
from agentic_editor.cover.remap import collect_overlay_defs
from agentic_editor.cover.style_load import load_overlays


def test_evidence_source_key_stable():
    assert evidence_source_key("sc-socialcounts.png") == "evidence_sc_socialcounts"
    assert evidence_source_key("SocialCounts.png") == "evidence_socialcounts"


def test_partition_evidence_with_cam(tmp_path: Path):
    events = [
        {
            "type": "evidence_with_cam",
            "start": 10.0,
            "end": 16.0,
            "src": "vidiq.png",
            "layout": "float",
        }
    ]
    parts = partition_range_by_cover(0.0, 30.0, events)
    modes = [p["mode"] for p in parts]
    assert "full_cam" in modes
    assert "evidence_with_cam" in modes
    ev = next(p for p in parts if p["mode"] == "evidence_with_cam")
    assert ev["src_key"] == "evidence_vidiq"
    assert ev["layout"] == "float"


def test_build_timeline_evidence_clip_and_pip(tmp_path: Path):
    # Drop a tiny PNG so collect path works if needed later
    evid = tmp_path / "raw" / "evidence"
    evid.mkdir(parents=True)
    png = evid / "sc.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    edl = {
        "sources": {"cam": "cam.mp4"},
        "ranges": [{"source": "cam", "start": 0.0, "end": 20.0}],
    }
    cover = {
        "camera_play": {"snap_on_cuts": False, "max_hold_sec": 60},
        "events": [
            {
                "type": "evidence_with_cam",
                "start": 5.0,
                "end": 12.0,
                "src": "sc.png",
                "layout": "float",
            }
        ],
        "overlays": [
            {
                "kind": "callout",
                "start": 5.0,
                "end": 8.5,
                "value": "Rp24 jt",
                "sourceLabel": "SocialCounts",
            }
        ],
        "sfx": [],
        "captions": [],
    }
    # Stage fake cam source key in edl for muted check
    edl["sources"]["evidence_sc"] = str(png)
    tl = build_timeline_from_edl_and_cover(edl, cover, episode=tmp_path)
    sources_used = {c["source"] for c in tl["clips"]}
    assert "evidence_sc" in sources_used
    assert any(c["layout"] == "float_centered" for c in tl["clips"])
    assert any(c["layout"] == "pip_corner" and c["source"] == "cam" for c in tl["clips"])
    ovs = collect_overlay_defs(cover)
    assert ovs[0]["kind"] == "callout"
    assert ovs[0]["value"] == "Rp24 jt"


def test_collect_evidence_sources(tmp_path: Path):
    evid = tmp_path / "raw" / "evidence"
    evid.mkdir(parents=True)
    f = evid / "a.png"
    f.write_bytes(b"x")
    cover = {
        "events": [
            {"type": "evidence", "start": 1, "end": 3, "src": "a.png"},
        ]
    }
    got = collect_evidence_sources_from_cover(tmp_path, cover)
    assert "evidence_a" in got
    assert Path(got["evidence_a"]).name == "a.png"


def test_suggest_and_apply_evidence(tmp_path: Path):
    (tmp_path / "project.yaml").write_text(
        "id: t\nstyle: evidence\nsources:\n  cam: raw/cam.mp4\n",
        encoding="utf-8",
    )
    evid = tmp_path / "raw" / "evidence"
    evid.mkdir(parents=True)
    (evid / "x.png").write_bytes(b"x")
    edit = tmp_path / "edit"
    edit.mkdir()
    (edit / "transcripts").mkdir()
    (edit / "transcripts" / "cam.json").write_text(
        json.dumps(
            {
                "words": [
                    {"word": "estimasi", "start": 4.0, "end": 4.5},
                    {"word": "pendapatan", "start": 5.0, "end": 5.6},
                ]
            }
        ),
        encoding="utf-8",
    )
    suggestion = suggest_evidence_events(tmp_path)
    assert suggestion["events"]
    assert suggestion["events"][0]["src"] == "x.png"
    path = apply_evidence_events(tmp_path, suggestion)
    cover = json.loads(path.read_text(encoding="utf-8"))
    types = [e["type"] for e in cover["events"]]
    assert any(t.startswith("evidence") for t in types)


def test_evidence_style_loads_callout_dwell():
    ov = load_overlays("evidence")
    assert ov["dwell"]["callout_sec"] == 3.6
    assert "callout" in ov
