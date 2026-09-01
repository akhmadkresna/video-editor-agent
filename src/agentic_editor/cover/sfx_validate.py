"""Validate the shared SFX pack so silent / mis-trimmed assets never ship."""

from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Peak must clear this floor (dBFS). The silent-shutter bug was ~-52 dBFS.
MIN_PEAK_DBFS = -12.0
# Onset (first sample ≥ threshold) must land within this many seconds.
MAX_LEAD_SILENCE_S = 0.05
# Absolute minimum useful duration for a one-shot.
MIN_DURATION_S = 0.03
# Onset threshold as fraction of full-scale (~-30.5 dBFS).
ONSET_THRESHOLD = 0.03

REQUIRED_KINDS = ("shutter", "click", "paper", "tick", "typing")


@dataclass(frozen=True)
class SfxAssetReport:
    path: Path
    duration_s: float
    peak_dbfs: float
    lead_silence_s: float
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _pack_yaml(pack_dir: Path) -> dict[str, Any]:
    path = pack_dir / "pack.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def listed_pack_files(pack_dir: Path) -> list[str]:
    """Basenames referenced by pack.yaml (all kinds)."""
    pack = _pack_yaml(pack_dir)
    names: list[str] = []
    for kind in REQUIRED_KINDS:
        section = pack.get(kind)
        if not isinstance(section, dict):
            continue
        if kind == "click":
            files = section.get("files")
            if isinstance(files, list):
                names.extend(str(f) for f in files)
            continue
        file_name = section.get("file")
        if file_name:
            names.append(str(file_name))
    # de-dupe, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def analyze_wav(path: Path) -> SfxAssetReport:
    """PCM peak + leading-silence check (16-bit WAV)."""
    errors: list[str] = []
    try:
        with wave.open(str(path), "rb") as w:
            if w.getsampwidth() != 2:
                errors.append(f"expected 16-bit PCM, got sampwidth={w.getsampwidth()}")
                return SfxAssetReport(path, 0.0, -99.0, 0.0, tuple(errors))
            channels = w.getnchannels()
            rate = w.getframerate()
            nframes = w.getnframes()
            raw = w.readframes(nframes)
    except wave.Error as exc:
        return SfxAssetReport(path, 0.0, -99.0, 0.0, (f"unreadable wav: {exc}",))

    if rate <= 0 or not raw:
        return SfxAssetReport(path, 0.0, -99.0, 0.0, ("empty or invalid wav",))

    samples = struct.unpack("<" + "h" * (len(raw) // 2), raw)
    if channels > 1:
        samples = samples[0::channels]
    if not samples:
        return SfxAssetReport(path, 0.0, -99.0, 0.0, ("no samples",))

    peak = max(abs(s) for s in samples)
    peak_db = -99.0 if peak <= 0 else 20.0 * math.log10(peak / 32767.0)
    thr = max(1, int(ONSET_THRESHOLD * 32767))
    onset = next((i for i, s in enumerate(samples) if abs(s) >= thr), len(samples))
    duration_s = len(samples) / float(rate)
    lead_s = onset / float(rate)

    if peak_db < MIN_PEAK_DBFS:
        errors.append(
            f"peak {peak_db:.1f} dBFS < {MIN_PEAK_DBFS:.1f} dBFS "
            "(likely silence / bad trim — same class of bug as the inaudible shutter)"
        )
    if lead_s > MAX_LEAD_SILENCE_S:
        errors.append(
            f"leading silence {lead_s:.3f}s > {MAX_LEAD_SILENCE_S:.3f}s "
            "(onset trimmed off — keep the click, not the quiet head)"
        )
    if duration_s < MIN_DURATION_S:
        errors.append(f"duration {duration_s:.3f}s < {MIN_DURATION_S:.3f}s")

    return SfxAssetReport(
        path=path,
        duration_s=duration_s,
        peak_dbfs=peak_db,
        lead_silence_s=lead_s,
        errors=tuple(errors),
    )


def validate_sfx_pack(pack_dir: Path) -> list[SfxAssetReport]:
    """Validate pack.yaml references + loudness/onset for every listed wav."""
    pack_dir = Path(pack_dir)
    reports: list[SfxAssetReport] = []
    if not pack_dir.is_dir():
        return [
            SfxAssetReport(
                pack_dir, 0.0, -99.0, 0.0, (f"pack dir missing: {pack_dir}",)
            )
        ]

    names = listed_pack_files(pack_dir)
    if not names:
        reports.append(
            SfxAssetReport(
                pack_dir / "pack.yaml",
                0.0,
                -99.0,
                0.0,
                ("pack.yaml lists no shutter/click/paper/tick/typing files",),
            )
        )
        return reports

    pack = _pack_yaml(pack_dir)
    for kind in REQUIRED_KINDS:
        if kind not in pack or not isinstance(pack.get(kind), dict):
            reports.append(
                SfxAssetReport(
                    pack_dir / "pack.yaml",
                    0.0,
                    -99.0,
                    0.0,
                    (f"pack.yaml missing kind section: {kind}",),
                )
            )

    for name in names:
        path = pack_dir / Path(name).name
        if not path.is_file():
            reports.append(
                SfxAssetReport(
                    path, 0.0, -99.0, 0.0, (f"missing file listed in pack.yaml: {name}",)
                )
            )
            continue
        if path.suffix.lower() != ".wav":
            reports.append(
                SfxAssetReport(
                    path,
                    0.0,
                    -99.0,
                    0.0,
                    (f"expected .wav in shared pack, got {path.suffix}",),
                )
            )
            continue
        reports.append(analyze_wav(path))
    return reports


def format_sfx_pack_errors(reports: list[SfxAssetReport]) -> str:
    lines: list[str] = []
    for r in reports:
        if r.ok:
            continue
        for err in r.errors:
            lines.append(f"{r.path.name}: {err}")
    return "\n".join(lines)
