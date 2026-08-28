from __future__ import annotations

import json
from pathlib import Path

import yaml

from agentic_editor.editor.storyboard import (
    _thumbnail_path,
    cover_badges_for_range,
    cover_mg_items_for_range,
    format_clock,
    generate_storyboard,
    render_cut_gap_html,
    render_mg_stack_html,
    render_range_card_html,
    speech_for_range,
)


def test_format_clock_uses_edit_timeline_units() -> None:
    assert format_clock(0) == "0:00"
    assert format_clock(65) == "1:05"
    assert format_clock(3661) == "1:01:01"


def test_thumbnail_cache_key_tracks_source_and_selected_range(tmp_path: Path) -> None:
    dashboard = tmp_path / "dashboard"
    source = tmp_path / "clip.mov"
    source.write_bytes(b"first version")

    original = _thumbnail_path(dashboard, source, start=10, end=20)
    assert original == _thumbnail_path(dashboard, source, start=10, end=20)
    assert original != _thumbnail_path(dashboard, source, start=11, end=20)

    source.write_bytes(b"changed source content")
    changed = _thumbnail_path(dashboard, source, start=10, end=20)
    assert changed != original


def test_speech_for_range_collects_overlapping_words() -> None:
    words = [
        {"text": "hello", "start": 0.0, "end": 0.5},
        {"text": "world", "start": 0.5, "end": 1.0},
        {"text": "later", "start": 5.0, "end": 5.5},
    ]
    assert speech_for_range(words, 0.2, 0.8) == "hello world"
    assert speech_for_range(words, 4.0, 6.0) == "later"


def test_render_range_card_html_includes_clocks_and_speech() -> None:
    html = render_range_card_html(
        index=1,
        source_name="cam",
        timeline_start=0.0,
        timeline_end=12.5,
        duration=12.5,
        source_start=10.0,
        source_end=22.5,
        note="hook",
        speech="intro line",
        thumb_relative="assets/thumb_abc.jpg",
        badges=[{"kind": "overlay", "label": "chapter", "detail": "Opening"}],
    )
    assert "Edit 0:00" in html
    assert "Source 10.00s" in html
    assert "intro line" in html
    assert "chapter" in html
    assert 'src="assets/thumb_abc.jpg"' in html


def test_render_cut_gap_html_shows_removed_span() -> None:
    html = render_cut_gap_html(gap_start=18.1, gap_end=24.6, duration=6.5)
    assert "Cut" in html
    assert "18.1s → 24.6s" in html
    assert "6.5s removed" in html


def test_cover_badges_for_range_filters_by_overlap() -> None:
    cover = {
        "events": [
            {"type": "screen_with_cam", "start": 5.0, "end": 12.0, "note": "demo"},
            {"type": "punch_in", "start": 6.0, "end": 7.0, "note": "hook"},
        ],
        "overlays": [
            {"kind": "chapter", "start": 0.0, "end": 4.0, "title": "Intro"},
        ],
        "sfx": [
            {"kind": "click", "start": 8.0, "note": "UI tap"},
        ],
    }
    badges = cover_badges_for_range(cover, 6.0, 14.0)
    labels = {b["label"] for b in badges}
    assert "screen_with_cam" not in labels
    assert "punch_in" in labels
    assert "click" in labels
    assert "chapter" not in labels


def test_cover_mg_items_for_range_includes_overlays_and_evidence() -> None:
    cover = {
        "overlays": [
            {"kind": "stat", "start": 10.0, "end": 14.0, "value": "92%"},
        ],
        "events": [
            {
                "type": "evidence_with_cam",
                "start": 11.0,
                "end": 15.0,
                "src": "microsoft-wti-92.png",
            },
        ],
    }
    items = cover_mg_items_for_range(cover, 10.5, 13.0)
    kinds = {
        (it["category"], it.get("kind") or it.get("type"))
        for it in items
    }
    assert ("overlay", "stat") in kinds
    assert ("evidence", "evidence_with_cam") in kinds


def test_render_mg_stack_html_shows_overlay_content() -> None:
    html_out = render_mg_stack_html(
        [
            {
                "category": "overlay",
                "kind": "callout",
                "start": 36.0,
                "end": 42.0,
                "value": "92% pakai GenAI",
                "sourceLabel": "Microsoft WTI 2024",
            }
        ]
    )
    assert "MG plan (text preview)" in html_out
    assert "92% pakai GenAI" in html_out
    assert "Microsoft WTI 2024" in html_out
    assert "mg-callout" in html_out


def test_render_range_card_html_includes_mg_stack() -> None:
    html_out = render_range_card_html(
        index=1,
        source_name="cam",
        timeline_start=0.0,
        timeline_end=12.5,
        duration=12.5,
        source_start=10.0,
        source_end=22.5,
        note="hook",
        speech="intro line",
        thumb_relative="assets/thumb_abc.jpg",
        badges=[{"kind": "event", "label": "punch_in", "detail": "92%"}],
        mg_stack_html='<div class="mg-stack">MG preview</div>',
    )
    assert "MG preview" in html_out
    assert "punch_in" in html_out


def _write_min_episode(tmp_path: Path) -> Path:
    (tmp_path / "raw").mkdir()
    (tmp_path / "edit" / "transcripts").mkdir(parents=True)
    (tmp_path / "raw" / "cam.mp4").write_bytes(b"fake video")
    (tmp_path / "project.yaml").write_text(
        yaml.safe_dump({"id": "test-ep", "sources": {"cam": "raw/cam.mp4"}}),
        encoding="utf-8",
    )
    (tmp_path / "edit" / "edl.suggest.json").write_text(
        json.dumps(
            {
                "sources": {"cam": "raw/cam.mp4"},
                "ranges": [
                    {"source": "cam", "start": 0.0, "end": 3.0, "note": "first"},
                    {"source": "cam", "start": 8.0, "end": 11.0, "note": "second"},
                ],
                "_meta": {
                    "keep_sec": 6.0,
                    "gap_classes": {"breath": 2, "think": 1, "ai_wait": 0, "retake": 0},
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "edit" / "transcripts" / "cam.json").write_text(
        json.dumps(
            {
                "words": [
                    {"text": "alpha", "start": 0.1, "end": 0.4},
                    {"text": "beta", "start": 8.2, "end": 8.6},
                ],
                "segments": [],
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_generate_storyboard_writes_html_with_cut_gap(tmp_path: Path, monkeypatch) -> None:
    episode = _write_min_episode(tmp_path)
    (episode / "edit" / "cover.json").write_text(
        json.dumps(
            {
                "overlays": [
                    {
                        "kind": "tag",
                        "start": 0.0,
                        "end": 2.5,
                        "text": "REAL DATA",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("agentic_editor.editor.storyboard.extract_frame", lambda *a, **k: None)
    monkeypatch.setattr("agentic_editor.editor.storyboard._probe_duration", lambda *a, **k: 20.0)

    out = generate_storyboard(episode, open_browser=False)
    assert out == episode / "edit" / "storyboard" / "index.html"
    page = out.read_text(encoding="utf-8")
    assert "test-ep" in page
    assert "6.0s output" in page
    assert "Cut" in page
    assert "3.0s → 8.0s" in page
    assert "alpha" in page
    assert "beta" in page
    assert "breath=2" in page
    assert "REAL DATA" in page
    assert "MG feedback" in page or "MG plan" in page
