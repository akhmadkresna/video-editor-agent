"""Map cam (source) time windows onto the radio-edit output timeline."""

from __future__ import annotations

from typing import Any

# Prefer slices at least this long; sole short slices are still kept.
_MIN_PREFERRED_SLICE = 0.5


def edl_keep_duration_sec(edl: dict[str, Any]) -> float:
    """Total output duration of all EDL keep ranges."""
    total = 0.0
    for r in edl.get("ranges") or []:
        total += max(0.0, float(r["end"]) - float(r["start"]))
    return total


def remap_source_window(
    edl: dict[str, Any],
    start: float,
    end: float,
    *,
    source: str = "cam",
) -> list[dict[str, float]]:
    """
    Return kept slices of [start, end) as output-timeline segments:
      [{fromSec, durationSec}, ...]
    Only EDL ranges whose source matches `source` contribute.
    """
    if end <= start:
        return []
    out: list[dict[str, float]] = []
    out_t = 0.0
    for r in edl.get("ranges") or []:
        rs = float(r["start"])
        re = float(r["end"])
        dur = max(0.0, re - rs)
        if str(r.get("source") or "cam") != source:
            out_t += dur
            continue
        ov_s = max(start, rs)
        ov_e = min(end, re)
        if ov_e > ov_s + 1e-4:
            local = ov_s - rs
            out.append(
                {
                    "fromSec": out_t + local,
                    "durationSec": ov_e - ov_s,
                }
            )
        out_t += dur
    return out


def collect_overlay_defs(cover: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Overlay creatives live on cover.overlays[] (preferred)."""
    if not cover:
        return []
    raw = cover.get("overlays") or []
    out: list[dict[str, Any]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or item.get("type") or "").lower().strip()
        if kind not in ("chapter", "emphasis", "diagram", "chip", "callout"):
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        entry = {
            "id": str(item.get("id") or f"ov-{kind}-{i}"),
            "kind": kind,
            "start": start,
            "end": end,
            "source": str(item.get("source") or "cam"),
            "text": str(item.get("text") or "").strip(),
            "kicker": str(item.get("kicker") or "").strip() or None,
            "title": str(item.get("title") or "").strip() or None,
            "note": str(item.get("note") or "").strip() or None,
        }
        steps = item.get("steps")
        if isinstance(steps, list):
            entry["steps"] = [str(s).strip() for s in steps if str(s).strip()]
        value = str(item.get("value") or "").strip()
        if value:
            entry["value"] = value
        source_label = str(
            item.get("sourceLabel") or item.get("source_label") or ""
        ).strip()
        if source_label:
            entry["sourceLabel"] = source_label
        # Optional manual source-time cues for diagram steps (cam seconds).
        raw_starts = item.get("stepStarts") or item.get("step_starts")
        if isinstance(raw_starts, list):
            starts: list[float] = []
            for x in raw_starts:
                try:
                    starts.append(float(x))
                except (TypeError, ValueError):
                    continue
            if starts:
                entry["stepStarts"] = starts
        out.append(entry)
    return out


CUTAWAY_SCENES = frozenset({"ledger_flow"})

_CUTAWAY_CUE_KEYS = {
    "ledgerIn": "ledgerInSec",
    "inOut": "inOutSec",
    "balance": "balanceSec",
    "lock": "lockSec",
    "stamp": "stampSec",
}


def collect_cutaway_defs(cover: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Generated MG cutaway scenes live on cover.cutaways[] (cam source time)."""
    if not cover:
        return []
    out: list[dict[str, Any]] = []
    for i, item in enumerate(cover.get("cutaways") or []):
        if not isinstance(item, dict):
            continue
        scene = str(item.get("scene") or "").lower().strip()
        if scene not in CUTAWAY_SCENES:
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        entry: dict[str, Any] = {
            "id": str(item.get("id") or f"cut-{scene}-{i}"),
            "scene": scene,
            "start": start,
            "end": end,
            "source": str(item.get("source") or "cam"),
        }
        for key in (
            "kicker",
            "title",
            "inLabel",
            "outLabel",
            "lockLabel",
            "stampLabel",
            "balanceLabel",
            "note",
        ):
            val = str(item.get(key) or "").strip()
            if val:
                entry[key] = val
        if item.get("openingBalance") is not None:
            try:
                entry["openingBalance"] = float(item["openingBalance"])
            except (TypeError, ValueError):
                pass
        labels = item.get("attemptLabels")
        if isinstance(labels, list):
            entry["attemptLabels"] = [str(x) for x in labels if str(x).strip()]
        feeds: list[dict[str, Any]] = []
        for f in item.get("feeds") or []:
            if not isinstance(f, dict):
                continue
            try:
                feeds.append(
                    {
                        "label": str(f.get("label") or "").strip(),
                        "amount": float(f["amount"]),
                        "at": float(f["at"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        if feeds:
            entry["feeds"] = feeds
        cues = item.get("cues")
        if isinstance(cues, dict):
            entry["cues"] = cues
        out.append(entry)
    return out


def build_timeline_cutaways(
    edl: dict[str, Any],
    cover: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Remap cover.cutaways[] to output time; cues become scene-local seconds.

    Scene beats are authored in cam source seconds (word-snapped, like
    overlays) and converted to offsets from the scene start so a Remotion
    scene never needs to know about the EDL.
    """
    timeline_dur = edl_keep_duration_sec(edl)
    out: list[dict[str, Any]] = []
    for cut in collect_cutaway_defs(cover):
        source = str(cut.get("source") or "cam")
        start = float(cut["start"])
        slices = remap_source_window(edl, start, float(cut["end"]), source=source)
        sl = _pick_best_slice(slices)
        if sl is None:
            continue
        from_sec = float(sl["fromSec"])
        dur = min(float(sl["durationSec"]), max(0.05, timeline_dur - from_sec))
        entry: dict[str, Any] = {
            "id": cut["id"],
            "scene": cut["scene"],
            "fromSec": round(from_sec, 3),
            "durationSec": round(dur, 3),
        }
        for key in (
            "kicker",
            "title",
            "inLabel",
            "outLabel",
            "lockLabel",
            "stampLabel",
            "balanceLabel",
            "attemptLabels",
            "openingBalance",
            "note",
        ):
            if key in cut:
                entry[key] = cut[key]
        # Source-time cue → local second inside the scene.
        def local(src_sec: float) -> float:
            return round(max(0.0, min(dur, float(src_sec) - start)), 3)

        feeds = []
        for f in cut.get("feeds") or []:
            feeds.append(
                {
                    "label": f["label"],
                    "amount": f["amount"],
                    "atSec": local(f["at"]),
                }
            )
        if feeds:
            entry["feeds"] = feeds
        raw_cues = cut.get("cues") or {}
        cues: dict[str, Any] = {}
        for src_key, out_key in _CUTAWAY_CUE_KEYS.items():
            if raw_cues.get(src_key) is None:
                continue
            try:
                cues[out_key] = local(float(raw_cues[src_key]))
            except (TypeError, ValueError):
                continue
        attempts = raw_cues.get("attempts")
        if isinstance(attempts, list):
            vals = []
            for a in attempts:
                try:
                    vals.append(local(float(a)))
                except (TypeError, ValueError):
                    continue
            if vals:
                cues["attemptSec"] = vals
        if cues:
            entry["cues"] = cues
        out.append(entry)
    out.sort(key=lambda x: float(x["fromSec"]))
    return out


def _pick_best_slice(slices: list[dict[str, float]]) -> dict[str, float] | None:
    """One instance per overlay: longest preferred slice; sole short slice kept."""
    if not slices:
        return None
    preferred = [s for s in slices if float(s["durationSec"]) >= _MIN_PREFERRED_SLICE]
    pool = preferred if preferred else slices
    return max(pool, key=lambda s: float(s["durationSec"]))


def _attach_diagram_step_motion(
    inst: dict[str, Any],
    ov: dict[str, Any],
    *,
    edl: dict[str, Any],
    words: list[dict[str, Any]] | None,
    dwell: dict[str, Any] | None = None,
) -> None:
    """Add ``stepAtSec`` cues; widen speech search past short cover windows."""
    steps = list(ov.get("steps") or [])
    if not steps:
        return
    from agentic_editor.cover.diagram_motion import (
        align_diagram_step_source_times,
        even_step_at_sec,
        source_steps_to_relative,
    )
    from agentic_editor.cover.overlay_schedule import DEFAULT_DWELL, diagram_floor

    d = {**DEFAULT_DWELL, **(dwell or {})}
    src = str(ov.get("source") or "cam")
    ov_s = float(ov["start"])
    ov_e = float(ov["end"])
    # Short cover windows cramped lists — search ahead in transcript for spoken steps.
    search_end = max(
        ov_e,
        ov_s + diagram_floor(len(steps), d),
        ov_e + float(d["diagram_search_pad_sec"]),
    )
    dur = float(inst["durationSec"])
    from_sec = float(inst["fromSec"])

    manual = ov.get("stepStarts")
    if isinstance(manual, list) and len(manual) >= len(steps):
        src_times = [float(manual[i]) for i in range(len(steps))]
        inst["stepMotion"] = "manual"
    elif words:
        src_times = align_diagram_step_source_times(
            steps,
            words,
            overlay_start=ov_s,
            overlay_end=search_end,
            lead_in_sec=0.55,
            min_gap_sec=0.65,
        )
        inst["stepMotion"] = "speech"
    else:
        # Provisional duration for even stagger; hold pass extends later.
        prov = max(dur, diagram_floor(len(steps), d))
        inst["stepAtSec"] = even_step_at_sec(len(steps), prov, lead_in_sec=0.55)
        inst["stepMotion"] = "even"
        return

    rel = source_steps_to_relative(
        src_times,
        overlay_source_start=ov_s,
        slice_from_sec=from_sec,
        edl=edl,
        source=src,
    )
    # Provisional clamp — finalize_overlays enforces hold-after + exitStartSec.
    hold = float(d["diagram_hold_after_last_sec"])
    need = (rel[-1] + hold) if rel else dur
    if need > dur:
        inst["durationSec"] = need
        dur = need
    max_step = max(0.25, dur - hold)
    clamped = [min(max(0.12, float(t)), max_step) for t in rel]
    for i in range(1, len(clamped)):
        if clamped[i] < clamped[i - 1] + 0.25:
            clamped[i] = min(max_step, clamped[i - 1] + 0.25)
    inst["stepAtSec"] = clamped


def build_timeline_overlays(
    edl: dict[str, Any],
    cover: dict[str, Any] | None,
    *,
    words: list[dict[str, Any]] | None = None,
    dwell: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Expand cover.overlays (source time) into timeline.overlays (output time).

    Diagram steps get ``stepAtSec`` cues aligned to cam transcript phrases when
    ``words`` is provided (sentence-level reveal, not per-word karaoke).
    Durations are finalized with hold-after-last + structure collision trims.
    """
    from agentic_editor.cover.overlay_schedule import (
        diagram_floor,
        dwell_for,
        finalize_overlays,
    )

    timeline_dur = edl_keep_duration_sec(edl)
    instances: list[dict[str, Any]] = []
    for ov in collect_overlay_defs(cover):
        slices = remap_source_window(
            edl,
            float(ov["start"]),
            float(ov["end"]),
            source=str(ov.get("source") or "cam"),
        )
        sl = _pick_best_slice(slices)
        if sl is None:
            continue
        kind = str(ov.get("kind") or "")
        n_steps = len(ov.get("steps") or []) if kind == "diagram" else 0
        floor = (
            diagram_floor(n_steps, dwell)
            if kind == "diagram"
            else dwell_for(kind, dwell)
        )
        remaining = max(0.05, timeline_dur - float(sl["fromSec"]))
        dur = min(max(float(sl["durationSec"]), floor), remaining)
        inst: dict[str, Any] = {
            "id": ov["id"],
            "kind": ov["kind"],
            "fromSec": sl["fromSec"],
            "durationSec": dur,
            "text": ov.get("text") or "",
        }
        if ov.get("kicker"):
            inst["kicker"] = ov["kicker"]
        if ov.get("title"):
            inst["title"] = ov["title"]
        if ov.get("steps"):
            inst["steps"] = ov["steps"]
        if ov.get("note"):
            inst["note"] = ov["note"]
        if ov.get("value"):
            inst["value"] = ov["value"]
        if ov.get("sourceLabel"):
            inst["sourceLabel"] = ov["sourceLabel"]
        if kind == "diagram" and ov.get("steps"):
            _attach_diagram_step_motion(
                inst, ov, edl=edl, words=words, dwell=dwell
            )
            # Clamp extended duration to timeline end
            inst["durationSec"] = min(
                float(inst["durationSec"]),
                max(0.05, timeline_dur - float(inst["fromSec"])),
            )
        instances.append(inst)
    return finalize_overlays(instances, timeline_dur=timeline_dur, dwell=dwell)


def build_timeline_sfx(
    edl: dict[str, Any],
    cover: dict[str, Any] | None,
    *,
    style_name: str = "tutorial",
    sfx_cfg: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Remap cover.sfx[] (source-time) → timeline.sfx[] (output fromSec)."""
    from agentic_editor.cover.sfx_suggest import SFX_KINDS, FORBIDDEN, resolve_sfx_file
    from agentic_editor.cover.style_load import load_sfx

    if not cover:
        return []
    cfg = sfx_cfg or load_sfx(style_name)
    if not bool(cfg.get("enabled", True)):
        return []
    vols = cfg.get("volumes") or {}
    shutter_max = float((cfg.get("shutter") or {}).get("max_sec", 0.22))
    click_max = float((cfg.get("click") or {}).get("max_sec", 0.18))
    out: list[dict[str, Any]] = []
    for i, item in enumerate(cover.get("sfx") or []):
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").lower().strip()
        if kind in FORBIDDEN or kind not in SFX_KINDS:
            continue
        try:
            start = float(item["start"])
        except (KeyError, TypeError, ValueError):
            continue
        end_raw = item.get("end")
        if end_raw is None:
            end = start + (shutter_max if kind == "shutter" else click_max)
        else:
            try:
                end = float(end_raw)
            except (TypeError, ValueError):
                continue
        if end <= start:
            continue
        slices = remap_source_window(edl, start, end, source=str(item.get("source") or "cam"))
        sl = _pick_best_slice(slices)
        if not sl:
            continue
        src_name = resolve_sfx_file(
            kind,
            style_name=style_name,
            bank_index=i,
            explicit=str(item["src"]) if item.get("src") else None,
        )
        dur = float(sl["durationSec"])
        if kind in ("shutter", "click"):
            max_sec = shutter_max if kind == "shutter" else click_max
            dur = min(dur, max_sec)
        entry: dict[str, Any] = {
            "id": str(item.get("id") or f"sfx-{kind}-{i}"),
            "kind": kind,
            "fromSec": round(float(sl["fromSec"]), 3),
            "durationSec": round(max(0.05, dur), 3),
            "src": f"ae-media/sfx/{src_name}",
            "volume": float(item.get("volume") if item.get("volume") is not None else vols.get(kind, 0.4)),
            "tile": kind == "typing",
        }
        if item.get("note"):
            entry["note"] = str(item["note"])
        out.append(entry)
    out.sort(key=lambda x: float(x["fromSec"]))
    return out
