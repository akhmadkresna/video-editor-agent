"""Static HTML storyboard for reviewing EDL / cover plans before apply."""

from __future__ import annotations

import hashlib
import html
import json
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from agentic_editor.asr.ingest import ffprobe_summary
from agentic_editor.cover.mockup import load_mockup
from agentic_editor.cover.remap import collect_overlay_defs
from agentic_editor.cover.suggest import load_cam_words
from agentic_editor.editor.qa import extract_frame
from agentic_editor.project import load_project, resolve_source

# Mirrors packages/remotion-kit/src/components/overlayZones.ts zoneBoxStyle —
# same cqw/cqh percentages the real A-roll renderer uses, so an on-frame chip
# here lands roughly where the actual overlay will land on the real render.
_ZONE_BOX_STYLE: dict[str, str] = {
    "right_third": "right:4.5%;left:auto;top:18%;text-align:right;max-width:42%",
    "lower_raised": "left:4.5%;bottom:28%;top:auto;max-width:42%",
    "top_sparse": "left:4.5%;top:10%;max-width:38%",
    "left_third": "left:4.5%;top:12%;max-width:42%",
}
_DEFAULT_ZONE_FOR_KIND: dict[str, str] = {
    "lower_third": "lower_raised",
    "stat": "lower_raised",
    "callout": "lower_raised",
    "emphasis": "lower_raised",
    "chip": "top_sparse",
    "tag": "top_sparse",
    "chapter": "top_sparse",
    "divider": "top_sparse",
}


def _zone_for_overlay(overlay: dict[str, Any]) -> str:
    zone = str(overlay.get("zone") or "").strip()
    if zone in _ZONE_BOX_STYLE:
        return zone
    return _DEFAULT_ZONE_FOR_KIND.get(str(overlay.get("kind") or ""), "left_third")


def _overlay_chip_text(overlay: dict[str, Any]) -> str:
    kind = str(overlay.get("kind") or "overlay")
    for field in ("value", "text", "title", "kicker"):
        val = str(overlay.get(field) or "").strip()
        if val:
            return val if len(val) <= 60 else val[:59].rstrip() + "…"
    return kind


def plan_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _html_rel_path(base: Path, target: Path) -> str:
    """Path from ``base`` (storyboard dir) to ``target`` for ``<img src>``."""
    try:
        return target.relative_to(base).as_posix()
    except ValueError:
        return Path(os.path.relpath(target, base)).as_posix()


def format_clock(seconds: float) -> str:
    total = max(0, round(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _thumbnail_path(
    dashboard: Path,
    source: Path,
    *,
    start: float,
    end: float,
) -> Path:
    stat = source.stat()
    identity = (
        f"{source.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|"
        f"{start:.3f}|{end:.3f}"
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return dashboard / "assets" / f"thumb_{digest}.jpg"


def _resolve_edl_path(episode: Path) -> tuple[Path, dict[str, Any]]:
    edit = episode / "edit"
    suggest = edit / "edl.suggest.json"
    edl_path = edit / "edl.json"
    # Applied cut (edl.json) wins over draft suggest once both exist.
    if edl_path.is_file():
        return edl_path, json.loads(edl_path.read_text(encoding="utf-8"))
    if suggest.is_file():
        return suggest, json.loads(suggest.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "Missing edit plan. Run `ae edl-suggest .` first (or provide edit/edl.json)."
    )


def _resolve_mockup_scenes(episode: Path) -> list[dict[str, Any]]:
    """``edit/mockup.json`` scenes, cam **source** seconds — same coordinate
    space ``_build_cards`` iterates EDL ranges in, so overlap is a plain
    interval check, no output-time remap needed here."""
    path = episode / "edit" / "mockup.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    scenes = data.get("scenes") if isinstance(data, dict) else None
    return [s for s in (scenes or []) if isinstance(s, dict)]


def mockup_scenes_for_range(
    scenes: list[dict[str, Any]],
    start: float,
    end: float,
) -> list[dict[str, Any]]:
    """Scenes overlapping ``[start, end)`` (cam source seconds).

    A scene straddling an EDL cut boundary will overlap two range cards —
    intentionally surfaced (not clamped to one slice like the real compose
    step does) so a straddling scene is visible during review, not hidden.
    """
    out: list[dict[str, Any]] = []
    for sc in scenes:
        try:
            s = float(sc.get("fromSec"))
            e = float(sc.get("toSec", sc.get("fromSec", 0)) or 0)
        except (TypeError, ValueError):
            continue
        if _interval_overlaps(start, end, s, e):
            out.append(sc)
    return out


def _resolve_cover(episode: Path) -> dict[str, Any] | None:
    edit = episode / "edit"
    cover_path = edit / "cover.json"
    suggest_path = edit / "cover.suggest.json"
    if cover_path.is_file():
        try:
            return json.loads(cover_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    if suggest_path.is_file():
        try:
            return json.loads(suggest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _resolve_source_video(episode: Path, edl: dict[str, Any], source_name: str) -> Path | None:
    rel = (edl.get("sources") or {}).get(source_name)
    if rel:
        path = resolve_source(episode, str(rel))
        if path.is_file():
            return path
    cfg = load_project(episode)
    rel = (cfg.get("sources") or {}).get(source_name)
    if rel:
        path = resolve_source(episode, str(rel))
        if path.is_file():
            return path
    return None


def _probe_duration(video: Path) -> float | None:
    try:
        summary = ffprobe_summary(video)
        dur = float((summary.get("format") or {}).get("duration") or 0)
        return dur if dur > 0 else None
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError, ValueError):
        return None


def speech_for_range(
    words: list[dict[str, Any]],
    start: float,
    end: float,
    *,
    max_chars: int = 280,
) -> str:
    """Return transcript text overlapping [start, end]."""
    parts: list[str] = []
    for w in words:
        ws, we = float(w["start"]), float(w["end"])
        if we <= start or ws >= end:
            continue
        text = str(w.get("text") or "").strip()
        if text:
            parts.append(text)
    speech = " ".join(parts).strip()
    if len(speech) > max_chars:
        return speech[: max_chars - 1].rstrip() + "…"
    return speech


def _interval_overlaps(start: float, end: float, a: float, b: float) -> bool:
    return a < end and b > start


def cover_badges_for_range(
    cover: dict[str, Any] | None,
    start: float,
    end: float,
) -> list[dict[str, str]]:
    """Compact chips for camera / sfx cues (MG uses render_mg_stack_html)."""
    if not cover:
        return []
    badges: list[dict[str, str]] = []
    for event in cover.get("events") or []:
        if not isinstance(event, dict):
            continue
        es, ee = float(event.get("start", 0)), float(event.get("end", 0))
        if not _interval_overlaps(start, end, es, ee):
            continue
        etype = str(event.get("type") or "event").lower()
        if etype in ("punch_in", "punch_out", "framing"):
            note = str(event.get("note") or "").strip()
            badges.append({"kind": "event", "label": etype, "detail": note})
    for sfx in cover.get("sfx") or []:
        if not isinstance(sfx, dict):
            continue
        ss = float(sfx.get("start", 0))
        se = float(sfx.get("end") or ss + 0.2)
        if not _interval_overlaps(start, end, ss, se):
            continue
        kind = str(sfx.get("kind") or "sfx")
        note = str(sfx.get("note") or "").strip()
        badges.append({"kind": "sfx", "label": kind, "detail": note})
    return badges


def _overlay_id_lookup(cover: dict[str, Any] | None) -> dict[tuple[str, float, float], str]:
    lookup: dict[tuple[str, float, float], str] = {}
    for ov in collect_overlay_defs(cover):
        key = (str(ov["kind"]), float(ov["start"]), float(ov["end"]))
        lookup[key] = str(ov["id"])
    return lookup


def cover_mg_items_for_range(
    cover: dict[str, Any] | None,
    start: float,
    end: float,
) -> list[dict[str, Any]]:
    """MG creatives (overlays + evidence stills) overlapping a keep range."""
    if not cover:
        return []
    id_lookup = _overlay_id_lookup(cover)
    items: list[dict[str, Any]] = []
    for overlay in cover.get("overlays") or []:
        if not isinstance(overlay, dict):
            continue
        os, oe = float(overlay.get("start", 0)), float(overlay.get("end", 0))
        if not _interval_overlaps(start, end, os, oe):
            continue
        kind = str(overlay.get("kind") or "overlay")
        item = {"category": "overlay", **overlay}
        item["id"] = str(
            overlay.get("id")
            or id_lookup.get((kind, os, oe))
            or f"ov-{kind}-?"
        )
        items.append(item)
    for event in cover.get("events") or []:
        if not isinstance(event, dict):
            continue
        etype = str(event.get("type") or "").lower()
        if etype != "evidence_with_cam":
            continue
        es, ee = float(event.get("start", 0)), float(event.get("end", 0))
        if not _interval_overlaps(start, end, es, ee):
            continue
        src = str(event.get("src") or "").strip()
        stem = Path(src).stem or "evidence"
        items.append(
            {
                "category": "evidence",
                "id": f"ev-{stem}",
                **event,
            }
        )
    items.sort(
        key=lambda it: (
            float(it.get("start") or 0),
            0 if it.get("category") == "overlay" else 1,
            str(it.get("kind") or it.get("type") or ""),
        )
    )
    return items


def render_frame_overlay_chips_html(items: list[dict[str, Any]]) -> str:
    """Small chips positioned ON the frame at each overlay's real zone —
    a cheap, no-Remotion-needed approximation of where MG will actually
    land, so a card shows "what + roughly where" at a glance.

    A card spans real time, so two overlays with the same zone but
    different (non-overlapping) moments both show up here at once — stack
    them (chronological order) instead of letting them print on top of
    each other unreadably.
    """
    overlays = [it for it in items if it.get("category") == "overlay"]
    overlays.sort(key=lambda it: float(it.get("start") or 0))
    chips: list[str] = []
    zone_counts: dict[str, int] = {}
    for item in overlays:
        zone = _zone_for_overlay(item)
        stack_index = zone_counts.get(zone, 0)
        zone_counts[zone] = stack_index + 1
        style = _ZONE_BOX_STYLE.get(zone, _ZONE_BOX_STYLE["left_third"])
        if stack_index:
            style += f";transform:translateY({stack_index * 30}px)"
        kind = html.escape(str(item.get("kind") or "overlay"))
        text = html.escape(_overlay_chip_text(item))
        chips.append(
            f'<div class="frame-chip frame-chip-{kind}" style="{style}">'
            f'<span class="frame-chip-kind">{kind}</span>{text}</div>'
        )
    return "".join(chips)


def _mockup_layer_text(layer: dict[str, Any]) -> str:
    comp = str(layer.get("component") or "")
    data = layer.get("data") if isinstance(layer.get("data"), dict) else {}
    if comp == "ClaudeChat":
        turns = data.get("turns") if isinstance(data.get("turns"), list) else []
        parts = []
        for t in turns[:2]:
            if not isinstance(t, dict):
                continue
            role = str(t.get("role") or "")
            text = str(t.get("text") or "").strip()
            if text:
                parts.append(f"{role}: {text}")
        return " / ".join(parts)
    if comp == "DiffPanel":
        before = str(data.get("before") or "").strip().splitlines()[0:1]
        after = str(data.get("after") or "").strip().splitlines()[0:1]
        b = (before[0] if before else "")[:70]
        a = (after[0] if after else "")[:70]
        return f"− {b}\n+ {a}" if (b or a) else ""
    if comp == "RepoView":
        return str(data.get("repo") or data.get("repoUrl") or "")
    if comp == "SkillsPanel":
        skills = data.get("skills") if isinstance(data.get("skills"), list) else []
        names = [str(s.get("name")) for s in skills if isinstance(s, dict) and s.get("name")]
        return ", ".join(names)
    if comp == "AppWindow":
        return f"{data.get('app', '')} · {data.get('content', '')}"
    return ""


def render_mockup_scene_card_html(
    scene: dict[str, Any],
    *,
    mock_tokens: dict[str, Any],
    overlay_chips_html: str = "",
) -> str:
    """Synthesized 'Mist' stage placeholder for a drawn-screen mockup scene.

    No real frame exists to grab (style: mockup records no screen) — this
    renders the same stage/window/chrome-dot chrome + a text summary per
    layer component, so the scene is visible in review instead of silently
    missing from the storyboard entirely.
    """
    stage = scene.get("stage") if isinstance(scene.get("stage"), dict) else {}
    title = html.escape(str(stage.get("title") or "").strip())
    layers = [ly for ly in (scene.get("layers") or []) if isinstance(ly, dict)]
    components = [str(ly.get("component") or "") for ly in layers if ly.get("component")]
    comp_pills = "".join(
        f'<span class="mock-comp-pill">{html.escape(c)}</span>'
        for c in components
        if c != "Cursor"
    )
    body_lines: list[str] = []
    for ly in layers:
        if ly.get("component") == "Cursor":
            continue
        text = _mockup_layer_text(ly)
        if text:
            body_lines.append(
                f'<div class="mock-layer-text">{html.escape(text)}</div>'
            )
    start = float(scene.get("fromSec", 0))
    end = float(scene.get("toSec", scene.get("fromSec", 0)) or 0)
    win_bg = html.escape(str(mock_tokens.get("window") or "#fdfefe"))
    stage_bg = html.escape(str(mock_tokens.get("stageBg") or "#eceff1"))
    win_border = html.escape(str(mock_tokens.get("windowBorder") or "#dee3e6"))
    chrome_dot = html.escape(str(mock_tokens.get("chromeDot") or "#c3ccd1"))
    chrome_title = html.escape(str(mock_tokens.get("chromeTitle") or "#7d878d"))
    scene_id = html.escape(str(scene.get("id") or ""))
    return (
        f'<div class="mock-card" style="background:{stage_bg}">'
        f'<div class="mock-window" style="background:{win_bg};border-color:{win_border}">'
        '<div class="mock-chrome">'
        f'<span class="mock-dot" style="border-color:{chrome_dot}"></span>'
        f'<span class="mock-dot" style="border-color:{chrome_dot}"></span>'
        f'<span class="mock-dot" style="border-color:{chrome_dot}"></span>'
        f'<span class="mock-chrome-title" style="color:{chrome_title}">{title}</span>'
        "</div>"
        f'<div class="mock-body">{"".join(body_lines) or "<em>(no content authored yet)</em>"}</div>'
        f"{overlay_chips_html}"
        "</div>"
        '<div class="mock-foot">'
        f'<span class="mock-scene-id">mockup · {scene_id}</span>'
        f'<span class="mock-pills">{comp_pills}</span>'
        f'<span class="mock-time">{start:.1f}s–{end:.1f}s (source)</span>'
        "</div>"
        "</div>"
    )


def _evidence_rel_path(episode: Path, src: str) -> str | None:
    name = Path(str(src or "").strip()).name
    if not name:
        return None
    path = episode / "raw" / "evidence" / name
    if path.is_file():
        return Path("../../raw/evidence") / name
    return None


def _mg_steps_html(steps: list[Any]) -> str:
    rows = []
    for step in steps or []:
        text = html.escape(str(step).strip())
        if text:
            rows.append(f'<li class="mg-step">{text}</li>')
    if not rows:
        return ""
    return f'<ul class="mg-steps">{"".join(rows)}</ul>'


def _render_mg_overlay_panel(overlay: dict[str, Any]) -> str:
    kind = str(overlay.get("kind") or "overlay")
    kicker = html.escape(str(overlay.get("kicker") or "").strip())
    title = html.escape(str(overlay.get("title") or "").strip())
    text = html.escape(str(overlay.get("text") or "").strip())
    value = html.escape(str(overlay.get("value") or "").strip())
    source = html.escape(str(overlay.get("sourceLabel") or "").strip())
    accent = html.escape(str(overlay.get("accent") or "").strip())
    tone = html.escape(str(overlay.get("tone") or "neutral").strip())
    steps = overlay.get("steps") if isinstance(overlay.get("steps"), list) else []
    note = html.escape(str(overlay.get("note") or "").strip())

    body_parts: list[str] = []
    if kind == "tag":
        body_parts.append(f'<div class="mg-display mg-display-sm">{text or title or value}</div>')
    elif kind == "callout":
        if value:
            body_parts.append(f'<div class="mg-display mg-display-lg">{value}</div>')
        if source:
            body_parts.append(f'<div class="mg-meta">{source}</div>')
    elif kind == "stat":
        if value:
            body_parts.append(f'<div class="mg-display mg-display-xl">{value}</div>')
        if source:
            body_parts.append(f'<div class="mg-meta">{source}</div>')
    elif kind == "divider":
        if kicker:
            body_parts.append(f'<div class="mg-kicker">{kicker}</div>')
        if title:
            body_parts.append(f'<div class="mg-display mg-display-md">{title}</div>')
    elif kind == "quote":
        if kicker:
            body_parts.append(f'<div class="mg-kicker">{kicker}</div>')
        raw_text = str(overlay.get("text") or "")
        if raw_text:
            raw_accent = str(overlay.get("accent") or "")
            if raw_accent and raw_accent in raw_text:
                before, after = raw_text.split(raw_accent, 1)
                line = (
                    f'{html.escape(before)}'
                    f'<span class="mg-accent">{html.escape(raw_accent)}</span>'
                    f'{html.escape(after)}'
                )
            else:
                line = html.escape(raw_text)
            body_parts.append(f'<div class="mg-display mg-display-md mg-italic">{line}</div>')
    elif kind == "title":
        if kicker:
            body_parts.append(f'<div class="mg-kicker">{kicker}</div>')
        raw_text = str(overlay.get("text") or "")
        if raw_text:
            raw_accent = str(overlay.get("accent") or "")
            if raw_accent and raw_accent in raw_text:
                before, after = raw_text.split(raw_accent, 1)
                line = (
                    f'{html.escape(before)}'
                    f'<span class="mg-accent">{html.escape(raw_accent)}</span>'
                    f'{html.escape(after)}'
                )
            else:
                line = html.escape(raw_text)
            body_parts.append(f'<div class="mg-display mg-display-md">{line}</div>')
    elif kind == "lower_third":
        if title:
            body_parts.append(f'<div class="mg-kicker">{title}</div>')
        if text:
            body_parts.append(f'<div class="mg-display mg-display-sm">{text}</div>')
        body_parts.append(_mg_steps_html(steps))
    elif kind == "illustration":
        if title:
            body_parts.append(f'<div class="mg-kicker">{title}</div>')
        body_parts.append(_mg_steps_html(steps))
    elif kind in ("chapter", "emphasis", "diagram", "chip"):
        if kicker:
            body_parts.append(f'<div class="mg-kicker">{kicker}</div>')
        headline = title or text or value
        if headline:
            body_parts.append(f'<div class="mg-display mg-display-md">{headline}</div>')
        body_parts.append(_mg_steps_html(steps))
        if source:
            body_parts.append(f'<div class="mg-meta">{source}</div>')
    else:
        headline = title or text or value
        if headline:
            body_parts.append(f'<div class="mg-display">{headline}</div>')

    timing = (
        f'{float(overlay.get("start", 0)):.1f}s–{float(overlay.get("end", 0)):.1f}s'
    )
    note_html = f'<div class="mg-note">{note}</div>' if note else ""
    return (
        f'<div class="mg-panel mg-{html.escape(kind)} mg-tone-{tone}">'
        f'<div class="mg-head"><span class="mg-kind">{html.escape(kind)}</span>'
        f'<span class="mg-time">{timing}</span></div>'
        f'<div class="mg-body">{"".join(body_parts)}</div>'
        f"{note_html}"
        "</div>"
    )


def _render_mg_evidence_panel(episode: Path, event: dict[str, Any]) -> str:
    src = str(event.get("src") or "").strip()
    rel = _evidence_rel_path(episode, src)
    note = html.escape(str(event.get("note") or "").strip())
    timing = f'{float(event.get("start", 0)):.1f}s–{float(event.get("end", 0)):.1f}s'
    if rel is not None:
        media = f'<img class="mg-evidence-img" src="{rel.as_posix()}" alt="">'
    else:
        media = f'<div class="mg-evidence-missing">{html.escape(src or "evidence")}</div>'
    note_html = f'<div class="mg-note">{note}</div>' if note else ""
    return (
        '<div class="mg-panel mg-evidence">'
        '<div class="mg-head"><span class="mg-kind">evidence</span>'
        f'<span class="mg-time">{timing}</span></div>'
        f"{media}"
        f'<div class="mg-meta">{html.escape(Path(src).name if src else "screenshot")}</div>'
        f"{note_html}"
        "</div>"
    )


def render_mg_stack_html(
    items: list[dict[str, Any]],
    *,
    episode: Path | None = None,
    still_index: dict[str, Path] | None = None,
    dashboard: Path | None = None,
    render_mode: str = "mock",
) -> str:
    if not items:
        return ""
    panels: list[str] = []
    for item in items:
        tile_id = str(item.get("id") or "")
        preview_rel: str | None = None
        if still_index and tile_id and dashboard is not None:
            preview = still_index.get(tile_id)
            if preview is not None and preview.is_file():
                preview_rel = _html_rel_path(dashboard, preview)

        if preview_rel and render_mode == "remotion":
            kind = html.escape(
                str(item.get("kind") or item.get("type") or item.get("category") or "mg")
            )
            timing = (
                f'{float(item.get("start", 0)):.1f}s–{float(item.get("end", 0)):.1f}s'
            )
            note = html.escape(str(item.get("note") or "").strip())
            note_html = f'<div class="mg-note">{note}</div>' if note else ""
            panels.append(
                f'<div class="mg-panel mg-render mg-{kind}">'
                f'<div class="mg-head"><span class="mg-kind">{kind}</span>'
                f'<span class="mg-time">{timing}</span>'
                f'<span class="mg-render-badge">Remotion</span></div>'
                f'<img class="mg-render-still" src="{html.escape(preview_rel)}" alt="">'
                f"{note_html}"
                "</div>"
            )
        elif item.get("category") == "evidence" and episode is not None:
            panels.append(_render_mg_evidence_panel(episode, item))
        elif item.get("category") == "overlay":
            panels.append(_render_mg_overlay_panel(item))
    if not panels:
        return ""
    label = (
        "MG render (Remotion still)"
        if render_mode == "remotion"
        else "MG plan (text preview)"
    )
    return (
        f'<div class="mg-stack mg-mode-{html.escape(render_mode)}">'
        f'<div class="mg-stack-label">{label}</div>'
        f'{"".join(panels)}</div>'
    )


def _cover_badges_html(badges: list[dict[str, str]]) -> str:
    if not badges:
        return ""
    chips = []
    for badge in badges:
        label = html.escape(badge["label"])
        detail = html.escape(badge.get("detail") or "")
        title = f' title="{detail}"' if detail else ""
        css = badge.get("kind") or "event"
        chips.append(f'<span class="badge badge-{css}"{title}>{label}</span>')
    return f'<div class="badges">{"".join(chips)}</div>'


def render_cut_gap_html(
    *,
    gap_start: float,
    gap_end: float,
    duration: float,
) -> str:
    return (
        '<div class="cut-gap">'
        f'<span class="cut-gap-label">Cut</span>'
        f'<span class="cut-gap-span">{gap_start:.1f}s → {gap_end:.1f}s</span>'
        f'<span class="cut-gap-dur">· {duration:.1f}s removed</span>'
        "</div>"
    )


def render_range_card_html(
    *,
    index: int,
    source_name: str,
    timeline_start: float,
    timeline_end: float,
    duration: float,
    source_start: float,
    source_end: float,
    note: str,
    speech: str,
    thumb_relative: str | None,
    badges: list[dict[str, str]],
    mg_stack_html: str = "",
    frame_chips_html: str = "",
    mockup_cards_html: str = "",
) -> str:
    if thumb_relative:
        media = f'<img src="{thumb_relative}" alt="">'
    else:
        media = '<div class="thumb-missing">No preview</div>'
    return (
        '<article class="card">'
        f'<div class="frame">{media}{frame_chips_html}</div>'
        f"{mockup_cards_html}"
        f'<div class="body">'
        f"<strong>#{index} · {html.escape(source_name)}</strong>"
        f'<div class="time">Edit {format_clock(timeline_start)} → '
        f"{format_clock(timeline_end)} · {duration:.2f}s</div>"
        f'<div class="source">Source {source_start:.2f}s → {source_end:.2f}s</div>'
        f"{mg_stack_html}"
        f"{_cover_badges_html(badges)}"
        f'<p class="note">{html.escape(note)}</p>'
        f'<p class="speech">{html.escape(speech) if speech else "(no speech)"}</p>'
        "</div></article>"
    )


def _cover_summary_html(cover: dict[str, Any] | None) -> str:
    if not cover:
        return ""
    events = [e for e in (cover.get("events") or []) if isinstance(e, dict)]
    overlays = [o for o in (cover.get("overlays") or []) if isinstance(o, dict)]
    sfx = [s for s in (cover.get("sfx") or []) if isinstance(s, dict)]
    screen = sum(
        1
        for e in events
        if str(e.get("type") or "").lower() in ("screen_with_cam", "screen", "screen_full")
    )
    return (
        "<p><strong>Cover plan:</strong> "
        f"{len(events)} event(s) ({screen} screen), "
        f"{len(overlays)} overlay(s), {len(sfx)} sfx</p>"
    )


def _meta_stats_html(meta: dict[str, Any]) -> str:
    if not meta:
        return ""
    gclass = meta.get("gap_classes") or {}
    parts = [
        f"breath={gclass.get('breath', 0)}",
        f"think={gclass.get('think', 0)}",
        f"ai_wait={gclass.get('ai_wait', 0)}",
        f"retake={gclass.get('retake', 0)}",
    ]
    extras = []
    for key in ("dropped_repeat", "clamped_wait", "dropped_wait"):
        if key in meta:
            extras.append(f"{key}={meta[key]}")
    extra_html = f" · {', '.join(extras)}" if extras else ""
    return (
        f"<p><strong>Gap classes:</strong> {', '.join(parts)}{extra_html}</p>"
    )


def _build_cards(
    episode: Path,
    edl: dict[str, Any],
    *,
    dashboard: Path,
    words: list[dict[str, Any]],
    cover: dict[str, Any] | None,
    still_index: dict[str, Path] | None = None,
    mg_render_mode: str = "mock",
    mockup_scenes: list[dict[str, Any]] | None = None,
    mock_tokens: dict[str, Any] | None = None,
) -> tuple[str, set[Path]]:
    cards: list[str] = []
    used_assets: set[Path] = set()
    ranges = [r for r in (edl.get("ranges") or []) if isinstance(r, dict)]
    timeline_cursor = 0.0
    prev_end: float | None = None
    mockup_scenes = mockup_scenes or []

    for idx, rng in enumerate(ranges, start=1):
        source_name = str(rng.get("source") or "cam")
        start = float(rng["start"])
        end = float(rng["end"])
        duration = end - start

        if prev_end is not None and start > prev_end + 0.05:
            gap_dur = start - prev_end
            cards.append(
                render_cut_gap_html(gap_start=prev_end, gap_end=start, duration=gap_dur)
            )

        video = _resolve_source_video(episode, edl, source_name)
        thumb_relative: str | None = None
        if video is not None:
            thumb_path = _thumbnail_path(dashboard, video, start=start, end=end)
            mid = (start + end) / 2
            if not thumb_path.is_file() or thumb_path.stat().st_size == 0:
                try:
                    extract_frame(video, mid, thumb_path)
                except (OSError, subprocess.CalledProcessError):
                    pass
            if thumb_path.is_file() and thumb_path.stat().st_size > 0:
                used_assets.add(thumb_path)
                thumb_relative = thumb_path.relative_to(dashboard).as_posix()

        timeline_start = timeline_cursor
        timeline_end = timeline_cursor + duration
        timeline_cursor = timeline_end
        prev_end = end

        speech = speech_for_range(words, start, end)
        badges = cover_badges_for_range(cover, start, end)
        mg_items = cover_mg_items_for_range(cover, start, end)

        # A mockup scene replaces the cam picture with a drawn screen — any
        # overlay landing inside that window should preview on the drawn
        # stage, not floated over an cam frame the viewer won't see there.
        scenes_here = (
            mockup_scenes_for_range(mockup_scenes, start, end) if source_name == "cam" else []
        )

        def _in_a_scene(item: dict[str, Any], _scenes=scenes_here) -> bool:
            mid_t = (float(item.get("start", 0)) + float(item.get("end", 0))) / 2
            return any(
                float(sc.get("fromSec", 0)) <= mid_t < float(sc.get("toSec", sc.get("fromSec", 0)) or 0)
                for sc in _scenes
            )

        frame_items = [it for it in mg_items if not (scenes_here and _in_a_scene(it))]
        scene_items = [it for it in mg_items if scenes_here and _in_a_scene(it)]

        frame_chips = render_frame_overlay_chips_html(frame_items)
        mg_stack = render_mg_stack_html(
            mg_items,
            episode=episode,
            still_index=still_index,
            dashboard=dashboard,
            render_mode=mg_render_mode,
        )

        mockup_cards = ""
        if scenes_here:
            tokens = mock_tokens or {}
            mockup_cards = "".join(
                render_mockup_scene_card_html(
                    sc,
                    mock_tokens=tokens,
                    overlay_chips_html=render_frame_overlay_chips_html(
                        [
                            it
                            for it in scene_items
                            if float(sc.get("fromSec", 0))
                            <= (float(it.get("start", 0)) + float(it.get("end", 0))) / 2
                            < float(sc.get("toSec", sc.get("fromSec", 0)) or 0)
                        ]
                    ),
                )
                for sc in scenes_here
            )

        note = str(rng.get("note") or "speech")

        cards.append(
            render_range_card_html(
                index=idx,
                source_name=source_name,
                timeline_start=timeline_start,
                timeline_end=timeline_end,
                duration=duration,
                source_start=start,
                source_end=end,
                note=note,
                speech=speech,
                thumb_relative=thumb_relative,
                badges=badges,
                frame_chips_html=frame_chips,
                mockup_cards_html=mockup_cards,
                mg_stack_html=mg_stack,
            )
        )

    grid = f'<div class="grid">{"".join(cards)}</div>'
    return grid, used_assets


def _mg_review_banner_html(
    *,
    render_mg: bool,
    mg_render_mode: str,
    still_count: int,
    episode: Path,
) -> str:
    review_html = episode / "edit" / "mg-review" / "review.html"
    if mg_render_mode == "remotion" and still_count:
        return (
            f'<p class="mg-banner mg-banner-ok"><strong>MG renders:</strong> '
            f"{still_count} Remotion still(s) embedded — exact A-Roll Text Motion System on A-roll. "
            f'Full gallery: <a href="../mg-review/review.html">edit/mg-review/review.html</a></p>'
        )
    if render_mg:
        return (
            '<p class="mg-banner mg-banner-warn"><strong>MG renders:</strong> '
            "Remotion still export failed or was skipped — showing text previews only. "
            "Re-run with <code>ae storyboard . --render-mg --force-mg</code></p>"
        )
    if review_html.is_file():
        return (
            '<p class="mg-banner"><strong>MG renders:</strong> cached gallery at '
            '<a href="../mg-review/review.html">edit/mg-review/review.html</a> '
            "(may be stale). Refresh with <code>ae storyboard . --render-mg</code></p>"
        )
    return (
        '<p class="mg-banner"><strong>MG feedback:</strong> run '
        "<code>ae storyboard . --render-mg</code> for exact Remotion stills on each clip, "
        "or <code>ae mg-review .</code> for the full overlay gallery</p>"
    )


def generate_storyboard(
    episode: Path,
    *,
    open_browser: bool = True,
    render_mg: bool = False,
    force_mg: bool = False,
    gl: str | None = None,
) -> Path:
    edl_path, edl = _resolve_edl_path(episode)
    cfg = load_project(episode)
    edit = episode / "edit"
    cover = _resolve_cover(episode)
    words = load_cam_words(edit)
    meta = edl.get("_meta") if isinstance(edl.get("_meta"), dict) else {}

    still_index: dict[str, Path] = {}
    mg_render_mode = "mock"
    if render_mg and cover:
        try:
            from agentic_editor.compose import ensure_mg_review_stills

            still_index = ensure_mg_review_stills(
                episode, force=force_mg, gl=gl, verbose=True
            )
            if still_index:
                mg_render_mode = "remotion"
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"! MG still render failed — falling back to text previews: {exc}")
    elif cover and (episode / "edit" / "mg-review" / "stills").is_dir():
        from agentic_editor.compose import load_mg_review_preview_index

        cached = load_mg_review_preview_index(episode)
        if cached:
            from agentic_editor.compose import mg_review_stills_fresh

            if mg_review_stills_fresh(episode):
                still_index = cached
                mg_render_mode = "remotion"

    mockup_scenes = _resolve_mockup_scenes(episode)
    mock_tokens = load_mockup(str(cfg.get("style") or "mockup")) if mockup_scenes else {}

    dashboard = edit / "storyboard"
    dashboard.mkdir(parents=True, exist_ok=True)
    cards_html, used_assets = _build_cards(
        episode,
        edl,
        dashboard=dashboard,
        words=words,
        cover=cover,
        still_index=still_index or None,
        mg_render_mode=mg_render_mode,
        mockup_scenes=mockup_scenes,
        mock_tokens=mock_tokens,
    )

    assets = dashboard / "assets"
    if assets.is_dir():
        for old in assets.glob("*.jpg"):
            if old not in used_assets:
                old.unlink()

    keep_sec = float(meta.get("keep_sec") or sum(
        float(r["end"]) - float(r["start"]) for r in (edl.get("ranges") or [])
    ))
    cam_video = _resolve_source_video(episode, edl, "cam")
    source_dur: float | None = None
    if cam_video is not None:
        source_dur = _probe_duration(cam_video)
    compress_pct = ""
    if source_dur and source_dur > 0:
        compress_pct = f" · {100 * keep_sec / source_dur:.0f}% kept"

    title = str(cfg.get("id") or episode.name)
    plan_label = edl_path.name
    digest = plan_digest(edl_path)[:12]
    range_count = len(edl.get("ranges") or [])

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Storyboard</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#0e1116;color:#e8edf4;
font:15px/1.5 system-ui,sans-serif}} header,main{{max-width:1400px;margin:auto;padding:28px}}
header{{background:#171d27;border-bottom:1px solid #293242}} h1{{margin:0 0 8px}}
.meta,.description{{color:#9ca9ba}} .grid{{display:grid;
grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin-top:8px}}
.card{{background:#171d27;border:1px solid #293242;border-radius:10px;overflow:hidden}}
.frame{{position:relative}}
.frame>img{{width:100%;aspect-ratio:16/9;object-fit:cover;background:#080a0d;display:block}}
.thumb-missing{{width:100%;aspect-ratio:16/9;background:#080a0d;color:#6b7280;
display:flex;align-items:center;justify-content:center;font-size:13px}}
.frame-chip{{position:absolute;padding:3px 8px;border-radius:5px;font-size:11px;line-height:1.3;
background:rgba(10,13,18,.72);border:1px solid rgba(255,255,255,.22);color:#fff;
text-shadow:0 1px 3px rgba(0,0,0,.5);pointer-events:none;overflow:hidden;text-overflow:ellipsis}}
.frame-chip-kind{{display:block;font-size:9px;font-weight:700;text-transform:uppercase;
letter-spacing:.06em;color:#a5b4fc;margin-bottom:1px}}
.mock-card{{padding:10px;border-top:1px solid #293242;border-bottom:1px solid #293242}}
.mock-window{{position:relative;border-radius:8px;border:1px solid;padding:8px 10px 10px;
aspect-ratio:16/9;overflow:hidden;display:flex;flex-direction:column}}
.mock-chrome{{display:flex;align-items:center;gap:5px;margin-bottom:8px}}
.mock-dot{{width:8px;height:8px;border-radius:999px;border:1.5px solid;background:transparent}}
.mock-chrome-title{{font-size:11px;margin-left:6px;font-weight:600}}
.mock-body{{flex:1;overflow:hidden;font-size:12px;color:#3a434b;display:flex;
flex-direction:column;gap:6px}}
.mock-layer-text{{white-space:pre-wrap;background:rgba(255,255,255,.55);border-radius:4px;
padding:4px 6px}}
.mock-body em{{color:#98a2a8}}
.mock-foot{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:8px;
font-size:11px;color:#9ca9ba}}
.mock-scene-id{{font-weight:700;color:#c7d2fe}}
.mock-pills{{display:flex;gap:4px;flex-wrap:wrap}}
.mock-comp-pill{{padding:2px 7px;border-radius:999px;background:#101826;border:1px solid #334155;
color:#7dd3fc;font-size:10px}}
.mock-time{{font:11px ui-monospace;color:#64748b;margin-left:auto}}
.body{{padding:14px}} .time{{font:13px ui-monospace;color:#7dd3fc;margin-top:6px}}
.source{{font:12px ui-monospace;color:#9ca9ba;margin-top:4px}}
.note{{margin:8px 0 0;color:#c6d0db}} .speech{{color:#e8bd72;margin:6px 0 0}}
code{{color:#7dd3fc}}
.badges{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;
border:1px solid #334155;background:#101826;color:#c7d2fe}}
.badge-overlay{{border-color:#6366f1}} .badge-event{{border-color:#2dd4bf;color:#99f6e4}}
.badge-sfx{{border-color:#fbbf24;color:#fde68a}}
.mg-stack{{margin-top:10px;padding:10px;border-radius:8px;background:#0a0d12;
border:1px solid #334155}}
.mg-stack-label{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
color:#94a3b8;margin-bottom:8px}}
.mg-panel{{margin-top:8px;padding:10px 12px;border-radius:6px;background:linear-gradient(135deg,#1a2030 0%,#121820 100%);
border-left:3px solid #6366f1;color:#f8fafc}}
.mg-panel:first-of-type{{margin-top:0}}
.mg-evidence{{border-left-color:#2dd4bf}}
.mg-stat,.mg-callout{{border-left-color:#38bdf8}}
.mg-quote{{border-left-color:#fbbf24}}
.mg-divider{{border-left-color:#a78bfa}}
.mg-illustration{{border-left-color:#34d399}}
.mg-head{{display:flex;justify-content:space-between;gap:8px;margin-bottom:6px}}
.mg-kind{{font-size:11px;font-weight:700;text-transform:uppercase;color:#c7d2fe}}
.mg-time{{font:11px ui-monospace;color:#64748b}}
.mg-kicker{{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
color:#94a3b8;margin-bottom:4px}}
.mg-display{{font-weight:700;line-height:1.25;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.35)}}
.mg-display-sm{{font-size:14px}} .mg-display-md{{font-size:18px}} .mg-display-lg{{font-size:22px}}
.mg-display-xl{{font-size:26px;letter-spacing:-.02em}}
.mg-italic{{font-style:italic;font-weight:600}}
.mg-accent{{text-decoration:underline;text-underline-offset:3px}}
.mg-meta{{margin-top:6px;font-size:12px;color:#cbd5e1;opacity:.85}}
.mg-steps{{margin:6px 0 0;padding-left:18px;color:#e2e8f0;font-size:13px}}
.mg-step{{margin:2px 0}}
.mg-note{{margin-top:6px;font-size:11px;color:#64748b;font-style:italic}}
.mg-evidence-img{{width:100%;margin-top:6px;border-radius:4px;border:1px solid #293242;
background:#080a0d;aspect-ratio:16/9;object-fit:cover}}
.mg-evidence-missing{{margin-top:6px;padding:16px;text-align:center;font:12px ui-monospace;
color:#64748b;background:#080a0d;border:1px dashed #334155;border-radius:4px}}
.mg-render-still{{display:block;width:100%;margin-top:6px;border-radius:4px;border:1px solid #293242;
aspect-ratio:16/9;object-fit:cover;background:#080a0d}}
.mg-render-badge{{font-size:10px;font-weight:700;text-transform:uppercase;color:#6ee7b7;
letter-spacing:.06em}}
.mg-mode-remotion .mg-panel{{border-left-color:#6ee7b7}}
.mg-banner{{margin-top:10px;padding:10px 12px;border-radius:8px;background:#101826;
border:1px solid #293242;font-size:14px}}
.mg-banner a{{color:#7dd3fc}}
.mg-banner-ok{{border-color:#065f46;background:#0f1f1a}}
.mg-banner-warn{{border-color:#92400e;background:#1f1710;color:#fcd34d}}
.cut-gap{{display:flex;align-items:center;gap:10px;grid-column:1/-1;margin:4px 0;
padding:10px 16px;border:1px dashed #7c3a2a;border-radius:8px;background:#1c1210;color:#fca5a5}}
.cut-gap-label{{font-weight:700;text-transform:uppercase;font-size:12px;letter-spacing:.06em}}
.cut-gap-span{{font:13px ui-monospace}} .cut-gap-dur{{font-size:13px;opacity:.9}}
.next-steps{{margin-top:12px;padding:10px 12px;border-radius:8px;background:#101826;
border:1px solid #293242;font-size:14px}}
</style></head>
<body><header>
<h1>{html.escape(title)}</h1>
<div class="meta">{range_count} keep range(s) · {keep_sec:.1f}s output
{compress_pct}
{f" · source {source_dur:.1f}s" if source_dur else ""}
· Plan <code>{html.escape(plan_label)}</code> <code>{digest}</code></div>
{_meta_stats_html(meta)}
{_cover_summary_html(cover)}
{_mg_review_banner_html(
    render_mg=render_mg,
    mg_render_mode=mg_render_mode,
    still_count=len(still_index),
    episode=episode,
)}
<div class="next-steps">After reviewing:
<code>ae edl-suggest . --apply</code> → <code>ae cut .</code> →
<code>ae cover .</code> → <code>ae storyboard . --render-mg</code> /
<code>ae compose . --studio</code></div>
</header>
<main>{cards_html}</main></body></html>"""

    output = dashboard / "index.html"
    output.write_text(page, encoding="utf-8")
    if open_browser:
        webbrowser.open(output.as_uri())
    print(f"Wrote {output}")
    return output
