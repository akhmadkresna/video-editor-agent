"""Drawn-screen (style: mockup) pipeline: remap, PIP, tokens, validation."""

from __future__ import annotations

import json

from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.mockup import (
    DEFAULT_MOCK,
    build_timeline_mockups,
    load_mockup,
    resolve_skill,
    suggest_mockups,
    validate_mockup,
)


def _edl():
    return {
        "sources": {"cam": "../raw/cam.mp4"},
        "ranges": [
            {"source": "cam", "start": 0.0, "end": 30.0},
            {"source": "cam", "start": 50.0, "end": 120.0},
        ],
    }


def test_load_mockup_shape_matches_ts_default():
    mk = load_mockup("mockup")
    for key in DEFAULT_MOCK:
        assert key in mk
    assert mk["cam"]["easeMs"] == 420
    assert set(mk["cam"]["scales"]) == {"establish", "read", "focus"}
    # accent stays slate, not the old violet
    assert mk["badgeInk"] == "#496573"


def test_remap_scene_and_inner_atsec_to_scene_local():
    cover = {
        "mockups": [
            {
                "id": "s1",
                "fromSec": 10.0,
                "toSec": 28.0,
                "camera": [
                    {"atSec": 10.0, "state": "establish"},
                    {"atSec": 13.0, "state": "focus", "focus": "chat.input", "track": "caret"},
                ],
                "layers": [
                    {
                        "component": "ClaudeChat",
                        "data": {"turns": [{"role": "user", "text": "hi", "atSec": 12.0}]},
                    }
                ],
            }
        ]
    }
    scenes, pips = build_timeline_mockups(_edl(), cover)
    assert len(scenes) == 1
    sc = scenes[0]
    assert sc["fromSec"] == 10.0 and sc["durationSec"] == 18.0
    assert sc["camera"][1]["atSec"] == 3.0  # 13 - 10
    assert sc["layers"][0]["data"]["turns"][0]["atSec"] == 2.0  # 12 - 10
    # one pip_corner cam clip covering the scene, with the real source range
    assert len(pips) == 1
    assert pips[0]["layout"] == "pip_corner"
    assert pips[0]["source"] == "cam"
    assert pips[0]["sourceIn"] == 10.0 and pips[0]["sourceOut"] == 28.0
    # Muted: the underlying main a_roll "full" clip covers this same window
    # with the same cam audio (the voiceover) — leaving the pip bubble
    # unmuted too doubles/phases it audibly. Pip is visual-only.
    assert pips[0]["muted"] is True


def test_scene_spanning_a_cut_clamps_to_longest_slice():
    # window 20..70 straddles the 30..50 cut; kept slices are 20..30 and 50..70
    cover = {"mockups": [{"id": "s", "fromSec": 20.0, "toSec": 70.0,
                          "layers": [{"component": "AppWindow", "data": {"app": "pptx"}}]}]}
    scenes, pips = build_timeline_mockups(_edl(), cover)
    assert len(scenes) == 1
    # longest kept slice is 50..70 (20s) -> output starts after the first 30s keep
    assert scenes[0]["durationSec"] == 20.0
    assert scenes[0]["fromSec"] == 30.0
    assert pips[0]["sourceIn"] == 50.0


def test_timeline_carries_mockups_pip_and_presentation():
    cover = {"mockups": [{"id": "s", "fromSec": 5.0, "toSec": 20.0,
                          "layers": [{"component": "DiffPanel",
                                      "data": {"before": "a", "after": "b"}}]}]}
    tl = build_timeline_from_edl_and_cover(_edl(), cover, fps=30)
    assert len(tl["mockups"]) == 1
    assert any(c["layout"] == "pip_corner" for c in tl["clips"])
    assert tl["presentation"]["mockup"]["badgeInk"] == "#496573"


def test_validate_catches_missing_pieces():
    bad = {"scenes": [{"id": "x", "fromSec": 1, "toSec": 2,
                       "layers": [{"component": "ClaudeChat", "data": {"turns": []}}]}]}
    errs = validate_mockup(bad)
    assert any("turns" in e for e in errs)

    no_surface = {"scenes": [{"id": "y", "fromSec": 1, "toSec": 2,
                              "layers": [{"component": "Cursor", "data": {"path": [{"atSec": 0}]}}]}]}
    assert any("surface" in e for e in validate_mockup(no_surface))

    ok = {"scenes": [{"id": "z", "fromSec": 1, "toSec": 2,
                      "camera": [{"atSec": 0, "state": "focus"}],
                      "layers": [{"component": "AppWindow", "data": {"app": "pptx"}}]}]}
    assert validate_mockup(ok) == []

    # RepoView needs markdown + repoUrl
    bad_repo = {"scenes": [{"id": "r", "fromSec": 1, "toSec": 2,
                            "layers": [{"component": "RepoView", "data": {"repoUrl": "x", "markdown": ""}}]}]}
    assert any("markdown" in e for e in validate_mockup(bad_repo))


def test_resolve_skill_urls():
    r = resolve_skill("avoid-ai-writing")
    assert r["repo"] == "conorbronsdon/avoid-ai-writing"
    assert r["source"] == "community"
    assert r["raw_url"].endswith("/main/SKILL.md")
    a = resolve_skill("pptx")
    assert a["web_url"] == "https://github.com/anthropics/skills/tree/main/skills/pptx"
    # unknown slug → anthropics/skills fallback
    u = resolve_skill("totally-made-up")
    assert u["repo"] == "anthropics/skills" and "skills/totally-made-up" in u["raw_url"]


def test_cue_mode_only_cued_beats_become_scenes(tmp_path):
    (tmp_path / "edit").mkdir()
    (tmp_path / "edit" / "script.md").write_text(
        "# Hook\n\nSkill `avoid-ai-writing`. Ngomongin pptx dan excel tapi cuma teaser.\n\n"
        "## Demo\n\n> \"benerin ini\"\n\n"
        "[MOCKUP: ClaudeChat — user + reply]\n"
        "[MOCKUP: DiffPanel — before/after]\n\n"
        "## Verdict\n\nWorth it. Minggu depan pptx.\n",
        encoding="utf-8",
    )
    out = suggest_mockups(tmp_path)
    assert out["_meta"]["mode"] == "cues"
    comps = [[l["component"] for l in s["layers"]] for s in out["scenes"]]
    # Hook + Verdict have no cue -> no scene. Demo's 2 cues -> 2 scenes.
    assert len(out["scenes"]) == 2
    assert ["ClaudeChat", "Cursor"] in comps
    assert ["DiffPanel"] in comps


def test_suggest_emits_repoview_on_source_beat(tmp_path):
    (tmp_path / "edit").mkdir()
    (tmp_path / "edit" / "script.md").write_text(
        "# Hook\n\nSkill `avoid-ai-writing`.\n\n"
        "## Dari mana\n\nIni bikinan komunitas. Buka SKILL.md-nya, sebelum saya percaya.\n",
        encoding="utf-8",
    )
    out = suggest_mockups(tmp_path)
    repo_layers = [
        l for s in out["scenes"] for l in s["layers"] if l["component"] == "RepoView"
    ]
    assert repo_layers, "expected a RepoView layer for the 'dari mana' beat"
    d = repo_layers[0]["data"]
    assert d["repoUrl"].startswith("https://github.com/")
    assert isinstance(d["markdown"], str) and d["markdown"]


def test_suggest_reads_script_and_finds_skill(tmp_path):
    ep = tmp_path
    (ep / "edit").mkdir()
    (ep / "edit" / "script.md").write_text(
        "# Skill Lab #01 — avoid-ai-writing\n\n"
        "Style pack: `mockup`.\n\n"
        "## [0:00–0:30] Hook\n\n"
        "Skill minggu ini `avoid-ai-writing`.\n\n"
        "## [1:30–5:00] Demo\n\n"
        "> \"Perbaiki paragraf ini biar nggak bau AI\"\n\n"
        "## [5:00–6:30] Buka hasilnya\n\n"
        "Deck-nya kebuka di PowerPoint.\n",
        encoding="utf-8",
    )
    out = suggest_mockups(ep)
    assert out["_meta"]["skill"] == "avoid-ai-writing"
    assert out["_meta"]["beats"] >= 3
    comps = [l["component"] for s in out["scenes"] for l in s["layers"]]
    assert "ClaudeChat" in comps and "AppWindow" in comps
    # no transcript -> windows are null, apply must refuse
    assert any(s["fromSec"] is None for s in out["scenes"])
    assert validate_mockup(out)  # has errors (null spans)
