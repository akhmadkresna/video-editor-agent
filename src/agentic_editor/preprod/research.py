"""Fetch public estimator / channel facts for evidence briefs (no AI stills)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

DEFAULT_USD_IDR = 17900.0
USER_AGENT = (
    "Mozilla/5.0 (compatible; agentic-editor/0.1; +https://github.com/akhmadkresna/video-editor-agent)"
)

# Seeded known subjects for the AI+YouTube IDR series (extend via project.yaml).
KNOWN_CHANNELS: dict[str, dict[str, str]] = {
    "theaigrid": {
        "title": "TheAIGRID",
        "handle": "@theaigrid",
        "youtube_id": "UCbY9xX3_jW5c2fjlZVBI4cg",
        "youtube_url": "https://www.youtube.com/@TheAiGrid",
    },
    "airevolution": {
        "title": "AI Revolution",
        "handle": "@airevolutionx",
        "youtube_id": "",
        "youtube_url": "https://www.youtube.com/@AIRevolution",
    },
}


def _http_get(url: str, *, timeout: float = 25.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def resolve_channel(subject: str, overrides: dict[str, Any] | None = None) -> dict[str, str]:
    """Resolve a channel subject string into title/handle/ids/urls."""
    ov = overrides or {}
    key = re.sub(r"[^a-z0-9]+", "", subject.lower())
    base = dict(KNOWN_CHANNELS.get(key) or {})
    title = str(ov.get("title") or base.get("title") or subject).strip()
    handle = str(ov.get("handle") or base.get("handle") or "").strip()
    if handle and not handle.startswith("@"):
        handle = f"@{handle}"
    youtube_id = str(ov.get("youtube_id") or base.get("youtube_id") or "").strip()
    youtube_url = str(ov.get("youtube_url") or base.get("youtube_url") or "").strip()
    if not youtube_url and handle:
        youtube_url = f"https://www.youtube.com/{handle}"
    elif not youtube_url and youtube_id:
        youtube_url = f"https://www.youtube.com/channel/{youtube_id}"
    return {
        "subject_key": key or "channel",
        "title": title,
        "handle": handle,
        "youtube_id": youtube_id,
        "youtube_url": youtube_url,
    }


def socialcounts_url(youtube_id: str) -> str:
    return f"https://socialcounts.org/youtube-channel-analytics/{youtube_id}"


def vidiq_url(handle: str) -> str:
    h = handle.lstrip("@")
    return f"https://vidiq.com/youtube-stats/channel/@{h}/"


def parse_socialcounts_html(html: str) -> dict[str, Any]:
    """Best-effort parse of SocialCounts public HTML."""
    # Strip comments / collapse tags so "Last <!-- -->29<!-- --> days" still matches.
    cleaned = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"&\w+;", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    out: dict[str, Any] = {"source": "socialcounts", "raw_ok": True}
    m_sub = re.search(
        r"Subscribers\s+(\d[\d,]*)\s*\|\s*Views\s+(\d[\d,]*)\s*\|\s*Videos\s+(\d[\d,]*)",
        cleaned,
        re.I,
    )
    if not m_sub:
        m_meta = re.search(
            r"(\d[\d,]*)\s*subscribers?,\s*([\d.]+)\s*([KMB])\s*views",
            cleaned,
            re.I,
        )
        # also: "398K subscribers, 68.1M views"
        m_meta2 = re.search(
            r"([\d.]+)\s*([KMB])\s*subscribers?,\s*([\d.]+)\s*([KMB])\s*views",
            cleaned,
            re.I,
        )
        if m_meta2:
            out["subscribers"] = int(_scale_num(m_meta2.group(1), m_meta2.group(2)))
            out["views"] = int(_scale_num(m_meta2.group(3), m_meta2.group(4)))
        elif m_meta:
            out["subscribers"] = int(m_meta.group(1).replace(",", ""))
    else:
        out["subscribers"] = int(m_sub.group(1).replace(",", ""))
        out["views"] = int(m_sub.group(2).replace(",", ""))
        out["videos"] = int(m_sub.group(3).replace(",", ""))

    m_rev = re.search(
        r"Last\s*2[89]\s*days:\s*\$([0-9.,]+K?)\s*[\u2013\u2014\-]\s*\$([0-9.,]+K?)",
        cleaned,
        re.I,
    )
    if m_rev:
        out["last_28d_usd_low"] = _parse_money_token(m_rev.group(1))
        out["last_28d_usd_high"] = _parse_money_token(m_rev.group(2))

    m_cpm = re.search(
        r"Based on estimated\s*\$([0-9.]+)\s*[\u2013\u2014\-]\s*\$([0-9.]+)\s*CPM",
        cleaned,
        re.I,
    )
    if m_cpm:
        out["cpm_low"] = float(m_cpm.group(1))
        out["cpm_high"] = float(m_cpm.group(2))
    return out


def _scale_num(num: str, suffix: str) -> float:
    n = float(num.replace(",", ""))
    s = suffix.upper()
    if s == "K":
        return n * 1_000
    if s == "M":
        return n * 1_000_000
    if s == "B":
        return n * 1_000_000_000
    return n


def _parse_money_token(tok: str) -> float:
    t = tok.strip().upper().replace(",", "")
    mult = 1.0
    if t.endswith("K"):
        mult = 1000.0
        t = t[:-1]
    return float(t) * mult


def parse_vidiq_html(html: str) -> dict[str, Any]:
    out: dict[str, Any] = {"source": "vidiq", "raw_ok": True}
    m = re.search(
        r"estimated at\s*\$([0-9.,]+)\s*([KkMm])?\s*monthly",
        html,
        re.I,
    )
    if m:
        n = float(m.group(1).replace(",", ""))
        suf = (m.group(2) or "").upper()
        if suf == "K":
            n *= 1000
        elif suf == "M":
            n *= 1_000_000
        out["monthly_usd"] = n
    m2 = re.search(r"Est\.\s*Monthly Earnings.*?\$([0-9.,]+)\s*([KkMm])?", html, re.S | re.I)
    if m2 and "monthly_usd" not in out:
        n = float(m2.group(1).replace(",", ""))
        suf = (m2.group(2) or "").upper()
        if suf == "K":
            n *= 1000
        elif suf == "M":
            n *= 1_000_000
        out["monthly_usd"] = n
    return out


def usd_to_idr(usd: float, rate: float = DEFAULT_USD_IDR) -> int:
    return int(round(usd * rate))


def format_rp_juta(idr: int) -> str:
    juta = idr / 1_000_000
    if juta >= 10:
        return f"Rp{juta:.0f} jt"
    return f"Rp{juta:.1f} jt".replace(".0 jt", " jt")


def fetch_research(
    channel: dict[str, str],
    *,
    usd_idr: float = DEFAULT_USD_IDR,
) -> dict[str, Any]:
    """Fetch public pages and normalize estimator bands."""
    now = datetime.now(timezone.utc).isoformat()
    research: dict[str, Any] = {
        "fetched_at": now,
        "channel": channel,
        "usd_idr": usd_idr,
        "sources": {},
        "errors": [],
    }

    yt_id = channel.get("youtube_id") or ""
    handle = channel.get("handle") or ""

    if yt_id:
        url = socialcounts_url(yt_id)
        research["sources"]["socialcounts"] = {"url": url}
        try:
            html = _http_get(url)
            parsed = parse_socialcounts_html(html)
            research["sources"]["socialcounts"].update(parsed)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            research["errors"].append(f"socialcounts: {exc}")
            research["sources"]["socialcounts"]["raw_ok"] = False

    if handle:
        url = vidiq_url(handle)
        research["sources"]["vidiq"] = {"url": url}
        try:
            html = _http_get(url)
            parsed = parse_vidiq_html(html)
            research["sources"]["vidiq"].update(parsed)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            research["errors"].append(f"vidiq: {exc}")
            research["sources"]["vidiq"]["raw_ok"] = False

    sc = research["sources"].get("socialcounts") or {}
    vq = research["sources"].get("vidiq") or {}
    bands: dict[str, Any] = {}
    if sc.get("last_28d_usd_low") is not None and sc.get("last_28d_usd_high") is not None:
        lo = float(sc["last_28d_usd_low"])
        hi = float(sc["last_28d_usd_high"])
        bands["socialcounts_28d"] = {
            "usd_low": lo,
            "usd_high": hi,
            "idr_low": usd_to_idr(lo, usd_idr),
            "idr_high": usd_to_idr(hi, usd_idr),
            "rp_low": format_rp_juta(usd_to_idr(lo, usd_idr)),
            "rp_high": format_rp_juta(usd_to_idr(hi, usd_idr)),
        }
    if vq.get("monthly_usd") is not None:
        m = float(vq["monthly_usd"])
        bands["vidiq_monthly"] = {
            "usd": m,
            "idr": usd_to_idr(m, usd_idr),
            "rp": format_rp_juta(usd_to_idr(m, usd_idr)),
        }

    # Title number = SocialCounts high when available (conservative public high).
    title_rp = None
    title_basis = None
    if "socialcounts_28d" in bands:
        title_rp = bands["socialcounts_28d"]["rp_high"]
        title_basis = "socialcounts_last_28d_high"
    elif "vidiq_monthly" in bands:
        title_rp = bands["vidiq_monthly"]["rp"]
        title_basis = "vidiq_monthly"

    research["bands"] = bands
    research["title_rp"] = title_rp
    research["title_basis"] = title_basis
    research["subscribers"] = sc.get("subscribers")
    research["views"] = sc.get("views")
    research["videos"] = sc.get("videos")
    return research


def dumps_research(research: dict[str, Any]) -> str:
    return json.dumps(research, indent=2, ensure_ascii=False) + "\n"
