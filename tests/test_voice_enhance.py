"""DeepFilterNet voice enhance — no real CLI / ffmpeg in CI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_editor.audio.voice import (
    DF_VERSION,
    cached_binary_path,
    deep_filter_cmd,
    find_deep_filter_binary,
    is_voice_cache_fresh,
    platform_asset,
    voice_wav_path,
)
from agentic_editor.compose.mezzanine import build_mezzanines
from agentic_editor.cover.style_load import DEFAULT_VOICE_ENHANCE, load_voice_enhance
from agentic_editor.editor.render import extract_segment


def test_voice_enhance_on_by_default():
    cfg = load_voice_enhance("tutorial")
    assert cfg["enabled"] is True
    assert cfg["backend"] == "deepfilternet"
    assert cfg["atten_lim_db"] == 12
    assert cfg["compensate_delay"] is True
    assert cfg["sample_rate"] == 48000
    assert cfg["sources"] == ["cam"]
    assert DEFAULT_VOICE_ENHANCE["enabled"] is True


def test_voice_enhance_project_can_disable():
    cfg = load_voice_enhance("tutorial", {"voice_enhance": {"enabled": False}})
    assert cfg["enabled"] is False
    assert cfg["atten_lim_db"] == 12


def test_voice_enhance_missing_style_keeps_defaults():
    cfg = load_voice_enhance("missing-style-pack")
    assert cfg["enabled"] is True
    assert cfg["atten_lim_db"] == 12


def test_platform_assets_cover_supported_hosts():
    win, win_name = platform_asset("windows", "x86_64")
    assert win.endswith(".exe")
    assert win_name == "deep-filter.exe"
    linux, linux_name = platform_asset("linux", "x86_64")
    assert "linux-musl" in linux
    assert linux_name == "deep-filter"
    mac, _ = platform_asset("darwin", "aarch64")
    assert "apple-darwin" in mac
    with pytest.raises(RuntimeError):
        platform_asset("windows", "aarch64")


def test_deep_filter_cmd_uses_delay_and_separate_outdir(tmp_path: Path):
    binary = tmp_path / "deep-filter.exe"
    binary.write_bytes(b"x")
    in_wav = tmp_path / "in" / "in48.wav"
    in_wav.parent.mkdir()
    in_wav.write_bytes(b"RIFF")
    out_dir = tmp_path / "enhanced"
    cmd = deep_filter_cmd(
        binary,
        in_wav,
        out_dir,
        {"atten_lim_db": 12, "compensate_delay": True},
    )
    assert cmd[0] == str(binary)
    assert "-D" in cmd
    assert cmd[cmd.index("-a") + 1] == "12"
    assert cmd[cmd.index("-o") + 1] == str(out_dir)
    assert str(in_wav) in cmd
    assert Path(cmd[cmd.index("-o") + 1]).resolve() != in_wav.parent.resolve()


def test_deep_filter_cmd_refuses_same_dir_output(tmp_path: Path):
    binary = tmp_path / "deep-filter"
    in_wav = tmp_path / "in48.wav"
    in_wav.write_bytes(b"x")
    with pytest.raises(ValueError, match="different directory"):
        deep_filter_cmd(binary, in_wav, tmp_path, {"atten_lim_db": 12})


def test_voice_cache_fresh_matches_source_and_settings(tmp_path: Path):
    src = tmp_path / "cam.mp4"
    src.write_bytes(b"raw-bytes")
    wav = tmp_path / "cam.voice.wav"
    wav.write_bytes(b"enhanced")
    settings = {
        "backend": "deepfilternet",
        "atten_lim_db": 12,
        "compensate_delay": True,
        "sample_rate": 48000,
    }
    meta = {
        "backend": "deepfilternet",
        "version": DF_VERSION,
        "atten_lim_db": 12,
        "compensate_delay": True,
        "sample_rate": 48000,
        "source_size": src.stat().st_size,
        "source_mtime_ns": src.stat().st_mtime_ns,
    }
    wav.with_suffix(".meta.json").write_text(json.dumps(meta), encoding="utf-8")
    assert is_voice_cache_fresh(wav, src, settings)
    src.write_bytes(b"raw-bytes-changed")
    assert not is_voice_cache_fresh(wav, src, settings)


def test_find_binary_respects_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    exe = tmp_path / "custom-df.exe"
    exe.write_bytes(b"cli")
    monkeypatch.setenv("AE_DEEP_FILTER_BIN", str(exe))
    assert find_deep_filter_binary() == exe.resolve()


def test_cached_binary_path_is_under_models():
    path = cached_binary_path()
    assert "models" in path.parts
    assert "deep-filter" in path.parts
    assert DF_VERSION in path.parts


def test_pad_temp_uses_wav_extension():
    dest = Path("edit/audio/cam.voice.wav")
    tmp = dest.with_name(f"{dest.stem}.partial{dest.suffix}")
    assert tmp.name == "cam.voice.partial.wav"
    assert tmp.suffix == ".wav"


def test_extract_segment_maps_voice_wav(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cmds: list[list[str]] = []
    monkeypatch.setattr(
        "agentic_editor.editor.render._run_ffmpeg", lambda cmd: cmds.append(cmd)
    )
    monkeypatch.setattr("agentic_editor.editor.render.is_portrait", lambda _p: False)
    src = tmp_path / "cam.mp4"
    src.write_bytes(b"v")
    wav = tmp_path / "cam.voice.wav"
    wav.write_bytes(b"a")
    out = tmp_path / "seg.mp4"
    extract_segment(src, 10.5, 2.0, out, preview=True, audio_src=wav)
    assert len(cmds) == 1
    cmd = cmds[0]
    assert cmd.count("-i") == 2
    assert str(wav) in cmd
    assert cmd[cmd.index("-map") + 1] == "0:v:0"
    assert "1:a:0" in cmd
    assert any("apad" in part for part in cmd if isinstance(part, str))
    assert any("afade" in part for part in cmd if isinstance(part, str))


def test_mezzanine_rebuilds_when_voice_wav_newer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "raw" / "cam.mp4"
    src.parent.mkdir()
    src.write_bytes(b"raw-master")
    mezz = tmp_path / "edit" / "mezzanine" / "cam.mp4"
    mezz.parent.mkdir(parents=True)
    mezz.write_bytes(b"old-mezz")
    voice = voice_wav_path(tmp_path, "cam")
    voice.parent.mkdir(parents=True)
    voice.write_bytes(b"voice")
    import os

    os.utime(mezz, (1_000, 1_000))
    os.utime(src, (2_000, 2_000))
    os.utime(voice, (3_000, 3_000))

    called: dict[str, Path | None] = {}

    def fake_encode(src_path: Path, dest: Path, **kwargs: object) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"new-mezz")
        audio = kwargs.get("audio_src")
        called["audio_src"] = audio if isinstance(audio, Path) else None
        return dest

    monkeypatch.setattr(
        "agentic_editor.compose.mezzanine.encode_mezzanine", fake_encode
    )
    build_mezzanines(
        tmp_path,
        {"cam": src},
        width=1920,
        height=1080,
        fps=30,
        audio_overrides={"cam": voice},
        verbose=False,
    )
    assert called["audio_src"] == voice
    assert mezz.read_bytes() == b"new-mezz"


def test_mezzanine_reuses_when_newer_than_voice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "raw" / "cam.mp4"
    src.parent.mkdir()
    src.write_bytes(b"raw-master")
    mezz = tmp_path / "edit" / "mezzanine" / "cam.mp4"
    mezz.parent.mkdir(parents=True)
    mezz.write_bytes(b"fresh-mezz")
    voice = voice_wav_path(tmp_path, "cam")
    voice.parent.mkdir(parents=True)
    voice.write_bytes(b"voice")
    import os

    os.utime(src, (1_000, 1_000))
    os.utime(voice, (2_000, 2_000))
    os.utime(mezz, (3_000, 3_000))

    def boom(*_a: object, **_k: object) -> Path:
        raise AssertionError("should reuse up-to-date mezzanine")

    monkeypatch.setattr("agentic_editor.compose.mezzanine.encode_mezzanine", boom)
    out = build_mezzanines(
        tmp_path,
        {"cam": src},
        width=1920,
        height=1080,
        fps=30,
        audio_overrides={"cam": voice},
        verbose=False,
    )
    assert out["cam"] == mezz
    assert mezz.read_bytes() == b"fresh-mezz"
