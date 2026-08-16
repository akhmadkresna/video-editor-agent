"""cutaway-suggest + family remap + asset staging + quality gates."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_editor.compose.cutaway_qa import pick_cutaway_qa_frames
from agentic_editor.compose.quality import audit_timeline_quality
from agentic_editor.cover.cutaway_assets import (
    collect_cutaway_asset_refs,
    stage_cutaway_assets_for_remotion,
)
from agentic_editor.cover.cutaway_families import resolve_family, validate_brief_against_family
from agentic_editor.cover.cutaway_fixtures import FIXTURES
from agentic_editor.cover.cutaway_suggest import (
    merge_cutaways_into_cover,
    suggest_cutaways,
    write_cutaway_suggest,
)
from agentic_editor.cover.remap import build_timeline_cutaways, collect_cutaway_defs


def _edl():
    return {
        "sources": {"cam": "../raw/cam.mp4"},
        "ranges": [
            {"source": "cam", "start": 0.0, "end": 10.0},
            {"source": "cam", "start": 100.0, "end": 130.0},
        ],
    }


def test_family_alias_receipt_tape_maps_to_document():
    cover = {
        "cutaways": [
            {
                "scene": "receipt_tape",
                "start": 106.0,
                "end": 120.0,
                "title": "Tape",
            }
        ]
    }
    defs = collect_cutaway_defs(cover)
    assert defs[0]["family"] == "document"
    cuts = build_timeline_cutaways(_edl(), cover)
    assert cuts[0]["family"] == "document"
    assert cuts[0]["scene"] == "receipt_tape"


def test_family_field_without_scene():
    cover = {
        "cutaways": [
            {
                "family": "minimal",
                "start": 106.0,
                "end": 112.0,
                "copy": {"title": "Claim"},
                "cues": {"open": 106.2},
            }
        ]
    }
    cuts = build_timeline_cutaways(_edl(), cover)
    assert len(cuts) == 1
    assert cuts[0]["family"] == "minimal"
    assert cuts[0]["scene"] == "minimal"
    assert abs(cuts[0]["cues"]["openSec"] - 0.2) < 0.01
    assert abs(cuts[0]["cues"]["ledgerInSec"] - 0.2) < 0.01


def test_entities_become_feeds_and_local_beats():
    cover = {
        "cutaways": [
            {
                "family": "document",
                "start": 106.0,
                "end": 120.0,
                "entities": [
                    {"label": "In", "value": 100, "at": 110.0},
                    {"label": "Out", "value": -40, "at": 112.0},
                ],
                "beats": [
                    {"kind": "open", "at": 106.2},
                    {"kind": "total", "at": 116.0},
                ],
            }
        ]
    }
    cut = build_timeline_cutaways(_edl(), cover)[0]
    assert [e["label"] for e in cut["entities"]] == ["In", "Out"]
    assert [round(f["atSec"], 1) for f in cut["feeds"]] == [4.0, 6.0]
    assert abs(cut["cues"]["balanceSec"] - 10.0) < 0.01


def test_validate_brief_against_family():
    issues = validate_brief_against_family(
        "minimal",
        entity_count=5,
        has_values=True,
        has_proof=True,
    )
    assert any("maxEntities" in i for i in issues)
    assert any("supportValues" in i for i in issues)


def test_suggest_cutaways_on_temp_episode(tmp_path: Path):
    edit = tmp_path / "edit"
    edit.mkdir()
    (tmp_path / "project.yaml").write_text("style: tutorial\nfps: 30\n", encoding="utf-8")
    edl = {
        "sources": {"cam": "../raw/cam.mp4"},
        "ranges": [{"source": "cam", "start": 0.0, "end": 60.0}],
    }
    (edit / "edl.json").write_text(json.dumps(edl) + "\n", encoding="utf-8")
    words = []
    t = 0.0
    for w in (
        "buku",
        "kas",
        "tercatat",
        "otomatis",
        "saldo",
        "berjalan",
        "tidak",
        "bisa",
        "diedit",
        "tervalidasi",
    ):
        words.append({"word": w, "start": t, "end": t + 0.4})
        t += 0.5
    (edit / "transcripts").mkdir()
    (edit / "transcripts" / "cam.json").write_text(
        json.dumps({"words": words}) + "\n", encoding="utf-8"
    )
    suggestion = suggest_cutaways(tmp_path)
    assert "cutaways" in suggestion
    out = write_cutaway_suggest(tmp_path, suggestion)
    assert out.is_file()
    cover = merge_cutaways_into_cover({"cutaways": []}, suggestion["cutaways"])
    assert all(str(c.get("note") or "").startswith("suggest:") for c in cover["cutaways"])


def test_stage_cutaway_assets(tmp_path: Path):
    episode = tmp_path / "ep"
    edit = episode / "edit" / "cutaway_assets"
    edit.mkdir(parents=True)
    src = edit / "proof.png"
    # Minimal PNG header
    src.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
        b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    cover = {
        "cutaways": [
            {
                "family": "evidence",
                "start": 1.0,
                "end": 5.0,
                "proof": {"src": "edit/cutaway_assets/proof.png", "caption": "Form"},
            }
        ]
    }
    public = tmp_path / "public"
    updated = stage_cutaway_assets_for_remotion(
        episode, cover, remotion_public=public, verbose=False
    )
    assert updated is not None
    proof_src = updated["cutaways"][0]["proof"]["src"]
    assert proof_src.startswith("ae-media/cutaways/")
    assert (public / proof_src.replace("/", "\\") if False else public.joinpath(*proof_src.split("/"))).is_file()
    refs = collect_cutaway_asset_refs(updated)
    assert refs


def test_quality_flags_absolute_cutaway_asset():
    timeline = {
        "durationSec": 40,
        "clips": [],
        "effects": [],
        "overlays": [],
        "cutaways": [
            {
                "id": "c1",
                "family": "evidence",
                "scene": "evidence",
                "fromSec": 1.0,
                "durationSec": 5.0,
                "proof": {"src": "D:/secrets/proof.png"},
            }
        ],
        "camera_play": {"scales": {"close": 1.4, "medium": 1.2}},
    }
    cover = {"cutaways": [{"id": "c1", "family": "evidence", "start": 1, "end": 5}]}
    errors, _warnings = audit_timeline_quality(timeline, cover=cover)
    assert any("absolute disk path" in e for e in errors)


def test_contact_frames_and_fixtures():
    assert "proof_ledger" in FIXTURES
    assert resolve_family({"family": "document"}) == "document"
    frames = pick_cutaway_qa_frames(
        {
            "durationSec": 20,
            "cues": {"ledgerInSec": 0.2, "stampSec": 18},
            "feeds": [{"atSec": 6}, {"atSec": 8}, {"atSec": 10}],
        },
        fps=30,
    )
    assert frames["opening"] < frames["dense"] <= frames["payoff"]
