"""Align diagram list steps to spoken phrases (sentence-level, not karaoke).

Each step appears when the speaker hits a matching idea in the cam transcript
inside the overlay's source window. Unmatched steps fill evenly after the last
matched beat so motion still feels paced when ASR is fuzzy.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Short / filler tokens — keep matching on content words.
_STOP = frozenset(
    {
        "yang",
        "dan",
        "atau",
        "untuk",
        "dari",
        "pada",
        "dengan",
        "ini",
        "itu",
        "ada",
        "juga",
        "sudah",
        "akan",
        "saat",
        "kalau",
        "kalo",
        "jadi",
        "lalu",
        "baru",
        "the",
        "and",
        "or",
        "for",
        "from",
        "with",
        "this",
        "that",
        "into",
        "onto",
        "a",
        "an",
        "to",
        "of",
        "in",
        "on",
        "di",
        "ke",
        "ya",
        "nih",
        "sih",
        "dong",
        "banget",
        "sekali",
        "next",
        "step",
        "fase",
        "bab",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.I)


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text or "")
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return raw.lower()


def step_keywords(step: str) -> list[str]:
    """Content tokens from a diagram step label."""
    toks = _TOKEN_RE.findall(_fold(step))
    out: list[str] = []
    for t in toks:
        if len(t) < 3 and not t.isdigit():
            continue
        if t in _STOP:
            continue
        out.append(t)
    # Prefer longer tokens first for scoring
    out.sort(key=len, reverse=True)
    return out


def _phrase_windows(
    words: list[dict[str, Any]],
    *,
    start: float,
    end: float,
    gap_sec: float = 0.45,
) -> list[dict[str, Any]]:
    """Group words in [start, end] into phrase-ish windows on silence gaps."""
    win = [
        w
        for w in words
        if float(w["end"]) > start and float(w["start"]) < end
    ]
    if not win:
        return []
    phrases: list[dict[str, Any]] = []
    buf: list[dict[str, Any]] = [win[0]]
    for prev, cur in zip(win, win[1:]):
        gap = float(cur["start"]) - float(prev["end"])
        if gap >= gap_sec:
            phrases.append(
                {
                    "start": float(buf[0]["start"]),
                    "end": float(buf[-1]["end"]),
                    "text": " ".join(str(w["text"]) for w in buf),
                }
            )
            buf = [cur]
        else:
            buf.append(cur)
    if buf:
        phrases.append(
            {
                "start": float(buf[0]["start"]),
                "end": float(buf[-1]["end"]),
                "text": " ".join(str(w["text"]) for w in buf),
            }
        )
    return phrases


def _score_phrase(phrase_text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    hay = _fold(phrase_text)
    hits = 0.0
    weight = 0.0
    for i, kw in enumerate(keywords):
        w = 1.0 + max(0, 3 - i) * 0.15  # first keywords matter more
        weight += w
        if kw.isdigit():
            if re.search(rf"(?<!\d){re.escape(kw)}(?!\d)", hay):
                hits += w
        elif kw in hay:
            hits += w
    return hits / weight if weight else 0.0


def align_diagram_step_source_times(
    steps: list[str],
    words: list[dict[str, Any]],
    *,
    overlay_start: float,
    overlay_end: float,
    lead_in_sec: float = 0.55,
    min_gap_sec: float = 0.55,
    min_score: float = 0.34,
) -> list[float]:
    """Return source-time (cam seconds) when each step should appear.

    Monotonic, inside ``[overlay_start + lead_in, overlay_end)``. Unmatched
    steps are spaced evenly after the previous assigned beat.
    """
    n = len(steps)
    if n == 0:
        return []
    t0 = float(overlay_start)
    t1 = float(overlay_end)
    if t1 <= t0:
        return [t0] * n

    usable0 = min(t1 - 0.05, t0 + max(0.15, lead_in_sec))
    usable1 = t1
    span = max(0.2, usable1 - usable0)

    # Explicit per-step source times on cover (optional) — validated later by caller.
    phrases = _phrase_windows(words, start=t0, end=t1) if words else []
    assigned: list[float | None] = [None] * n
    used_phrase_i: set[int] = set()

    for si, step in enumerate(steps):
        kws = step_keywords(step)
        if not kws or not phrases:
            continue
        best_i = -1
        best_score = 0.0
        cursor = usable0 if si == 0 else (assigned[si - 1] or usable0)
        for pi, ph in enumerate(phrases):
            if pi in used_phrase_i:
                continue
            ph_s = float(ph["start"])
            if ph_s + 1e-3 < cursor - 0.05:
                continue
            score = _score_phrase(str(ph["text"]), kws)
            if score > best_score:
                best_score = score
                best_i = pi
        if best_i >= 0 and best_score >= min_score:
            used_phrase_i.add(best_i)
            assigned[si] = max(usable0, float(phrases[best_i]["start"]))

    # Fill gaps evenly; enforce min gaps + clamp.
    out: list[float] = []
    for si in range(n):
        if assigned[si] is not None:
            t = float(assigned[si])
        else:
            # Even remainder among trailing unmatched from previous fixed point.
            prev = out[-1] if out else usable0
            remaining_slots = n - si
            room = max(min_gap_sec * remaining_slots, usable1 - prev)
            t = prev + room / remaining_slots
        if out:
            t = max(t, out[-1] + min_gap_sec)
        t = min(max(t, usable0), usable1 - 0.05)
        if out and t <= out[-1]:
            t = min(usable1 - 0.05, out[-1] + min_gap_sec)
        out.append(t)

    # If everything collapsed near the end, redistribute evenly.
    if n >= 2 and (out[-1] - out[0]) < min_gap_sec * (n - 1) * 0.6:
        out = [usable0 + (span * i / max(1, n - 1)) for i in range(n)]
    return out


def source_steps_to_relative(
    step_source_times: list[float],
    *,
    overlay_source_start: float,
    slice_from_sec: float,
    edl: dict[str, Any],
    source: str = "cam",
) -> list[float]:
    """Map absolute source step times → seconds relative to timeline overlay start.

    Uses the same EDL remap as overlays: output_time(step) - slice_from_sec.
    """
    from agentic_editor.cover.remap import remap_source_window

    rel: list[float] = []
    for t in step_source_times:
        # Zero-width probe around spoken start
        slices = remap_source_window(edl, float(t), float(t) + 0.05, source=source)
        if not slices:
            # Fallback: offset from overlay source start (ignores cuts)
            rel.append(max(0.0, float(t) - float(overlay_source_start)))
            continue
        out_t = float(slices[0]["fromSec"])
        rel.append(max(0.0, out_t - float(slice_from_sec)))
    # Monotonic relative
    for i in range(1, len(rel)):
        if rel[i] < rel[i - 1] + 0.2:
            rel[i] = rel[i - 1] + 0.2
    return rel


def even_step_at_sec(n: int, duration_sec: float, *, lead_in_sec: float = 0.55) -> list[float]:
    """Fallback stagger when no transcript is available."""
    if n <= 0:
        return []
    if n == 1:
        return [min(lead_in_sec, max(0.2, duration_sec * 0.2))]
    usable0 = min(lead_in_sec, max(0.2, duration_sec * 0.12))
    usable1 = max(usable0 + 0.3, duration_sec * 0.92)
    span = usable1 - usable0
    return [usable0 + span * i / (n - 1) for i in range(n)]
