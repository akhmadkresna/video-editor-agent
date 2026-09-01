"""Suggest modern-tech SFX from camera_play / cover / MG (no whoosh)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from agentic_editor.cover import _pick_base_framing
from agentic_editor.cover.style_load import load_sfx, sfx_pack_dir
from agentic_editor.cover.suggest import load_cam_words
from agentic_editor.editor.edl import load_edl
from agentic_editor.project import load_project

SFX_KINDS = frozenset({"typing", "shutter", "click", "paper", "tick"})
FORBIDDEN = frozenset({"whoosh", "riser", "swoosh", "whoosh_in", "whoosh_out"})

CLICK_DEIXIS = ("klik", "click", "tombol", "button")
TYPING_HINTS = (
    "code",
    "terminal",
    "seed",
    "cloud",
    "cursor",
    "python",
    "server",
    "action",
    "script",
    "prompt",
    "cli",
    "json",
    "yaml",
)

# Default MG → SFX kind (overridable via style sfx.mg). The original
# chapter/diagram/emphasis/chip kinds keep shutter/click; the kinds that
# used to carry a paper card (title/stat/lower_third/divider/quote/
# illustration/code) still default to "paper" on appear — a page-turn read
# well as an appear cue even after the card itself was dropped for the
# no-panel "Open Overlay" v7 look — except "tag", a small chip that reads
# better with a light "tick" than a full page sound.
DEFAULT_MG_KINDS = {
    "chapter": "shutter",
    "diagram": "shutter",
    "emphasis": "click",
    "chip": "click",
    "title": "paper",
    "stat": "paper",
    "lower_third": "paper",
    "divider": "paper",
    "quote": "paper",
    "illustration": "paper",
    "code": "paper",
    "tag": "tick",
}
MG_PRIORITY = {
    "chapter": 4,
    "diagram": 4,
    "emphasis": 3,
    "chip": 2,
    "title": 4,
    "stat": 3,
    "lower_third": 3,
    "divider": 4,
    "quote": 3,
    "illustration": 3,
    "code": 3,
    "tag": 2,
}


def _load_pack_yaml(pack_dir: Path) -> dict[str, Any]:
    path = pack_dir / "pack.yaml"
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_sfx_file(
    kind: str,
    *,
    style_name: str = "tutorial",
    bank_index: int = 0,
    explicit: str | None = None,
) -> str:
    """Return filename (basename) inside the framework SFX pack (``assets/sfx``)."""
    if explicit:
        name = Path(explicit).name
        if any(bad in name.lower() for bad in FORBIDDEN):
            raise ValueError(f"whoosh-like SFX forbidden: {name}")
        return name
    pack_dir = sfx_pack_dir(style_name)
    pack = _load_pack_yaml(pack_dir)
    kind_l = kind.lower()
    if kind_l not in SFX_KINDS:
        raise ValueError(f"unsupported sfx kind: {kind}")
    section = pack.get(kind_l) if isinstance(pack.get(kind_l), dict) else {}
    if kind_l == "click":
        files = section.get("files") if isinstance(section, dict) else None
        if isinstance(files, list) and files:
            return str(files[bank_index % len(files)])
        return f"click_{(bank_index % 4) + 1:02d}.wav"
    if kind_l == "shutter":
        return str((section or {}).get("file") or "shutter.wav")
    if kind_l == "paper":
        return str((section or {}).get("file") or "paper_page.wav")
    if kind_l == "tick":
        return str((section or {}).get("file") or "soft_tick.wav")
    return str((section or {}).get("file") or "typing-thock.wav")


def _keep_ranges(edl: dict[str, Any]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for r in edl.get("ranges") or []:
        if str(r.get("source") or "cam") != "cam":
            continue
        s, e = float(r["start"]), float(r["end"])
        if e > s:
            out.append((s, e))
    return out


def _in_keep(t: float, keeps: list[tuple[float, float]]) -> bool:
    return any(s <= t < e for s, e in keeps)


#: How far into a cut gap a candidate's nominal source-time can sit and
#: still get snapped to the nearest kept instant instead of being dropped.
#: Covers e.g. an intro tag/overlay authored at t=0 that lands before the
#: first kept range because the radio edit trimmed a leading silence —
#: the overlay itself still renders at output t=0 (its own remap is more
#: lenient), so its SFX would otherwise silently vanish for no reason
#: visible in cover.json. Kept small so this never yanks a genuinely
#: mid-video cut sound far from where it was actually authored.
_KEEP_SNAP_TOLERANCE_SEC = 3.0


def _snap_to_keep(
    t: float, keeps: list[tuple[float, float]], tolerance: float = _KEEP_SNAP_TOLERANCE_SEC
) -> float | None:
    """Return `t` if inside a kept range, else the nearest kept instant if
    within `tolerance`, else None (genuinely cut, don't relocate it)."""
    if not keeps:
        return None
    if _in_keep(t, keeps):
        return t
    best: float | None = None
    best_dist = tolerance
    for s, e in keeps:
        if t < s:
            dist = s - t
            candidate = s
        else:  # t >= e
            dist = t - e
            candidate = max(s, e - 1e-3)
        if dist <= best_dist:
            best_dist = dist
            best = candidate
    return best


def _clip_to_keep(
    start: float, end: float, keeps: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    slices: list[tuple[float, float]] = []
    for ks, ke in keeps:
        lo, hi = max(start, ks), min(end, ke)
        if hi > lo + 0.05:
            slices.append((lo, hi))
    return slices


def _word_hay_at(words: list[dict[str, Any]], start: float, end: float) -> str:
    parts: list[str] = []
    for w in words:
        ws, we = float(w["start"]), float(w["end"])
        if we < start or ws > end:
            continue
        parts.append(str(w.get("text") or "").lower())
    return " ".join(parts)


def _screen_intervals(events: list[dict[str, Any]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for e in events:
        kind = str(e.get("type") or "").lower()
        if kind not in ("screen_with_cam", "cam_pip", "screen", "screen_full"):
            continue
        try:
            s, en = float(e["start"]), float(e["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if en > s:
            out.append((s, en))
    return out


def suggest_sfx(episode: Path) -> dict[str, Any]:
    """Build sfx suggestion from cover events + overlays + cam words."""
    episode = Path(episode)
    cfg = load_project(episode)
    style_name = str(cfg.get("style") or "tutorial")
    sfx_cfg = load_sfx(style_name)
    if not bool(sfx_cfg.get("enabled", True)):
        return {"sfx": [], "_meta": {"enabled": False, "style": style_name}}

    dens = sfx_cfg.get("density") or {}
    min_gap = float(dens.get("min_gap_sec", 1.2))
    shutter_click_gap = float(dens.get("shutter_click_min_gap_sec", 0.4))
    typing_merge = float(dens.get("typing_merge_gap_sec", 1.5))
    typing_cfg = sfx_cfg.get("typing") or {}
    typing_enabled = bool(typing_cfg.get("enabled", False))
    typing_min = float(typing_cfg.get("min_hold_sec", 4.0))
    shutter_max = float((sfx_cfg.get("shutter") or {}).get("max_sec", 0.22))
    click_max = float((sfx_cfg.get("click") or {}).get("max_sec", 0.18))
    paper_max = float((sfx_cfg.get("paper") or {}).get("max_sec", 0.45))
    tick_max = float((sfx_cfg.get("tick") or {}).get("max_sec", 0.15))
    max_by_kind = {
        "shutter": shutter_max,
        "click": click_max,
        "paper": paper_max,
        "tick": tick_max,
    }
    vols = sfx_cfg.get("volumes") or {}
    mg_cfg = sfx_cfg.get("mg") or {}
    mg_enabled = bool(mg_cfg.get("enabled", True))

    edl_path = episode / "edit" / "edl.json"
    if not edl_path.is_file():
        return {"sfx": [], "_meta": {"error": "missing edl.json"}}
    edl = load_edl(edl_path)
    keeps = _keep_ranges(edl)
    keep_dur = sum(e - s for s, e in keeps)

    cover_path = episode / "edit" / "cover.json"
    cover: dict[str, Any] = {}
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
    from agentic_editor.cover.composite import effective_camera_play, is_camera_play_enabled

    camera_play = effective_camera_play(cover, cfg)
    play_enabled = is_camera_play_enabled(camera_play)
    events = list(cover.get("events") or [])
    overlays = list(cover.get("overlays") or [])
    screens = _screen_intervals(events)
    words = load_cam_words(episode / "edit")

    candidates: list[dict[str, Any]] = []
    click_i = 0

    for ev in events:
        kind = str(ev.get("type") or "").lower()
        try:
            start_raw = float(ev["start"])
        except (KeyError, TypeError, ValueError):
            continue
        start = _snap_to_keep(start_raw, keeps)
        if start is None:
            continue
        if kind in ("punch_in", "punch") and play_enabled:
            candidates.append(
                {
                    "kind": "shutter",
                    "start": start,
                    "end": start + shutter_max,
                    "note": "punch",
                    "priority": 3,
                }
            )
        elif (
            play_enabled
            and kind == "framing"
            and str(ev.get("motion") or "").lower() == "snap"
        ):
            candidates.append(
                {
                    "kind": "shutter",
                    "start": start,
                    "end": start + shutter_max,
                    "note": "framing_snap",
                    "priority": 2,
                }
            )

    # Shutter marks a *zoom* cut, not every cut — only fire when the fake-
    # multicam framing actually lands on "close" or "wide" (a reset), same
    # alternation logic the real render uses (_pick_base_framing), so a cut
    # that just snaps between two "medium" home shots stays silent.
    camera_play = cover.get("camera_play") or {}
    cam_ranges = [
        (float(r["start"]), float(r["end"]), str(r.get("note") or ""))
        for r in edl.get("ranges") or []
        if str(r.get("source") or "cam") == "cam" and float(r["end"]) > float(r["start"])
    ]
    if play_enabled and bool(camera_play.get("snap_on_cuts", True)) and len(cam_ranges) > 1:
        for idx, (ks, _ke, note) in enumerate(cam_ranges):
            if idx == 0 or not _in_keep(ks, keeps):
                continue
            framing, motion = _pick_base_framing(
                range_index=idx, note=note, camera_play=camera_play
            )
            if motion not in ("snap", "ease") or framing not in ("close", "wide"):
                continue
            candidates.append(
                {
                    "kind": "shutter",
                    "start": ks,
                    "end": ks + shutter_max,
                    "note": f"cut_snap_{framing}",
                    "priority": 1,
                }
            )

    for s, _e in screens:
        snapped = _snap_to_keep(s, keeps)
        if snapped is not None:
            candidates.append(
                {
                    "kind": "click",
                    "start": snapped,
                    "end": snapped + click_max,
                    "note": "screen_enter",
                    "priority": 2,
                    "bank": click_i,
                }
            )
            click_i += 1

    for w in words:
        token = str(w.get("text") or "").lower().strip()
        if not token or not any(d in token for d in CLICK_DEIXIS):
            continue
        ws = float(w["start"])
        if not _in_keep(ws, keeps):
            continue
        candidates.append(
            {
                "kind": "click",
                "start": ws,
                "end": ws + click_max,
                "note": f"deixis:{token}",
                "priority": 3,
                "bank": click_i,
            }
        )
        click_i += 1

    if mg_enabled:
        for ov in overlays:
            if not isinstance(ov, dict):
                continue
            ov_kind = str(ov.get("kind") or "").lower().strip()
            if ov_kind not in DEFAULT_MG_KINDS:
                continue
            sfx_kind = str(mg_cfg.get(ov_kind) or DEFAULT_MG_KINDS[ov_kind]).lower()
            if sfx_kind not in SFX_KINDS or sfx_kind == "typing":
                continue
            try:
                start_raw = float(ov["start"])
            except (KeyError, TypeError, ValueError):
                continue
            start = _snap_to_keep(start_raw, keeps)
            if start is None:
                continue
            dur = max_by_kind.get(sfx_kind, click_max)
            entry: dict[str, Any] = {
                "kind": sfx_kind,
                "start": start,
                "end": start + dur,
                "note": f"mg_{ov_kind}",
                "priority": int(MG_PRIORITY.get(ov_kind, 3)),
            }
            if sfx_kind == "click":
                entry["bank"] = click_i
                click_i += 1
            candidates.append(entry)

    if typing_enabled:
        for s, e in screens:
            for lo, hi in _clip_to_keep(s, e, keeps):
                if hi - lo < typing_min:
                    continue
                blob = _word_hay_at(words, lo, hi)
                if not any(h in blob for h in TYPING_HINTS):
                    has_diagram = any(
                        str(o.get("kind") or "").lower() == "diagram"
                        and float(o.get("start", -1)) < hi
                        and float(o.get("end", -1)) > lo
                        for o in overlays
                        if isinstance(o, dict)
                    )
                    if not has_diagram:
                        continue
                candidates.append(
                    {
                        "kind": "typing",
                        "start": lo,
                        "end": hi,
                        "note": "screen_demo",
                        "priority": 1,
                    }
                )

        typing = [c for c in candidates if c["kind"] == "typing"]
        others = [c for c in candidates if c["kind"] != "typing"]
        typing.sort(key=lambda c: float(c["start"]))
        merged_typing: list[dict[str, Any]] = []
        for c in typing:
            if (
                merged_typing
                and float(c["start"]) <= float(merged_typing[-1]["end"]) + typing_merge
            ):
                merged_typing[-1]["end"] = max(
                    float(merged_typing[-1]["end"]), float(c["end"])
                )
            else:
                merged_typing.append(dict(c))
        candidates = others + merged_typing

    candidates.sort(key=lambda c: (-int(c.get("priority", 0)), float(c["start"])))
    accepted: list[dict[str, Any]] = []

    def conflicts(a: dict[str, Any], b: dict[str, Any]) -> bool:
        as_, ae = float(a["start"]), float(a["end"])
        bs, be = float(b["start"]), float(b["end"])
        gap = max(0.0, max(bs - ae, as_ - be))
        overlap = as_ < be and bs < ae
        if overlap:
            if {a["kind"], b["kind"]} == {"shutter", "click"}:
                return True
            if a["kind"] == b["kind"] == "typing":
                return True
            if a["kind"] != "typing" and b["kind"] != "typing":
                return True
            return False
        if gap < min_gap and a["kind"] != "typing" and b["kind"] != "typing":
            return True
        if {a["kind"], b["kind"]} == {"shutter", "click"} and gap < shutter_click_gap:
            return True
        return False

    for c in candidates:
        if any(conflicts(c, a) for a in accepted):
            continue
        accepted.append(c)

    accepted.sort(key=lambda c: float(c["start"]))

    out_sfx: list[dict[str, Any]] = []
    for i, c in enumerate(accepted):
        kind = str(c["kind"])
        bank = int(c.get("bank") or i)
        src = resolve_sfx_file(kind, style_name=style_name, bank_index=bank)
        start = round(float(c["start"]), 3)
        end = round(float(c["end"]), 3)
        if end <= start:
            end = start + (shutter_max if kind == "shutter" else click_max)
        out_sfx.append(
            {
                "id": f"sfx-{kind}-{i}",
                "kind": kind,
                "start": start,
                "end": end,
                "src": src,
                "volume": float(vols.get(kind, 0.4)),
                "note": f"suggest:{c.get('note') or kind}",
            }
        )

    return {
        "sfx": out_sfx,
        "_meta": {
            "enabled": True,
            "style": style_name,
            "no_whoosh": True,
            "typing_enabled": typing_enabled,
            "mg_enabled": mg_enabled,
            "keep_sec": round(keep_dur, 2),
            "counts": {
                "total": len(out_sfx),
                "typing": sum(1 for s in out_sfx if s["kind"] == "typing"),
                "shutter": sum(1 for s in out_sfx if s["kind"] == "shutter"),
                "click": sum(1 for s in out_sfx if s["kind"] == "click"),
                "paper": sum(1 for s in out_sfx if s["kind"] == "paper"),
                "tick": sum(1 for s in out_sfx if s["kind"] == "tick"),
            },
            "candidates": len(candidates),
        },
    }


def write_sfx_suggest(episode: Path, suggestion: dict[str, Any]) -> Path:
    episode = Path(episode)
    out = episode / "edit" / "sfx.suggest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(suggestion, indent=2) + "\n", encoding="utf-8")
    return out


def merge_sfx_into_cover(
    cover: dict[str, Any],
    suggested: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace prior suggest:* entries; keep hand-authored notes."""
    kept: list[dict[str, Any]] = []
    for item in cover.get("sfx") or []:
        if not isinstance(item, dict):
            continue
        note = str(item.get("note") or "").lower()
        if note.startswith("suggest:"):
            continue
        kept.append(item)
    return kept + list(suggested)
