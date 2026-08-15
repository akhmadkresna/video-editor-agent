"""Portrait social export built from sibling ``edit/social`` artifacts.

The long-form tutorial remains untouched. Social exports share raw sources and
the cached word transcript, but use their own EDL, cover, timeline, props, and
final render.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from agentic_editor.compose import (
    _remotion_cli,
    remotion_kit_dir,
    remotion_render_accel_args,
    stage_sfx_for_remotion,
    stage_sources_for_remotion,
    validate_timeline_for_studio,
)
from agentic_editor.compose.mezzanine import resolve_compose_sources
from agentic_editor.cover import build_timeline_from_edl_and_cover, write_timeline
from agentic_editor.cover.remap import remap_source_window
from agentic_editor.cover.style_load import (
    load_overlays,
    load_screen_explainer,
    load_social,
    _load_style_yaml,
)
from agentic_editor.editor.edl import load_edl
from agentic_editor.project import load_project, resolve_source

_TOKEN_EDGE = re.compile(r"(^[^\w]+|[^\w]+$)", re.UNICODE)


def _load_words(episode: Path) -> list[dict[str, Any]]:
    path = episode / "edit" / "transcripts" / "cam.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing word transcript: {path}; run ae ingest first")
    data = json.loads(path.read_text(encoding="utf-8"))
    return [w for w in (data.get("words") or []) if isinstance(w, dict)]


def _correct_word(raw: str, replacements: dict[str, str]) -> str:
    """Apply case-insensitive token corrections while preserving punctuation."""
    text = str(raw or "").strip()
    bare = _TOKEN_EDGE.sub("", text).lower()
    replacement = replacements.get(bare)
    if replacement is None:
        return text
    prefix_len = len(text) - len(text.lstrip(".,!?;:-–—\"'()[]"))
    suffix_len = len(text) - len(text.rstrip(".,!?;:-–—\"'()[]"))
    prefix = text[:prefix_len] if prefix_len else ""
    suffix = text[len(text) - suffix_len :] if suffix_len else ""
    return f"{prefix}{replacement}{suffix}"


def build_karaoke_captions(
    edl: dict[str, Any],
    words: list[dict[str, Any]],
    *,
    replacements: dict[str, str] | None = None,
    max_words: int = 5,
    max_chars: int = 28,
    pause_sec: float = 0.38,
) -> list[dict[str, Any]]:
    """Remap source-time words through a short EDL and group readable captions."""
    corrections = {str(k).lower(): str(v) for k, v in (replacements or {}).items()}
    mapped: list[dict[str, Any]] = []
    for word in words:
        try:
            start = float(word["start"])
            end = float(word["end"])
        except (KeyError, TypeError, ValueError):
            continue
        slices = remap_source_window(edl, start, end, source="cam")
        if not slices:
            continue
        sl = max(slices, key=lambda x: float(x["durationSec"]))
        text = _correct_word(str(word.get("word") or word.get("text") or ""), corrections)
        if not text:
            continue
        range_index = next(
            (
                i
                for i, r in enumerate(edl.get("ranges") or [])
                if str(r.get("source") or "cam") == "cam"
                and float(r["start"]) < end
                and float(r["end"]) > start
            ),
            -1,
        )
        normalized = _TOKEN_EDGE.sub("", text).lower()
        if mapped and normalized and normalized == mapped[-1].get("normalized"):
            # Whisper often emits hyphenated duplicates as two words:
            # ``ONKM -ONKM`` / ``aplikasi -aplikasi``.
            continue
        out_start = float(sl["fromSec"])
        out_end = out_start + float(sl["durationSec"])
        mapped.append(
            {
                "text": text,
                "start": out_start,
                "end": out_end,
                "rangeIndex": range_index,
                "normalized": normalized,
            }
        )

    captions: list[dict[str, Any]] = []
    chunk: list[dict[str, Any]] = []

    def flush() -> None:
        if not chunk:
            return
        captions.append(
            {
                "text": " ".join(str(w["text"]) for w in chunk),
                "start": round(float(chunk[0]["start"]), 3),
                "end": round(float(chunk[-1]["end"]) + 0.12, 3),
                "words": [
                    {k: v for k, v in w.items() if k in {"text", "start", "end"}}
                    for w in chunk
                ],
                "style": "karaoke",
            }
        )
        chunk.clear()

    for word in mapped:
        gap = float(word["start"]) - float(chunk[-1]["end"]) if chunk else 0.0
        proposed = " ".join([*(str(w["text"]) for w in chunk), str(word["text"])])
        previous_ends_phrase = bool(chunk and re.search(r"[.!?]$", str(chunk[-1]["text"])))
        if chunk and (
            word.get("rangeIndex") != chunk[-1].get("rangeIndex")
            or
            gap > pause_sec
            or len(chunk) >= max_words
            or len(proposed) > max_chars
            or previous_ends_phrase
        ):
            flush()
        chunk.append(word)
    flush()
    return captions


_STAGE_EVENT_TYPES = frozenset({"screen_with_cam", "cam_pip", "screen", "screen_full"})


def force_screen_stage(cover: dict[str, Any], edl: dict[str, Any]) -> dict[str, Any]:
    """Put every cam keep on the screen + cam PIP stage.

    A 16:9 full-cam clip cropped to 9:16 keeps only about a third of its width,
    so the host reads as heavily zoomed. The stage shows the UI and a framed cam
    instead, and cam audio still comes from the PIP clip.
    """
    events = [
        ev
        for ev in (cover.get("events") or [])
        if str(ev.get("type") or "").lower() not in _STAGE_EVENT_TYPES
    ]
    for i, r in enumerate(edl.get("ranges") or []):
        if str(r.get("source") or "cam") != "cam":
            continue
        events.append(
            {
                "type": "screen_with_cam",
                "start": float(r["start"]),
                "end": float(r["end"]),
                "note": f"social stage (range {i})",
            }
        )
    return {**cover, "events": events}


def prepare_social(episode: Path, *, verbose: bool = True) -> Path:
    cfg = load_project(episode)
    social = episode / "edit" / "social"
    edl_path = social / "edl.json"
    cover_path = social / "cover.json"
    if not edl_path.is_file():
        raise FileNotFoundError(f"Missing confirmed social EDL: {edl_path}")
    if not cover_path.is_file():
        raise FileNotFoundError(f"Missing social cover: {cover_path}")

    edl = load_edl(edl_path)
    cover = json.loads(cover_path.read_text(encoding="utf-8"))
    abs_sources: dict[str, str] = {
        name: str(resolve_source(episode, rel))
        for name, rel in (cfg.get("sources") or {}).items()
    }
    for name, rel in edl["sources"].items():
        p = Path(rel)
        if not p.is_absolute():
            p = (social / p).resolve()
        abs_sources.setdefault(name, str(p))

    social_cfg = load_social("social")
    force = cover.get("force_screen_with_cam")
    if force is None:
        force = bool(social_cfg.get("force_screen_with_cam", True))
    if force and "screen" in abs_sources:
        cover = force_screen_stage(cover, edl)
        if verbose:
            print("• social stage: screen + cam PIP on every keep (no portrait full-cam)")

    compose_sources = resolve_compose_sources(episode, abs_sources, cfg, verbose=verbose)
    staged = stage_sources_for_remotion(compose_sources, verbose=verbose)
    runtime_edl = dict(edl)
    runtime_edl["sources"] = staged

    timeline = build_timeline_from_edl_and_cover(
        runtime_edl,
        cover,
        fps=int(cfg.get("fps", 30)),
        width=1080,
        height=1920,
        screen_explainer=load_screen_explainer("social"),
        overlays=load_overlays("social"),
        episode=episode,
    )
    caption_cfg = cover.get("karaoke") or {}
    style_captions = (_load_style_yaml("social").get("captions") or {})
    timeline["captions"] = build_karaoke_captions(
        edl,
        _load_words(episode),
        replacements=dict(caption_cfg.get("replacements") or {}),
        max_words=int(caption_cfg.get("max_words") or 5),
        max_chars=int(caption_cfg.get("max_chars") or 28),
        pause_sec=float(caption_cfg.get("pause_sec") or 0.38),
    )
    timeline.setdefault("presentation", {})["profile"] = "social"
    timeline["presentation"]["captions"] = {
        "style": "karaoke",
        "accent": str(style_captions.get("accent") or "#7dd3fc"),
        "safeBottomRatio": float(
            style_captions.get("safeBottomRatio")
            or caption_cfg.get("safeBottomRatio")
            or 0.17
        ),
    }
    cta = dict(social_cfg.get("cta") or {})
    episode_cta = cover.get("cta")
    if isinstance(episode_cta, dict):
        cta.update(episode_cta)
    timeline["presentation"]["cta"] = cta
    timeline["sources"] = staged
    timeline["sfx"] = stage_sfx_for_remotion(
        list(timeline.get("sfx") or []),
        style_name="social",
        verbose=verbose,
    )
    timeline["sourcePaths"] = compose_sources
    timeline["rawSourcePaths"] = abs_sources

    social.mkdir(parents=True, exist_ok=True)
    timeline_path = social / "timeline.json"
    write_timeline(timeline_path, timeline)
    props = social / "remotion-props.json"
    props.write_text(json.dumps({"timeline": timeline}, indent=2) + "\n", encoding="utf-8")
    errors = validate_timeline_for_studio(timeline, props)
    if errors:
        raise RuntimeError("social compose preflight failed:\n  - " + "\n  - ".join(errors))
    if verbose:
        print(
            f"• social props → {props.relative_to(episode)} "
            f"({timeline['durationSec']:.1f}s, {len(timeline['captions'])} karaoke lines)"
        )
    return props


def run_social_studio(episode: Path) -> None:
    props = prepare_social(episode)
    kit = remotion_kit_dir()
    cmd = [*_remotion_cli(kit), "studio", "src/index.ts", "--props", str(props)]
    subprocess.run(cmd, cwd=str(kit), check=True)


def render_social(
    episode: Path,
    *,
    output: Path | None = None,
    nvenc: bool = False,
    gl: str | None = None,
) -> Path:
    props = prepare_social(episode)
    kit = remotion_kit_dir()
    out = output or (episode / "edit" / "social" / "final.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["AE_TIMELINE_PROPS"] = str(props)
    env["AE_EPISODE"] = str(episode.resolve())
    cmd = [
        *_remotion_cli(kit),
        "render",
        "src/index.ts",
        "AgenticTimeline",
        str(out),
        "--props",
        str(props),
        *remotion_render_accel_args(nvenc=nvenc, gl=gl),
    ]
    print(f"$ cd {kit} && {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(kit), env=env, check=True)
    return out


def qa_social(episode: Path) -> Path:
    """Extract representative portrait frames for a quick visual QA pass."""
    final = episode / "edit" / "social" / "final.mp4"
    timeline_path = episode / "edit" / "social" / "timeline.json"
    if not final.is_file() or not timeline_path.is_file():
        raise FileNotFoundError("Run ae social first; final.mp4 or timeline.json is missing")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg is required for social QA")
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    duration = float(timeline.get("durationSec") or 0)
    verify = episode / "edit" / "social" / "verify"
    verify.mkdir(parents=True, exist_ok=True)
    for i, ratio in enumerate((0.04, 0.28, 0.52, 0.72, 0.96), start=1):
        at = max(0.0, min(duration - 0.05, duration * ratio))
        out = verify / f"social-{i:02d}-{at:.1f}s.png"
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{at:.3f}",
                "-i",
                str(final),
                "-frames:v",
                "1",
                str(out),
            ],
            check=True,
        )
    print(f"• social QA frames → {verify.relative_to(episode)}")
    return verify
