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


#: How many words a local match window may span, and how big a silence
#: inside it may be before it's cut short. Fluid conversational Indonesian
#: routinely runs 10+ seconds between pauses over 0.45s — grouping on
#: silence alone (the old approach) merged an entire multi-sentence stretch
#: into one "phrase", so only the *first* step in a list could ever match
#: it (every other step's keywords were technically inside that phrase too,
#: but the phrase was already claimed) and fell back to being evenly
#: spaced across the window regardless of when it was actually said.
_MATCH_WINDOW_WORDS = 5
_MATCH_WINDOW_GAP_SEC = 0.6


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

    in_range = sorted(
        (w for w in words if float(w["end"]) > t0 and float(w["start"]) < t1),
        key=lambda w: float(w["start"]),
    ) if words else []
    assigned: list[float | None] = [None] * n
    used_word_i: set[int] = set()

    for si, step in enumerate(steps):
        kws = step_keywords(step)
        if not kws or not in_range:
            continue
        # Candidates must start at/after where the previous step actually
        # landed — not the lead-in point. Using the lead-in here was the
        # other half of the bug: a step's own real utterance often starts
        # inside [t0, usable0), so filtering against usable0 discarded the
        # correct match before scoring ever ran, and every later step
        # inherited the same wrong floor once the first one came up empty.
        cursor = t0 if si == 0 else (assigned[si - 1] if assigned[si - 1] is not None else t0)
        best_score = 0.0
        best_hit_start: float | None = None
        best_hits: list[int] = []
        for i, w in enumerate(in_range):
            if i in used_word_i:
                continue
            wt = float(w["start"])
            if wt + 1e-3 < cursor - 0.05:
                continue
            # A short local window from this anchor, cut off at a real pause
            # — not a silence-delimited "phrase" that can run for a whole
            # multi-sentence stretch of fluid speech and swallow every other
            # step's words along with it.
            window: list[int] = [i]
            j = i + 1
            while j < len(in_range) and len(window) < _MATCH_WINDOW_WORDS:
                gap = float(in_range[j]["start"]) - float(in_range[window[-1]]["end"])
                if gap >= _MATCH_WINDOW_GAP_SEC:
                    break
                window.append(j)
                j += 1
            text = " ".join(str(in_range[k]["text"]) for k in window)
            score = _score_phrase(text, kws)
            if score > best_score:
                hits = [k for k in window if any(kw in _fold(str(in_range[k]["text"])) for kw in kws)]
                if hits:
                    best_score = score
                    best_hit_start = min(float(in_range[k]["start"]) for k in hits)
                    best_hits = hits
        if best_hit_start is not None and best_score >= min_score:
            assigned[si] = max(usable0, best_hit_start)
            used_word_i.update(best_hits)

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
