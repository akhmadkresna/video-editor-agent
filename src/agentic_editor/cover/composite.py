"""Single-file cam+screen composite (OBS baked PIP) helpers.

When ``project.yaml`` has ``composite.enabled: true`` and only ``sources.cam``,
the episode is treated as having a screen track for cover-suggest / overlays,
but Remotion must **not** add a second ``pip_corner`` on top of the baked face.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from agentic_editor.project import resolve_source

# Softer fake-multicam on a full-frame OBS composite — zooming the whole frame
# crops UI; cut-snap shutter without a visible punch reads as "missing MG".
DEFAULT_COMPOSITE_CAMERA_PLAY: dict[str, Any] = {
    "snap_on_cuts": False,
    "home": "wide",
    "alt": "medium",
    "wide_on_resets": True,
    "max_hold_sec": 12,
    "scales": {"wide": 1.0, "medium": 1.08, "close": 1.15},
}


def load_composite(project: dict[str, Any]) -> dict[str, Any]:
    """Return normalized composite config (``enabled`` false when absent)."""
    raw = project.get("composite")
    if not isinstance(raw, dict):
        return {"enabled": False, "baked_pip": True}
    cfg: dict[str, Any] = {
        "enabled": bool(raw.get("enabled", False)),
        "baked_pip": bool(raw.get("baked_pip", True)),
    }
    cp_raw = raw.get("camera_play")
    if isinstance(cp_raw, dict):
        cp = deepcopy(DEFAULT_COMPOSITE_CAMERA_PLAY)
        for k, v in cp_raw.items():
            if k == "scales" and isinstance(v, dict):
                scales = dict(cp.get("scales") or {})
                scales.update({sk: float(sv) for sk, sv in v.items()})
                cp["scales"] = scales
            elif v is not None:
                cp[k] = v
        cfg["camera_play"] = cp
    elif cfg["enabled"]:
        cfg["camera_play"] = deepcopy(DEFAULT_COMPOSITE_CAMERA_PLAY)
    return cfg


def has_composite_screen(project: dict[str, Any]) -> bool:
    """True when composite mode supplies screen beats without ``sources.screen``."""
    return bool(load_composite(project).get("enabled"))


def has_screen_cover(project: dict[str, Any]) -> bool:
    """Dual-source screen **or** composite single-file."""
    sources = project.get("sources") or {}
    return "screen" in sources or has_composite_screen(project)


def is_baked_pip(composite: dict[str, Any]) -> bool:
    return bool(composite.get("enabled")) and bool(composite.get("baked_pip", True))


def activity_probe_path(episode: Path, project: dict[str, Any]) -> Path:
    """File used for ffmpeg activity bins (screen file, else composite cam)."""
    sources = project.get("sources") or {}
    if "screen" in sources:
        return resolve_source(episode, str(sources["screen"]))
    if "cam" not in sources:
        raise FileNotFoundError("project.yaml needs sources.cam for composite activity probe")
    return resolve_source(episode, str(sources["cam"]))


def effective_camera_play(
    cover: dict[str, Any] | None,
    project: dict[str, Any],
) -> dict[str, Any]:
    """Merge cover.json camera_play with composite defaults when enabled."""
    from agentic_editor.cover.style_load import _deep_merge

    cp = deepcopy((cover or {}).get("camera_play") or {})
    comp = load_composite(project)
    if comp.get("enabled") and isinstance(comp.get("camera_play"), dict):
        cp = _deep_merge(cp, comp["camera_play"])
    return cp
