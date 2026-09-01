"""Composite single-file cam+screen (OBS baked PIP) cover tests."""

from __future__ import annotations

from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.composite import (
    effective_camera_play,
    has_screen_cover,
    is_camera_play_enabled,
    is_composite_episode,
    load_composite,
    overlay_explain_fill_enabled,
    overlay_stale_screen_fill_enabled,
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


def test_camera_play_disabled_flat_clips(tmp_path, monkeypatch):
    ep = tmp_path / "ep"
    (ep / "edit").mkdir(parents=True)
    (ep / "raw").mkdir()
    (ep / "project.yaml").write_text(
        "id: flat\nsources:\n  cam: raw/cam.mkv\nstyle: tutorial\n"
        "composite:\n  enabled: true\n  camera_play:\n    enabled: false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENTIC_EDITOR_HOME", str(tmp_path.parent))
    from agentic_editor import paths

    monkeypatch.setattr(paths, "framework_home", lambda: tmp_path.parent)

    edl = _edl([{"source": "cam", "start": 0.0, "end": 20.0}])
    cover = {
        "camera_play": {"snap_on_cuts": True, "scales": {"close": 1.42}},
        "events": [
            {"type": "framing", "start": 1.0, "end": 4.0, "framing": "close", "motion": "snap"},
        ],
    }
    tl = build_timeline_from_edl_and_cover(edl, cover, episode=ep)
    assert len(tl["clips"]) == 1
    c = tl["clips"][0]
    assert c["scale"] == 1.0
    assert c["framing"] == "wide"
    assert c["motion"] == "hold"
    assert tl["camera_play"]["enabled"] is False or tl["camera_play"]["scales"]["close"] == 1.0


def test_effective_camera_play_merges_composite_defaults():
    project = {"composite": {"enabled": True, "camera_play": {"enabled": False}}}
    cp = effective_camera_play({"camera_play": {"home": "medium"}}, project)
    assert cp["enabled"] is False
    assert cp["scales"]["close"] == 1.0
    assert cp["snap_on_cuts"] is False


def test_dual_source_without_composite_uses_screen_and_pip():
    """Normal cam+screen episodes must not inherit composite baked-PIP behavior."""
    edl = _edl(
        [{"source": "cam", "start": 0.0, "end": 30.0}],
        sources={"cam": "/tmp/cam.mp4", "screen": "/tmp/screen.mp4"},
    )
    cover = {
        "camera_play": {
            "snap_on_cuts": True,
            "scales": {"wide": 1.0, "medium": 1.22, "close": 1.42},
        },
        "events": [{"type": "screen_with_cam", "start": 5.0, "end": 20.0}],
    }
    project = {"sources": {"cam": "raw/cam.mp4", "screen": "raw/screen.mp4"}}
    assert is_composite_episode(project) is False
    assert overlay_explain_fill_enabled(project) is False
    assert overlay_stale_screen_fill_enabled(project) is False

    tl = build_timeline_from_edl_and_cover(edl, cover)
    pip = [c for c in tl["clips"] if c["layout"] == "pip_corner"]
    screen_clips = [c for c in tl["clips"] if c["source"] == "screen"]
    assert pip
    assert screen_clips
    assert tl.get("composite") is None
    assert tl["camera_play"]["scales"]["close"] == 1.42
    assert tl["camera_play"]["snap_on_cuts"] is True


def test_effective_camera_play_no_composite_passthrough():
    project = {"sources": {"cam": "raw/cam.mp4", "screen": "raw/screen.mp4"}}
    cp = effective_camera_play(
        {"camera_play": {"home": "medium", "scales": {"close": 1.42}}},
        project,
    )
    assert cp["home"] == "medium"
    assert cp["scales"]["close"] == 1.42
    assert is_camera_play_enabled(cp) is True


def test_overlay_density_extras_opt_in_on_dual_source():
    project = {
        "sources": {"cam": "raw/cam.mp4", "screen": "raw/screen.mp4"},
        "overlays": {"density": {"explain_fill": True, "stale_screen_fill": False}},
    }
    assert is_composite_episode(project) is False
    assert overlay_explain_fill_enabled(project) is True
    assert overlay_stale_screen_fill_enabled(project) is False


def test_overlay_density_extras_default_on_composite_only():
    project = {"sources": {"cam": "raw/cam.mkv"}, "composite": {"enabled": True}}
    assert overlay_explain_fill_enabled(project) is True
    assert overlay_stale_screen_fill_enabled(project) is True
