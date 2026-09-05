"""Drawn-screen (style: mockup) pipeline: remap, PIP, tokens, validation."""

from __future__ import annotations

import json

from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.mockup import (
    DEFAULT_MOCK,
    build_timeline_mockups,
    diff_marks,
    load_mockup,
    resolve_skill,
    suggest_mockups,
    validate_mockup,
)


def _write_transcript(episode, spoken: str, *, wps: float = 2.5, t0: float = 0.0):
    """Write edit/transcripts/cam.json from a plain string, one word per token."""
    (episode / "edit" / "transcripts").mkdir(parents=True, exist_ok=True)
    words = []
    t = t0
    for tok in spoken.split():
        words.append({"text": tok, "start": round(t, 2), "end": round(t + 1 / wps, 2), "score": 1.0})
        t += 1 / wps
    (episode / "edit" / "transcripts" / "cam.json").write_text(
        json.dumps({"words": words}), encoding="utf-8"
    )
    return words


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


def test_suggest_needs_a_transcript(tmp_path):
    (tmp_path / "edit").mkdir()
    out = suggest_mockups(tmp_path)
    assert out["scenes"] == []
    assert "cam.json" in out["_meta"]["error"]


def test_suggest_repoview_anchored_to_spoken_github(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agentic_editor.cover.mockup.fetch_skill_md", lambda *a, **k: "# SKILL\nbody"
    )
    # "repo" at token idx 7 (2.8s), "di github" phrase at idx 9 (3.6s)
    _write_transcript(
        tmp_path,
        "oke jadi minggu ini kita coba buka repo nya di github biar kelihatan "
        "isinya seperti apa dan siapa yang bikin",
    )
    out = suggest_mockups(tmp_path)
    repo = [s for s in out["scenes"] if s["layers"][0]["component"] == "RepoView"]
    assert repo, out["_meta"]
    # anchored on the spoken repo/github moment, not drifted elsewhere
    assert 2.5 <= repo[0]["fromSec"] <= 4.5
    assert repo[0]["layers"][0]["data"]["repoUrl"].startswith("https://github.com/")


def test_spoken_prompt_beats_repo_keyword_and_fills_user_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agentic_editor.cover.mockup.fetch_skill_md", lambda *a, **k: "# SKILL"
    )
    # A spoken prompt lead-in AND a "skill.md" mention in the same stretch.
    _write_transcript(
        tmp_path,
        "terus aku bilang perbaiki paragraf ini biar rapi. habis itu aku buka "
        "skill.md nya buat lihat isinya",
    )
    out = suggest_mockups(tmp_path)
    first = out["scenes"][0]
    assert first["layers"][0]["component"] == "ClaudeChat"
    user_turn = first["layers"][0]["data"]["turns"][0]
    assert user_turn["role"] == "user"
    assert "perbaiki paragraf ini" in user_turn["text"].lower()


def test_generic_single_word_trigger_is_flagged_low_confidence(tmp_path):
    _write_transcript(
        tmp_path,
        "sekarang kita masuk ke settings terus scroll sampai bawah pelan pelan",
    )
    out = suggest_mockups(tmp_path)
    assert any(s["layers"][0]["component"] == "SkillsPanel" for s in out["scenes"])
    low = out["_meta"]["low_confidence_scenes"]
    assert low and low[0]["component"] == "SkillsPanel"


def test_repeat_triggers_collapse_within_min_gap(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agentic_editor.cover.mockup.fetch_skill_md", lambda *a, **k: "# SKILL"
    )
    # two "github" mentions ~4s apart (< default 12s min gap) -> one scene
    _write_transcript(
        tmp_path,
        "buka github sekarang lihat filenya oke balik lagi ke github yang tadi ya",
    )
    out = suggest_mockups(tmp_path)
    repo = [s for s in out["scenes"] if s["layers"][0]["component"] == "RepoView"]
    assert len(repo) == 1


def test_two_distinct_spoken_prompts_stay_separate_scenes(tmp_path):
    # both prompts are close in this compressed transcript but different text
    _write_transcript(
        tmp_path,
        "aku bilang perbaiki paragraf ini. lalu aku ketik lets improve the "
        "avoid ai writing skill dong",
    )
    out = suggest_mockups(tmp_path)
    chats = [s for s in out["scenes"] if s["layers"][0]["component"] == "ClaudeChat"]
    assert len(chats) == 2
    texts = [c["layers"][0]["data"]["turns"][0]["text"].lower() for c in chats]
    assert "perbaiki paragraf ini" in texts[0]
    assert "avoid ai writing skill" in texts[1]


def test_diff_marks_word_level_spans():
    before = "the quick brown fox"
    after = "the slow brown fox"
    b, a = diff_marks(before, after)
    assert b == [{"type": "del", "span": [4, 9]}]  # "quick"
    assert a == [{"type": "add", "span": [4, 8]}]  # "slow"
    assert before[4:9] == "quick" and after[4:8] == "slow"


def test_diff_marks_insert_and_delete():
    b, a = diff_marks("keep this", "keep this extra")
    assert b == []
    assert a and a[0]["type"] == "add"
    b2, a2 = diff_marks("drop this word", "drop word")
    assert b2 and b2[0]["type"] == "del"
    assert a2 == []


def test_build_timeline_injects_diff_marks_and_respects_author_marks():
    cover = {
        "mockups": [
            {
                "id": "auto",
                "fromSec": 5.0,
                "toSec": 20.0,
                "layers": [
                    {
                        "component": "DiffPanel",
                        "data": {"before": "a red car", "after": "a blue car"},
                    }
                ],
            },
            {
                "id": "todo",
                "fromSec": 55.0,
                "toSec": 70.0,
                "layers": [
                    {
                        "component": "DiffPanel",
                        "data": {"before": "<TODO before>", "after": "<TODO after>"},
                    }
                ],
            },
        ]
    }
    scenes, _ = build_timeline_mockups(_edl(), cover)
    auto = next(s for s in scenes if s["id"] == "auto")["layers"][0]["data"]
    assert auto["beforeMarks"] == [{"type": "del", "span": [2, 5]}]
    assert auto["afterMarks"] == [{"type": "add", "span": [2, 6]}]
    todo = next(s for s in scenes if s["id"] == "todo")["layers"][0]["data"]
    assert "beforeMarks" not in todo and "afterMarks" not in todo
