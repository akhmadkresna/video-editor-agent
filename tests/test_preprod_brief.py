"""Pre-prod brief + research parsing tests."""

from __future__ import annotations

from pathlib import Path

from agentic_editor.preprod.brief import build_brief, write_brief_bundle
from agentic_editor.preprod.research import (
    format_rp_juta,
    parse_socialcounts_html,
    resolve_channel,
    usd_to_idr,
)


def test_resolve_theaigrid():
    ch = resolve_channel("TheAIGRID")
    assert ch["youtube_id"].startswith("UC")
    assert "youtube.com" in ch["youtube_url"]


def test_parse_socialcounts_sample():
    html = """
    Subscribers 398,346 | Views 68,117,423 | Videos 990
    Last 29 days: $456 – $1.30K
    Based on estimated $0.7–$2 CPM.
    """
    parsed = parse_socialcounts_html(html)
    assert parsed["subscribers"] == 398346
    assert parsed["last_28d_usd_low"] == 456
    assert parsed["last_28d_usd_high"] == 1300
    assert abs(parsed["cpm_low"] - 0.7) < 1e-6


def test_parse_socialcounts_comment_broken_label():
    html = (
        'Last <!-- -->29<!-- --> days:</span> '
        '<span>$456 \u2013 $1.30K</span>'
        '<p>Based on estimated $<!-- -->0.7<!-- -->\u2013$<!-- -->2 CPM</p>'
        'content="398K subscribers, 68.1M views"'
    )
    parsed = parse_socialcounts_html(html)
    assert parsed["last_28d_usd_low"] == 456
    assert parsed["last_28d_usd_high"] == 1300
    assert parsed["subscribers"] == 398000
    assert parsed["views"] == 68_100_000


def test_rp_formatting():
    assert "jt" in format_rp_juta(usd_to_idr(1320, 17900))


def test_brief_offline_writes_script(tmp_path: Path):
    (tmp_path / "project.yaml").write_text(
        "id: part1\nstyle: evidence\nseries: ai-youtube-idr\n"
        "brief:\n  channel: TheAIGRID\n"
        "sources:\n  cam: raw/cam.mp4\n",
        encoding="utf-8",
    )
    bundle = build_brief(tmp_path, fetch=False)
    paths = write_brief_bundle(tmp_path, bundle)
    script = paths["script"].read_text(encoding="utf-8")
    assert "[[EVIDENCE:sc-socialcounts" in script
    assert "[[EVIDENCE:vidiq-earnings" in script
    plan = bundle["plan"]
    assert any(s["id"] == "sc-socialcounts" for s in plan["shots"])
    assert paths["record"].is_file()
    assert (tmp_path / "raw" / "evidence").is_dir()
