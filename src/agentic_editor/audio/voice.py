"""DeepFilterNet cam-VO enhance — official CLI, cached under models/deep-filter/.

Approved treatment (do not substitute ffmpeg denoise/gate chains):
DeepFilterNet 3 CLI v0.5.6 with ``-D`` (compensate delay) and ``-a 12``.

Raw footage is never rewritten. Cache: ``edit/audio/<source>.voice.wav``.
The CLI writes ``<output-dir>/<input-basename>`` — always use a separate
``enhanced/`` directory so the dry 48 kHz wav is not overwritten.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

from agentic_editor.cover.style_load import load_voice_enhance
from agentic_editor.paths import ensure_edit_dirs, framework_home
from agentic_editor.project import resolve_source

DF_VERSION = "0.5.6"
DF_RELEASE_BASE = (
    f"https://github.com/Rikorose/DeepFilterNet/releases/download/v{DF_VERSION}"
)
USER_AGENT = "agentic-editor/0.1 (DeepFilterNet CLI fetch)"

# (system, machine) → (release asset name, cached filename)
_ASSETS: dict[tuple[str, str], tuple[str, str]] = {
    ("windows", "x86_64"): (
        f"deep-filter-{DF_VERSION}-x86_64-pc-windows-msvc.exe",
        "deep-filter.exe",
    ),
    ("linux", "x86_64"): (
        f"deep-filter-{DF_VERSION}-x86_64-unknown-linux-musl",
        "deep-filter",
    ),
    ("linux", "aarch64"): (
        f"deep-filter-{DF_VERSION}-aarch64-unknown-linux-gnu",
        "deep-filter",
    ),
    ("darwin", "aarch64"): (
        f"deep-filter-{DF_VERSION}-aarch64-apple-darwin",
        "deep-filter",
    ),
    ("darwin", "x86_64"): (
        f"deep-filter-{DF_VERSION}-x86_64-apple-darwin",
        "deep-filter",
    ),
}


def _norm_system() -> str:
    return platform.system().lower()


def _norm_machine() -> str:
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64", "x64"):
        return "x86_64"
    if machine in ("arm64", "aarch64"):
        return "aarch64"
    return machine


def platform_asset(system: str | None = None, machine: str | None = None) -> tuple[str, str]:
    """Return (release-asset-name, cached-filename) for this OS/arch."""
    key = (system or _norm_system(), machine or _norm_machine())
    asset = _ASSETS.get(key)
    if asset is None:
        raise RuntimeError(
            f"No DeepFilterNet {DF_VERSION} CLI for {key[0]}/{key[1]}. "
            "Set AE_DEEP_FILTER_BIN to a deep-filter binary."
        )
    return asset


def cached_binary_path() -> Path:
    _asset_name, filename = platform_asset()
    return framework_home() / "models" / "deep-filter" / DF_VERSION / filename


def find_deep_filter_binary() -> Path | None:
    """Locate a DeepFilterNet CLI without downloading (doctor / tests)."""
    env = os.environ.get("AE_DEEP_FILTER_BIN", "").strip()
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p.resolve()
    cached = cached_binary_path()
    if cached.is_file() and cached.stat().st_size > 0:
        return cached
    return None


def ensure_deep_filter_binary(*, verbose: bool = True) -> Path:
    found = find_deep_filter_binary()
    if found is not None:
        return found
    asset_name, filename = platform_asset()
    dest = framework_home() / "models" / "deep-filter" / DF_VERSION / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{DF_RELEASE_BASE}/{asset_name}"
    tmp = dest.with_name(dest.name + ".partial")
    if tmp.exists():
        tmp.unlink()
    if verbose:
        print(f"• downloading DeepFilterNet CLI {DF_VERSION} → {dest}")
        print(f"  {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp, tmp.open("wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception as exc:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Failed to download DeepFilterNet CLI from {url}: {exc}\n"
            "Set AE_DEEP_FILTER_BIN to a local deep-filter binary, or retry."
        ) from exc
    if tmp.stat().st_size < 1_000_000:
        size = tmp.stat().st_size
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"DeepFilterNet download too small ({size} bytes): {url}")
    tmp.replace(dest)
    if os.name != "nt":
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def voice_wav_path(episode: Path, source_name: str = "cam") -> Path:
    return episode / "edit" / "audio" / f"{source_name}.voice.wav"


def voice_meta_path(wav: Path) -> Path:
    return wav.with_suffix(".meta.json")


def is_voice_cache_fresh(wav: Path, source: Path, settings: dict[str, Any]) -> bool:
    meta_file = voice_meta_path(wav)
    if not wav.is_file() or wav.stat().st_size <= 0 or not meta_file.is_file():
        return False
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(meta, dict):
        return False
    try:
        st = source.stat()
    except OSError:
        return False
    return (
        str(meta.get("backend") or "") == str(settings.get("backend") or "deepfilternet")
        and str(meta.get("version") or "") == DF_VERSION
        and int(meta.get("atten_lim_db") or -1) == int(settings.get("atten_lim_db") or 12)
        and bool(meta.get("compensate_delay")) == bool(settings.get("compensate_delay", True))
        and int(meta.get("sample_rate") or 0) == int(settings.get("sample_rate") or 48000)
        and int(meta.get("source_size") or -1) == int(st.st_size)
        and int(meta.get("source_mtime_ns") or -1) == int(st.st_mtime_ns)
    )


def deep_filter_cmd(
    binary: Path,
    in_wav: Path,
    out_dir: Path,
    settings: dict[str, Any],
) -> list[str]:
    """Build the official CLI invocation. ``out_dir`` must not be ``in_wav.parent``."""
    if out_dir.resolve() == in_wav.parent.resolve():
        raise ValueError(
            "deep-filter -o must be a different directory than the input wav "
            "(the CLI overwrites same-basename files in -o)"
        )
    atten = int(settings.get("atten_lim_db") or 12)
    cmd = [str(binary)]
    if bool(settings.get("compensate_delay", True)):
        cmd.append("-D")
    cmd.extend(["-a", str(atten), "-o", str(out_dir), str(in_wav)])
    return cmd


def _run(cmd: list[str], *, what: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            f"{what} failed ({proc.returncode}): {err[-4000:]}\n$ {' '.join(cmd)}"
        )


def _probe_duration_sec(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return float((proc.stdout or "").strip() or 0)
    except ValueError:
        return 0.0


def _extract_wav(source: Path, dest: Path, sample_rate: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-sn",
        "-dn",
        "-map",
        "0:a:0",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(int(sample_rate)),
        str(dest),
    ]
    _run(cmd, what="extract 48 kHz wav for DeepFilterNet")


def _pad_copy(src: Path, dest: Path, whole_dur: float, sample_rate: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".partial")
    cmd = ["ffmpeg", "-y", "-i", str(src), "-c:a", "pcm_s16le", "-ar", str(int(sample_rate))]
    if whole_dur > 0:
        cmd.extend(["-af", f"apad=whole_dur={whole_dur:.6f}", "-t", f"{whole_dur:.6f}"])
    cmd.append(str(tmp))
    _run(cmd, what="pad enhanced wav to source duration")
    tmp.replace(dest)


def enhance_source(
    episode: Path,
    source: Path,
    source_name: str,
    settings: dict[str, Any],
    *,
    force: bool = False,
    verbose: bool = True,
) -> Path:
    """Run DeepFilterNet on ``source`` → ``edit/audio/<name>.voice.wav``."""
    if not source.is_file():
        raise FileNotFoundError(f"voice enhance source missing: {source}")
    dest = voice_wav_path(episode, source_name)
    ensure_edit_dirs(episode)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not force and is_voice_cache_fresh(dest, source, settings):
        if verbose:
            print(f"• voice {source_name}: reuse {dest.relative_to(episode)}")
        return dest

    binary = ensure_deep_filter_binary(verbose=verbose)
    sample_rate = int(settings.get("sample_rate") or 48000)
    work = episode / "edit" / "audio" / "_df-work" / source_name
    if work.exists():
        shutil.rmtree(work)
    in_dir = work / "in"
    out_dir = work / "enhanced"
    in_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    in_wav = in_dir / "in48.wav"
    if verbose:
        print(
            f"• voice {source_name}: DeepFilterNet {DF_VERSION} "
            f"atten-lim {int(settings.get('atten_lim_db') or 12)} dB → "
            f"{dest.relative_to(episode)}"
        )
    try:
        _extract_wav(source, in_wav, sample_rate)
        orig_dur = _probe_duration_sec(in_wav)
        cmd = deep_filter_cmd(binary, in_wav, out_dir, settings)
        if verbose:
            print(f"  $ {' '.join(cmd)}")
        _run(cmd, what="deep-filter")
        enhanced = out_dir / in_wav.name
        if not enhanced.is_file() or enhanced.stat().st_size <= 0:
            raise RuntimeError(
                f"deep-filter did not write {enhanced} "
                "(CLI writes <output-dir>/<input-basename>)"
            )
        _pad_copy(enhanced, dest, orig_dur, sample_rate)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    st = source.stat()
    meta = {
        "backend": str(settings.get("backend") or "deepfilternet"),
        "version": DF_VERSION,
        "atten_lim_db": int(settings.get("atten_lim_db") or 12),
        "compensate_delay": bool(settings.get("compensate_delay", True)),
        "sample_rate": sample_rate,
        "source": source.name,
        "source_size": int(st.st_size),
        "source_mtime_ns": int(st.st_mtime_ns),
        "binary": str(binary),
    }
    voice_meta_path(dest).write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    if verbose:
        print(f"  wrote {dest.stat().st_size} bytes")
    return dest


def ensure_episode_voice(
    episode: Path,
    cfg: dict[str, Any],
    *,
    force: bool = False,
    verbose: bool = True,
) -> dict[str, Path]:
    """Enhance configured cam source(s). Never touches screen. Empty if disabled."""
    style_name = str(cfg.get("style") or "tutorial")
    settings = load_voice_enhance(style_name, cfg)
    if not settings.get("enabled"):
        if verbose:
            print("• voice enhance: off (voice_enhance.enabled: false)")
        return {}
    backend = str(settings.get("backend") or "deepfilternet")
    if backend != "deepfilternet":
        raise RuntimeError(
            f"unsupported voice_enhance.backend {backend!r} "
            "(only deepfilternet is implemented)"
        )
    wanted = settings.get("sources") or ["cam"]
    if not isinstance(wanted, list):
        wanted = ["cam"]
    out: dict[str, Path] = {}
    sources = cfg.get("sources") or {}
    for name in wanted:
        name = str(name)
        if name != "cam":
            if verbose:
                print(f"• voice enhance skip {name} (audio always from cam)")
            continue
        rel = sources.get(name)
        if not rel:
            continue
        src = resolve_source(episode, str(rel))
        if not src.is_file():
            raise FileNotFoundError(f"voice enhance: missing {name} source {src}")
        out[name] = enhance_source(
            episode, src, name, settings, force=force, verbose=verbose
        )
    return out
