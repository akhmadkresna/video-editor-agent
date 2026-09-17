"""Timeline -> HyperFrames composition templating.

Remotion got its per-episode structure (which clips, in what order, with
what overlays/captions/cutaways/mockups) via `--props timeline.json` at
render time, and React re-rendered its component tree from that data.
HyperFrames has no equivalent live-props system for structural/array data
-- only scalar `data-composition-variables`. So this module materializes
`timeline.json` as repeated HTML markup at *generation* time, per
`remotion-to-hyperframes/references/parameters.md`'s "Nested object / array
props" guidance, producing one `index.html` HyperFrames composition per
episode.

This is a clean rebuild, not a pixel-accurate port: HyperFrames' own
GSAP/CSS primitives express the same *roles* the old Remotion layers played
(camera drift/pull_back, burned-in captions, the A-Roll Text Motion System
overlay kinds, cutaway explainer graphics, screen-recording mockups) rather
than reproducing each React component 1:1. See MIGRATION_NOTES.md at the
repo root for the specific simplifications made per family.
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path
from typing import Any

from agentic_editor.paths import framework_home

# ─────────────────────────── small helpers ───────────────────────────


def _esc(text: Any) -> str:
    return _html.escape(str(text if text is not None else ""), quote=True)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class _Doc:
    """Accumulates body markup + main-timeline GSAP statements."""

    def __init__(self) -> None:
        self.body: list[str] = []
        self.tl: list[str] = []
        self._ids: set[str] = set()

    def uid(self, base: str) -> str:
        cand = base
        n = 2
        while cand in self._ids:
            cand = f"{base}-{n}"
            n += 1
        self._ids.add(cand)
        return cand


# ─────────────────────────── camera / clips ───────────────────────────

# Old Remotion `drift`: ~1.5%/sec push-in, clamped 5-15%, Sine in/out.
_DRIFT_RATE_PER_SEC = 0.015
_DRIFT_MIN = 1.05
_DRIFT_MAX = 1.15

_LAYOUT_CLASS = {
    "full": "layout-full",
    "float_centered": "layout-float",
    "pip_corner": "layout-pip",
    "stack_top": "layout-stack-top",
    "stack_bottom": "layout-stack-bottom",
}


def _clip_asset(clip: dict[str, Any], asset_map: dict[str, str]) -> str:
    source = str(clip.get("source") or "cam")
    return asset_map.get(source, f"assets/{source}.mp4")


def _emit_clip(doc: _Doc, clip: dict[str, Any], asset_map: dict[str, str], track_offset: int) -> None:
    cid = doc.uid(str(clip.get("id") or "clip"))
    start = _num(clip.get("fromSec"))
    dur = max(0.05, _num(clip.get("durationSec"), 0.05))
    media_start = _num(clip.get("sourceIn"))
    layout = str(clip.get("layout") or "full")
    layout_cls = _LAYOUT_CLASS.get(layout, "layout-full")
    track_index = track_offset + (0 if str(clip.get("track")) == "a_roll" else 5)
    muted_source = bool(clip.get("muted"))
    src = _clip_asset(clip, asset_map)

    doc.body.append(
        f'<video id="{cid}" class="clip cam-clip {layout_cls}" src="{_esc(src)}" '
        f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-media-start="{media_start:.3f}" '
        f'data-track-index="{track_index}" muted playsinline></video>'
    )
    if not muted_source:
        aid = doc.uid(f"{cid}-audio")
        doc.body.append(
            f'<audio id="{aid}" src="{_esc(src)}" data-start="{start:.3f}" '
            f'data-duration="{dur:.3f}" data-media-start="{media_start:.3f}" '
            f'data-track-index="{track_index + 20}"></audio>'
        )

    motion = str(clip.get("motion") or "hold")
    sel = f'"#{cid}"'
    if motion == "drift" and layout == "full":
        peak = _clamp(1.0 + dur * _DRIFT_RATE_PER_SEC, _DRIFT_MIN, _DRIFT_MAX)
        doc.tl.append(f'tl.set({sel}, {{ scale: 1 }}, {start:.3f});')
        doc.tl.append(
            f'tl.to({sel}, {{ scale: {peak:.4f}, duration: {dur:.3f}, '
            f'ease: "sine.inOut", overwrite: "auto" }}, {start:.3f});'
        )
    elif motion == "pull_back" and layout == "full":
        peak = _clamp(1.0 + dur * _DRIFT_RATE_PER_SEC, _DRIFT_MIN, _DRIFT_MAX)
        doc.tl.append(f'tl.set({sel}, {{ scale: {peak:.4f} }}, {start:.3f});')
        doc.tl.append(
            f'tl.to({sel}, {{ scale: 1, duration: {dur:.3f}, '
            f'ease: "sine.inOut", overwrite: "auto" }}, {start:.3f});'
        )
    elif motion in ("ease_in", "ease"):
        scale = _num(clip.get("scale"), 1.0)
        doc.tl.append(f'tl.set({sel}, {{ scale: 1 }}, {start:.3f});')
        doc.tl.append(
            f'tl.to({sel}, {{ scale: {scale:.4f}, duration: {min(dur, 0.6):.3f}, '
            f'ease: "sine.out", overwrite: "auto" }}, {start:.3f});'
        )
    elif motion == "ease_out":
        scale = _num(clip.get("scale"), 1.0)
        doc.tl.append(f'tl.set({sel}, {{ scale: {scale:.4f} }}, {start:.3f});')
        doc.tl.append(
            f'tl.to({sel}, {{ scale: 1, duration: {min(dur, 0.6):.3f}, '
            f'ease: "sine.in", overwrite: "auto" }}, {max(start, start + dur - 0.6):.3f});'
        )
    # hold / snap: static framing, no tween.


def _emit_punch_effects(doc: _Doc, effects: list[dict[str, Any]], clips: list[dict[str, Any]]) -> None:
    """Manual punch_in/punch_out events layered on whichever clip is on screen.

    Only applied to clips holding a static frame (`hold`/`snap`): a clip
    already carrying its own drift/pull_back/ease camera move owns the
    `scale` property for its whole span, so stacking a second tween on the
    same property there would fight it (lint: overlapping_gsap_tweens).
    """
    for i, eff in enumerate(effects):
        start = _num(eff.get("fromSec"))
        dur = max(0.05, _num(eff.get("durationSec"), 0.3))
        scale = _num(eff.get("scale"), 1.3)
        kind = str(eff.get("type") or "punch_in")
        host = None
        for clip in clips:
            cs = _num(clip.get("fromSec"))
            ce = cs + _num(clip.get("durationSec"))
            motion = str(clip.get("motion") or "hold")
            if cs <= start < ce and str(clip.get("layout")) == "full" and motion in ("hold", "snap"):
                host = clip
                break
        if host is None:
            continue
        cid = str(host.get("id") or "clip")
        sel = f'"#{cid}"'
        if kind == "punch_out":
            doc.tl.append(f'tl.set({sel}, {{ scale: {scale:.4f} }}, {start:.3f});')
            doc.tl.append(
                f'tl.to({sel}, {{ scale: 1, duration: {dur:.3f}, ease: "power2.out", overwrite: "auto" }}, {start:.3f});'
            )
        else:
            doc.tl.append(f'tl.set({sel}, {{ scale: 1 }}, {start:.3f});')
            doc.tl.append(
                f'tl.to({sel}, {{ scale: {scale:.4f}, duration: {dur:.3f}, ease: "power2.out", overwrite: "auto" }}, {start:.3f});'
            )


# ─────────────────────────── captions ───────────────────────────


def _emit_caption(doc: _Doc, cap: dict[str, Any], idx: int) -> None:
    start = _num(cap.get("start"))
    end = _num(cap.get("end"), start + 1.0)
    dur = max(0.1, end - start)
    cid = doc.uid(f"caption-{idx}")
    text = _esc(cap.get("text"))
    doc.body.append(
        f'<div id="{cid}" class="clip caption-line" data-start="{start:.3f}" '
        f'data-duration="{dur:.3f}" data-track-index="60"><span class="caption-text">{text}</span></div>'
    )
    fade = min(0.15, dur / 4)
    doc.tl.append(
        f'tl.fromTo("#{cid} .caption-text", {{ autoAlpha: 0, y: 6 }}, '
        f'{{ autoAlpha: 1, y: 0, duration: {fade:.3f}, ease: "power1.out" }}, {start:.3f});'
    )
    doc.tl.append(
        f'tl.to("#{cid} .caption-text", {{ autoAlpha: 0, duration: {fade:.3f}, ease: "power1.in" }}, '
        f'{max(start, end - fade):.3f});'
    )


# ─────────────────────────── overlays (A-Roll Text Motion System) ───────────────────────────

# 13 Remotion overlay kinds collapse onto a small set of HF markup shapes.
# All share the locked look from types.ts DEFAULT_OVERLAY_STYLE: white ink,
# translucent scrim, no panels/accent color -- readability from the veil,
# not a surface.

_OVERLAY_ZONE_CLASS = {
    "left_third": "zone-left",
    "right_third": "zone-right",
    "lower_raised": "zone-lower",
    "top_sparse": "zone-top",
}

# ─── treatment classifier: transcript beat -> HF catalog motion language ───
#
# Each `kind` from the overlay classifier gets one of these named motion
# treatments. Treatments are hand-rolled GSAP here (consistent with the rest
# of this module -- see MIGRATION_NOTES.md), but each one is modeled on a
# specific hosted HyperFrames catalog item so the *behavior* it approximates
# is traceable (confirm/refresh via `npx hyperframes catalog --query "<name>"`):
#
#   kind="emphasis", 1 word              -> kinetic-slam         (caption-kinetic-slam:
#                                            full-screen single word, alternating entrance)
#   kind="emphasis", contrast marker     -> type-swap             (kinetic-type-swap:
#                                            sentence holds, one word-slot swaps + settles)
#   kind="emphasis", short phrase        -> editorial-emphasis    (caption-editorial-emphasis:
#                                            dual-font size contrast on the heaviest word)
#   kind in title/quote, >=6 words       -> camera-follow         (caption-camera-follow:
#                                            sentence grows while camera slowly pulls back)
#   kind="chapter"                       -> background-emphasis   (mk-emphasis-type:
#                                            oversized low-contrast word, drifts as texture)
#   kind="code", snippet not seen yet    -> code-typing           (code-typing: token-streamed
#                                            reveal, first time this snippet appears)
#   kind="code", snippet changed         -> code-morph            (code-morph: prior snippet's
#                                            tokens glide/fade into the new one)
#   everything else                      -> "" (the original generic fade-in/fade-out)
#
# Bilingual (ID + EN) since episode transcripts are Indonesian-language.
_CONTRAST_MARKERS = (
    "bukan ", "tapi ", "tetapi ", "padahal", "ternyata", "justru",
    "instead of", "actually", "turns out", "not just", "not only", " but ",
)


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w])


def _has_contrast_marker(text: str) -> bool:
    low = f" {text.lower()} "
    return any(marker in low for marker in _CONTRAST_MARKERS)


def _choose_treatment(kind: str, raw_text: str, steps: list[str], code_history: list[str]) -> str:
    if kind == "code":
        norm = "\n".join(s.strip() for s in steps).strip()
        if not norm:
            return ""
        # Any earlier code beat in this episode means this one is a change to
        # code already on screen, not a fresh introduction -- even if the two
        # snippets happen to differ completely; code_history[-1] (when
        # present) becomes the code-morph "before" state.
        return "code-morph" if code_history else "code-typing"
    if kind == "emphasis":
        wc = _word_count(raw_text)
        if wc <= 1:
            return "kinetic-slam"
        if _has_contrast_marker(raw_text):
            return "type-swap"
        return "editorial-emphasis"
    if kind in ("title", "quote"):
        # Every quote/title gets real per-word motion; long ones additionally
        # get the slow pull-back. A flat single-block fade was the single
        # biggest source of "nothing is moving" -- most spoken quotes are
        # short, so gating any motion behind a >=6-word threshold meant most
        # overlays in a typical episode got no distinct treatment at all.
        return "camera-follow" if _word_count(raw_text) >= 6 else "word-cascade"
    if kind == "chapter":
        return "background-emphasis"
    if kind in ("chip", "tag"):
        return "badge-pop"
    return ""


def _word_spans(
    escaped_text: str, *, word_cls: str = "ov-word", accent_idx: int | None = None, accent_extra_cls: str = ""
) -> str:
    """Wraps every word in its own span so GSAP's `stagger` can cascade them in
    one word at a time, the way the hosted caption-* catalog components read
    (a static text block, however faded, is what real motion is not)."""
    words = [w for w in escaped_text.split(" ") if w]
    out = []
    for i, w in enumerate(words):
        cls = word_cls
        if i == accent_idx:
            cls = f"{word_cls} ov-word-accent {accent_extra_cls}".strip()
        out.append(f'<span class="{cls}">{w}</span>')
    return " ".join(out)


def _longest_word_idx(escaped_text: str) -> int | None:
    words = [w for w in escaped_text.split(" ") if w]
    if not words:
        return None
    return max(range(len(words)), key=lambda i: len(words[i]))


def _emit_word_stagger(
    doc: _Doc, oid: str, selector: str, *, start: float, fade: float, stagger: float = 0.05
) -> None:
    """Cascades `selector`'s children in word-by-word (GSAP `stagger`), instead
    of the whole block fading in as one static unit."""
    doc.tl.append(
        f'tl.fromTo("{selector}", {{ autoAlpha: 0, y: 22 }}, '
        f'{{ autoAlpha: 1, y: 0, duration: {max(0.16, fade):.3f}, ease: "power2.out", '
        f'stagger: {stagger:.3f} }}, {start:.3f});'
    )


def _overlay_body_html(ov: dict[str, Any], treatment: str = "") -> tuple[str, str]:
    """Returns (inner_html, css_kind_class) for one overlay kind."""
    kind = str(ov.get("kind") or "title")
    text = _esc(ov.get("text"))
    kicker = _esc(ov.get("kicker"))
    title = _esc(ov.get("title"))
    accent = _esc(ov.get("accent"))
    value = _esc(ov.get("value"))
    source_label = _esc(ov.get("sourceLabel"))
    steps = [str(s) for s in (ov.get("steps") or [])]

    if kind == "title":
        second = f'<div class="ov-accent">{accent}</div>' if accent else ""
        hero = _word_spans(text, word_cls="ov-word ov-hero-word", accent_idx=_longest_word_idx(text))
        return (f'<div class="ov-kicker">{kicker}</div><div class="ov-hero">{hero}</div>{second}', "ov-title")
    if kind == "stat":
        desc = f'<div class="ov-body">{title}</div>' if title else ""
        src = f'<div class="ov-meta">{source_label}</div>' if source_label else ""
        return (f'<div class="ov-stat-value">{value}</div>{desc}{src}', "ov-stat")
    if kind == "lower_third":
        tags = "".join(f'<span class="ov-chip">{_esc(s)}</span>' for s in steps)
        return (
            f'<div class="ov-body">{text}</div><div class="ov-meta">{title}</div><div class="ov-chips">{tags}</div>',
            "ov-lower-third",
        )
    if kind == "tag":
        return (f'<span class="ov-badge"><span class="ov-badge-dot"></span>{text}</span>', "ov-tag")
    if kind == "divider":
        return (f'<div class="ov-kicker">{kicker}</div><div class="ov-hero">{title}</div>', "ov-divider")
    if kind == "quote":
        body = _word_spans(text, word_cls="ov-word ov-quote-word")
        markup = (
            f'<div class="ov-quote-mark">&ldquo;</div><div class="ov-body ov-quote">{body}</div>'
            f'<div class="ov-meta">{kicker}</div>'
        )
        return (markup, "ov-quote")
    if kind == "code":
        lines = "".join(f'<div class="ov-code-line">{_esc(s)}</div>' for s in steps)
        return (f'<div class="ov-meta">{kicker}</div><div class="ov-code">{lines}</div>', "ov-code")
    if kind == "illustration":
        items = "".join(f'<li>{_esc(s)}</li>' for s in steps)
        return (f'<div class="ov-body">{title}</div><ul class="ov-illustration-list">{items}</ul>', "ov-illustration")
    if kind == "chapter":
        # overlay_suggest.py's chapter beats always carry kicker+text, never
        # title (confirmed by rendering real footage: the hero was silently
        # empty for every chapter overlay until this fallback was added).
        # Plain text, not _word_spans: background-emphasis (mkEmphasisIn)
        # fades the whole block in as one texture unit, not word-by-word --
        # individual .ov-word spans would never get revealed under it.
        hero_text = title or text
        return (f'<div class="ov-kicker">{kicker}</div><div class="ov-hero">{hero_text}</div>', "ov-chapter")
    if kind == "emphasis":
        if treatment == "kinetic-slam":
            return (f'<div class="ov-emphasis ov-emphasis-slam">{text}</div>', "ov-emphasis")
        accent_cls = "ov-swap-target" if treatment == "type-swap" else ""
        body = _word_spans(
            text, word_cls="ov-word ov-emphasis-word", accent_idx=_longest_word_idx(text), accent_extra_cls=accent_cls
        )
        return (f'<div class="ov-emphasis">{body}</div>', "ov-emphasis")
    if kind == "diagram":
        items = "".join(f'<div class="ov-diagram-step" data-step="{i}">{_esc(s)}</div>' for i, s in enumerate(steps))
        return (f'<div class="ov-body">{title}</div><div class="ov-diagram">{items}</div>', "ov-diagram")
    if kind == "callout":
        return (f'<div class="ov-callout-value">{value}</div><div class="ov-meta">{source_label}</div>', "ov-callout")
    if kind == "chip":
        return (f'<span class="ov-badge ov-badge-float"><span class="ov-badge-dot"></span>{text}</span>', "")
    if kind == "list_cycle":
        items = "".join(f'<li class="ov-list-item" data-step="{i}">{_esc(s)}</li>' for i, s in enumerate(steps))
        return (f'<div class="ov-body">{text}</div><ul class="ov-list-cycle">{items}</ul>', "ov-list")
    # fallback: plain title-like card
    return (f'<div class="ov-body">{text or title}</div>', "ov-title")


def _emit_treatment_motion(
    doc: _Doc, oid: str, treatment: str, start: float, dur: float, fade: float, exit_at: float
) -> None:
    sel = f"#{oid} .overlay-inner"
    word_sel = f"#{oid} .ov-word"
    exit_at = max(start, exit_at)

    def _exit_fade() -> None:
        doc.tl.append(
            f'tl.to("{sel}", {{ autoAlpha: 0, duration: {fade:.3f}, ease: "power1.in" }}, {exit_at:.3f});'
        )

    if treatment == "kinetic-slam":
        from_x = -60 if (hash(oid) % 2 == 0) else 60
        doc.tl.append(
            f'tl.fromTo("{sel}", {{ autoAlpha: 0, x: {from_x}, scale: 1.15 }}, '
            f'{{ autoAlpha: 1, x: 0, scale: 1, duration: {min(fade, 0.22):.3f}, ease: "back.out(2.2)" }}, {start:.3f});'
        )
        _exit_fade()
        return

    if treatment in ("camera-follow", "word-cascade"):
        # Real per-word motion (GSAP `stagger`), not one static block fading
        # in -- the container itself just becomes available; each `.ov-word`
        # span carries its own entrance, cascading like the hosted
        # caption-camera-follow / caption-editorial-emphasis catalog items.
        doc.tl.append(f'tl.set("{sel}", {{ autoAlpha: 1 }}, {start:.3f});')
        stagger_dur = 0.34 if treatment == "camera-follow" else 0.26
        doc.tl.append(
            f'tl.fromTo("{word_sel}", {{ autoAlpha: 0, y: 22 }}, '
            f'{{ autoAlpha: 1, y: 0, duration: {stagger_dur:.3f}, ease: "power2.out", stagger: 0.055 }}, {start:.3f});'
        )
        if treatment == "camera-follow":
            # The slow pull-back: real footage push-in/pull-back convention,
            # not the full radial-blur camera-follow engine (see
            # MIGRATION_NOTES.md) -- but a genuine continuous camera move
            # over the whole hold, not a one-shot fade.
            doc.tl.append(
                f'tl.fromTo("{sel}", {{ scale: 1.05 }}, '
                f'{{ scale: 0.94, duration: {max(0.1, dur):.3f}, ease: "sine.inOut", immediateRender: false }}, '
                f'{start:.3f});'
            )
        _exit_fade()
        return

    if treatment == "editorial-emphasis":
        doc.tl.append(f'tl.set("{sel}", {{ autoAlpha: 1 }}, {start:.3f});')
        doc.tl.append(
            f'tl.fromTo("{word_sel}", {{ autoAlpha: 0, scale: 1.12, transformOrigin: "0% 100%" }}, '
            f'{{ autoAlpha: 1, scale: 1, duration: 0.26, ease: "power2.out", stagger: 0.06 }}, {start:.3f});'
        )
        _exit_fade()
        return

    if treatment == "background-emphasis":
        # Real mkEmphasisIn/mkEmphasisOut helpers (verbatim from the
        # installed mk-emphasis-type component, injected once in the script
        # preamble) -- one decorative block sliding as a unit, matching the
        # catalog's actual "typography as texture" design, not a per-word
        # cascade (that reveal treats it as content, this treats it as
        # background texture, which is the whole point of the component).
        hold = max(0.6, dur - 1.0)
        doc.tl.append(f'window.mkEmphasisIn(tl, "{sel}", {start:.3f}, {{ drift: -90, hold: {hold:.3f} }});')
        doc.tl.append(f'window.mkEmphasisOut(tl, "{sel}", {exit_at:.3f});')
        return

    if treatment == "badge-pop":
        doc.tl.append(
            f'tl.fromTo("{sel}", {{ autoAlpha: 0, scale: 0.7, y: -12 }}, '
            f'{{ autoAlpha: 1, scale: 1, y: 0, duration: {min(fade, 0.28):.3f}, ease: "back.out(2.4)" }}, {start:.3f});'
        )
        _exit_fade()
        return

    if treatment == "type-swap":
        doc.tl.append(
            f'tl.fromTo("{sel}", {{ autoAlpha: 0, y: 14 }}, '
            f'{{ autoAlpha: 1, y: 0, duration: {fade:.3f}, ease: "power2.out" }}, {start:.3f});'
        )
        swap_at = start + max(fade, dur * 0.45)
        # Both tweens target the same element after the timeline's start, so
        # GSAP's immediateRender default would otherwise apply the later
        # call's "from" values as the resting state for any pre-swap seek.
        doc.tl.append(
            f'tl.fromTo("#{oid} .ov-swap-target", {{ filter: "blur(0px)" }}, '
            f'{{ filter: "blur(6px)", duration: 0.12, ease: "power1.in", immediateRender: false }}, {swap_at:.3f});'
        )
        doc.tl.append(
            f'tl.fromTo("#{oid} .ov-swap-target", {{ filter: "blur(6px)", autoAlpha: .4 }}, '
            f'{{ filter: "blur(0px)", autoAlpha: 1, duration: 0.22, ease: "power2.out", immediateRender: false }}, '
            f'{swap_at + 0.12:.3f});'
        )
        _exit_fade()
        return

    if treatment in ("code-typing", "code-morph"):
        doc.tl.append(
            f'tl.fromTo("{sel}", {{ autoAlpha: 0, y: 8 }}, '
            f'{{ autoAlpha: 1, y: 0, duration: {fade:.3f}, ease: "power2.out" }}, {start:.3f});'
        )
        if treatment == "code-typing":
            # token-streamed reveal: each line steps in in sequence, caret-like.
            doc.tl.append(
                f'tl.fromTo("#{oid} .ov-code-line", {{ autoAlpha: 0 }}, '
                f'{{ autoAlpha: 1, duration: 0.05, stagger: 0.09, ease: "none" }}, {start + 0.05:.3f});'
            )
        else:
            # code-morph: prior snippet's lines glide/fade into the new ones.
            doc.tl.append(
                f'tl.fromTo("#{oid} .ov-code-line", {{ autoAlpha: .3, x: -6 }}, '
                f'{{ autoAlpha: 1, x: 0, duration: 0.28, stagger: 0.05, ease: "power2.out" }}, {start + 0.05:.3f});'
            )
        _exit_fade()
        return

    # default ("") -- kinds with their own reveal mechanic (diagram/list_cycle
    # step-ins) or not yet given a distinct treatment keep the generic fade.
    doc.tl.append(
        f'tl.fromTo("{sel}", {{ autoAlpha: 0, y: 14 }}, '
        f'{{ autoAlpha: 1, y: 0, duration: {fade:.3f}, ease: "power2.out" }}, {start:.3f});'
    )
    _exit_fade()


# ─────────────── catalog-derived sub-compositions (framework dependencies) ───────────────
#
# caption-camera-follow and caption-editorial-emphasis are real hosted
# HyperFrames catalog items (installed at packages/hyperframes-kit/
# compositions/... via `npx hyperframes add`) with substantial standalone JS
# engines -- camera-follow derives its whole shot (word-box growth, camera
# pose, radial motion blur) from live DOM measurement of a WORDS list keyed
# by word count and a per-word cadence, NOT per-word ASR timestamps; editorial-
# emphasis lays out two-line "blocks" with real font-fit / scale-to-safe-width
# logic. Rather than re-derive that logic in Python (the earlier pass's
# mistake -- see git history), these functions read the ACTUAL installed
# catalog file, substitute real transcript text into its data section, and
# write a standalone sub-composition file wired in via data-composition-src
# (HyperFrames' native child-composition pattern). The catalog component is
# the render; hf_template.py is a compiler that feeds it real data.


def _catalog_source(*parts: str) -> str:
    path = framework_home() / "packages" / "hyperframes-kit" / "compositions" / Path(*parts)
    return path.read_text(encoding="utf-8")


def _replace_block(source: str, start_marker: str, end_marker: str, replacement: str) -> str:
    """Replaces everything from `start_marker` through the next `end_marker`
    (inclusive of both) with `replacement`. Raises if either marker is
    missing -- silently keeping the catalog file's DEMO data would ship a
    render with the wrong words in it, which is worse than a loud failure
    (and a marker going missing means the installed catalog file changed
    shape and this generator needs updating, not silent papering-over)."""
    start = source.index(start_marker)
    end = source.index(end_marker, start + len(start_marker)) + len(end_marker)
    return source[:start] + replacement + source[end:]


def _js_str(text: str) -> str:
    return json.dumps(text)


def _camera_follow_subcomp(instance_id: str, raw_text: str, dur: float) -> str:
    words = [w for w in raw_text.split() if w] or ["…"]
    accent_idx = max(range(len(words)), key=lambda i: len(words[i]))
    # STEP is the fixed per-word cadence the real engine advances the camera
    # on; DUR just needs to comfortably fit every word plus the closing
    # pull-back (~1.6s) -- there is no per-word timing data to thread in.
    step = max(0.32, min(0.62, (max(1.6, dur) - 1.6) / max(1, len(words) - 1)))

    src = _catalog_source("components", "caption-camera-follow.html")
    # Unwrap the <template> mount-contract wrapper: we're not cloning this
    # into a live document, we ship it as its own standalone composition
    # file, so it needs no template-clone runtime at all. Search after the
    # header comment closes -- its prose literally contains the substring
    # "<template>" describing the pattern, which is not the real tag.
    body_start = src.index("-->")
    tag_start = src.index("<template>", body_start)
    inner = src[tag_start + len("<template>") : src.index("</template>", tag_start)]

    js_words = ",\n              ".join(
        f'{{ text: {_js_str(w)}{", accent: true" if i == accent_idx else ""} }}' for i, w in enumerate(words)
    )
    inner = _replace_block(inner, "var WORDS = [", "];", f"var WORDS = [\n              {js_words}\n            ];")
    inner = inner.replace("var DUR = 9;", f"var DUR = {dur:.3f};")
    inner = inner.replace("var STEP = 0.52;", f"var STEP = {step:.3f};")
    inner = inner.replace('data-duration="9"', f'data-duration="{dur:.3f}" data-width="1920" data-height="1080"')
    inner = inner.replace("caption-camera-follow", instance_id)

    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="UTF-8" />'
        f'<meta name="viewport" content="width=1920, height=1080" /></head><body>{inner}</body></html>\n'
    )


def _editorial_emphasis_subcomp(instance_id: str, raw_text: str, dur: float) -> str:
    words = [w for w in raw_text.split() if w] or ["…"]
    accent_idx = max(range(len(words)), key=lambda i: len(words[i]))
    n = len(words)
    # No per-word ASR timing threaded in here either -- evenly space words
    # across the beat's duration (see MIGRATION_NOTES.md); a real fix is
    # plumbing actual word timestamps from the transcript through
    # timeline.json, not something this templater has today.
    word_dur = max(0.18, dur / max(1, n))
    gap = word_dur * 0.18
    w_entries = []
    for i, w in enumerate(words):
        w_start = i * word_dur
        w_end = w_start + max(0.05, word_dur - gap)
        w_entries.append(f"{{ text: {_js_str(w)}, start: {w_start:.3f}, end: {w_end:.3f} }}")
    js_w = ",\n        ".join(w_entries)

    if n <= 1:
        js_blocks = '{ line1: [[0, "e"]], line2: null }'
    else:
        line1_pairs = ", ".join(f'[{i}, "n"]' for i in range(n) if i != accent_idx)
        js_blocks = f'{{ line1: [{line1_pairs}], line2: [[{accent_idx}, "e"]] }}'

    out = _catalog_source("components", "caption-editorial-emphasis.html")
    out = _replace_block(out, "var W = [", "];", f"var W = [\n        {js_w}\n      ];")
    out = _replace_block(out, "var BLOCKS = [", "];", f"var BLOCKS = [\n        {js_blocks}\n      ];")
    out = out.replace("var DURATION = 8;", f"var DURATION = {dur:.3f};")
    out = out.replace('data-duration="8"', f'data-duration="{dur:.3f}"')
    return out.replace("caption-editorial-emphasis", instance_id)


def _split_type_swap(raw_text: str) -> tuple[str, list[str], str]:
    """Best-effort split of a contrast-marker sentence into kinetic-type-
    swap's (prefix, options, suffix) variable contract -- not a general NLU
    parser, just enough to turn "Bukan X, tapi Y" into a two-option roll
    that settles on Y (the correction), or a single-option roll (fade to the
    remainder, no visible swap) when only one marker is found."""
    low = f" {raw_text.lower()} "
    for marker in _CONTRAST_MARKERS:
        idx = low.find(marker)
        if idx == -1:
            continue
        idx = max(0, idx - 1)  # low has a leading space pad
        prefix = raw_text[:idx].strip()
        rest = raw_text[idx + len(marker) :].strip()
        rest_low = f" {rest.lower()} "
        for marker2 in _CONTRAST_MARKERS:
            idx2 = rest_low.find(marker2)
            if idx2 > 1:
                idx2 = max(0, idx2 - 1)
                opt1 = rest[:idx2].strip().rstrip(",")
                opt2 = rest[idx2 + len(marker2) :].strip()
                if opt1 and opt2:
                    return prefix, [opt1, opt2], ""
        return prefix, [rest], ""
    return "", [raw_text], ""


def _type_swap_subcomp(instance_id: str, raw_text: str, dur: float) -> tuple[str, dict[str, str]]:
    prefix, options, suffix = _split_type_swap(raw_text)
    src = _catalog_source("components", "kinetic-type-swap.html")
    body_start = src.index("-->")
    tag_start = src.index("<template>", body_start)
    inner = src[tag_start + len("<template>") : src.index("</template>", tag_start)]
    # Only the root div's data-duration carries data-composition-id right
    # next to it -- swap that occurrence first (adding data-width/height, per
    # hyperframes lint's root_missing_dimensions), then the remaining generic
    # data-duration="4" (the inner clip div) separately.
    inner = inner.replace(
        'data-composition-id="kinetic-type-swap" data-duration="4"',
        f'data-composition-id="{instance_id}" data-duration="{dur:.3f}" data-width="1920" data-height="1080"',
    )
    inner = inner.replace('data-duration="4"', f'data-duration="{dur:.3f}"')
    inner = inner.replace("kinetic-type-swap", instance_id)
    html_out = (
        '<!doctype html>\n<html lang="en"><head><meta charset="UTF-8" />'
        f'<meta name="viewport" content="width=1920, height=1080" /></head><body>{inner}</body></html>\n'
    )
    variable_values = {"prefix": prefix, "options": ",".join(options), "suffix": suffix}
    return html_out, variable_values


def _kinetic_slam_subcomp(instance_id: str, raw_text: str, dur: float) -> str:
    word = raw_text.strip() or "…"
    js_word = f'{{ text: {_js_str(word)}, start: 0, end: {dur:.3f} }}'
    out = _catalog_source("components", "caption-kinetic-slam.html")
    out = _replace_block(out, "var WORDS = [", "];", f"var WORDS = [\n          {js_word}\n        ];")
    # Single word, so it's the composition's whole message -- treat it as
    # the real component's "keyword" (gold accent), matching the accent
    # convention already used by camera-follow/editorial-emphasis.
    out = out.replace(
        "var KEYWORDS = new Set([8, 12, 15, 24, 27]); // HyperFrames, HTML, professional, code, cinema.",
        "var KEYWORDS = new Set([0]);",
    )
    out = out.replace('data-duration="8"', f'data-duration="{dur:.3f}"')
    return out.replace("caption-kinetic-slam", instance_id)


def _code_state_js(code_text: str) -> str:
    """One uniform-color token spanning the whole snippet. The real per-
    token *syntax* coloring needs a JS tokenizer (Shiki) this Python
    templater doesn't have -- but the typewriter/diff engines split
    characters out of token *content* regardless of token boundaries, so a
    single token still gets the real motion, just without syntax color."""
    return (
        "{\n"
        f"              code: {_js_str(code_text)},\n"
        "              tokens: [\n"
        f'                {{ key: "t0", content: {_js_str(code_text)}, color: "#e1e4e8", fontStyle: 0 }},\n'
        "              ],\n"
        "            }"
    )


def _code_typing_subcomp(instance_id: str, code_text: str, dur: float) -> str:
    # Rename the catalog's literal id ("code-typing") to our instance id
    # FIRST, on the untouched source -- doing it last would also match the
    # instance id's own text below (every instance id starts with
    # "code-typing-", which contains "code-typing" as a substring), turning
    # e.g. "code-typing-0" into the corrupted "code-typing-0-0".
    out = _catalog_source("code-typing.html").replace("code-typing", instance_id)
    replacement = (
        "window.__TOKENS = {\n"
        "        feature: {\n"
        '          lang: "text",\n'
        '          theme: "github-dark",\n'
        '          bg: "#24292e",\n'
        '          fg: "#e1e4e8",\n'
        "          states: [\n"
        f"            {_code_state_js(code_text)},\n"
        "          ],\n"
        "        },\n"
        "      };\n"
        f'      window.__BLOCK = {{ id: "{instance_id}", effect: "typing", seq: "feature", duration: {dur:.3f} }};'
    )
    out = _replace_block(out, "window.__TOKENS = {", 'duration: 5 };', replacement)
    return out.replace('data-duration="5"', f'data-duration="{dur:.3f}"')


def _code_morph_subcomp(instance_id: str, before_text: str, after_text: str, dur: float) -> str:
    out = _catalog_source("code-morph.html").replace("code-morph", instance_id)  # see _code_typing_subcomp
    replacement = (
        "window.__TOKENS = {\n"
        "        morph: {\n"
        '          lang: "text",\n'
        '          theme: "github-dark",\n'
        '          bg: "#24292e",\n'
        '          fg: "#e1e4e8",\n'
        "          states: [\n"
        f"            {_code_state_js(before_text)},\n"
        f"            {_code_state_js(after_text)},\n"
        "          ],\n"
        "        },\n"
        "      };\n"
        f'      window.__BLOCK = {{ id: "{instance_id}", effect: "morph", seq: "morph", duration: {dur:.3f} }};'
    )
    out = _replace_block(out, "window.__TOKENS = {", 'duration: 7 };', replacement)
    return out.replace('data-duration="7"', f'data-duration="{dur:.3f}"')


_SUBCOMP_TREATMENTS = (
    "camera-follow",
    "editorial-emphasis",
    "type-swap",
    "kinetic-slam",
    "code-typing",
    "code-morph",
)


def _emit_overlay(
    doc: _Doc, ov: dict[str, Any], idx: int, code_history: list[str], subcomps: dict[str, str]
) -> None:
    start = _num(ov.get("fromSec"))
    dur = max(0.2, _num(ov.get("durationSec"), 1.5))
    zone = str(ov.get("zone") or "")
    zone_cls = _OVERLAY_ZONE_CLASS.get(zone, "")
    kind = str(ov.get("kind") or "title")
    raw_text = str(ov.get("text") or ov.get("title") or "")
    steps_raw = [str(s) for s in (ov.get("steps") or [])]

    treatment = _choose_treatment(kind, raw_text, steps_raw, code_history)
    code_norm = ""
    previous_code = ""
    if kind == "code":
        code_norm = "\n".join(s.strip() for s in steps_raw).strip()
        previous_code = code_history[-1] if code_history else code_norm
        if code_norm:
            code_history.append(code_norm)

    content_ready = bool(code_norm) if kind == "code" else bool(raw_text.strip())
    if treatment in _SUBCOMP_TREATMENTS and content_ready:
        instance_id = f"{treatment}-{idx}"
        rel_path = f"compositions/generated/{instance_id}.html"
        variable_values: dict[str, str] | None = None
        if treatment == "camera-follow":
            subcomps[rel_path] = _camera_follow_subcomp(instance_id, raw_text, dur)
        elif treatment == "editorial-emphasis":
            subcomps[rel_path] = _editorial_emphasis_subcomp(instance_id, raw_text, dur)
        elif treatment == "kinetic-slam":
            subcomps[rel_path] = _kinetic_slam_subcomp(instance_id, raw_text, dur)
        elif treatment == "type-swap":
            subcomps[rel_path], variable_values = _type_swap_subcomp(instance_id, raw_text, dur)
        elif treatment == "code-typing":
            subcomps[rel_path] = _code_typing_subcomp(instance_id, code_norm, dur)
        else:  # code-morph
            subcomps[rel_path] = _code_morph_subcomp(instance_id, previous_code, code_norm, dur)
        scrim_id = doc.uid(f"{instance_id}-scrim")
        var_values_attr = (
            f" data-variable-values='{_esc(json.dumps(variable_values))}'" if variable_values else ""
        )
        doc.body.append(
            f'<div id="{scrim_id}" class="clip overlay-scrim-only {zone_cls}" data-start="{start:.3f}" '
            f'data-duration="{dur:.3f}" data-track-index="69"></div>'
            f'<div id="{instance_id}-mount" data-composition-id="{instance_id}" data-composition-src="{rel_path}" '
            f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="70" '
            f'data-width="1920" data-height="1080"{var_values_attr}></div>'
        )
        return

    inner, kind_cls = _overlay_body_html(ov, treatment)
    tr_cls = f"tr-{treatment}" if treatment else ""
    oid = doc.uid(f"overlay-{idx}")
    doc.body.append(
        f'<div id="{oid}" class="clip overlay-card {kind_cls} {zone_cls} {tr_cls}" '
        f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="70">'
        f'<div class="overlay-scrim"></div><div class="overlay-inner">{inner}</div></div>'
    )
    fade = min(0.3, dur / 4)
    exit_start_sec = ov.get("exitStartSec")
    exit_at = start + (_num(exit_start_sec) if exit_start_sec is not None else max(0.0, dur - fade))
    _emit_treatment_motion(doc, oid, treatment, start, dur, fade, exit_at)

    steps = ov.get("steps") or []
    step_at = ov.get("stepAtSec") or []
    if steps and step_at:
        selector_cls = ".ov-diagram-step" if "ov-diagram" in kind_cls else ".ov-list-item"
        for i, at_local in enumerate(step_at[: len(steps)]):
            doc.tl.append(
                f'tl.fromTo("#{oid} {selector_cls}[data-step=\\"{i}\\"]", {{ autoAlpha: 0, x: -8 }}, '
                f'{{ autoAlpha: 1, x: 0, duration: 0.3, ease: "power1.out" }}, {start + _num(at_local):.3f});'
            )


# ─────────────────────────── cutaways ───────────────────────────

_CUTAWAY_STYLE_CLASS = {
    "press": "cut-press",
    "thermal": "cut-thermal",
    "darkroom": "cut-darkroom",
    "cyanotype": "cut-cyanotype",
    "night": "cut-night",
    "daylight": "cut-daylight",
}


def _emit_cutaway(doc: _Doc, cut: dict[str, Any], idx: int, asset_map: dict[str, str]) -> None:
    start = _num(cut.get("fromSec"))
    dur = max(0.5, _num(cut.get("durationSec"), 3.0))
    style_name = str(cut.get("style") or "press")
    style_cls = _CUTAWAY_STYLE_CLASS.get(style_name, "cut-press")
    copy = cut.get("copy") or {}
    kicker = _esc(copy.get("kicker") or cut.get("kicker"))
    title = _esc(copy.get("title") or cut.get("title"))
    footer = _esc(copy.get("footerLabel"))

    entities = cut.get("entities") or cut.get("feeds") or []
    rows_html = []
    for i, ent in enumerate(entities):
        label = _esc(ent.get("label"))
        val = ent.get("value", ent.get("amount"))
        val_html = f'<span class="cut-row-value">{_esc(val)}</span>' if val is not None else ""
        rows_html.append(
            f'<div class="cut-row" data-row="{i}"><span class="cut-row-label">{label}</span>{val_html}</div>'
        )
    rows = "".join(rows_html)

    proof = cut.get("proof")
    proof_html = ""
    if proof and proof.get("src"):
        proof_html = f'<img class="cut-proof" src="{_esc(asset_map.get(proof["src"], proof["src"]))}" alt="" />'

    cid = doc.uid(f"cutaway-{idx}")
    doc.body.append(
        f'<div id="{cid}" class="clip cutaway-card {style_cls}" '
        f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="40">'
        f'<div class="cutaway-inner">'
        f'<div class="cut-kicker">{kicker}</div><div class="cut-title">{title}</div>'
        f'<div class="cut-rows">{rows}</div>{proof_html}'
        f'<div class="cut-footer">{footer}</div>'
        f'</div></div>'
    )
    doc.tl.append(
        f'tl.fromTo("#{cid} .cutaway-inner", {{ autoAlpha: 0, scale: 0.97 }}, '
        f'{{ autoAlpha: 1, scale: 1, duration: 0.4, ease: "power2.out" }}, {start:.3f});'
    )
    doc.tl.append(
        f'tl.to("#{cid} .cutaway-inner", {{ autoAlpha: 0, duration: 0.3, ease: "power1.in" }}, '
        f'{max(start, start + dur - 0.3):.3f});'
    )
    for ent, row_html in zip(entities, rows_html):
        at = start + _num(ent.get("atSec"))
        i = entities.index(ent)
        doc.tl.append(
            f'tl.fromTo("#{cid} .cut-row[data-row=\\"{i}\\"]", {{ autoAlpha: 0, x: -10 }}, '
            f'{{ autoAlpha: 1, x: 0, duration: 0.25, ease: "power1.out" }}, {at:.3f});'
        )


# ─────────────────────────── mockups ───────────────────────────


def _emit_mockup(doc: _Doc, mock: dict[str, Any], idx: int) -> None:
    start = _num(mock.get("fromSec"))
    dur = max(0.5, _num(mock.get("durationSec"), 4.0))
    stage = mock.get("stage") or {}
    title = _esc(stage.get("title") or "Session")
    mid = doc.uid(f"mockup-{idx}")

    layer_html = []
    for layer in mock.get("layers") or []:
        component = str(layer.get("component") or "")
        data = layer.get("data") or {}
        if component == "ClaudeChat":
            turns = data.get("turns") or []
            bubbles = "".join(
                f'<div class="mock-turn mock-turn-{_esc(t.get("role"))}">{_esc(t.get("text"))}</div>'
                for t in turns
            )
            layer_html.append(f'<div class="mock-chat">{bubbles}</div>')
        elif component == "DiffPanel":
            before = _esc(data.get("before"))
            after = _esc(data.get("after"))
            layer_html.append(
                f'<div class="mock-diff"><pre class="mock-diff-before">{before}</pre>'
                f'<pre class="mock-diff-after">{after}</pre></div>'
            )
        elif component == "AppWindow":
            content = _esc(data.get("content") or data.get("app") or "")
            layer_html.append(f'<div class="mock-appwindow">{content}</div>')
        elif component == "SkillsPanel":
            skills = data.get("skills") or []
            items = "".join(
                f'<div class="mock-skill{" on" if s.get("on") else ""}">{_esc(s.get("name"))}</div>'
                for s in skills
            )
            layer_html.append(f'<div class="mock-skills">{items}</div>')
        elif component == "RepoView":
            layer_html.append(
                f'<pre class="mock-repo">{_esc(data.get("markdown") or "")}</pre>'
            )
        # Cursor: purely a moving dot driven by keyframes; skipped in this
        # simplified rebuild (role: pointer emphasis, not core information).

    doc.body.append(
        f'<div id="{mid}" class="clip mockup-scene" data-start="{start:.3f}" '
        f'data-duration="{dur:.3f}" data-track-index="20">'
        f'<div class="mock-window">'
        f'<div class="mock-chrome"><span class="mock-dot"></span><span class="mock-dot"></span>'
        f'<span class="mock-dot"></span><span class="mock-title">{title}</span></div>'
        f'<div class="mock-body">{"".join(layer_html)}</div>'
        f'</div></div>'
    )
    doc.tl.append(
        f'tl.fromTo("#{mid} .mock-window", {{ autoAlpha: 0, y: 10 }}, '
        f'{{ autoAlpha: 1, y: 0, duration: 0.35, ease: "power2.out" }}, {start:.3f});'
    )
    doc.tl.append(
        f'tl.to("#{mid} .mock-window", {{ autoAlpha: 0, duration: 0.3, ease: "power1.in" }}, '
        f'{max(start, start + dur - 0.3):.3f});'
    )
    for kf in mock.get("camera") or []:
        state = str(kf.get("state") or "establish")
        scale = {"establish": 1.0, "read": 1.2, "focus": 1.45}.get(state, 1.0)
        at = start + _num(kf.get("atSec"))
        doc.tl.append(
            f'tl.to("#{mid} .mock-body", {{ scale: {scale:.3f}, duration: 0.42, ease: "sine.inOut" }}, {at:.3f});'
        )


# ─────────────────────────── sfx ───────────────────────────


def _emit_sfx(doc: _Doc, sfx: dict[str, Any], idx: int, asset_map: dict[str, str]) -> None:
    """One-shot SFX cue (shutter/click/paper/tick/typing), staged by
    `compose.stage_sfx_for_hyperframes` into `assets/sfx/`. Static gain via
    `data-volume` -- these are short one-shots, not faded, so a GSAP volume
    tween would be needless (see variables-and-media.md: a tween's values
    replace the static baseline entirely, so don't add one with nothing to
    animate).
    """
    start = _num(sfx.get("fromSec"))
    dur = max(0.05, _num(sfx.get("durationSec"), 0.2))
    src = str(sfx.get("src") or "")
    src = asset_map.get(src, src)
    volume = _clamp(_num(sfx.get("volume"), 0.4), 0.0, 3.98)
    sid = doc.uid(f"sfx-{idx}")
    doc.body.append(
        f'<audio id="{sid}" class="clip" src="{_esc(src)}" '
        f'data-start="{start:.3f}" data-duration="{dur:.3f}" '
        f'data-volume="{volume:.3f}" data-track-index="80"></audio>'
    )


# ─────────────────────────── privacy bars ───────────────────────────


def _emit_privacy(doc: _Doc, priv: dict[str, Any], idx: int) -> None:
    start = _num(priv.get("fromSec"))
    dur = max(0.1, _num(priv.get("durationSec"), 1.0))
    pid = doc.uid(f"privacy-{idx}")
    rects = priv.get("rects") or []
    bars = "".join(
        f'<div class="privacy-bar" style="left:{_num(r.get("x")):.2f}%;top:{_num(r.get("y")):.2f}%;'
        f'width:{_num(r.get("w")):.2f}%;height:{_num(r.get("h")):.2f}%;"></div>'
        for r in rects
    )
    doc.body.append(
        f'<div id="{pid}" class="clip privacy-layer" data-start="{start:.3f}" '
        f'data-duration="{dur:.3f}" data-track-index="90">{bars}</div>'
    )


# ─────────────────────────── document assembly ───────────────────────────

_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; background: #05070a; }
#root { position: relative; width: 100%; height: 100%; font-family: "Plus Jakarta Sans", Inter, ui-sans-serif, system-ui, sans-serif; }
.clip { position: absolute; inset: 0; }
.cam-clip { width: 100%; height: 100%; object-fit: cover; transform-origin: 50% 50%; }
.layout-full { width: 100%; height: 100%; }
.layout-float { inset: 9% 11%; width: 78%; height: 82%; margin: auto; border-radius: 24px; object-fit: fill; box-shadow: 0 30px 70px rgba(0,0,0,.45); }
.layout-pip { inset: auto 3.5% 4.5% auto; left: auto; width: 18%; height: 24%; border-radius: 26px; object-fit: cover; box-shadow: 0 14px 34px rgba(0,0,0,.4); border: 2px solid rgba(255,255,255,.35); }
.layout-stack-top { inset: 0 0 50% 0; height: 50%; object-fit: cover; }
.layout-stack-bottom { inset: 50% 0 0 0; height: 50%; object-fit: cover; }

.caption-line { display: flex; align-items: flex-end; justify-content: center; padding-bottom: 9%; pointer-events: none; }
.caption-text { opacity: 0; max-width: 82%; text-align: center; color: #fff; font-weight: 700; font-size: 3.4cqh; line-height: 1.25; text-shadow: 0 2px 18px rgba(0,0,0,.65); background: rgba(0,0,0,.35); padding: .35em .9em; border-radius: 10px; }

.overlay-card { display: flex; pointer-events: none; }
.overlay-scrim { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,.55) 100%); }
.overlay-scrim-only { background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,.55) 100%); pointer-events: none; }
.overlay-inner { position: relative; opacity: 0; color: #fff; text-shadow: 0 2px 18px rgba(0,0,0,.55); max-width: 48cqw; padding: 4.5% 4.5%; }
.zone-left .overlay-inner { margin-right: auto; }
.zone-right .overlay-inner { margin-left: auto; text-align: right; }
.zone-lower .overlay-inner { margin-top: auto; align-self: flex-end; }
.zone-top .overlay-inner { margin-bottom: auto; }
.ov-kicker { font-size: 2.4cqh; letter-spacing: .14em; text-transform: uppercase; color: rgba(255,255,255,.68); margin-bottom: .4em; }
.ov-hero { font-size: 8cqh; font-weight: 800; letter-spacing: -.02em; line-height: .98; }
.ov-accent { font-size: 8cqh; font-weight: 800; letter-spacing: -.02em; line-height: .98; background: rgba(255,255,255,.16); display: inline-block; padding: .05em .12em; margin-top: .1em; }
.ov-body { font-size: 4.5cqh; font-weight: 600; }
.ov-meta { font-size: 2.6cqh; color: rgba(255,255,255,.68); margin-top: .3em; }
.ov-stat-value { font-size: 9cqh; font-weight: 800; }
.ov-chips { display: flex; gap: .4em; margin-top: .5em; flex-wrap: wrap; }
.ov-chip { display: inline-block; border: 2px solid rgba(255,255,255,.28); border-radius: 999px; padding: .2em .9em; font-size: 2.2cqh; }

/* Catalog-modeled "chip"/"tag" badge (caption-camera-follow's accent
   language: a filled glass pill with a soft dot, not a bare outline). */
.ov-badge { display: inline-flex; align-items: center; gap: .5em; background: rgba(20,20,26,.55); backdrop-filter: blur(6px); border-radius: 999px; padding: .32em .95em .32em .7em; font-size: 2.2cqh; font-weight: 700; letter-spacing: .01em; box-shadow: 0 8px 24px rgba(0,0,0,.35), inset 0 0 0 1px rgba(255,255,255,.12); }
.ov-badge-dot { width: .55em; height: .55em; border-radius: 50%; background: #ffd84d; box-shadow: 0 0 10px rgba(255,216,77,.8); flex: none; }
.ov-badge-float { position: absolute; top: 8%; left: 4.5%; }

.ov-quote-mark { font-family: "Playfair Display", serif; font-size: 8cqh; opacity: .5; line-height: .5; }
.ov-quote { font-family: "Playfair Display", serif; font-style: italic; font-weight: 800; }
.ov-code { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 2.6cqh; background: rgba(0,0,0,.4); border-radius: 10px; padding: .8em 1em; }
.ov-code-line { white-space: pre; }
.ov-illustration-list, .ov-list-cycle { list-style: none; margin-top: .3em; }
.ov-illustration-list li, .ov-list-cycle li { font-size: 3.6cqh; font-weight: 600; padding: .15em 0; opacity: 0; }
.ov-list-cycle li { opacity: 1; }

/* Word-by-word cascade: every span starts hidden independent of its parent
   (the parent just becomes available; GSAP `stagger` reveals each word). */
.ov-word { display: inline-block; opacity: 0; }
.ov-hero-word, .ov-quote-word { will-change: transform, opacity; }

.ov-emphasis { font-size: 7cqh; font-weight: 800; }
.ov-emphasis-slam { font-family: "Anton", sans-serif; text-transform: uppercase; letter-spacing: .01em; font-size: 15cqh; text-align: center; color: #fff; }
/* editorial-emphasis's real dual-font contrast: Inter body vs. a much
   larger italic Playfair Display display word -- not a same-font 1.35x. */
.ov-emphasis-word.ov-word-accent { font-family: "Playfair Display", serif; font-style: italic; font-weight: 800; font-size: 1.7em; display: block; line-height: .95; color: #f5f0d0; text-shadow: 0 2px 18px rgba(0,0,0,.6), 0 4px 30px rgba(0,0,0,.35); }
.ov-word-accent { color: #ffd84d; }
.ov-swap-target { display: inline-block; }

/* mk-emphasis-type's real recipe: ~8% alpha (texture, not a headline),
   oversized, uppercase, drifting -- not a semi-opaque near-white block. */
.tr-background-emphasis .ov-kicker { color: rgba(255,255,255,.55); }
/* Verbatim mk-emphasis-type recipe: Inter 600, 24cqh (~260px @1080p), -.02em,
   rgba(245,245,247,.08) -- texture, not a headline. */
.tr-background-emphasis .ov-hero { font-family: "Inter", -apple-system, sans-serif; font-size: 24cqh; font-weight: 600; text-transform: uppercase; letter-spacing: -.02em; color: rgba(245,245,247,.08); text-shadow: none; }
.ov-diagram-step { font-size: 3.4cqh; font-weight: 600; padding: .2em 0; opacity: 0; border-left: 2px solid rgba(255,255,255,.4); padding-left: .5em; margin-top: .3em; }
.ov-callout-value { font-size: 8cqh; font-weight: 800; }

.cutaway-card { background: #05070a; display: flex; align-items: center; justify-content: center; }
.cutaway-inner { opacity: 0; width: 82%; max-width: 1400px; color: #f2efe9; }
.cut-kicker { font-size: 2.2cqh; letter-spacing: .16em; text-transform: uppercase; opacity: .7; }
.cut-title { font-size: 6.5cqh; font-weight: 800; margin: .2em 0 .6em; }
.cut-rows { display: flex; flex-direction: column; gap: .3em; }
.cut-row { display: flex; justify-content: space-between; font-size: 3cqh; opacity: 0; border-bottom: 1px solid rgba(255,255,255,.14); padding: .25em 0; }
.cut-row-value { font-variant-numeric: tabular-nums; font-weight: 700; }
.cut-footer { margin-top: .6em; font-size: 1.8cqh; opacity: .55; }
.cut-proof { max-width: 40%; margin-top: .8em; border-radius: 8px; }
.cut-press { background: #08090b; }
.cut-thermal { background: #12100c; color: #f4e8d0; }
.cut-darkroom { background: #05070a; color: #d7dee6; }
.cut-cyanotype { background: #0a2540; color: #dcecff; }
.cut-night { background: #04050a; color: #cfd6e6; }
.cut-daylight { background: #eef1f3; color: #12151a; }

.mockup-scene { display: flex; align-items: center; justify-content: center; background: #dfe4e7; }
.mock-window { opacity: 0; width: 82%; height: 78%; background: #fdfefe; border-radius: 18px; box-shadow: 0 24px 60px rgba(0,0,0,.3); overflow: hidden; display: flex; flex-direction: column; }
.mock-chrome { height: 8%; display: flex; align-items: center; gap: .5em; padding: 0 1.2em; background: #f4f6f7; border-bottom: 1px solid #e6eaec; }
.mock-dot { width: .8em; height: .8em; border-radius: 50%; background: #c3ccd1; }
.mock-title { margin-left: 1em; color: #7d878d; font-size: 1.8cqh; }
.mock-body { flex: 1; padding: 2em; overflow: hidden; transform-origin: 50% 50%; }
.mock-chat { display: flex; flex-direction: column; gap: .6em; }
.mock-turn { max-width: 70%; padding: .6em .9em; border-radius: 10px; font-size: 2.4cqh; }
.mock-turn-user { align-self: flex-end; background: #eef2f4; color: #293136; }
.mock-turn-assistant { align-self: flex-start; background: #f6f7f8; color: #3a434b; }
.mock-diff { display: grid; grid-template-columns: 1fr 1fr; gap: 1em; font-family: "IBM Plex Mono", monospace; font-size: 1.7cqh; }
.mock-diff-before { background: rgba(177,86,107,.12); padding: 1em; white-space: pre-wrap; }
.mock-diff-after { background: rgba(92,138,104,.12); padding: 1em; white-space: pre-wrap; }
.mock-appwindow { font-size: 2.2cqh; color: #3a434b; white-space: pre-wrap; }
.mock-skills { display: flex; flex-direction: column; gap: .4em; font-size: 2cqh; }
.mock-skill { padding: .3em .6em; border-radius: 6px; background: #eef1f2; color: #79848b; }
.mock-skill.on { background: #dfe9f0; color: #2f3a40; font-weight: 700; }
.mock-repo { font-family: "IBM Plex Mono", monospace; font-size: 1.6cqh; white-space: pre-wrap; color: #3a434b; }

.privacy-layer { pointer-events: none; }
.privacy-bar { position: absolute; background: #05070a; }
"""


def render_timeline_html(
    timeline: dict[str, Any],
    *,
    composition_id: str = "episode",
    asset_map: dict[str, str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Materialize a timeline.json dict as a standalone HyperFrames index.html.

    Returns (html, subcomps): `subcomps` maps a project-relative path (e.g.
    "compositions/generated/camera-follow-3.html") to file content for any
    catalog-derived sub-compositions the overlays needed -- the caller
    (`write_hf_composition`) writes these alongside index.html.
    """
    asset_map = asset_map or dict(timeline.get("sources") or {})
    width = int(timeline.get("width") or 1920)
    height = int(timeline.get("height") or 1080)
    duration_sec = _num(timeline.get("durationSec"), 1.0)

    doc = _Doc()
    subcomps: dict[str, str] = {}

    clips = list(timeline.get("clips") or [])
    for clip in clips:
        _emit_clip(doc, clip, asset_map, track_offset=0)
    _emit_punch_effects(doc, list(timeline.get("effects") or []), clips)
    for i, cap in enumerate(timeline.get("captions") or []):
        _emit_caption(doc, cap, i)
    for i, mock in enumerate(timeline.get("mockups") or []):
        _emit_mockup(doc, mock, i)
    for i, cut in enumerate(timeline.get("cutaways") or []):
        _emit_cutaway(doc, cut, i, asset_map)
    code_history: list[str] = []
    for i, ov in enumerate(timeline.get("overlays") or []):
        _emit_overlay(doc, ov, i, code_history, subcomps)
    for i, sfx in enumerate(timeline.get("sfx") or []):
        _emit_sfx(doc, sfx, i, asset_map)
    for i, priv in enumerate(timeline.get("privacy") or []):
        _emit_privacy(doc, priv, i)

    body = "\n      ".join(doc.body)
    tl_lines = "\n      ".join(doc.tl)
    cid = _esc(composition_id)

    html_out = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=IBM+Plex+Mono:wght@500&family=Anton&family=Playfair+Display:ital,wght@1,800&family=Inter:wght@400;600;900&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
{_CSS}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="{cid}"
      data-start="0"
      data-duration="{duration_sec:.3f}"
      data-width="{width}"
      data-height="{height}"
    >
      {body}
    </div>
    <script>
      // Verbatim from the installed mk-emphasis-type catalog component
      // (packages/hyperframes-kit/compositions/components/mk-emphasis-type.html)
      // -- copied per its own "copy these helpers into the host script" note.
      window.mkEmphasisIn = function (tl, target, at, opts) {{
        opts = opts || {{}};
        var drift = opts.drift === undefined ? -100 : opts.drift;
        var hold = opts.hold === undefined ? 5 : opts.hold;
        gsap.set(target, {{ opacity: 0, x: 40 }});
        tl.to(target, {{ opacity: 1, duration: 1.0, ease: "power2.out" }}, at);
        tl.to(target, {{ x: 40 + drift, duration: hold, ease: "sine.inOut" }}, at);
      }};
      window.mkEmphasisOut = function (tl, target, at) {{
        tl.to(target, {{ opacity: 0, duration: 0.5, ease: "power2.in" }}, at);
      }};

      const tl = gsap.timeline({{ paused: true }});
      {tl_lines}
      window.__timelines["{cid}"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""
    return html_out, subcomps


def write_hf_composition(
    project_dir: Path,
    timeline: dict[str, Any],
    *,
    composition_id: str = "episode",
    asset_map: dict[str, str] | None = None,
) -> Path:
    """Render + write index.html (+ any generated sub-compositions) for
    `project_dir` (a HyperFrames project)."""
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    html_out, subcomps = render_timeline_html(timeline, composition_id=composition_id, asset_map=asset_map)
    index_path = project_dir / "index.html"
    index_path.write_text(html_out, encoding="utf-8")
    generated_dir = project_dir / "compositions" / "generated"
    if subcomps and generated_dir.is_dir():
        # A previous compose left stale per-overlay sub-compositions behind
        # (fewer overlays this time, or different treatments) -- don't let
        # last episode's camera-follow-7.html linger unreferenced.
        for stale in generated_dir.glob("*.html"):
            stale.unlink()
    for rel_path, content in subcomps.items():
        out_path = project_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
    return index_path
