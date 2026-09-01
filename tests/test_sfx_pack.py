"""Guardrails for the shared assets/sfx pack (no silent / mis-trimmed one-shots)."""

from __future__ import annotations

from pathlib import Path

from agentic_editor.cover.sfx_validate import (
    MAX_LEAD_SILENCE_S,
    MIN_PEAK_DBFS,
    analyze_wav,
    format_sfx_pack_errors,
    listed_pack_files,
    validate_sfx_pack,
)
from agentic_editor.cover.style_load import sfx_pack_dir


def test_shared_sfx_pack_audible_and_onset_ok():
    pack = sfx_pack_dir("tutorial")
    assert pack.is_dir(), f"missing shared SFX pack: {pack}"
    assert (pack / "pack.yaml").is_file()

    reports = validate_sfx_pack(pack)
    bad = [r for r in reports if not r.ok]
    assert not bad, "SFX pack failed loudness/onset checks:\n" + format_sfx_pack_errors(
        reports
    )

    # Every style must resolve to the same shared pack.
    for style in ("tutorial", "evidence", "social"):
        assert sfx_pack_dir(style).resolve() == pack.resolve()


def test_pack_yaml_lists_required_files_that_exist():
    pack = sfx_pack_dir("tutorial")
    names = listed_pack_files(pack)
    assert "shutter.wav" in names
    assert any(n.startswith("click_") for n in names)
    assert "paper_page.wav" in names
    assert "soft_tick.wav" in names
    assert "typing-thock.wav" in names
    for name in names:
        assert (pack / name).is_file(), name


def test_analyze_wav_flags_quiet_fixture(tmp_path: Path):
    import math
    import struct
    import wave

    # Near-silent 0.2s tone at ~-60 dBFS — must fail the peak floor.
    rate = 48000
    n = int(rate * 0.2)
    amp = int(32767 * (10 ** (-60 / 20)))
    samples = [int(amp * math.sin(2 * math.pi * 1000 * i / rate)) for i in range(n)]
    path = tmp_path / "quiet.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<" + "h" * n, *samples))

    report = analyze_wav(path)
    assert not report.ok
    assert any("peak" in e for e in report.errors)
    assert report.peak_dbfs < MIN_PEAK_DBFS


def test_analyze_wav_flags_leading_silence(tmp_path: Path):
    import struct
    import wave

    rate = 48000
    lead = int(rate * 0.2)  # 200ms quiet head — above MAX_LEAD_SILENCE_S
    click = [0] * lead + [20000] * int(rate * 0.05)
    path = tmp_path / "late_click.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<" + "h" * len(click), *click))

    report = analyze_wav(path)
    assert not report.ok
    assert report.lead_silence_s > MAX_LEAD_SILENCE_S
    assert any("leading silence" in e for e in report.errors)
