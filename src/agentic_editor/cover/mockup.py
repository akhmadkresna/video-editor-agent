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
_SURFACES = _COMPONENTS - {"Cursor"}
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
        dur = round(float(sl["durationSec"]), 3)
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
            "layers": [_remap_atsec(layer, local) for layer in (sc.get("layers") or [])],
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
                "sourceOut": round(float(sl["sourceOut"]), 3),
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


# ── suggest (script.md + transcript → skeleton) ────────────────────────────

_STOP = frozenset(
    "yang dan di ke dari itu ini kita kalian saya untuk buat aja atau nggak "
    "sih kok kan nih the a an of to is".split()
)


def _norm_tokens(text: str) -> list[str]:
    text = re.sub(r"[`*_>#\[\]\(\)\"“”…—–]", " ", text.lower())
    text = re.sub(r"<[^>]*>", " ", text)
    return [t for t in re.split(r"[^a-z0-9]+", text) if t and t not in _STOP and len(t) > 2]


def _split_beats(script: str) -> list[tuple[str, str]]:
    beats: list[tuple[str, str]] = []
    head = "intro"
    body: list[str] = []
    for line in script.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            if body:
                beats.append((head, "\n".join(body)))
            head = m.group(1).strip()
            body = []
        else:
            body.append(line)
    if body:
        beats.append((head, "\n".join(body)))
    return [b for b in beats if b[1].strip()]


def _match_time(tokens: list[str], words: list[dict[str, Any]]) -> float | None:
    """Best cam-source start second for a run of transcript words overlapping `tokens`."""
    if not tokens or not words:
        return None
    want = set(tokens[:10])
    wtok = [_norm_tokens(w["text"]) for w in words]
    flat = [(t, words[i]["start"]) for i, ts in enumerate(wtok) for t in ts]
    best_score, best_t = 0, None
    win = 14
    for i in range(len(flat)):
        seg = {t for t, _ in flat[i : i + win]}
        score = len(seg & want)
        if score > best_score:
            best_score, best_t = score, flat[i][1]
    return best_t if best_score >= 2 else None


_NOT_A_SKILL = frozenset(
    "tutorial mockup evidence social edit raw cam screen style bash edl "
    "cover compose ingest".split()
)


def _skill_slug(beats: list[tuple[str, str]]) -> str | None:
    """First backtick token that looks like a skill slug (hyphenated preferred)."""
    cands: list[str] = []
    for head, body in beats[:3]:
        cands += re.findall(r"`([a-z][a-z0-9-]{2,40})`", head + "\n" + body)
    cands = [c for c in cands if c not in _NOT_A_SKILL]
    hyphenated = [c for c in cands if "-" in c]
    return (hyphenated or cands or [None])[0]


def _layers_for(
    body: str, skill: str | None, edit: Path | None = None
) -> list[dict[str, Any]]:
    low = body.lower()
    quote = re.search(r'^\s*>\s*["“](.+?)["”]\s*$', body, re.M) or re.search(
        r"^\s*>\s*(.+)$", body, re.M
    )
    # "where it's from" beat → RepoView with the real SKILL.md
    if re.search(
        r"skill\.md|\bdari mana\b|\brepo\b|github|bikinan|komunitas|"
        r"sebelum saya percaya|anthropics/skills|baca dulu isinya",
        low,
    ):
        info = resolve_skill(skill or "avoid-ai-writing")
        md = fetch_skill_md(skill or "avoid-ai-writing", edit) if edit else None
        return [
            {
                "component": "RepoView",
                "data": {
                    "repoUrl": info["web_url"],
                    "repo": info["repo"],
                    "path": info["path"],
                    "source": info["source"],
                    "markdown": md or "<TODO: SKILL.md not fetched — paste it here>",
                    "scroll": True,
                    "atSec": 0.3,
                },
            }
        ]
    if re.search(r"powerpoint|\.pptx|\bdeck\b|\bslide", low):
        return [{"component": "AppWindow", "data": {"app": "pptx", "content": "mock-deck", "atSec": 0.3}}]
    if re.search(r"excel|\.xlsx|spreadsheet|\bsheet\b|\bcsv\b", low):
        return [{"component": "AppWindow", "data": {"app": "xlsx", "content": "mock-sheet", "atSec": 0.3}}]
    if re.search(r"\bword\b|\.docx|surat|dokumen", low):
        return [{"component": "AppWindow", "data": {"app": "docx", "content": "mock-doc", "atSec": 0.3}}]
    if re.search(r"settings|capabilities|skills|aktif|unggah|upload|toggle", low):
        act = "upload" if re.search(r"unggah|upload|drop|zip", low) else (
            f"toggle:{skill}" if skill else None
        )
        data: dict[str, Any] = {
            "skills": [
                {"name": skill or "avoid-ai-writing", "source": "GitHub", "on": True},
            ],
            "atSec": 2.4,
        }
        if act:
            data["action"] = act
        return [{"component": "SkillsPanel", "data": data}]
    if re.search(r"sebelum|sesudah|before|after|revisi|perbaiki|tandai", low):
        return [
            {
                "component": "DiffPanel",
                "data": {"before": "<TODO before>", "after": "<TODO after>", "atSec": 0.4},
            }
        ]
    turns: list[dict[str, Any]] = []
    if quote:
        turns.append(
            {
                "role": "user",
                "reveal": "type",
                "text": quote.group(1).strip().strip('"“”'),
            }
        )
    turns.append(
        {
            "role": "assistant",
            "reveal": "stream",
            "text": "<TODO assistant reply>",
            **({"skillBadge": f"Pakai skill · {skill}"} if skill else {}),
        }
    )
    chat: list[dict[str, Any]] = [{"component": "ClaudeChat", "data": {"turns": turns}}]
    if quote:
        # cursor texture: rest near the composer, click as the message sends
        chat.append(
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
    return chat


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


_CUE_RE = re.compile(r"\[MOCKUP:\s*(\w+)([^\]]*)\]", re.I)


def _explicit_cues(body: str) -> list[str]:
    """Component names from `[MOCKUP: <Component> …]` cues, in order."""
    out: list[str] = []
    for m in _CUE_RE.finditer(body):
        name = m.group(1)
        hit = next((c for c in _SURFACES if c.lower() == name.lower()), None)
        if hit:
            out.append(hit)
    return out


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
        "role": "assistant", "reveal": "stream", "text": "<TODO assistant reply>",
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
    edit = episode / "edit"
    script_path = edit / "script.md"
    if not script_path.is_file():
        return {"scenes": [], "_meta": {"error": "no edit/script.md"}}
    beats = _split_beats(script_path.read_text(encoding="utf-8"))
    skill = _skill_slug(beats)

    from agentic_editor.cover.suggest import load_cam_words

    words = load_cam_words(edit)
    times: list[float | None] = [_match_time(_norm_tokens(b[1]), words) for b in beats]

    # If the script uses `[MOCKUP: X]` cues anywhere, they are the ONLY
    # source of scenes — other beats stay full cam. A script with no cues
    # falls back to keyword guessing (older scripts) with a loud warning.
    any_cue = any(_explicit_cues(b[1]) for b in beats)

    scenes: list[dict[str, Any]] = []
    unmatched: list[str] = []
    keyword_hints: list[str] = []
    for i, (head, body) in enumerate(beats):
        cues = _explicit_cues(body)
        if any_cue:
            if not cues:
                if _layers_for(body, skill, None)[0]["component"] != "ClaudeChat" or re.search(
                    r"\bTAMPILKAN\b|\bAKSI\b", body
                ):
                    keyword_hints.append(head)
                continue
            specs = [(c, _layers_for_component(c, body, skill, edit)) for c in cues]
        else:
            specs = [(None, _layers_for(body, skill, edit))]

        start = times[i]
        if start is None:
            unmatched.append(head)
        end = next((t for t in times[i + 1 :] if t is not None), None)
        if start is not None and (end is None or end <= start):
            end = start + 25.0

        n = len(specs)
        for j, (_c, layers) in enumerate(specs):
            sub_s = None if start is None else round(start + (end - start) * j / n, 2)
            sub_e = None if start is None else round(start + (end - start) * (j + 1) / n, 2)
            scene_slug = re.sub(r"[^a-z0-9]+", "-", head.lower()).strip("-")[:20] or f"beat-{i}"
            sfx = f"-{layers[0]['component'].lower()}" if n > 1 else ""
            camera = (
                _camera_for(layers, sub_s, sub_e, skill)
                if sub_s is not None and sub_e is not None
                else []
            )
            scenes.append(
                {
                    "id": f"sc-{i:02d}-{scene_slug}{sfx}",
                    "_beat": head,
                    "fromSec": sub_s,
                    "toSec": sub_e,
                    "stage": {
                        "title": skill or "",
                        "chrome": _CHROME.get(layers[0]["component"], "claude"),
                    },
                    "camera": camera,
                    "layers": layers,
                }
            )
    repo_scenes = [
        s for s in scenes if any(l["component"] == "RepoView" for l in s["layers"])
    ]
    return {
        "scenes": scenes,
        "_meta": {
            "beats": len(beats),
            "scenes": len(scenes),
            "mode": "cues" if any_cue else "keyword-guess",
            "keyword_hint_beats": keyword_hints,
            "unmatched_beats": unmatched,
            "skill": skill,
            "has_transcript": bool(words),
            "repo": resolve_skill(skill)["web_url"] if skill else None,
            "repo_md_fetched": any(
                not l["data"]["markdown"].startswith("<TODO")
                for s in repo_scenes
                for l in s["layers"]
                if l["component"] == "RepoView"
            ),
        },
    }


def write_mockup_suggest(episode: Path, data: dict[str, Any]) -> Path:
    out = episode / "edit" / "mockup.suggest.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
