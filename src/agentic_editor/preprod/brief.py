"""Build A-roll script + evidence plan + record guide for evidence episodes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_editor.preprod.research import (
    DEFAULT_USD_IDR,
    fetch_research,
    resolve_channel,
    socialcounts_url,
    vidiq_url,
)
from agentic_editor.project import load_project


def build_brief(
    episode: Path,
    *,
    subject: str | None = None,
    usd_idr: float | None = None,
    fetch: bool = True,
) -> dict[str, Any]:
    """Create brief + research + script + evidence plan (in memory)."""
    cfg = load_project(episode)
    brief_cfg = cfg.get("brief") if isinstance(cfg.get("brief"), dict) else {}
    subj = (
        subject
        or brief_cfg.get("channel")
        or brief_cfg.get("subject")
        or cfg.get("id")
        or episode.name
    )
    channel = resolve_channel(str(subj), overrides=brief_cfg if isinstance(brief_cfg, dict) else None)
    rate = float(usd_idr if usd_idr is not None else brief_cfg.get("usd_idr") or DEFAULT_USD_IDR)

    if fetch:
        research = fetch_research(channel, usd_idr=rate)
    else:
        research = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "usd_idr": rate,
            "sources": {},
            "bands": {},
            "title_rp": None,
            "title_basis": None,
            "errors": ["fetch skipped"],
        }

    title_rp = research.get("title_rp") or "RpXX jt"
    title_line = f"AI + YouTube = {title_rp}/Bulan?"
    evidence_shots = _default_shots(channel, research)
    script_md = render_script_md(channel, research, evidence_shots, title_line=title_line)
    record_md = render_record_md(channel, title_line=title_line)
    plan = {
        "style": str(cfg.get("style") or "evidence"),
        "series": cfg.get("series"),
        "channel": channel,
        "title_line": title_line,
        "title_rp": title_rp,
        "title_basis": research.get("title_basis"),
        "shots": evidence_shots,
        "cue_map": {s["id"]: s for s in evidence_shots},
        "rule": "Real captures only. Run ae evidence-gather after brief.",
    }
    brief = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "episode_id": cfg.get("id") or episode.name,
        "style": str(cfg.get("style") or "evidence"),
        "series": cfg.get("series") or "ai-youtube-idr",
        "channel": channel,
        "title_line": title_line,
        "title_rp": title_rp,
        "title_basis": research.get("title_basis"),
        "usd_idr": rate,
        "next": [
            "Review edit/script.md (teleprompter)",
            "ae evidence-gather .   # framework captures real screenshots",
            "Record cam A-roll reading script.md (speak cue lines aloud)",
            "Drop raw/cam.mp4 -> ae ingest . -> EDL -> evidence-suggest / cover / compose",
        ],
    }
    return {
        "brief": brief,
        "research": research,
        "plan": plan,
        "script_md": script_md,
        "record_md": record_md,
    }


def _default_shots(channel: dict[str, str], research: dict[str, Any]) -> list[dict[str, Any]]:
    yt_id = channel.get("youtube_id") or ""
    handle = channel.get("handle") or ""
    bands = research.get("bands") or {}
    sc = bands.get("socialcounts_28d") or {}
    vq = bands.get("vidiq_monthly") or {}
    shots: list[dict[str, Any]] = []

    if yt_id:
        shots.append(
            {
                "id": "sc-socialcounts",
                "src": "sc-socialcounts.png",
                "url": socialcounts_url(yt_id),
                "label": "SocialCounts",
                "speak": "SocialCounts",
                "callout_value": sc.get("rp_high") or research.get("title_rp") or "RpXX jt",
                "callout_title": f"{sc.get('rp_low', '?')} – {sc.get('rp_high', '?')} (28 hari)",
                "layout": "float",
                "pip": True,
                "note": "Revenue estimate last 28 days — real page capture",
            }
        )
    if handle:
        shots.append(
            {
                "id": "vidiq-earnings",
                "src": "vidiq-earnings.png",
                "url": vidiq_url(handle),
                "label": "vidIQ",
                "speak": "vidIQ",
                "callout_value": vq.get("rp") or "~Rp66 jt",
                "callout_title": "estimasi bulanan vidIQ (bisa beda jauh)",
                "layout": "float",
                "pip": True,
                "note": "vidIQ monthly estimate page",
            }
        )
    yt = channel.get("youtube_url") or ""
    if yt:
        shots.append(
            {
                "id": "yt-channel",
                "src": "yt-channel.png",
                "url": yt,
                "label": "YouTube",
                "speak": "channel YouTube",
                "callout_value": channel.get("title") or "Channel",
                "callout_title": handle or yt,
                "layout": "float",
                "pip": True,
                "note": "Channel home / about for subscriber proof",
            }
        )
    shots.append(
        {
            "id": "free-stack",
            "src": "free-stack.png",
            "url": "",
            "label": "Free stack",
            "speak": "tools gratis",
            "callout_value": "Rp0 tools",
            "callout_title": "ChatGPT · Edge TTS · CapCut · Pexels",
            "layout": "float",
            "pip": True,
            "note": "Optional: capture your free-tool desktop later; diagram overlay can cover this",
            "optional": True,
            "skip_gather": True,
        }
    )
    return shots


def render_script_md(
    channel: dict[str, str],
    research: dict[str, Any],
    shots: list[dict[str, Any]],
    *,
    title_line: str,
) -> str:
    title = channel.get("title") or "channel ini"
    handle = channel.get("handle") or ""
    subs = research.get("subscribers")
    views = research.get("views")
    subs_s = f"~{subs:,}" if isinstance(subs, int) else "ratusan ribu"
    views_s = f"~{views:,}" if isinstance(views, int) else "puluhan juta"
    sc = (research.get("bands") or {}).get("socialcounts_28d") or {}
    vq = (research.get("bands") or {}).get("vidiq_monthly") or {}
    sc_lo = sc.get("rp_low") or "Rp8 jt"
    sc_hi = sc.get("rp_high") or title_line.split("=")[-1].replace("/Bulan?", "").strip()
    vq_rp = vq.get("rp") or "Rp66 jt"

    by_id = {s["id"]: s for s in shots}

    def cue(shot_id: str) -> str:
        s = by_id.get(shot_id) or {}
        return (
            f"[[EVIDENCE:{shot_id}"
            f"|src={s.get('src', '')}"
            f"|callout={s.get('callout_value', '')}"
            f"|source={s.get('label', '')}]]"
        )

    lines = [
        f"# A-roll script — {title_line}",
        "",
        f"**Channel:** {title} {handle}".strip(),
        f"**Title number basis:** {research.get('title_basis') or 'TBD'} -> **{sc_hi}**",
        "",
        "Baca natural. Saat ketemu baris `[[EVIDENCE:...]]`, sebut nama situs/angka di VO",
        "(biar ASR + evidence-suggest bisa nempel). Jangan buru-buru — tahan 1 napas di cue.",
        "",
        "---",
        "",
        "## 1. Hook",
        "",
        f"Channel faceless AI ini, {title}, punya sekitar {subs_s} subscriber",
        f"dan {views_s} total views.",
        f"Pertanyaannya: AI plus YouTube — apakah ini benar-benar {sc_hi} per bulan?",
        "Kita bedah formatnya, bukti estimator publiknya, dan apakah bisa ditiru dengan tools gratis.",
        "",
        "## 2. Evidence — jangan percaya satu angka",
        "",
        "Pertama, bukti — bukan dongeng.",
        cue("sc-socialcounts"),
        f"SocialCounts untuk last twenty-eight days bilang kira-kira {sc_lo} sampai {sc_hi}.",
        "Itu pakai asumsi CPM rendah, sekitar nol koma tujuh sampai dua dolar.",
        "",
        cue("vidiq-earnings"),
        f"vidIQ bisa nunjukin estimasi sekitar {vq_rp} per bulan — beda jauh.",
        "Ini kenapa kita pakai tanda tanya di judul. Estimasi publik, bukan slip gaji.",
        "",
        cue("yt-channel"),
        f"Ini channel aslinya di YouTube: {title}. Kita adaptasi format, bukan nyolong brand.",
        "",
        "## 3. Format yang ditiru",
        "",
        f"Format {title} kira-kira begini: berita AI atau model drop,",
        "hook yang terasa urgent, breakdown singkat, lalu apa artinya buat kamu.",
        "Visualnya faceless — stock, screen, teks. Audionya narasi.",
        "Yang susah bukan softwarenya — yang susah ritme upload-nya.",
        "",
        "## 4. Free stack",
        "",
        cue("free-stack"),
        "Tools gratis cukup: riset di browser, script di ChatGPT atau Gemini,",
        "suara Edge TTS, B-roll Pexels, edit CapCut atau DaVinci.",
        "Biaya tools bisa nol. Biaya waktu: beberapa jam per video, berkali-kali seminggu.",
        "",
        "## 5. Verdict + CTA",
        "",
        f"Verdict: format {title} gampang ditiru dengan tools gratis,",
        f"tapi angka {sc_hi} di judul itu SocialCounts high — bukan jaminan kamu dapat sama.",
        "Kalau kamu mau sistemnya — riset, script, evidence, edit — bukan janji kaya mendadak,",
        "ikut series ini. Part berikutnya kita bedah channel serupa dengan packaging beda.",
        "",
        "---",
        "",
        "## Cue index (agent)",
        "",
    ]
    for s in shots:
        lines.append(
            f"- `{s['id']}` -> `{s['src']}` · speak «{s.get('speak')}» · "
            f"callout {s.get('callout_value')} ({s.get('label')})"
        )
    lines.append("")
    return "\n".join(lines)


def render_record_md(channel: dict[str, str], *, title_line: str) -> str:
    return "\n".join(
        [
            f"# Record checklist — {title_line}",
            "",
            "## Before cam",
            "1. `ae brief . --channel …` already done (you are here).",
            "2. Run `ae evidence-gather .` so `raw/evidence/*.png` exists.",
            "3. Open `edit/script.md` on a second screen / teleprompter.",
            "4. Skim callout numbers so you say them aloud at each `[[EVIDENCE:]]` cue.",
            "",
            "## Record",
            "- One continuous take OK (radio-edit later).",
            "- At each evidence cue: glance off-cam / gesture as if pointing at a screen,",
            "  say the site name + number, pause ~1s.",
            f"- Channel under review: **{channel.get('title')}** {channel.get('handle') or ''}".rstrip(),
            "",
            "## After",
            "1. Save master as `raw/cam.mp4` (do not rename evidence stills).",
            "2. `ae ingest .`",
            "3. Confirm radio-edit → `edit/edl.json` → `ae cut .`",
            "4. `ae evidence-suggest .` (ties ASR deixis to stills) → confirm → `--apply`",
            "5. Add/adjust `callout` overlays → `ae cover .` → `ae compose . --studio`",
            "",
        ]
    )


def write_brief_bundle(episode: Path, bundle: dict[str, Any]) -> dict[str, Path]:
    """Write edit/brief.json, research.json, evidence.plan.json, script.md, record.md."""
    edit = episode / "edit"
    edit.mkdir(parents=True, exist_ok=True)
    (episode / "raw" / "evidence").mkdir(parents=True, exist_ok=True)

    paths = {
        "brief": edit / "brief.json",
        "research": edit / "research.json",
        "plan": edit / "evidence.plan.json",
        "script": edit / "script.md",
        "record": edit / "record.md",
    }
    paths["brief"].write_text(
        json.dumps(bundle["brief"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["research"].write_text(
        json.dumps(bundle["research"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["plan"].write_text(
        json.dumps(bundle["plan"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    paths["script"].write_text(bundle["script_md"], encoding="utf-8")
    paths["record"].write_text(bundle["record_md"], encoding="utf-8")
    return paths
