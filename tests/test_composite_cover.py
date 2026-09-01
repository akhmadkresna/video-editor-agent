"""Composite single-file cam+screen (OBS baked PIP) cover tests."""

from __future__ import annotations

from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.composite import (
    effective_camera_play,
    has_screen_cover,
    load_composite,
)


def _edl(ranges: list[dict], sources: dict | None = None) -> dict:
    return {
        "sources": sources or {"cam": "/tmp/cam.mkv"},
        "ranges": ranges,
    }


def test_has_screen_cover_when_composite_enabled():
    project = {"sources": {"cam": "raw/cam.mkv"}, "composite": {"enabled": True}}
    assert has_screen_cover(project) is True
    assert load_composite(project)["baked_pip"] is True


def test_composite_baked_pip_with_episode(tmp_path, monkeypatch):
    ep = tmp_path / "ep"
    (ep / "edit").mkdir(parents=True)
    (ep / "raw").mkdir()
    (ep / "project.yaml").write_text(
        "id: comp-test\nsources:\n  cam: raw/cam.mkv\nstyle: tutorial\n"
        "composite:\n  enabled: true\n  baked_pip: true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENTIC_EDITOR_HOME", str(tmp_path.parent))
    from agentic_editor import paths

    monkeypatch.setattr(paths, "framework_home", lambda: tmp_path.parent)

    edl = _edl([{"source": "cam", "start": 0.0, "end": 30.0}])
    cover = {
        "events": [{"type": "screen_with_cam", "start": 5.0, "end": 20.0}],
    }
    tl = build_timeline_from_edl_and_cover(edl, cover, episode=ep)
    full = [c for c in tl["clips"] if c["layout"] == "full"]
    pip = [c for c in tl["clips"] if c["layout"] == "pip_corner"]
    assert tl.get("composite", {}).get("baked_pip") is True
    # Screen beat: one full cam clip, no Remotion PIP overlay
    screen_clips = [c for c in full if c["sourceIn"] >= 5.0 and c["sourceOut"] <= 20.0]
    assert len(screen_clips) == 1
    assert screen_clips[0]["source"] == "cam"
    assert screen_clips[0]["scale"] == 1.0
    assert screen_clips[0]["motion"] == "hold"
    assert len(pip) == 0
    # Softer composite camera_play merged
    assert tl["camera_play"]["snap_on_cuts"] is False
    assert tl["camera_play"]["scales"]["close"] <= 1.2


def test_effective_camera_play_merges_composite_defaults():
    project = {"composite": {"enabled": True}}
    cp = effective_camera_play({"camera_play": {"home": "medium"}}, project)
    assert cp["home"] == "wide"
    assert cp["snap_on_cuts"] is False
