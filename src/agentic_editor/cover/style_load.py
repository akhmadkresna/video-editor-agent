"""Load presentation tokens from styles/<name>/style.md YAML fence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agentic_editor.paths import framework_home

# Locked A-roll MG = bold type + cool mist sky accent
DEFAULT_OVERLAYS: dict[str, Any] = {
    "preset": "bold_mist",
    "treatment": "bold",
    "accent": "#7dd3fc",
    "accentName": "cool_mist_sky",
    "ink": "#ffffff",
    "dim": "rgba(255,255,255,0.55)",
    # Readable on-screen time (OverlayLayer fades out; do not hard-cut early)
    "dwell": {
        "chip_sec": 4.0,
        "chapter_sec": 5.5,
        "diagram_sec": 10.0,
        "emphasis_sec": 2.4,
        "min_sec": 1.8,
        # List must remain after the last step appears (was ~0.35s — unreadable)
        "diagram_hold_after_last_sec": 2.6,
        "diagram_sec_per_step": 1.45,
        "diagram_search_pad_sec": 8.0,
        "exit_sec": 0.9,
    },
    "fonts": {
        "display": "Syne",
        "ui": "Instrument Sans",
    },
    "chapter": {
        "kickerSizeCqh": 2.4,
        "titleSizeCqh": 9,
        "leftCqw": 4.5,
        "topCqh": 12,
        "maxWidthCqw": 42,
    },
    "emphasis": {
        "sizeCqh": 16,
        "leftCqw": 4.5,
        "bottomCqh": 28,
        "underline": True,
    },
    "diagram": {
        "leftCqw": 4.5,
        "topCqh": 10,
        "maxWidthCqw": 40,
        "stepSizeCqh": 3.6,
    },
    "callout": {
        "leftCqw": 4.5,
        "bottomCqh": 22,
        "valueSizeCqh": 14,
        "sourceSizeCqh": 2.8,
        "maxWidthCqw": 48,
    },
    "chip": {
        "leftCqw": 4.5,
        "topCqh": 10,
        "sizeCqh": 3.4,
    },
    "safe": {
        "faceClear": True,
        "zones": ["left_third", "lower_third"],
    },
}

# Locked defaults = cozy + cool mist + smart window detect
DEFAULT_SCREEN_EXPLAINER: dict[str, Any] = {
    "preset": "cozy",
    "canvas": {
        "background": "#d9e2ec",
        "backgroundDeep": "#c4d0dc",
        "gradient": "radial",
    },
    "screen": {
        "presentation": "float_centered",
        "widthRatio": 0.78,
        "maxHeightRatio": 0.82,
        "borderRadiusPx": 24,
        "shadow": "soft_float",
        "objectFit": "fill",
        "crop": {
            "mode": "none",
        },
    },
    "pip": {
        "anchor": "stage_lower_right",
        "widthRatio": 0.18,
        "aspectRatio": "4:5",
        "insetRightRatio": 0.035,
        "insetBottomRatio": 0.045,
        "borderRadiusPx": 14,
        "border": "none",
        "objectFit": "cover",
        "objectPosition": "center 28%",
    },
}


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def _load_style_yaml(style_name: str) -> dict[str, Any]:
    path = framework_home() / "styles" / style_name / "style.md"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    m = re.search(r"```ya?ml\s*\n(.*?)```", text, re.S | re.I)
    if not m:
        return {}
    try:
        parsed = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_overlays(style_name: str = "tutorial") -> dict[str, Any]:
    """Return A-roll overlay tokens (bold + cool mist accent — locked)."""
    cfg = _deep_merge({}, DEFAULT_OVERLAYS)
    parsed = _load_style_yaml(style_name)
    ov = parsed.get("overlays")
    if isinstance(ov, dict):
        cfg = _deep_merge(cfg, ov)
    return cfg


def load_screen_explainer(style_name: str = "tutorial") -> dict[str, Any]:
    """Return screen_explainer tokens (cozy / cool mist locked by style pack)."""
    cfg = _deep_merge({}, DEFAULT_SCREEN_EXPLAINER)
    parsed = _load_style_yaml(style_name)
    se = parsed.get("screen_explainer")
    if isinstance(se, dict):
        cfg = _deep_merge(cfg, se)
    return cfg


DEFAULT_SFX: dict[str, Any] = {
    "enabled": True,
    "no_whoosh": True,
    "pack": "styles/tutorial/sfx",
    "volumes": {"typing": 0.38, "shutter": 0.38, "click": 0.32},
    "density": {
        "sec_per_sfx": 30,
        "min_gap_sec": 1.2,
        "shutter_click_min_gap_sec": 0.4,
        "typing_merge_gap_sec": 1.5,
    },
    # Typing holds run the full screen demo — off by default; prefer one-shots.
    "typing": {"enabled": False, "min_hold_sec": 4.0, "tile_sec": 1.2},
    "shutter": {"max_sec": 0.22},
    "click": {"max_sec": 0.22},
    # One-shot at MG appear (cover.overlays).
    "mg": {
        "enabled": True,
        "chapter": "shutter",
        "diagram": "shutter",
        "emphasis": "click",
        "chip": "click",
    },
}


def load_sfx(style_name: str = "tutorial") -> dict[str, Any]:
    """Return sfx pack config (modern tech — no whoosh)."""
    cfg = _deep_merge({}, DEFAULT_SFX)
    parsed = _load_style_yaml(style_name)
    sfx = parsed.get("sfx")
    if isinstance(sfx, dict):
        cfg = _deep_merge(cfg, sfx)
    return cfg


DEFAULT_SOCIAL: dict[str, Any] = {
    # Portrait crops a 16:9 full-cam clip to roughly a third of its width, which
    # reads as an extreme zoom. Keep every beat on the screen + cam PIP stage.
    "force_screen_with_cam": True,
    # Always-on pointer back to the long-form upload.
    "cta": {
        "enabled": True,
        "text": "Full video di YouTube",
        "blink": True,
        "blinkPeriodSec": 1.2,
        "anchor": "band_top_center",
        "bandTopCqh": 3.2,
        "sizeCqh": 2.0,
    },
}


def load_social(style_name: str = "social") -> dict[str, Any]:
    """Return portrait profile knobs (stage forcing)."""
    cfg = _deep_merge({}, DEFAULT_SOCIAL)
    parsed = _load_style_yaml(style_name)
    social = parsed.get("social")
    if isinstance(social, dict):
        cfg = _deep_merge(cfg, social)
    return cfg


def sfx_pack_dir(style_name: str = "tutorial") -> Path:
    """Absolute path to styles/<style>/sfx (or pack override)."""
    cfg = load_sfx(style_name)
    pack = str(cfg.get("pack") or f"styles/{style_name}/sfx")
    p = Path(pack)
    if p.is_absolute():
        return p
    return framework_home() / p
