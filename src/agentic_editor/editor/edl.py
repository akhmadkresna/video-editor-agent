"""EDL load / validate / snap helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CONTINUATION_START_RE = re.compile(
    r"(?i)^(oke|ok|nah|lanjut|setelah|kemudian|selanjutnya|now|so)\b"
)


def load_edl(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_edl(data)
    return data


def validate_edl(edl: dict[str, Any]) -> None:
    if "sources" not in edl or not isinstance(edl["sources"], dict):
        raise ValueError("EDL missing sources map")
    if "ranges" not in edl or not isinstance(edl["ranges"], list) or not edl["ranges"]:
        raise ValueError("EDL missing non-empty ranges list")
    for i, r in enumerate(edl["ranges"]):
        if "source" not in r or "start" not in r or "end" not in r:
            raise ValueError(f"EDL ranges[{i}] needs source, start, end")
        if float(r["end"]) <= float(r["start"]):
            raise ValueError(f"EDL ranges[{i}] end must be > start")
        if r["source"] not in edl["sources"]:
            raise ValueError(f"EDL ranges[{i}] unknown source {r['source']!r}")


def snap_range_to_words(
    start: float,
    end: float,
    words: list[dict[str, Any]],
    *,
    pad_before: float = 0.05,
    pad_after: float = 0.08,
    hold_tail: bool = False,
) -> tuple[float, float]:
    """Snap cut edges to nearest word boundaries and apply padding.

    ``hold_tail=True`` preserves an intentional non-speech end (AI wait beat).
    Only the start is speech-snapped; ``end`` is kept so the beat survives.
    """
    word_tokens = [
        w
        for w in words
        if w.get("type", "word") == "word" and w.get("start") is not None
    ]
    if not word_tokens:
        return max(0.0, start - pad_before), end + (0.0 if hold_tail else pad_after)

    # find first word overlapping/after start
    first = None
    for w in word_tokens:
        if float(w["end"]) > start:
            first = w
            break
    last = None
    for w in reversed(word_tokens):
        if float(w["start"]) < end:
            last = w
            break
    if first is None or last is None:
        return max(0.0, start - pad_before), end + (0.0 if hold_tail else pad_after)

    snapped_start = max(0.0, float(first["start"]) - pad_before)
    if hold_tail:
        # Keep requested end (wait beat); never pull it back to last word
        snapped_end = max(float(end), snapped_start + 0.05)
    else:
        snapped_end = float(last["end"]) + pad_after
        if snapped_end <= snapped_start:
            snapped_end = snapped_start + 0.05
    return snapped_start, snapped_end


def _words_in_gap(
    words: list[dict[str, Any]], gap_start: float, gap_end: float
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for w in words:
        try:
            ws, we = float(w["start"]), float(w["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if we > gap_start + 0.02 and ws < gap_end - 0.02:
            tok = str(w.get("text") or w.get("word") or "").strip()
            if tok:
                out.append(w)
    return out


def _first_clause_text(
    words: list[dict[str, Any]], t: float, *, radius: float = 4.0
) -> str:
    parts: list[str] = []
    for w in words:
        try:
            ws = float(w["start"])
        except (KeyError, TypeError, ValueError):
            continue
        if ws < t - 0.05 or ws > t + radius:
            continue
        tok = str(w.get("text") or w.get("word") or "").strip()
        if tok:
            parts.append(tok)
        if len(parts) >= 6:
            break
    return " ".join(parts)


#: `edl_suggest`'s gap-classify loop tags nearly every hard-cut range with
#: one of these two notes — "speech" is the default for a THINK cut,
#: "speech+wait-beat" for AI_WAIT. They carry no topic information at all
#: (they don't mean "same beat", they mean "this range has spoken words in
#: it", which is true of almost every range), so treating a match between
#: them as bridging evidence defeats the THINK hard-cut for nearly any pause
#: under `note_bridge_max_gap_sec` regardless of whether the two clauses are
#: actually related — this was the bug behind "weird silent" pauses
#: surviving the radio-edit uncut.
_GENERIC_BRIDGE_NOTES = frozenset({"speech", "speech+wait-beat", ""})


def _note_bridgeable(a: str | None, b: str | None) -> bool:
    na, nb = (a or "").strip().lower(), (b or "").strip().lower()
    if not na or not nb:
        return False
    if na in _GENERIC_BRIDGE_NOTES or nb in _GENERIC_BRIDGE_NOTES:
        return False
    if na == nb:
        return True
    stem_a = re.split(r"\s*[+|,]", na)[0].strip()
    stem_b = re.split(r"\s*[+|,]", nb)[0].strip()
    return stem_a == stem_b and len(stem_a) >= 4


def merge_bridge_gaps(
    ranges: list[dict[str, Any]],
    words: list[dict[str, Any]] | None = None,
    *,
    max_gap_sec: float = 8.0,
    note_bridge_max_gap_sec: float = 3.0,
) -> tuple[list[dict[str, Any]], int]:
    """Merge adjacent keeps across short silent gaps (same topic / continuation).

    Fixes hard jumps when radio-edit cuts a mid pause (THINK/AI_WAIT) between
    clauses that belong to one beat — e.g. WinFSP explanation → brief silence →
    "Oke setelah kita install…".

    Two signals justify keeping the silence instead of a hard cut, and they
    are not equally strong evidence of continuity — so they don't share one
    ceiling:
      - An explicit continuation opener on the next clause ("Oke", "Nah",
        "Setelah", ...) is a real content signal — trusted up to
        ``max_gap_sec`` (a speaker can pause a while before "Oke, lanjut…").
      - Two clauses merely sharing the same generic gap-class ``note`` (both
        "speech", say) is *not* a content signal — almost every clause is
        tagged "speech", so this fires on nearly any adjacent pair regardless
        of whether they're actually the same thought. Giving it the same 8s
        ceiling as an explicit continuation word silently keeps long, truly
        unrelated silences (e.g. between two separate, complete sentences on
        different sub-topics) — capped tighter at ``note_bridge_max_gap_sec``.
    """
    if len(ranges) < 2 or max_gap_sec <= 0:
        return ranges, 0
    word_rows = words or []
    merged: list[dict[str, Any]] = []
    bridges = 0
    ordered = sorted(ranges, key=lambda r: float(r["start"]))
    i = 0
    while i < len(ordered):
        cur = {k: v for k, v in ordered[i].items() if not str(k).startswith("_")}
        j = i + 1
        while j < len(ordered):
            nxt = ordered[j]
            if str(cur.get("source") or "cam") != str(nxt.get("source") or "cam"):
                break
            gap = float(nxt["start"]) - float(cur["end"])
            if gap < -0.05 or gap > max_gap_sec:
                break
            if word_rows and _words_in_gap(
                word_rows, float(cur["end"]), float(nxt["start"])
            ):
                break
            nxt_open = _first_clause_text(word_rows, float(nxt["start"]))
            has_continuation_word = bool(nxt_open and CONTINUATION_START_RE.search(nxt_open))
            bridgeable = (
                gap <= 0.05
                or has_continuation_word
                or (
                    _note_bridgeable(cur.get("note"), nxt.get("note"))
                    and gap <= note_bridge_max_gap_sec
                )
            )
            if bridgeable:
                cur["end"] = round(float(nxt["end"]), 3)
                if cur.get("note") != nxt.get("note") and nxt.get("note"):
                    cur["note"] = str(cur.get("note") or nxt.get("note"))
                bridges += 1
                j += 1
            else:
                break
        merged.append(cur)
        i = j
    return merged, bridges


def example_edl(episode_rel_cam: str = "../raw/cam.mp4") -> dict[str, Any]:
    return {
        "sources": {"cam": episode_rel_cam},
        "ranges": [
            {
                "source": "cam",
                "start": 0.0,
                "end": 5.0,
                "note": "example — replace after radio-edit",
            }
        ],
        "grade": None,
    }
