"""Drawn-screen ("mockup") scenes for `style: mockup` (Claude Skill Lab).

The pipeline half of the feature whose Remotion half lives in
``packages/remotion-kit/src/components/mockup/``. Three jobs:

* ``load_mockup``          — Mist tokens + MockCam config → ``presentation.mockup``
* ``build_timeline_mockups`` — remap ``cover["mockups"]`` (cam source seconds)
  onto the output timeline, plus a ``pip_corner`` cam clip per scene so the
  host still composites into the frame (shot grammar: full cam ⇄ mockup+PIP,
  never full-frame b-roll).
* ``suggest_mockups``      — draft ``edit/mockup.suggest.json`` from
  ``edit/script.md`` + the cam transcript.

``edit/mockup.json`` authors every time in **cam source seconds**; the remap
converts scene windows to output time and every inner ``atSec`` (camera
keyframes, chat turns, cursor waypoints) to **scene-local** seconds, exactly
like ``build_timeline_cutaways`` does for cutaway cues.
"""

from __future__ import annotations

import difflib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from agentic_editor.cover.style_load import _deep_merge, _load_style_yaml
from agentic_editor.paths import framework_home

# ── Mist defaults ── mirror packages/remotion-kit/src/types.ts DEFAULT_MOCK_STYLE.
DEFAULT_MOCK: dict[str, Any] = {
    "stageBg": "#eceff1",
    "window": "#fdfefe",
    "windowBorder": "#dee3e6",
    "windowShadow": (
        "0 18px 44px -24px rgba(38,58,68,0.24), 0 2px 8px -4px rgba(38,58,68,0.10)"
    ),
    "rail": "#f4f6f7",
    "railLine": "#e6eaec",
    "chromeTitle": "#7d878d",
    "chromeDot": "#c3ccd1",
    "userBubble": "#eef2f4",
    "userInk": "#293136",
    "asstInk": "#3a434b",
    "badgeBg": "#e9eef0",
    "badgeInk": "#496573",
    "chipBorder": "#d8dfe2",
    "chipInk": "#79848b",
    "inputBg": "#f1f4f5",
    "inputInk": "#98a2a8",
    "caret": "#496573",
    "cursor": "#2f3a40",
    "pipGradient": "linear-gradient(150deg, #ccd5da, #a4b2ba)",
    "pipRing": "rgba(255,255,255,0.60)",
    "diffDel": "#b1566b",
    "diffAdd": "#5c8a68",
    "cam": {
        "easeMs": 420,
        "holdMinSec": 1.2,
        "scales": {"establish": 1.0, "read": 1.2, "focus": 1.45},
        "maxScale": 1.6,
        "followGain": 0.12,
        "settleAfterRead": True,
        "intensity": "calm",
    },
}


def load_mockup(style_name: str = "mockup") -> dict[str, Any]:
    """Mist tokens + MockCam config, merged from ``styles/<name>/style.md``.

    Returned dict is passed straight to ``<MockupLayer style=…>`` so it must
    match the TS ``MockStyle`` shape (camelCase, ``cam`` nested).
    """
    cfg = _deep_merge({}, DEFAULT_MOCK)
    parsed = _load_style_yaml(style_name)
    mk = parsed.get("mockup")
    if isinstance(mk, dict):
        cfg = _deep_merge(cfg, mk)
    cam = parsed.get("mock_cam")
    if isinstance(cam, dict):
        cfg["cam"] = _deep_merge(cfg["cam"], cam)
    return cfg


# ── EDL remap ──────────────────────────────────────────────────────────────

_COMPONENTS = frozenset(
    {"ClaudeChat", "DiffPanel", "Cursor", "AppWindow", "SkillsPanel", "RepoView"}
)
_CAM_STATES = frozenset({"establish", "read", "focus"})


# ── skill → GitHub source ─────────────────────────────────────────────────

_SKILL_MD_MAX = 4200  # chars of SKILL.md baked into the mock


def _skill_registry() -> dict[str, Any]:
    path = (
        framework_home()
        / "styles"
        / "series"
        / "claude-skill-lab"
        / "skills.yaml"
    )
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_skill(slug: str) -> dict[str, str]:
    """Registry entry → {source, repo, branch, path, web_url, raw_url}.
    Unknown slug → anthropics/skills + skills/<slug>."""
    reg = _skill_registry().get(slug) or {}
    repo = str(reg.get("repo") or "anthropics/skills")
    branch = str(reg.get("branch") or "main")
    path = str(reg.get("path", f"skills/{slug}")).strip("/")
    source = str(reg.get("source") or ("Anthropic" if repo == "anthropics/skills" else "community"))
    seg = f"{path}/" if path else ""
    raw = str(reg.get("skill_md") or f"https://raw.githubusercontent.com/{repo}/{branch}/{seg}SKILL.md")
    web = f"https://github.com/{repo}" + (f"/tree/{branch}/{path}" if path else "")
    return {
        "source": source,
        "repo": repo,
        "branch": branch,
        "path": path,
        "web_url": web,
        "raw_url": raw,
    }


def fetch_skill_md(slug: str, edit: Path) -> str | None:
    """Real SKILL.md text (cached under edit/.mockup-cache/). None if offline."""
    cache = edit / ".mockup-cache" / f"{slug}.SKILL.md"
    if cache.is_file():
        return cache.read_text(encoding="utf-8")[:_SKILL_MD_MAX]
    url = resolve_skill(slug)["raw_url"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agentic-editor/mockup"})
        with urllib.request.urlopen(req, timeout=8) as r:  # noqa: S310 (https only)
            if r.status != 200:
                return None
            text = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text[:_SKILL_MD_MAX]


def _best_source_slice(
    edl: dict[str, Any], start: float, end: float
) -> dict[str, float] | None:
    """Longest contiguous cam slice of ``[start, end)`` as
    ``{fromSec, durationSec, sourceIn, sourceOut}`` in output/source seconds."""
    if end <= start:
        return None
    out_t = 0.0
    best: dict[str, float] | None = None
    for r in edl.get("ranges") or []:
        rs = float(r["start"])
        re_ = float(r["end"])
        dur = max(0.0, re_ - rs)
        if str(r.get("source") or "cam") != "cam":
            out_t += dur
            continue
        ov_s = max(start, rs)
        ov_e = min(end, re_)
        if ov_e > ov_s + 1e-4:
            cand = {
                "fromSec": out_t + (ov_s - rs),
                "durationSec": ov_e - ov_s,
                "sourceIn": ov_s,
                "sourceOut": ov_e,
            }
            if best is None or cand["durationSec"] > best["durationSec"]:
                best = cand
        out_t += dur
    return best


def _remap_atsec(obj: Any, local) -> Any:
    """Deep-copy `obj`, rewriting any ``atSec`` key through ``local``."""
    if isinstance(obj, dict):
        return {
            k: (local(v) if k == "atSec" and isinstance(v, (int, float)) else _remap_atsec(v, local))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_remap_atsec(v, local) for v in obj]
    return obj


_TODO_RE = re.compile(r"^\s*<TODO", re.I)


def _word_spans(text: str) -> list[tuple[str, int, int]]:
    """``[(token, char_start, char_end)]`` for every whitespace-delimited run."""
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\S+", text)]


def _merge_spans(spans: list[list[int]]) -> list[list[int]]:
    """Coalesce spans that touch or are separated only by whitespace."""
    if not spans:
        return []
    spans = sorted(spans)
    out = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def diff_marks(
    before: str, after: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Word-level diff of ``before`` vs ``after`` → DiffPanel highlight marks.

    Returns ``(beforeMarks, afterMarks)`` — ``{"type": "del"|"add",
    "span": [start_char, end_char]}`` ranges the renderer strikes / underlines.
    Removed/changed words are ``del`` on the *before* side, inserted/changed
    words are ``add`` on the *after* side.
    """
    b_tok = _word_spans(before)
    a_tok = _word_spans(after)
    if not b_tok or not a_tok:
        return [], []
    sm = difflib.SequenceMatcher(
        None, [t[0] for t in b_tok], [t[0] for t in a_tok], autojunk=False
    )
    b_raw: list[list[int]] = []
    a_raw: list[list[int]] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace") and i2 > i1:
            b_raw.append([b_tok[i1][1], b_tok[i2 - 1][2]])
        if op in ("insert", "replace") and j2 > j1:
            a_raw.append([a_tok[j1][1], a_tok[j2 - 1][2]])
    b_marks = [{"type": "del", "span": s} for s in _merge_spans(b_raw)]
    a_marks = [{"type": "add", "span": s} for s in _merge_spans(a_raw)]
    return b_marks, a_marks


def _inject_diff_marks(layer: dict[str, Any]) -> dict[str, Any]:
    """Add auto ``beforeMarks``/``afterMarks`` to a DiffPanel layer with real
    before/after text and no author-supplied marks. Returns the layer."""
    if not isinstance(layer, dict) or layer.get("component") != "DiffPanel":
        return layer
    d = layer.get("data")
    if not isinstance(d, dict):
        return layer
    before, after = d.get("before"), d.get("after")
    if not isinstance(before, str) or not isinstance(after, str):
        return layer
    if _TODO_RE.match(before) or _TODO_RE.match(after):
        return layer
    if d.get("beforeMarks") or d.get("afterMarks"):
        return layer  # author override wins
    b_marks, a_marks = diff_marks(before, after)
    if b_marks:
        d["beforeMarks"] = b_marks
    if a_marks:
        d["afterMarks"] = a_marks
    return layer


def build_timeline_mockups(
    edl: dict[str, Any],
    cover: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(timeline_mockups, pip_clips)``.

    * ``timeline_mockups`` — one entry per authored scene, output-time
      ``fromSec``/``durationSec``, every inner ``atSec`` made scene-local.
    * ``pip_clips`` — a ``pip_corner`` cam clip per scene (extend
      ``timeline["clips"]`` with these).
    """
    scenes_in = (cover or {}).get("mockups") or []
    out_scenes: list[dict[str, Any]] = []
    pip_clips: list[dict[str, Any]] = []
    cam_src_max = max(
        (float(r["end"]) for r in (edl.get("ranges") or [])
         if str(r.get("source") or "cam") == "cam"),
        default=0.0,
    )
    for idx, sc in enumerate(scenes_in):
        try:
            start = float(sc["fromSec"])
            end = float(sc.get("toSec", sc.get("fromSec", 0)) or 0)
            if "toSec" not in sc and "durationSec" in sc:
                end = start + float(sc["durationSec"])
        except (KeyError, TypeError, ValueError):
            continue
        sl = _best_source_slice(edl, start, end)
        if sl is None:
            continue
        from_sec = round(float(sl["fromSec"]), 3)
        # On-screen length: the surviving cam slice, but never so short the
        # scene just flashes — a mockup is an illustration laid over
        # continuous VO, so hold at least `_MIN_MOCK_SEC` even when the radio
        # edit gutted the trigger window. Never exceed the authored span.
        authored = max(0.0, end - start)
        survived = float(sl["durationSec"])
        dur = round(min(authored, max(survived, _MIN_MOCK_SEC)), 3) if authored else round(survived, 3)
        if dur < 0.4:
            continue

        def local(src_sec: float, _start=start, _dur=dur) -> float:
            return round(max(0.0, min(_dur, float(src_sec) - _start)), 3)

        scene_id = str(sc.get("id") or f"mock-{idx}")
        entry: dict[str, Any] = {
            "id": scene_id,
            "fromSec": from_sec,
            "durationSec": dur,
            "stage": sc.get("stage") or {},
            "camera": [
                {**kf, "atSec": local(kf.get("atSec", 0))}
                for kf in (sc.get("camera") or [])
                if str(kf.get("state")) in _CAM_STATES
            ],
            "layers": [
                _inject_diff_marks(_remap_atsec(layer, local))
                for layer in (sc.get("layers") or [])
            ],
        }
        for opt in ("in", "out"):
            if opt in sc:
                entry[opt] = sc[opt]
        out_scenes.append(entry)

        pip_clips.append(
            {
                "id": f"mpip-{scene_id}",
                "track": "overlay",
                "source": "cam",
                "sourceIn": round(float(sl["sourceIn"]), 3),
                # cover the whole (possibly floored) scene; may run a little
                # past the kept slice into trimmed cam — fine, the bubble is
                # muted and visual-only.
                "sourceOut": round(
                    min(float(sl["sourceIn"]) + dur, cam_src_max or float(sl["sourceOut"])),
                    3,
                ),
                "fromSec": from_sec,
                "durationSec": dur,
                "layout": "pip_corner",
                "framing": "medium",
                "scale": 1.0,
                "motion": "hold",
                # This clip and the underlying main a_roll "full" clip source
                # the *same* cam audio for the *same* window (the pip bubble
                # is a picture-in-picture of the same take) — both unmuted
                # plays the voiceover twice, phasing/doubling audibly. The
                # main clip carries the continuous voiceover across cuts;
                # the pip bubble is visual only.
                "muted": True,
            }
        )
    return out_scenes, pip_clips


# ── validation (hand-rolled — repo has no jsonschema dep) ───────────────────


def validate_mockup(data: dict[str, Any]) -> list[str]:
    """Return a list of human-readable errors ("" = valid)."""
    errs: list[str] = []
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return ["top level: `scenes` must be a non-empty list"]
    todo = sorted(
        set(re.findall(r"<TODO[^>]*>", json.dumps(scenes, ensure_ascii=False)))
    )
    if todo:
        errs.append(
            "unfilled placeholder(s) — replace before --apply: " + ", ".join(todo)
        )
    for i, sc in enumerate(scenes):
        tag = f"scene[{i}] ({sc.get('id', '?')})"
        if not isinstance(sc, dict):
            errs.append(f"{tag}: must be an object")
            continue
        if not isinstance(sc.get("id"), str):
            errs.append(f"{tag}: `id` (string) required")
        has_span = isinstance(sc.get("fromSec"), (int, float)) and (
            isinstance(sc.get("toSec"), (int, float))
            or isinstance(sc.get("durationSec"), (int, float))
        )
        if not has_span:
            errs.append(f"{tag}: need numeric `fromSec` + `toSec` (cam source seconds)")
        layers = sc.get("layers")
        if not isinstance(layers, list) or not layers:
            errs.append(f"{tag}: `layers` must be a non-empty list")
            continue
        surfaces = 0
        for j, ly in enumerate(layers):
            lt = f"{tag} layer[{j}]"
            comp = ly.get("component") if isinstance(ly, dict) else None
            if comp not in _COMPONENTS:
                errs.append(f"{lt}: unknown component {comp!r} (one of {sorted(_COMPONENTS)})")
                continue
            d = ly.get("data") or {}
            if comp == "ClaudeChat":
                surfaces += 1
                if not isinstance(d.get("turns"), list) or not d["turns"]:
                    errs.append(f"{lt}: ClaudeChat needs `data.turns[]`")
            elif comp == "DiffPanel":
                surfaces += 1
                if not (d.get("before") and d.get("after")):
                    errs.append(f"{lt}: DiffPanel needs `data.before` and `data.after`")
            elif comp == "AppWindow":
                surfaces += 1
                if not d.get("app"):
                    errs.append(f"{lt}: AppWindow needs `data.app`")
            elif comp == "SkillsPanel":
                surfaces += 1
                if not isinstance(d.get("skills"), list) or not d["skills"]:
                    errs.append(f"{lt}: SkillsPanel needs `data.skills[]`")
            elif comp == "RepoView":
                surfaces += 1
                if not isinstance(d.get("markdown"), str) or not d["markdown"].strip():
                    errs.append(f"{lt}: RepoView needs `data.markdown` (SKILL.md text)")
                if not isinstance(d.get("repoUrl"), str):
                    errs.append(f"{lt}: RepoView needs `data.repoUrl`")
            elif comp == "Cursor":
                if not isinstance(d.get("path"), list) or not d["path"]:
                    errs.append(f"{lt}: Cursor needs `data.path[]`")
        if surfaces == 0:
            errs.append(
                f"{tag}: needs one surface layer "
                "(ClaudeChat/DiffPanel/AppWindow/SkillsPanel/RepoView)"
            )
        for k, kf in enumerate(sc.get("camera") or []):
            if not isinstance(kf, dict) or kf.get("state") not in _CAM_STATES:
                errs.append(f"{tag} camera[{k}]: `state` must be establish|read|focus")
            if not isinstance(kf.get("atSec"), (int, float)):
                errs.append(f"{tag} camera[{k}]: numeric `atSec` required")
    return errs


# ── suggest (cam transcript → skeleton) ────────────────────────────────────
#
# The episode script is a *recording guide*, not an editing source of truth —
# the speaker ad-libs, so matching script beats back onto the transcript
# placed scenes on the wrong spoken moment. Placement is driven entirely by
# the cam transcript now: spoken-phrase triggers, anchored to ASR word times.
# `edit/mockup.json` stays the suggest→fill→confirm→apply artifact.

#: component → spoken trigger phrases (lowercase). A multi-word phrase is a
#: strong signal (confidence "high"); a bare word in ``_GENERIC_TRIGGERS`` is
#: weak ("low") and every scene it places is flagged for review.
_MOCKUP_TRIGGERS: dict[str, list[str]] = {
    "RepoView": [
        "repo", "reponya", "repo-nya", "github", "di github", "sumbernya",
        "sumber skill", "skill.md", "isi skill", "isinya", "anthropics/skills",
        "bikinan komunitas", "dari komunitas", "baca dulu isinya",
    ],
    "SkillsPanel": [
        "settings", "setting", "pengaturan", "capabilities", "kapabilitas",
        "bagian skill", "menu skill", "aktifin skill", "aktifkan skill",
        "toggle", "unggah skill", "upload skill", "nyalain skill",
    ],
    "DiffPanel": [
        "sebelum", "sebelumnya", "sesudah", "setelah", "before", "after",
        "jadi begini", "dirapikan", "hasil revisi", "yang ditandai",
        "sebelum sesudah", "versi sebelum", "versi sesudah",
    ],
    "AppWindow": [
        "kebuka di", "powerpoint", "pptx", "excel", "xlsx",
        "word", "docx", "decknya", "slidenya", "sheetnya", "dokumennya",
    ],
}

#: Bare single-word triggers — always low confidence.
_GENERIC_TRIGGERS = frozenset(
    {"repo", "github", "settings", "setting", "pengaturan", "toggle",
     "sebelum", "sesudah", "setelah", "before", "after", "powerpoint",
     "pptx", "excel", "xlsx", "word", "docx"}
)

#: Spoken lead-ins that introduce a prompt the speaker is about to read aloud.
#: The words after one of these become the ClaudeChat user turn.
_PROMPT_LEADINS: list[str] = [
    "aku bilang", "gue bilang", "saya bilang", "aku ketik", "gue ketik",
    "saya ketik", "aku minta", "minta claude", "aku suruh", "gue suruh",
    "aku tulis", "gue tulis", "promptnya", "prompt-nya", "prompt nya",
    "nge-prompt", "nge-prom", "prompt seperti ini", "prompt-nya seperti ini",
    "kira-kira gini", "gini kira-kira", "i said", "i typed", "i asked",
]

#: Per-component planned scene length. A drawn scene runs this long and no
#: longer; cam carries the time between scenes (and gives A-roll overlays
#: somewhere to live). Only shortened when the next trigger is close.
_DEFAULT_DWELL_SEC: dict[str, float] = {
    "ClaudeChat": 22.0,
    "DiffPanel": 12.0,
    "RepoView": 14.0,
    "SkillsPanel": 10.0,
    "AppWindow": 10.0,
}

#: Minimum cam breath kept between a drawn scene and the next trigger, so
#: mockups never butt straight into each other.
_SCENE_GAP_SEC = 2.0

#: Floor for a drawn scene's on-screen length after the radio edit remap —
#: below this a before/after wipe or a scroll has no time to read.
_MIN_MOCK_SEC = 8.0

_DEFAULT_MIN_GAP_SEC = 12.0
_PROMPT_MIN_WORDS = 3
_PROMPT_MAX_WORDS = 16


def load_mockup_triggers(
    style_name: str = "mockup",
) -> tuple[dict[str, list[str]], float]:
    """Trigger table + min-gap, with optional ``mockup_suggest:`` overrides
    from ``styles/<style>/style.md``."""
    table = {k: list(v) for k, v in _MOCKUP_TRIGGERS.items()}
    gap = _DEFAULT_MIN_GAP_SEC
    parsed = _load_style_yaml(style_name).get("mockup_suggest")
    if isinstance(parsed, dict):
        over = parsed.get("triggers")
        if isinstance(over, dict):
            for comp, phrases in over.items():
                if comp in table and isinstance(phrases, list):
                    table[comp] = [
                        str(p).lower().strip() for p in phrases if str(p).strip()
                    ]
        if isinstance(parsed.get("min_gap_sec"), (int, float)):
            gap = float(parsed["min_gap_sec"])
    return table, gap


def _word_stream(words: list[dict[str, Any]]) -> tuple[str, list[tuple[int, int, int]]]:
    """Lowercase ``"w0 w1 w2 …"`` haystack + ``[(char_start, char_end, word_i)]``."""
    parts: list[str] = []
    spans: list[tuple[int, int, int]] = []
    cursor = 0
    for i, w in enumerate(words):
        tok = str(w["text"]).lower()
        if parts:
            parts.append(" ")
            cursor += 1
        spans.append((cursor, cursor + len(tok), i))
        parts.append(tok)
        cursor += len(tok)
    return "".join(parts), spans


def _word_at_char(spans: list[tuple[int, int, int]], idx: int) -> int | None:
    for cs, ce, i in spans:
        if cs <= idx < ce:
            return i
    return None


#: Crude Indonesian affixes — enough to tie "ditandai" / "menandai" /
#: "tandai" together, and to treat a slug's hyphens as word breaks.
_ID_PREFIXES = ("meng", "meny", "mem", "men", "peng", "pen", "nge", "per",
                "ter", "ber", "ke", "se", "di", "me", "pe")
_ID_SUFFIXES = ("kannya", "annya", "nya", "kan", "an", "i")

#: A window scores a fuzzy hit at/above this ratio (1.0 = exact after
#: normalisation). Fuzzy-only hits are always demoted to "low" confidence.
#: Only *multi-word* triggers are fuzzed — fuzzing bare words ("settings",
#: "sesudah") just collapses them into every near-homophone the speaker
#: happens to use ("aturan", "sudah").
_FUZZY_MIN = 0.88


def _norm_phrase(s: str) -> str:
    """Lowercase; drop ``. - _`` joins so ``avoid-ai-writing`` == ``avoid ai
    writing`` and ``nge-prompt`` == ``nge prompt``; collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[.\-_]", " ", s.lower())).strip()


def _stem_id(tok: str) -> str:
    """Strip at most one prefix + one suffix. ``ditandai`` -> ``tandai`` ->
    (prefix ``di``) not stripped again; ``menandai`` -> ``nandai``… good
    enough for equality tests, not linguistically correct."""
    t = re.sub(r"[.\-_]", "", tok.lower())
    for suf in _ID_SUFFIXES:
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            t = t[: -len(suf)]
            break
    for pre in _ID_PREFIXES:
        if t.startswith(pre) and len(t) - len(pre) >= 3:
            t = t[len(pre) :]
            break
    return t


def _fuzzy_phrase_words(
    words: list[dict[str, Any]], phrase: str
) -> list[tuple[int, float]]:
    """``[(word_i, ratio)]`` where ``phrase`` ~matches a short spoken window,
    tolerating ASR spelling drift and Indonesian affixes. Windows of k-1..k+1
    tokens are tried so token-count drift ("dia tandai" ~ "ditandai") still
    lands."""
    pn = _norm_phrase(phrase)
    ps = pn.split()
    k = len(ps)
    if k < 2:  # bare words: exact-match only
        return []
    p_stems = [_stem_id(x) for x in ps]
    toks = [str(w["text"]) for w in words]
    n = len(toks)
    out: list[tuple[int, float]] = []
    i = 0
    while i < n:
        best = 0.0
        for j in (k - 1, k, k + 1):
            if j < 1 or i + j > n:
                continue
            win = _norm_phrase(" ".join(toks[i : i + j]))
            r = difflib.SequenceMatcher(None, win, pn).ratio()
            # morphology bonus, but only as a nudge and only when the raw
            # ratio already shows real overlap — a stem coincidence alone
            # ("pengaturan" -> "aturan") must not fire.
            if (
                j == k
                and r >= 0.6
                and [_stem_id(x) for x in toks[i : i + j]] == p_stems
            ):
                r = max(r, 0.9)
            best = max(best, r)
        if best >= _FUZZY_MIN:
            out.append((i, round(best, 2)))
            i += k
        else:
            i += 1
    return out


def _phrase_hits(
    hay: str, spans: list[tuple[int, int, int]], phrase: str
) -> list[int]:
    """Word indices where ``phrase`` occurs on whitespace boundaries."""
    out: list[int] = []
    start = 0
    while True:
        idx = hay.find(phrase, start)
        if idx < 0:
            break
        end = idx + len(phrase)
        left_ok = idx == 0 or hay[idx - 1] == " "
        right_ok = end == len(hay) or hay[end] == " "
        if left_ok and right_ok:
            wi = _word_at_char(spans, idx)
            if wi is not None:
                out.append(wi)
        start = end
    return out


def _scan_triggers(
    words: list[dict[str, Any]], table: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """All ``{component, tSec, word_i, trigger, confidence}`` trigger hits."""
    hay, spans = _word_stream(words)
    hits: list[dict[str, Any]] = []
    for comp, phrases in table.items():
        seen: set[int] = set()
        for ph in sorted({p for p in phrases if p}, key=len, reverse=True):
            exact = set(_phrase_hits(hay, spans, ph))
            fuzzy = {wi: r for wi, r in _fuzzy_phrase_words(words, ph)}
            for wi in sorted(exact | set(fuzzy)):
                if wi in seen:
                    continue
                seen.add(wi)
                is_exact = wi in exact
                # a bare generic word, or a match only reached by fuzzing,
                # is weak — flag its scene for review.
                conf = (
                    "high"
                    if is_exact and ph not in _GENERIC_TRIGGERS
                    else "low"
                )
                ctx = " ".join(
                    str(w["text"]).lower()
                    for w in words[max(0, wi - 2) : wi + 8]
                )
                hits.append(
                    {
                        "component": comp,
                        "tSec": float(words[wi]["start"]),
                        "word_i": wi,
                        "trigger": ph,
                        "context": ctx,
                        "confidence": conf,
                        "match": "exact" if is_exact else f"fuzzy:{fuzzy[wi]:.2f}",
                    }
                )
    return hits


#: Filler the speaker drops between "…prompt" and the actual read-aloud
#: prompt ("kira-kira gini seperti ini kurang lebih, tolong …").
_PROMPT_FILLER_RE = re.compile(
    r"^(seperti|kira|kira-kira|kurang|lebih|gini|begini|kayak|gitu|ini|itu|"
    r"ya|nya|jadi|nah|oke|adalah)[.,]?$",
    re.I,
)


def _extract_spoken_prompt(words: list[dict[str, Any]], after_i: int) -> str | None:
    """Words following a prompt lead-in, up to a clause break / word cap.
    A leading run of filler is skipped so the user turn starts on the real
    prompt."""
    window = words[after_i : after_i + _PROMPT_MAX_WORDS + 12]
    lead = 0
    for w in window:
        if _PROMPT_FILLER_RE.match(str(w["text"]).strip()):
            lead += 1
        else:
            break
    if lead < len(window):
        window = window[lead:]
    picked: list[str] = []
    for w in window[: _PROMPT_MAX_WORDS + 4]:
        tok = str(w["text"]).strip()
        if not tok:
            continue
        picked.append(tok.strip('"“”'))
        if tok.rstrip()[-1:] in ".?!" and len(picked) >= _PROMPT_MIN_WORDS:
            break
        if len(picked) >= _PROMPT_MAX_WORDS:
            break
    if len(picked) < _PROMPT_MIN_WORDS:
        return None
    text = " ".join(picked).strip(" ,;:").rstrip(".")
    return text or None


def _scan_prompts(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Spoken-prompt hits → ClaudeChat (high confidence, wins ties). Also
    grabs the narration right after the read-aloud prompt so the drawn reply
    can echo what the speaker says Claude does next."""
    hay, spans = _word_stream(words)
    hits: list[dict[str, Any]] = []
    seen: set[int] = set()
    for lead in sorted(_PROMPT_LEADINS, key=len, reverse=True):
        n_lead = len(_norm_phrase(lead).split())
        starts = set(_phrase_hits(hay, spans, lead))
        starts |= {wi for wi, _ in _fuzzy_phrase_words(words, lead)}
        for wi in sorted(starts):
            if wi in seen:
                continue
            text = _extract_spoken_prompt(words, wi + n_lead)
            if not text:
                continue
            seen.add(wi)
            after_i = wi + n_lead + len(text.split())
            narration = " ".join(
                str(w["text"]) for w in words[after_i : after_i + 40]
            ).strip()
            hits.append(
                {
                    "component": "ClaudeChat",
                    "tSec": float(words[wi]["start"]),
                    "word_i": wi,
                    "trigger": lead,
                    "confidence": "high",
                    "promptText": text,
                    "narrationAfter": narration,
                }
            )
    return hits


def _dedupe_hits(
    hits: list[dict[str, Any]], *, min_gap_sec: float
) -> list[dict[str, Any]]:
    """Collapse repeat hits of the same component within ``min_gap_sec``;
    a high-confidence hit replaces a low one it shadows. Then drop any scene
    starting within 2s of the previous kept scene (keep the stronger)."""
    per_comp: dict[str, list[dict[str, Any]]] = {}
    for h in sorted(hits, key=lambda x: (x["tSec"], 0 if x["confidence"] == "high" else 1)):
        kept = per_comp.setdefault(h["component"], [])
        if kept and h["tSec"] - kept[-1]["tSec"] < min_gap_sec:
            # Two distinct spoken prompts are distinct demos — keep both even
            # when close (a real episode spaces them out anyway).
            distinct_prompt = (
                h.get("promptText")
                and kept[-1].get("promptText")
                and h["promptText"] != kept[-1]["promptText"]
            )
            if distinct_prompt:
                kept.append(h)
                continue
            if h["confidence"] == "high" and kept[-1]["confidence"] == "low":
                kept[-1] = h
            continue
        kept.append(h)

    flat = sorted(
        (h for group in per_comp.values() for h in group), key=lambda x: x["tSec"]
    )
    out: list[dict[str, Any]] = []
    for h in flat:
        if out and h["tSec"] - out[-1]["tSec"] < 2.0:
            if h["confidence"] == "high" and out[-1]["confidence"] == "low":
                out[-1] = h
            continue
        out.append(h)
    return out


def _synth_assistant_reply(
    prompt: str | None, narration: str, skill: str | None
) -> str:
    """A representative drawn reply. The mock is an *ilustrasi*, not a real
    transcript — so this echoes the narration that follows the spoken prompt,
    keeping the drawn screen consistent with what the presenter says Claude
    does next."""
    sk = skill or "skill ini"
    low = re.sub(r"\s+", " ", (narration or "")).strip().lower()
    # order matters: "improve the skill" narration also mentions "pola", so
    # test the add/update intent before the audit catch-all.
    if re.search(r"tambah|update|perbarui|baris|entri|masuk(in|kan)", low):
        body = (
            f"Sudah aku tambahkan pola itu ke {sk} dan aku perbarui "
            "SKILL.md-nya."
        )
    elif re.search(r"tandai|ditandai|highlight|pola|ai-?ism|bau ai", low):
        body = (
            f"Aku audit teksmu pakai {sk}. Bagian yang bunyinya seperti "
            "tulisan AI aku tandai, lalu aku beri versi gantinya yang lebih "
            "natural."
        )
    elif re.search(r"ganti|revisi|rapik|perbaik|benerin|rewrite|natural", low):
        body = f"Ini versi revisinya setelah aku rapikan pakai {sk}."
    else:
        base = (prompt or "permintaanmu").rstrip(".").lower()
        body = f"Oke, aku kerjakan pakai {sk}: {base}."
    return body if len(body) <= 240 else body[:237].rstrip() + "…"


def _layers_for_hit(
    hit: dict[str, Any], skill: str | None, edit: Path | None
) -> list[dict[str, Any]]:
    """Surface (+ optional Cursor) for a trigger hit."""
    comp = hit["component"]
    if comp != "ClaudeChat":
        # `_layers_for_component` reads its `body` arg for AppWindow app-type
        # and SkillsPanel action — feed it the spoken context around the
        # trigger word.
        body = hit.get("context") or hit.get("trigger", "")
        return _layers_for_component(comp, body, skill, edit)

    turns: list[dict[str, Any]] = []
    prompt = hit.get("promptText")
    if prompt:
        turns.append({"role": "user", "reveal": "type", "text": prompt})
    turns.append(
        {
            "role": "assistant",
            "reveal": "stream",
            "text": _synth_assistant_reply(
                prompt, hit.get("narrationAfter", ""), skill
            ),
            **({"skillBadge": f"Pakai skill · {skill}"} if skill else {}),
        }
    )
    out: list[dict[str, Any]] = [{"component": "ClaudeChat", "data": {"turns": turns}}]
    if prompt:
        out.append(
            {
                "component": "Cursor",
                "data": {
                    "path": [
                        {"atSec": 0.4, "point": [0.55, 0.42]},
                        {"atSec": 4.5, "target": "chat.input", "action": "click"},
                        {"atSec": 7.0, "point": [0.62, 0.58]},
                    ]
                },
            }
        )
    return out


def _resolve_episode_skill(
    cfg: dict[str, Any], words: list[dict[str, Any]]
) -> str | None:
    """Episode skill: explicit ``skill:`` in project.yaml, else the registry
    slug the speaker mentions most, else None."""
    sk = cfg.get("skill")
    if isinstance(sk, str) and sk.strip():
        return sk.strip()
    reg = _skill_registry()
    if not reg:
        return None
    # match on the spoken form: "avoid-ai-writing" (slug) == "avoid ai
    # writing" (as said aloud). Normalise both sides before counting.
    hay = _norm_phrase(" ".join(str(w["text"]) for w in words))
    counts = {slug: hay.count(_norm_phrase(slug)) for slug in reg}
    best = max(counts, key=lambda s: counts[s], default=None)
    return best if best and counts[best] > 0 else None


_CHROME = {
    "AppWindow": "app",
    "SkillsPanel": "app",
    "RepoView": "none",
}


def _camera_for(layers: list[dict[str, Any]], start: float, end: float, skill: str | None):
    comp = layers[0]["component"]
    if comp == "AppWindow":
        mid = {"state": "read", "focus": "app.window"}
    elif comp == "SkillsPanel":
        mid = {"state": "read", "focus": f"skills.row.{skill or 'avoid-ai-writing'}"}
    elif comp == "DiffPanel":
        mid = {"state": "read", "focus": "diff.after"}
    elif comp == "RepoView":
        mid = {"state": "read", "focus": "repo.doc"}
    else:
        mid = {"state": "focus", "focus": "chat.input", "track": "caret"}
    span = max(2.0, end - start)
    return [
        {"atSec": round(start, 2), "state": "establish"},
        {"atSec": round(start + min(1.4, span * 0.15), 2), **mid},
        {"atSec": round(end - min(1.2, span * 0.15), 2), "state": "establish"},
    ]


def _layers_for_component(
    comp: str, body: str, skill: str | None, edit: Path | None
) -> list[dict[str, Any]]:
    """One surface (+ optional Cursor) for an explicit `[MOCKUP: comp]` cue."""
    if comp == "RepoView":
        info = resolve_skill(skill or "avoid-ai-writing")
        md = fetch_skill_md(skill or "avoid-ai-writing", edit) if edit else None
        return [{
            "component": "RepoView",
            "data": {
                "repoUrl": info["web_url"], "repo": info["repo"],
                "path": info["path"], "source": info["source"],
                "markdown": md or "<TODO: SKILL.md not fetched — paste it here>",
                "scroll": True, "atSec": 0.3,
            },
        }]
    if comp == "AppWindow":
        app = "pptx" if re.search(r"pptx|deck|slide", body, re.I) else (
            "xlsx" if re.search(r"xlsx|sheet|csv", body, re.I) else "docx"
        )
        content = {"pptx": "mock-deck", "xlsx": "mock-sheet", "docx": "mock-doc"}[app]
        return [{"component": "AppWindow", "data": {"app": app, "content": content, "atSec": 0.3}}]
    if comp == "SkillsPanel":
        act = "upload" if re.search(r"unggah|upload|zip|drop", body, re.I) else (
            f"toggle:{skill}" if skill else None
        )
        d: dict[str, Any] = {"skills": [{"name": skill or "avoid-ai-writing", "source": "GitHub", "on": True}], "atSec": 2.4}
        if act:
            d["action"] = act
        return [{"component": "SkillsPanel", "data": d}]
    if comp == "DiffPanel":
        return [{"component": "DiffPanel", "data": {"before": "<TODO before>", "after": "<TODO after>", "atSec": 0.4}}]
    # ClaudeChat
    quote = re.search(r'^\s*>\s*["“](.+?)["”]\s*$', body, re.M) or re.search(r"^\s*>\s*(.+)$", body, re.M)
    turns: list[dict[str, Any]] = []
    if quote:
        turns.append({"role": "user", "reveal": "type", "text": quote.group(1).strip().strip('"“”')})
    turns.append({
        "role": "assistant", "reveal": "stream",
        "text": _synth_assistant_reply(
            quote.group(1) if quote else None, body, skill
        ),
        **({"skillBadge": f"Pakai skill · {skill}"} if skill else {}),
    })
    out: list[dict[str, Any]] = [{"component": "ClaudeChat", "data": {"turns": turns}}]
    if quote or re.search(r"cursor|klik|kirim", body, re.I):
        out.append({"component": "Cursor", "data": {"path": [
            {"atSec": 0.4, "point": [0.55, 0.42]},
            {"atSec": 4.5, "target": "chat.input", "action": "click"},
            {"atSec": 7.0, "point": [0.62, 0.58]},
        ]}})
    return out


def suggest_mockups(episode: Path) -> dict[str, Any]:
    """Draft ``edit/mockup.suggest.json`` from the cam transcript.

    Placement comes from spoken-phrase triggers (see ``_MOCKUP_TRIGGERS`` /
    ``_scan_prompts``), each anchored to the ASR ``start`` of its trigger
    word. The episode script is not read. Low-confidence scenes are still
    emitted, flagged in ``_meta.low_confidence_scenes`` for review.
    """
    edit = episode / "edit"

    from agentic_editor.cover.suggest import load_cam_words
    from agentic_editor.project import load_project

    words = load_cam_words(edit)
    if not words:
        return {
            "scenes": [],
            "_meta": {
                "error": "no edit/transcripts/cam.json — run `ae ingest .` first",
                "has_transcript": False,
            },
        }

    try:
        cfg = load_project(episode)
    except (FileNotFoundError, ValueError, KeyError):
        cfg = {}
    table, min_gap = load_mockup_triggers("mockup")
    skill = _resolve_episode_skill(cfg, words)

    hits = _dedupe_hits(
        _scan_triggers(words, table) + _scan_prompts(words), min_gap_sec=min_gap
    )
    transcript_end = float(words[-1]["end"])

    scenes: list[dict[str, Any]] = []
    low_conf: list[dict[str, Any]] = []
    for i, h in enumerate(hits):
        start = round(float(h["tSec"]), 2)
        nxt = hits[i + 1]["tSec"] if i + 1 < len(hits) else None
        dwell = _DEFAULT_DWELL_SEC.get(h["component"], 12.0)
        end = start + dwell
        if nxt is not None:
            end = min(end, nxt - _SCENE_GAP_SEC)
        end = round(min(end, transcript_end), 2)
        if end <= start:
            end = round(min(start + 2.0, transcript_end), 2)
        layers = _layers_for_hit(h, skill, edit)
        # Layer-inner atSec are authored scene-local; mockup.json stores every
        # atSec in cam-source seconds (build_timeline_mockups normalises them
        # back). Shift them onto the scene start.
        layers = _remap_atsec(layers, lambda v, _s=start: round(_s + float(v), 3))
        comp = layers[0]["component"]
        scene_id = f"sc-{i:02d}-{comp.lower()}"
        scenes.append(
            {
                "id": scene_id,
                "_trigger": h["trigger"],
                "_match": h.get("match", "exact"),
                "fromSec": start,
                "toSec": end,
                "stage": {
                    "title": skill or "",
                    "chrome": _CHROME.get(comp, "claude"),
                },
                "camera": _camera_for(layers, start, end, skill),
                "layers": layers,
            }
        )
        if h["confidence"] == "low":
            low_conf.append(
                {
                    "id": scene_id,
                    "tSec": start,
                    "component": comp,
                    "trigger": h["trigger"],
                }
            )

    repo_layers = [
        l for s in scenes for l in s["layers"] if l["component"] == "RepoView"
    ]
    synth_reply_scenes = [
        s["id"]
        for s in scenes
        for l in s["layers"]
        if l["component"] == "ClaudeChat"
        for t in l["data"].get("turns", [])
        if t.get("role") == "assistant"
    ]
    fuzzy_scenes = [s["id"] for s in scenes if s.get("_match", "").startswith("fuzzy")]
    return {
        "scenes": scenes,
        "_meta": {
            "mode": "transcript-triggers",
            "scenes": len(scenes),
            "low_confidence_scenes": low_conf,
            "fuzzy_trigger_scenes": fuzzy_scenes,
            "synth_reply_scenes": synth_reply_scenes,
            "skill": skill,
            "has_transcript": True,
            "repo": resolve_skill(skill)["web_url"] if skill else None,
            "repo_md_fetched": any(
                not str(l["data"].get("markdown", "")).startswith("<TODO")
                for l in repo_layers
            ),
        },
    }


def write_mockup_suggest(episode: Path, data: dict[str, Any]) -> Path:
    out = episode / "edit" / "mockup.suggest.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
