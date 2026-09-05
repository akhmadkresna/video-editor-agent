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


#: Original left-rail kinds (Remotion OverlayLayer's OneOverlay) — same
#: white-ink, no-panel look as the kinds below, see
#: packages/remotion-kit/src/components/OverlayLayer.tsx.
_LEGACY_OVERLAY_KINDS = ("chapter", "emphasis", "diagram", "chip", "callout")
#: Kinds dispatched through the A-Roll Text Motion System
#: (packages/remotion-kit/src/components/overlay/dispatch.tsx) — white ink,
#: no panel, same palette as the kinds above, just a different primitive per
#: kind's structure. `code`/`illustration` stay on the legacy GlassOverlays.tsx
#: renderer (explicitly out of scope for the port).
_GLASS_OVERLAY_KINDS = (
    "title",
    "stat",
    "lower_third",
    "tag",
    "divider",
    "quote",
    "code",
    "illustration",
    # Added to TimelineOverlay/OverlayKind in the step-1 tokens commit but
    # never added here — silently dropped by collect_overlay_defs until now.
    "list_cycle",
)
_ALLOWED_OVERLAY_KINDS = _LEGACY_OVERLAY_KINDS + _GLASS_OVERLAY_KINDS


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
        if kind not in _ALLOWED_OVERLAY_KINDS:
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
        # "glass" kinds: tone (teal/amber/neutral — dashed vs solid border,
        # not a color) and title's accent (2nd-line highlighted phrase text,
        # not a style color). See glass/tokens.ts.
        tone = str(item.get("tone") or "").strip().lower()
        if tone in ("teal", "amber", "neutral"):
            entry["tone"] = tone
        accent = str(item.get("accent") or "").strip()
        if accent:
            entry["accent"] = accent
        zone = str(item.get("zone") or "").strip().lower()
        if zone in (
            "left_third",
            "right_third",
            "lower_raised",
            "top_sparse",
        ):
            entry["zone"] = zone
        # CalloutArrow target: [x, y] as 0-1 of frame. A `callout` carrying one
        # draws an arrow at that point; without it the beat falls back to a
        # PunchWord rather than rendering nothing.
        at = item.get("at")
        if (
            isinstance(at, (list, tuple))
            and len(at) == 2
            and all(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0 for v in at)
        ):
            entry["at"] = [float(at[0]), float(at[1])]
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


from agentic_editor.cover.cutaway_families import (
    BEAT_ALIASES,
    FAMILY_TO_SCENE,
    apply_cutaway_defaults,
    resolve_family,
    tighten_cutaway_motion,
)

CUTAWAY_SCENES = frozenset(FAMILY_TO_SCENE.values()) | frozenset(
    {
        "ledger_flow",
        "receipt_tape",
        "kinetic_figures",
        "blueprint_nodes",
        "evidence",
        "minimal",
    }
)

# Legacy + generic source cue keys → timeline *Sec fields.
_CUTAWAY_CUE_KEYS = {
    "ledgerIn": "ledgerInSec",
    "inOut": "inOutSec",
    "balance": "balanceSec",
    "lock": "lockSec",
    "stamp": "stampSec",
    "open": "openSec",
    "classify": "classifySec",
    "total": "totalSec",
    "resolve": "resolveSec",
}


def collect_cutaway_defs(cover: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Generated MG cutaway scenes live on cover.cutaways[] (cam source time)."""
    if not cover:
        return []
    out: list[dict[str, Any]] = []
    for i, item in enumerate(cover.get("cutaways") or []):
        if not isinstance(item, dict):
            continue
        family = resolve_family(item)
        if not family:
            continue
        scene = FAMILY_TO_SCENE.get(family, family)
        # Prefer explicit legacy scene when provided and still known.
        raw_scene = str(item.get("scene") or "").lower().strip()
        if raw_scene in CUTAWAY_SCENES:
            scene = raw_scene
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        entry: dict[str, Any] = {
            "id": str(item.get("id") or f"cut-{family}-{i}"),
            "family": family,
            "scene": scene,
            "start": start,
            "end": end,
            "source": str(item.get("source") or "cam"),
        }
        for key in (
            "style",
            "look",
            "intent",
            "tone",
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
        copy = item.get("copy")
        if isinstance(copy, dict):
            entry["copy"] = copy
            for ck, flat in (
                ("kicker", "kicker"),
                ("title", "title"),
                ("totalLabel", "balanceLabel"),
                ("lockLabel", "lockLabel"),
                ("stampLabel", "stampLabel"),
                ("inLabel", "inLabel"),
                ("outLabel", "outLabel"),
                ("openingLabel", "openingLabel"),
                ("footerLabel", "footerLabel"),
            ):
                if flat not in entry and copy.get(ck):
                    entry[flat] = str(copy[ck]).strip()
            labels = copy.get("attemptLabels")
            if isinstance(labels, list) and "attemptLabels" not in entry:
                entry["attemptLabels"] = [str(x) for x in labels if str(x).strip()]
        backdrop = item.get("backdrop")
        if isinstance(backdrop, dict) and backdrop.get("kind"):
            entry["backdrop"] = backdrop
        proof = item.get("proof")
        if isinstance(proof, dict) and str(proof.get("src") or "").strip():
            entry["proof"] = proof
        assets = item.get("assets")
        if isinstance(assets, list):
            cleaned = [
                a
                for a in assets
                if isinstance(a, dict) and str(a.get("src") or "").strip()
            ]
            if cleaned:
                entry["assets"] = cleaned
                if "proof" not in entry:
                    proof_like = next(
                        (
                            a
                            for a in cleaned
                            if str(a.get("role") or "") in ("proof", "hero", "")
                        ),
                        cleaned[0],
                    )
                    entry["proof"] = proof_like
        if item.get("openingBalance") is not None:
            try:
                entry["openingBalance"] = float(item["openingBalance"])
            except (TypeError, ValueError):
                pass
        labels = item.get("attemptLabels")
        if isinstance(labels, list):
            entry["attemptLabels"] = [str(x) for x in labels if str(x).strip()]

        # entities (preferred) or feeds (legacy)
        entities: list[dict[str, Any]] = []
        for e in item.get("entities") or []:
            if not isinstance(e, dict):
                continue
            try:
                ent = {
                    "label": str(e.get("label") or "").strip(),
                    "at": float(e["at"]),
                }
            except (KeyError, TypeError, ValueError):
                continue
            if e.get("value") is not None:
                try:
                    ent["value"] = float(e["value"])
                except (TypeError, ValueError):
                    pass
            elif e.get("amount") is not None:
                try:
                    ent["value"] = float(e["amount"])
                except (TypeError, ValueError):
                    pass
            for opt in ("id", "unit", "icon", "state"):
                if e.get(opt):
                    ent[opt] = e[opt]
            if isinstance(e.get("focus"), dict):
                ent["focus"] = e["focus"]
            if isinstance(e.get("asset"), dict) and e["asset"].get("src"):
                ent["asset"] = e["asset"]
            entities.append(ent)
        feeds: list[dict[str, Any]] = []
        for f in item.get("feeds") or []:
            if not isinstance(f, dict):
                continue
            try:
                feed = {
                    "label": str(f.get("label") or "").strip(),
                    "at": float(f["at"]),
                }
            except (KeyError, TypeError, ValueError):
                continue
            if f.get("amount") is not None:
                try:
                    feed["amount"] = float(f["amount"])
                except (TypeError, ValueError):
                    pass
            icon = str(f.get("icon") or "").strip()
            if icon:
                feed["icon"] = icon
            if f.get("unit"):
                feed["unit"] = str(f["unit"])
            if f.get("state"):
                feed["state"] = str(f["state"])
            if isinstance(f.get("focus"), dict):
                feed["focus"] = f["focus"]
            feeds.append(feed)
            if not entities:
                ent = {
                    "label": feed["label"],
                    "at": feed["at"],
                }
                if "amount" in feed:
                    ent["value"] = feed["amount"]
                if icon:
                    ent["icon"] = icon
                if feed.get("state"):
                    ent["state"] = feed["state"]
                if feed.get("focus"):
                    ent["focus"] = feed["focus"]
                entities.append(ent)
        if feeds:
            entry["feeds"] = feeds
        if entities:
            entry["entities"] = entities
            if "feeds" not in entry:
                entry["feeds"] = [
                    {
                        "label": e["label"],
                        "at": e["at"],
                        **({"amount": e["value"]} if "value" in e else {}),
                        **({"icon": e["icon"]} if e.get("icon") else {}),
                        **({"unit": e["unit"]} if e.get("unit") else {}),
                        **({"state": e["state"]} if e.get("state") else {}),
                        **({"focus": e["focus"]} if e.get("focus") else {}),
                    }
                    for e in entities
                ]

        beats = item.get("beats")
        if isinstance(beats, list):
            cleaned_beats = []
            for b in beats:
                if not isinstance(b, dict):
                    continue
                kind = str(b.get("kind") or "").strip()
                if not kind:
                    continue
                try:
                    cleaned_beats.append(
                        {
                            "kind": kind,
                            "at": float(b["at"]),
                            **(
                                {"label": str(b["label"]).strip()}
                                if b.get("label")
                                else {}
                            ),
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    continue
            if cleaned_beats:
                entry["beats"] = cleaned_beats

        cues = item.get("cues")
        if isinstance(cues, dict):
            entry["cues"] = cues
        apply_cutaway_defaults(entry)
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
            "family": cut["family"],
            "fromSec": round(from_sec, 3),
            "durationSec": round(dur, 3),
        }
        for key in (
            "style",
            "look",
            "intent",
            "tone",
            "backdrop",
            "proof",
            "assets",
            "copy",
            "kicker",
            "title",
            "inLabel",
            "outLabel",
            "lockLabel",
            "stampLabel",
            "balanceLabel",
            "attemptLabels",
            "openingBalance",
            "openingLabel",
            "footerLabel",
            "note",
        ):
            if key in cut:
                entry[key] = cut[key]

        def local(src_sec: float) -> float:
            return round(max(0.0, min(dur, float(src_sec) - start)), 3)

        feeds = []
        for f in cut.get("feeds") or []:
            feed: dict[str, Any] = {
                "label": f["label"],
                "atSec": local(f["at"]),
            }
            if "amount" in f:
                feed["amount"] = f["amount"]
            if f.get("icon"):
                feed["icon"] = f["icon"]
            if f.get("unit"):
                feed["unit"] = f["unit"]
            if f.get("state"):
                feed["state"] = f["state"]
            if f.get("focus"):
                feed["focus"] = f["focus"]
            feeds.append(feed)
        if feeds:
            entry["feeds"] = feeds

        entities = []
        for e in cut.get("entities") or []:
            ent: dict[str, Any] = {
                "label": e["label"],
                "atSec": local(e["at"]),
            }
            if e.get("id"):
                ent["id"] = e["id"]
            if "value" in e:
                ent["value"] = e["value"]
            if e.get("unit"):
                ent["unit"] = e["unit"]
            if e.get("icon"):
                ent["icon"] = e["icon"]
            if e.get("state"):
                ent["state"] = e["state"]
            if e.get("focus"):
                ent["focus"] = e["focus"]
            if e.get("asset"):
                ent["asset"] = e["asset"]
            entities.append(ent)
        if entities:
            entry["entities"] = entities

        beats_out = []
        for b in cut.get("beats") or []:
            beats_out.append(
                {
                    "kind": b["kind"],
                    "atSec": local(b["at"]),
                    **({"label": b["label"]} if b.get("label") else {}),
                }
            )
        if beats_out:
            entry["beats"] = beats_out

        raw_cues = cut.get("cues") or {}
        cues: dict[str, Any] = {}
        for src_key, out_key in _CUTAWAY_CUE_KEYS.items():
            if raw_cues.get(src_key) is None:
                continue
            try:
                cues[out_key] = local(float(raw_cues[src_key]))
            except (TypeError, ValueError):
                continue
        # Also mirror generic → legacy for existing Remotion skins.
        for gen, legacy in (
            ("openSec", "ledgerInSec"),
            ("classifySec", "inOutSec"),
            ("totalSec", "balanceSec"),
            ("resolveSec", "stampSec"),
        ):
            if gen in cues and legacy not in cues:
                cues[legacy] = cues[gen]
            if legacy in cues and gen not in cues:
                cues[gen] = cues[legacy]
        for list_key, out_key in (
            ("attempts", "attemptSec"),
            ("reject", "rejectSec"),
        ):
            raw_list = raw_cues.get(list_key)
            if not isinstance(raw_list, list):
                continue
            vals = []
            for a in raw_list:
                try:
                    vals.append(local(float(a)))
                except (TypeError, ValueError):
                    continue
            if vals:
                cues[out_key] = vals
        if "rejectSec" in cues and "attemptSec" not in cues:
            cues["attemptSec"] = cues["rejectSec"]
        if "attemptSec" in cues and "rejectSec" not in cues:
            cues["rejectSec"] = cues["attemptSec"]

        # Derive cues from beats[] when cues omitted.
        if beats_out and not cues:
            for b in beats_out:
                kind = str(b["kind"])
                out_key = BEAT_ALIASES.get(kind)
                if not out_key:
                    if kind in ("reveal", "open"):
                        out_key = "ledgerInSec"
                    elif kind == "resolve":
                        out_key = "stampSec"
                    else:
                        continue
                if out_key.endswith("Sec") and out_key != "attemptSec":
                    cues.setdefault(out_key, b["atSec"])
                elif out_key == "attemptSec":
                    cues.setdefault("attemptSec", []).append(b["atSec"])
            for gen, legacy in (
                ("openSec", "ledgerInSec"),
                ("classifySec", "inOutSec"),
                ("totalSec", "balanceSec"),
            ):
                if legacy in cues and gen not in cues:
                    cues[gen] = cues[legacy]

        if cues:
            entry["cues"] = cues
        tighten_cutaway_motion(entry)
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
    """Add ``stepAtSec`` cues; widen speech search past short cover windows.

    Shared by ``diagram`` and ``list_cycle`` — both are a fixed list of steps
    that should reveal in sync with when each one is actually said, not on a
    generic timer.
    """
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
        if ov.get("tone"):
            inst["tone"] = ov["tone"]
        if ov.get("accent"):
            inst["accent"] = ov["accent"]
        if ov.get("zone"):
            inst["zone"] = ov["zone"]
        # CalloutArrow's target, [x, y] as 0-1 of frame. Without this the field
        # is dropped here and the arrow renderer is unreachable — the handoff's
        # "no remap.py change needed" is wrong on this one point.
        at = ov.get("at")
        if (
            isinstance(at, (list, tuple))
            and len(at) == 2
            and all(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0 for v in at)
        ):
            inst["at"] = [float(at[0]), float(at[1])]
        if kind in ("diagram", "list_cycle") and ov.get("steps"):
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
    paper_max = float((cfg.get("paper") or {}).get("max_sec", 0.45))
    tick_max = float((cfg.get("tick") or {}).get("max_sec", 0.15))
    max_by_kind = {
        "shutter": shutter_max,
        "click": click_max,
        "paper": paper_max,
        "tick": tick_max,
    }
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
            end = start + max_by_kind.get(kind, click_max)
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
        if kind in max_by_kind:
            dur = min(dur, max_by_kind[kind])
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


def _normalize_privacy_rects(raw: Any) -> list[dict[str, float]]:
    """Clamp percent-of-frame rects; drop empty / invalid ones."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, float]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            x = float(item["x"])
            y = float(item["y"])
            w = float(item["w"])
            h = float(item["h"])
        except (KeyError, TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        out.append(
            {
                "x": max(0.0, min(100.0, x)),
                "y": max(0.0, min(100.0, y)),
                "w": max(0.5, min(100.0, w)),
                "h": max(0.5, min(100.0, h)),
            }
        )
    return out


DEFAULT_SCREEN_BLUR_RECT = {"x": 0.0, "y": 0.0, "w": 100.0, "h": 100.0}


def build_timeline_privacy(
    edl: dict[str, Any],
    cover: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Remap cover.privacy[] (source-time) → timeline.privacy[] (output fromSec).

    Exact duration through EDL — no dwell floor / collision trim (unlike MG overlays).
    Emits **one timeline entry per keep slice** so radio-edit gaps never leave
    a secret fragment unmasked.
    """
    if not cover:
        return []
    out: list[dict[str, Any]] = []
    for i, item in enumerate(cover.get("privacy") or []):
        if not isinstance(item, dict):
            continue
        mode = str(item.get("mode") or "bar").lower().strip()
        if mode not in {"bar", "screen_blur"}:
            mode = "bar"
        rects = _normalize_privacy_rects(item.get("rects"))
        if mode == "screen_blur" and not rects:
            rects = [dict(DEFAULT_SCREEN_BLUR_RECT)]
        if not rects:
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        slices = remap_source_window(
            edl, start, end, source=str(item.get("source") or "cam")
        )
        if not slices:
            continue
        base_id = str(item.get("id") or f"privacy-{i}")
        label = str(item["label"]) if item.get("label") else None
        note = str(item["note"]) if item.get("note") else None
        for j, sl in enumerate(slices):
            entry: dict[str, Any] = {
                "id": base_id if len(slices) == 1 else f"{base_id}-{j}",
                "fromSec": round(float(sl["fromSec"]), 3),
                "durationSec": round(max(0.05, float(sl["durationSec"])), 3),
                "rects": rects,
                "mode": mode,
            }
            if label:
                entry["label"] = label
            if note:
                entry["note"] = note
            out.append(entry)
    out.sort(key=lambda x: float(x["fromSec"]))
    return out
