"""Suggest generative MG cutaways from transcript + cover context.

Hybrid planner: deterministic timing/schema + intent heuristics.
Emits edit/cutaways.suggest.json; --apply only after human confirm.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agentic_editor.cover.cutaway_families import (
    FAMILY_CAPABILITIES,
    FAMILY_TO_SCENE,
    validate_brief_against_family,
)
from agentic_editor.cover.suggest import load_cam_words, snap_window_to_words
from agentic_editor.editor.edl import load_edl
from agentic_editor.project import load_project

CUTAWAY_MIN_SEC = 4.0
CUTAWAY_MAX_SEC = 24.0
CUTAWAY_MIN_GAP = 45.0
MAX_CUTAWAYS = 6

# Intent lexicon (ID + EN) — scored, not hard-required.
INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "prove",
        re.compile(
            r"(?i)\b(tervalidasi|immutable|bukti|ledger|buku kas|"
            r"tidak bisa diedit|audit|record|prove|proof)\b"
        ),
    ),
    (
        "accumulate",
        re.compile(
            r"(?i)\b(saldo|balance|total|jumlah|penjualan|pembelian|"
            r"biaya|rp\.?|rupiah|running)\b"
        ),
    ),
    (
        "compare",
        re.compile(r"(?i)\b(vs|versus|banding|lebih|daripada|compare|before|after)\b"),
    ),
    (
        "sequence",
        re.compile(
            r"(?i)\b(langkah|step|pertama|kedua|ketiga|lalu|kemudian|"
            r"fase|phase|urutan|sequence)\b"
        ),
    ),
    (
        "transform",
        re.compile(
            r"(?i)\b(jadi|menjadi|otomatis|transform|flow|alur|masuk|keluar)\b"
        ),
    ),
    (
        "warn",
        re.compile(r"(?i)\b(jangan|hati-hati|error|gagal|reject|hapus|edit|warn)\b"),
    ),
    (
        "summarize",
        re.compile(r"(?i)\b(jadi|kesimpulan|intinya|summary|rekap|singkat)\b"),
    ),
    (
        "explain",
        re.compile(r"(?i)\b(artinya|maksudnya|yaitu|adalah|explain|cara)\b"),
    ),
]

INTENT_TO_FAMILIES: dict[str, list[str]] = {
    "prove": ["document", "evidence", "system_map"],
    "accumulate": ["document", "flow", "kinetic_type"],
    "compare": ["comparison", "kinetic_type", "minimal"],
    "sequence": ["sequence", "flow", "system_map"],
    "transform": ["flow", "system_map", "kinetic_type"],
    "warn": ["document", "kinetic_type", "minimal"],
    "summarize": ["kinetic_type", "minimal", "document"],
    "explain": ["flow", "system_map", "evidence", "minimal"],
}

# Prefer cutaway only when speech suggests a visual payoff.
CUTAWAY_WORTH_RE = re.compile(
    r"(?i)\b("
    r"buku kas|ledger|immutable|tervalidasi|otomatis|"
    r"saldo|penjualan|pembelian|flow|alur|langkah|"
    r"banding|vs|bukti|dashboard|diagram|arsitektur|"
    r"tidak bisa diedit|record"
    r")\b"
)

FILLER = frozenset(
    {
        "ini",
        "itu",
        "ya",
        "yah",
        "guys",
        "oke",
        "ok",
        "nah",
        "dan",
        "atau",
        "yang",
        "di",
        "ke",
        "dari",
        "juga",
        "sih",
        "the",
        "a",
        "an",
        "of",
        "to",
        "for",
    }
)


def _load_cover(episode: Path) -> dict[str, Any] | None:
    path = episode / "edit" / "cover.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _word_text(w: dict[str, Any]) -> str:
    return str(w.get("word") or w.get("text") or "").strip()


def _window_text(words: list[dict[str, Any]], start: float, end: float) -> str:
    parts = []
    for w in words:
        try:
            ws = float(w.get("start") or 0)
            we = float(w.get("end") or ws)
        except (TypeError, ValueError):
            continue
        if we < start or ws > end:
            continue
        t = _word_text(w)
        if t:
            parts.append(t)
    return " ".join(parts)


def _classify_intent(text: str) -> str:
    scores: dict[str, int] = {}
    for intent, pat in INTENT_PATTERNS:
        hits = pat.findall(text)
        if hits:
            scores[intent] = scores.get(intent, 0) + len(hits)
    if not scores:
        return "explain"
    return max(scores.items(), key=lambda kv: kv[1])[0]


def _title_from_text(text: str, *, max_words: int = 5) -> str:
    toks = [t for t in re.split(r"\s+", text.strip()) if t and t.lower() not in FILLER]
    if not toks:
        return ""
    # Prefer a payoff token if present.
    for needle, label in (
        ("buku kas", "Buku kas"),
        ("immutable", "Immutable"),
        ("tervalidasi", "Tervalidasi"),
        ("otomatis", "Otomatis"),
        ("saldo", "Saldo berjalan"),
    ):
        if needle in text.lower():
            return label
    chunk = " ".join(toks[:max_words])
    return chunk[:1].upper() + chunk[1:] if chunk else ""


def _pick_family(
    intent: str,
    *,
    duration: float,
    recent: list[str],
    has_proof_hint: bool,
) -> str:
    candidates = list(INTENT_TO_FAMILIES.get(intent) or ["minimal"])
    # Variety: avoid repeating the last family when alternatives exist.
    ranked = [f for f in candidates if f not in recent[-2:]] or candidates
    for fam in ranked:
        caps = FAMILY_CAPABILITIES.get(fam) or {}
        min_dur = float(caps.get("minDurationSec") or 0)
        if duration < min_dur and fam != "minimal":
            continue
        if has_proof_hint and not caps.get("supportsProof") and fam != "minimal":
            continue
        issues = validate_brief_against_family(
            fam,
            duration_sec=duration,
            intent=intent,
            has_proof=has_proof_hint,
        )
        # Intent mismatch is soft; duration/proof hard.
        hard = [i for i in issues if "minDuration" in i or "supportProof" in i]
        if not hard:
            return fam
    return "minimal"


def _idea_windows(words: list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    """Segment speech into idea windows around cutaway-worthy hits."""
    if not words:
        return []
    hits: list[float] = []
    for w in words:
        t = _word_text(w)
        if not t:
            continue
        if CUTAWAY_WORTH_RE.search(t):
            try:
                hits.append(float(w.get("start") or 0))
            except (TypeError, ValueError):
                continue
    # Also scan multi-word spans by joining nearby words.
    if not hits:
        # Fall back: scan 8s rolling windows for phrase hits.
        try:
            t0 = float(words[0].get("start") or 0)
            t1 = float(words[-1].get("end") or t0)
        except (TypeError, ValueError, IndexError):
            return []
        t = t0
        while t < t1:
            text = _window_text(words, t, t + 10.0)
            if CUTAWAY_WORTH_RE.search(text):
                hits.append(t + 1.0)
            t += 8.0

    windows: list[tuple[float, float, str]] = []
    used_ends: list[float] = []
    for h in hits:
        start = max(0.0, h - 1.5)
        end = h + 14.0
        start, end = snap_window_to_words(start, end, words)
        dur = end - start
        if dur < CUTAWAY_MIN_SEC:
            end = start + CUTAWAY_MIN_SEC
            start, end = snap_window_to_words(start, end, words)
        if end - start > CUTAWAY_MAX_SEC:
            end = start + CUTAWAY_MAX_SEC
        if any(abs(end - ue) < CUTAWAY_MIN_GAP for ue in used_ends):
            continue
        if any(start < ue and end > ue - CUTAWAY_MIN_GAP for ue in used_ends):
            continue
        text = _window_text(words, start, end)
        if not CUTAWAY_WORTH_RE.search(text):
            continue
        windows.append((start, end, text))
        used_ends.append(end)
        if len(windows) >= MAX_CUTAWAYS:
            break
    return windows


def _overlap_screen(cover: dict[str, Any] | None, start: float, end: float) -> bool:
    if not cover:
        return False
    for ev in cover.get("events") or []:
        if not isinstance(ev, dict):
            continue
        typ = str(ev.get("type") or "")
        if typ not in ("screen_with_cam", "cam_pip", "screen", "screen_full"):
            continue
        try:
            es = float(ev["start"])
            ee = float(ev["end"])
        except (KeyError, TypeError, ValueError):
            continue
        # Heavy overlap with screen demo → usually skip cutaway.
        overlap = max(0.0, min(end, ee) - max(start, es))
        if overlap > 0.6 * (end - start):
            return True
    return False


def suggest_cutaways(episode: Path) -> dict[str, Any]:
    episode = episode.resolve()
    edit = episode / "edit"
    edl_path = edit / "edl.json"
    if not edl_path.is_file():
        return {
            "cutaways": [],
            "_meta": {"error": "missing edit/edl.json", "counts": {"total": 0}},
        }
    load_edl(edl_path)  # validate
    words = load_cam_words(edit)
    cover = _load_cover(episode)
    cfg = load_project(episode)

    cutaways: list[dict[str, Any]] = []
    recent_families: list[str] = []
    skipped = {"screen_overlap": 0, "none": 0}

    for start, end, text in _idea_windows(words):
        if _overlap_screen(cover, start, end):
            skipped["screen_overlap"] += 1
            continue
        intent = _classify_intent(text)
        duration = end - start
        has_proof = bool(
            re.search(r"(?i)\b(bukti|form|odoo|screenshot|ledger|buku)\b", text)
        )
        family = _pick_family(
            intent,
            duration=duration,
            recent=recent_families,
            has_proof_hint=has_proof,
        )
        title = _title_from_text(text)
        if not title:
            skipped["none"] += 1
            continue

        scene = FAMILY_TO_SCENE.get(family, "minimal")
        kicker = intent.replace("_", " ").title()
        entry: dict[str, Any] = {
            "id": f"suggest-{family}-{len(cutaways)}",
            "family": family,
            "scene": scene,
            "start": round(start, 3),
            "end": round(end, 3),
            "source": "cam",
            "intent": intent,
            "tone": "technical" if family in ("system_map", "flow") else "editorial",
            "copy": {"kicker": kicker, "title": title},
            "kicker": kicker,
            "title": title,
            "cues": {
                "open": round(start + 0.15, 3),
                "ledgerIn": round(start + 0.15, 3),
            },
            "backdrop": {"kind": "cam_blur", "blurPx": 34, "dim": 0.65},
            "note": "suggest:cutaway",
        }
        # Lightweight entity extraction: capitalized-ish tokens / payoff words.
        entities = []
        for m in re.finditer(
            r"(?i)\b(penjualan|pembelian|biaya|saldo|otomatis|studio|odoo)\b",
            text,
        ):
            label = m.group(0)
            label = label[:1].upper() + label[1:]
            at = start + 2.0 + 1.2 * len(entities)
            if at >= end - 1.0:
                break
            entities.append({"label": label, "at": round(at, 3)})
            if len(entities) >= 3:
                break
        if entities:
            entry["entities"] = entities
            entry["feeds"] = [
                {"label": e["label"], "amount": 0, "at": e["at"]} for e in entities
            ]

        issues = validate_brief_against_family(
            family,
            entity_count=len(entities),
            duration_sec=duration,
            intent=intent,
            copy_chars=len(title),
        )
        if any("maxEntities" in i or "maxCopy" in i for i in issues):
            family = "minimal"
            entry["family"] = "minimal"
            entry["scene"] = "minimal"
            entry.pop("entities", None)
            entry.pop("feeds", None)

        cutaways.append(entry)
        recent_families.append(entry["family"])

    return {
        "cutaways": cutaways,
        "_meta": {
            "counts": {
                "total": len(cutaways),
                **{
                    fam: sum(1 for c in cutaways if c.get("family") == fam)
                    for fam in sorted({c.get("family") for c in cutaways})
                },
            },
            "skipped": skipped,
            "has_cover": cover is not None,
            "style": str(cfg.get("style") or "tutorial"),
            "rules": {
                "min_sec": CUTAWAY_MIN_SEC,
                "max_sec": CUTAWAY_MAX_SEC,
                "min_gap": CUTAWAY_MIN_GAP,
                "max_cutaways": MAX_CUTAWAYS,
            },
        },
    }


def write_cutaway_suggest(episode: Path, suggestion: dict[str, Any]) -> Path:
    out = episode / "edit" / "cutaways.suggest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(suggestion, indent=2) + "\n", encoding="utf-8")
    return out


def merge_cutaways_into_cover(
    cover: dict[str, Any],
    cutaways: list[dict[str, Any]],
) -> dict[str, Any]:
    """Replace prior suggest:* cutaways; keep hand-authored ones."""
    existing = [
        c
        for c in (cover.get("cutaways") or [])
        if isinstance(c, dict)
        and not str(c.get("note") or "").startswith("suggest:")
    ]
    cover = dict(cover)
    cover["cutaways"] = existing + list(cutaways)
    return cover
