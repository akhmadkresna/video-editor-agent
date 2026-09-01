"""Load presentation tokens from styles/<name>/style.md YAML fence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agentic_editor.paths import framework_home

# Locked A-roll MG (2026-08+, "Open Overlay" v7) = white ink straight on the
# a-roll, no panel, no accent color — readability from the veil scrim behind
# the text. One look, shared by every kind (title/stat/lower_third/tag/
# divider/quote/code/illustration/chapter/emphasis/diagram/callout/chip) and
# every style pack. See packages/remotion-kit/src/components/glass/tokens.ts.
DEFAULT_OVERLAYS: dict[str, Any] = {
    "preset": "open_overlay",
    "treatment": "bold",
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
    # Middle-ground size hierarchy (~1.3–1.4× prior hero)
    "sizeBands": {
        "heroCqh": 22,
        "bodyCqh": 9,
        "metaCqh": 3.4,
    },
    "density": {
        "maxPrimary": 1,
        "maxSecondary": 1,
    },
    "chapter": {
        "kickerSizeCqh": 2.4,
        "titleSizeCqh": 12,
        "leftCqw": 4.5,
        "topCqh": 12,
        "maxWidthCqw": 42,
    },
    "emphasis": {
        "sizeCqh": 22,
        "leftCqw": 4.5,
        "bottomCqh": 28,
        "maxWidthCqw": 48,
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
        "valueSizeCqh": 18,
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
        # Surround OK (left/right/above/below); never cover face oval
        "zones": ["left_third", "right_third", "lower_raised", "top_sparse"],
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
        "aspectRatio": "5:6",
        "insetRightRatio": 0.035,
        "insetBottomRatio": 0.045,
        "borderRadiusPx": 26,
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
    """Return A-roll overlay tokens (white ink, no panel, no accent — locked)."""
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
    "pack": "assets/sfx",
    "volumes": {"typing": 0.38, "shutter": 0.48, "click": 0.32, "paper": 0.35, "tick": 0.28},
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
    # paper = MG appear (glass kinds); tick = small "tag" chip appear.
    "paper": {"max_sec": 0.45},
    "tick": {"max_sec": 0.15},
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


# Locked cam-VO treatment: DeepFilterNet 3 CLI, 12 dB atten-lim, delay compensated.
# Opt out per episode with project.yaml voice_enhance.enabled: false.
DEFAULT_VOICE_ENHANCE: dict[str, Any] = {
    "enabled": True,
    "backend": "deepfilternet",
    "atten_lim_db": 12,
    "compensate_delay": True,
    "sample_rate": 48000,
    "sources": ["cam"],
}


def load_voice_enhance(
    style_name: str = "tutorial",
    project: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return cam voice-enhance knobs (DEFAULT ← style yaml ← project.yaml)."""
    cfg = _deep_merge({}, DEFAULT_VOICE_ENHANCE)
    parsed = _load_style_yaml(style_name)
    ve = parsed.get("voice_enhance")
    if isinstance(ve, dict):
        cfg = _deep_merge(cfg, ve)
    if project:
        ep = project.get("voice_enhance")
        if isinstance(ep, dict):
            cfg = _deep_merge(cfg, ep)
    return cfg


def sfx_pack_dir(style_name: str = "tutorial") -> Path:
    """Absolute path to the shared SFX pack (default ``assets/sfx``)."""
    cfg = load_sfx(style_name)
    pack = str(cfg.get("pack") or "assets/sfx")
    p = Path(pack)
    if p.is_absolute():
        return p
    return framework_home() / p
