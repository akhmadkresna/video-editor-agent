"""Remotion compose helpers — write props + invoke remotion CLI."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from agentic_editor.compose.mezzanine import resolve_compose_sources
from agentic_editor.cover import build_timeline_from_edl_and_cover, write_timeline
from agentic_editor.editor.edl import load_edl
from agentic_editor.paths import framework_home
from agentic_editor.project import load_project, resolve_source

# Absolute / drive-letter paths are not loadable in Remotion Studio (browser).
_ABS_PATH = re.compile(r"^(?:/|[A-Za-z]:[\\/]|\\\\)")


def _remotion_scratch_root() -> Path:
    """House scratch dir for Remotion temp + browser binaries (prefer G: on Windows)."""
    if raw := os.environ.get("REMOTION_SCRATCH_ROOT"):
        return Path(raw)
    if os.name == "nt":
        root = Path("G:/AI/remotion-cache")
        root.mkdir(parents=True, exist_ok=True)
        return root
    return framework_home() / ".cache" / "remotion-scratch"


def _remotion_env() -> dict[str, str]:
    """Env for subprocess calls into the Remotion CLI.

    Remotion's webpack bundle + frame-extraction cache land in the OS temp
    dir by default (os.tmpdir(), which Node resolves from TEMP/TMP on
    Windows). Each `still`/`render` invocation leaves a multi-GB
    `remotion-webpack-bundle-*` / `remotion-v*-assets*` dir behind that is
    never cleaned up automatically, so repeated mg-review/compose calls can
    silently fill the system drive (hit in production: 461 leftover dirs,
    218GB, ENOSPC) even though the project's own drive has plenty of room.
    Point TEMP/TMP at a folder under REMOTION_SCRATCH_ROOT (G:/AI/remotion-cache
    on this house Windows PC) instead of C:.
    """
    env = os.environ.copy()
    scratch = _remotion_scratch_root()
    cache_dir = scratch / "tmp"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (scratch / "binaries").mkdir(parents=True, exist_ok=True)
    cache_str = str(cache_dir)
    env["TEMP"] = cache_str
    env["TMP"] = cache_str
    env["TMPDIR"] = cache_str
    env.setdefault("REMOTION_CACHE_DIR", str(scratch / "bundle-cache"))
    binaries = scratch / "binaries"
    binaries.mkdir(parents=True, exist_ok=True)
    remotion_exe = binaries / ("remotion.exe" if os.name == "nt" else "remotion")
    if remotion_exe.is_file():
        env.setdefault("REMOTION_BINARIES_DIR", str(binaries))
    return env


def _wipe_dir(path: Path) -> None:
    """Best-effort delete of a file or directory tree."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
    except OSError:
        pass


def _clear_os_temp_remotion_dirs() -> None:
    """Remove Remotion leftovers in the *process* TEMP (often C:)."""
    roots: list[Path] = []
    for key in ("TEMP", "TMP", "TMPDIR"):
        raw = os.environ.get(key)
        if raw:
            roots.append(Path(raw))
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        roots.append(Path(local_app) / "Temp")
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        try:
            children = list(resolved.iterdir())
        except OSError:
            continue
        for child in children:
            name = child.name.lower()
            if name.startswith("remotion-") or name.startswith("remotion_"):
                _wipe_dir(child)


def cleanup_remotion_after_final(*, verbose: bool = True) -> None:
    """After a successful final mp4, drop staged copies and Remotion caches.

    ``public/ae-media`` is a full copy of cam/screen (can be tens of GB). Keep
    it during Studio / draft / MG review; delete it once the final file
    has been written.
    """
    _clear_remotion_cache()
    staged = remotion_kit_dir() / "public" / "ae-media"
    existed = staged.exists()
    if existed:
        _wipe_dir(staged)
    if verbose:
        if existed:
            print(f"• cleaned Remotion staged media → {staged}")
        else:
            print("• cleaned Remotion webpack/temp cache")


def _clear_remotion_cache() -> None:
    """Delete webpack/frame caches so they cannot pile up across renders.

    Moving the cache off C: (see `_remotion_env`) stopped it from filling the
    system drive, but each render/still invocation still leaves its
    multi-GB bundle+assets dir behind with nothing to clean it up — it just
    piles up on the project drive instead (hit in production: 123GB across
    83 leftover dirs after one evening of mg-review/compose calls). Call
    this after every Remotion CLI invocation finishes (success or failure)
    so the cache never accumulates past what the *current* call needed.
    """
    cache_dir = _remotion_scratch_root() / "tmp"
    if cache_dir.is_dir():
        for child in cache_dir.iterdir():
            _wipe_dir(child)
    extra = os.environ.get("REMOTION_CACHE_DIR")
    if extra:
        extra_path = Path(extra)
        if extra_path.is_dir():
            for child in extra_path.iterdir():
                _wipe_dir(child)
    _wipe_dir(remotion_kit_dir() / "node_modules" / ".cache")
    _clear_os_temp_remotion_dirs()


def probe_video_aspect(path: Path) -> float | None:
    """Return width/height from ffprobe, or None if unavailable."""
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        line = (proc.stdout or "").strip().splitlines()[:1]
        if not line:
            return None
        parts = line[0].split(",")
        if len(parts) < 2:
            return None
        w, h = float(parts[0]), float(parts[1])
        return w / h if w > 0 and h > 0 else None
    except Exception:
        return None


def apply_screen_aspect(
    screen_explainer: dict[str, Any],
    screen_path: Path | str | None,
    *,
    verbose: bool = False,
) -> dict[str, Any]:
    """Stamp screen.mp4 AR onto explainer so the float card fits without distorting."""
    if not screen_path:
        return screen_explainer
    path = Path(screen_path)
    if not path.is_file():
        return screen_explainer
    ar = probe_video_aspect(path)
    if not ar:
        return screen_explainer
    screen = dict(screen_explainer.get("screen") or {})
    screen["aspectRatio"] = round(ar, 6)
    out = {**screen_explainer, "screen": screen}
    if verbose:
        print(f"• screen card AR ← {path.name} ({ar:.5f})")
    return out


def remotion_kit_dir() -> Path:
    return framework_home() / "packages" / "remotion-kit"


def _pnpm_cmd() -> str:
    """Resolve pnpm for subprocess (Windows: prefer .cmd over .ps1 shim)."""
    if os.name == "nt":
        for name in ("pnpm.cmd", "pnpm.exe", "pnpm"):
            found = shutil.which(name)
            if found:
                return found
    found = shutil.which("pnpm")
    if found:
        return found
    raise FileNotFoundError(
        "pnpm not found on PATH — install pnpm, then retry ae compose"
    )


def _remotion_cli(kit: Path) -> list[str]:
    """Prefer local remotion bin; fall back to pnpm exec."""
    if os.name == "nt":
        local = kit / "node_modules" / ".bin" / "remotion.CMD"
    else:
        local = kit / "node_modules" / ".bin" / "remotion"
    if local.is_file():
        return [str(local)]
    return [_pnpm_cmd(), "exec", "remotion"]


def stage_sources_for_remotion(
    abs_sources: dict[str, str], *, verbose: bool = True
) -> dict[str, str]:
    """Copy episode media into remotion-kit/public for Studio HTTP serve.

    Always **copy** — never hardlink. On Windows, overwriting a hardlinked
    ``public/ae-media/*.mp4`` rewrites the same inode as episode ``raw/``, which
    can destroy masters when draft proxies are copied into public.

    Remotion cannot load absolute filesystem paths in the browser — only ``public/``
    via ``staticFile()``. Symlinks that escape ``public/`` are also rejected.
    See https://www.remotion.dev/docs/miscellaneous/absolute-paths
    """
    public = remotion_kit_dir() / "public" / "ae-media"
    if public.exists():
        shutil.rmtree(public)
    public.mkdir(parents=True, exist_ok=True)

    staged: dict[str, str] = {}
    for name, abs_path in abs_sources.items():
        src = Path(abs_path).resolve()
        if not src.is_file():
            raise FileNotFoundError(f"Source {name!r} missing: {src}")
        dest_name = f"{name}{src.suffix.lower()}"
        dest = public / dest_name
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        shutil.copy2(src, dest)
        if not dest.is_file():
            raise RuntimeError(f"Failed to stage source {name!r} into {dest}")
        # Guaranteed independent file — overwriting dest must not touch src.
        if dest.resolve() == src:
            raise RuntimeError(
                f"staged path for {name!r} resolves to source {src} — refusing"
            )
        try:
            if os.path.samefile(src, dest):
                raise RuntimeError(
                    f"staged {dest} is the same file as source {src} "
                    "(hardlink/symlink) — refusing to protect raw masters"
                )
        except OSError:
            pass
        # path relative to public/ — SourceClip wraps with staticFile()
        staged[name] = f"ae-media/{dest_name}"
        if verbose:
            print(f"• staged {name} → public/{staged[name]} ({dest.stat().st_size} bytes)")
    return staged


def stage_sfx_for_remotion(
    timeline_sfx: list[dict[str, Any]],
    *,
    style_name: str = "tutorial",
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Copy referenced style-pack SFX into public/ae-media/sfx/ and normalize src."""
    from agentic_editor.cover.style_load import sfx_pack_dir

    if not timeline_sfx:
        return []
    pack = sfx_pack_dir(style_name)
    dest_root = remotion_kit_dir() / "public" / "ae-media" / "sfx"
    dest_root.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in timeline_sfx:
        if not isinstance(item, dict):
            continue
        entry = dict(item)
        name = Path(str(entry.get("src") or "")).name
        if not name:
            continue
        src_file = pack / name
        if not src_file.is_file():
            if verbose:
                print(f"• sfx missing in pack, skipped: {name}")
            continue
        dest = dest_root / name
        if name not in seen:
            shutil.copy2(src_file, dest)
            seen.add(name)
            if verbose:
                print(f"• staged sfx → public/ae-media/sfx/{name}")
        entry["src"] = f"ae-media/sfx/{name}"
        out.append(entry)
    return out


def validate_timeline_for_studio(timeline: dict[str, Any], props_path: Path) -> list[str]:
    """Return human-readable errors if Studio would show black/empty media."""
    errors: list[str] = []
    clips = timeline.get("clips") or []
    sources = timeline.get("sources") or {}
    frames = int(timeline.get("durationInFrames") or 0)
    dur = float(timeline.get("durationSec") or 0)

    if not clips:
        errors.append("timeline has no clips (did you write edit/edl.json?)")
    if frames < 30 or dur < 1.0:
        errors.append(
            f"timeline too short ({dur:.2f}s / {frames} frames) — looks like empty defaults"
        )

    public = remotion_kit_dir() / "public"
    for name, rel in sources.items():
        if not isinstance(rel, str) or not rel.strip():
            errors.append(f"source {name!r} is empty")
            continue
        if _ABS_PATH.match(rel) or rel.startswith("file:"):
            errors.append(
                f"source {name!r} is an absolute path ({rel!r}) — "
                "Studio cannot read disk paths; must be public-relative (ae-media/…)"
            )
            continue
        if rel.startswith("http://") or rel.startswith("https://"):
            continue
        disk = public / rel
        if not disk.is_file():
            errors.append(f"staged file missing for {name!r}: expected {disk}")

    if not props_path.is_file():
        errors.append(f"missing props file {props_path}")
    return errors


def prepare_compose(episode: Path, *, verbose: bool = True) -> Path:
    cfg = load_project(episode)
    edit = episode / "edit"
    edl_path = edit / "edl.json"
    if not edl_path.is_file():
        raise FileNotFoundError(f"Missing {edl_path}")
    edl = load_edl(edl_path)

    abs_sources: dict[str, str] = {}
    for name, rel in (cfg.get("sources") or {}).items():
        abs_sources[name] = str(resolve_source(episode, rel))
    for name, rel in edl["sources"].items():
        p = Path(rel)
        if not p.is_absolute():
            p = (edit / p).resolve()
        abs_sources.setdefault(name, str(p))

    cover_path = edit / "cover.json"
    cover = None
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
        from agentic_editor.cover.evidence import collect_evidence_sources_from_cover
        from agentic_editor.cover.cutaway_assets import stage_cutaway_assets_for_remotion

        abs_sources.update(collect_evidence_sources_from_cover(episode, cover))
        staged_cover = stage_cutaway_assets_for_remotion(
            episode,
            cover,
            remotion_public=remotion_kit_dir() / "public",
            verbose=verbose,
        )
        if staged_cover is not None:
            cover = staged_cover
            # Persist rewritten public-relative paths so Studio reloads stay valid.
            cover_path.write_text(
                json.dumps(cover, indent=2) + "\n", encoding="utf-8"
            )

    # Prefer edit/mezzanine/* (deliverable size) over multi-GB raw masters.
    compose_sources = resolve_compose_sources(
        episode, abs_sources, cfg, verbose=verbose
    )
    staged_sources = stage_sources_for_remotion(compose_sources, verbose=verbose)

    edl_abs = dict(edl)
    edl_abs["sources"] = staged_sources

    from agentic_editor.cover.style_load import load_overlays, load_screen_explainer

    style_name = str(cfg.get("style") or "tutorial")
    screen_explainer = load_screen_explainer(style_name)
    ep_se = cfg.get("screen_explainer")
    if isinstance(ep_se, dict):
        from agentic_editor.cover.style_load import _deep_merge

        screen_explainer = _deep_merge(screen_explainer, ep_se)
    # Card AR from screen pixels (fit/center only — no distort).
    screen_path = abs_sources.get("screen") or compose_sources.get("screen")
    screen_explainer = apply_screen_aspect(
        screen_explainer, screen_path, verbose=verbose
    )
    overlays = load_overlays(style_name)

    timeline = build_timeline_from_edl_and_cover(
        edl_abs,
        cover,
        fps=int(cfg.get("fps", 30)),
        width=int(cfg.get("width", 1920)),
        height=int(cfg.get("height", 1080)),
        screen_explainer=screen_explainer,
        overlays=overlays,
        episode=episode,
    )
    timeline["sources"] = staged_sources
    timeline["sfx"] = stage_sfx_for_remotion(
        list(timeline.get("sfx") or []),
        style_name=style_name,
        verbose=verbose,
    )
    # absolute paths for tooling: compose media + raw masters
    timeline["sourcePaths"] = compose_sources
    timeline["rawSourcePaths"] = abs_sources

    # Dynamic smart window crop per float_centered clip (midpoint sample).
    crop_cfg = ((screen_explainer.get("screen") or {}).get("crop") or {})
    if str(crop_cfg.get("mode") or "") == "smart_window_detect":
        _attach_smart_window_crops(
            timeline,
            abs_sources,
            crop_cfg=crop_cfg,
            episode=episode,
            verbose=verbose,
        )

    out = edit / "timeline.json"
    write_timeline(out, timeline)
    props = edit / "remotion-props.json"
    props.write_text(json.dumps({"timeline": timeline}, indent=2) + "\n", encoding="utf-8")

    errors = validate_timeline_for_studio(timeline, props)
    if errors:
        msg = "compose preflight failed:\n  - " + "\n  - ".join(errors)
        raise RuntimeError(msg)

    from agentic_editor.compose.quality import audit_timeline_quality, format_audit
    from agentic_editor.compose.cutaway_qa import write_cutaway_contact_plan

    write_cutaway_contact_plan(episode, timeline)

    q_err, q_warn = audit_timeline_quality(timeline, cover=cover)
    if verbose and (q_err or q_warn):
        print("• quality audit:")
        for line in format_audit(q_err, q_warn).splitlines():
            print(f"  {line}")
    if q_err:
        raise RuntimeError(
            "compose quality gate failed:\n  - " + "\n  - ".join(q_err)
        )

    if verbose:
        print(f"• timeline → {out.relative_to(episode)}")
        print(f"• props → {props.relative_to(episode)}")
        print(f"• duration {timeline['durationSec']:.1f}s / {timeline['durationInFrames']} frames")
        print("• preflight OK (staged public media + non-empty timeline)")
    return out


def prepare_draft(
    episode: Path,
    *,
    limit_sec: float = 120.0,
    verbose: bool = True,
) -> Path:
    """Prepare compose, then write a correctly sliced draft props file.

    Always slices via ``draft_slice.slice_timeline`` (fromSec-aware) so overlays
    are not silently dropped.
    """
    from agentic_editor.compose.draft_slice import slice_timeline
    from agentic_editor.compose.quality import audit_timeline_quality, format_audit

    prepare_compose(episode, verbose=verbose)
    props_path = episode / "edit" / "remotion-props.json"
    full = json.loads(props_path.read_text(encoding="utf-8"))
    timeline = full.get("timeline") or full
    sliced = slice_timeline(timeline, limit_sec)

    # Draft slices intentionally drop overlays past limit_sec. Audit scales /
    # crops / punches on the slice, but only require cover overlays that land
    # inside the draft window (matched via full-timeline fromSec remap).
    cover = None
    cover_path = episode / "edit" / "cover.json"
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
    in_window_ids = {
        str(o.get("id") or "")
        for o in (timeline.get("overlays") or [])
        if isinstance(o, dict) and float(o.get("fromSec") or 0) < float(limit_sec)
    }
    cover_for_draft = None
    if cover and isinstance(cover, dict):
        from agentic_editor.cover.remap import collect_overlay_defs

        defs = collect_overlay_defs(cover)
        cover_for_draft = {
            **cover,
            "overlays": [d for d in defs if d.get("id") in in_window_ids],
        }
    q_err, q_warn = audit_timeline_quality(sliced, cover=cover_for_draft)
    # Slice integrity: every full-timeline overlay that starts in-window must survive.
    sliced_ids = {
        str(o.get("id") or "")
        for o in (sliced.get("overlays") or [])
        if isinstance(o, dict)
    }
    dropped_slice = sorted(i for i in in_window_ids if i and i not in sliced_ids)
    if dropped_slice:
        sample = ", ".join(dropped_slice[:3])
        q_err.append(
            f"{len(dropped_slice)} in-window overlay(s) dropped by draft slice "
            f"(e.g. {sample}) — fromSec trim bug"
        )
    if verbose and (q_err or q_warn):
        print("• draft quality audit:")
        for line in format_audit(q_err, q_warn).splitlines():
            print(f"  {line}")
    if q_err:
        raise RuntimeError("draft quality gate failed:\n  - " + "\n  - ".join(q_err))

    drafts = episode / "edit" / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    tag = int(limit_sec) if float(limit_sec).is_integer() else limit_sec
    out = drafts / f"remotion-props-{tag}s.json"
    out.write_text(json.dumps({"timeline": sliced}, indent=2) + "\n", encoding="utf-8")
    if verbose:
        n_ov = len(sliced.get("overlays") or [])
        n_fx = len(sliced.get("effects") or [])
        print(
            f"• draft props → {out.relative_to(episode)} "
            f"({limit_sec:.0f}s, {len(sliced.get('clips') or [])} clips, "
            f"{n_ov} overlays, {n_fx} effects)"
        )
    return out


def _load_stable_window_crop(episode: Path) -> dict[str, Any] | None:
    """Prefer hand-tuned / verified edit/window_crop.json when present."""
    path = episode / "edit" / "window_crop.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    stable = data.get("stable") if isinstance(data, dict) else None
    if not isinstance(stable, dict) or not stable.get("ok", True):
        return None
    norm = stable.get("normalized")
    if not isinstance(norm, dict):
        return None
    try:
        return {
            "normalized": {
                "x": float(norm["x"]),
                "y": float(norm["y"]),
                "w": float(norm["w"]),
                "h": float(norm["h"]),
            },
            "px": {
                "x": int(stable["x"]),
                "y": int(stable["y"]),
                "w": int(stable["w"]),
                "h": int(stable["h"]),
            },
        }
    except (KeyError, TypeError, ValueError):
        return None


def _attach_smart_window_crops(
    timeline: dict[str, Any],
    abs_sources: dict[str, str],
    *,
    crop_cfg: dict[str, Any],
    episode: Path | None = None,
    verbose: bool = True,
) -> None:
    """Annotate float_centered clips with normalized windowCrop from pixel detect."""
    from agentic_editor.cover.window_crop import detect_window_crop

    stable = _load_stable_window_crop(episode) if episode is not None else None
    if stable is not None:
        n = 0
        for clip in timeline.get("clips") or []:
            if clip.get("layout") != "float_centered":
                continue
            clip["windowCrop"] = dict(stable["normalized"])
            clip["windowCropPx"] = dict(stable["px"])
            n += 1
        if verbose and n:
            print(
                f"• smart_window_detect → {n} float clip(s) "
                f"(stable edit/window_crop.json)"
            )
        return

    kwargs = {
        "analysis_max_width": int(crop_cfg.get("analysisMaxWidth") or 480),
        "chrome_side_inset_frac_max": float(
            crop_cfg.get("chromeSideInsetFracMax") or 0.12
        ),
        "window_relative_pad": float(crop_cfg.get("windowRelativePad") or 0.003),
    }
    cache: dict[tuple[str, float], dict[str, Any]] = {}
    n = 0
    for clip in timeline.get("clips") or []:
        if clip.get("layout") != "float_centered":
            continue
        src_name = str(clip.get("source") or "")
        abs_path = abs_sources.get(src_name)
        if not abs_path or not Path(abs_path).is_file():
            continue
        mid = float(clip.get("sourceIn") or 0) + float(clip.get("durationSec") or 0) / 2
        mid = round(mid, 2)
        key = (src_name, mid)
        if key not in cache:
            try:
                crop = detect_window_crop(abs_path, t_sec=mid, **kwargs)
                cache[key] = crop.as_dict()
            except Exception as exc:  # noqa: BLE001 — compose must not die on crop
                if verbose:
                    print(f"• window crop skipped for {src_name}@{mid}s: {exc}")
                cache[key] = {}
        if cache[key]:
            clip["windowCrop"] = cache[key]["normalized"]
            clip["windowCropPx"] = {
                "x": cache[key]["x"],
                "y": cache[key]["y"],
                "w": cache[key]["w"],
                "h": cache[key]["h"],
            }
            n += 1
    if verbose and n:
        print(f"• smart_window_detect → {n} float clip(s)")


def run_studio(episode: Path) -> None:
    prepare_compose(episode)
    kit = remotion_kit_dir()
    props = episode / "edit" / "remotion-props.json"
    # Re-check after write (belt + suspenders)
    timeline = json.loads(props.read_text(encoding="utf-8")).get("timeline") or {}
    errors = validate_timeline_for_studio(timeline, props)
    if errors:
        raise RuntimeError("refusing to start Studio:\n  - " + "\n  - ".join(errors))

    env = _remotion_env()
    env["AE_TIMELINE_PROPS"] = str(props)
    env["AE_EPISODE"] = str(episode.resolve())
    if not (kit / "package.json").is_file():
        raise FileNotFoundError(f"Remotion kit missing at {kit}")
    cmd = [
        *_remotion_cli(kit),
        "studio",
        "src/index.ts",
        "--props",
        str(props),
    ]
    print(f"$ cd {kit} && {' '.join(cmd)}")
    print("  (always pass --props — without it Studio shows a ~3s black empty timeline)")
    try:
        subprocess.run(cmd, cwd=str(kit), env=env, check=True)
    finally:
        _clear_remotion_cache()


def _ffmpeg_encoders_blob(ffmpeg_exe: Path) -> str:
    try:
        proc = subprocess.run(
            [str(ffmpeg_exe), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (proc.stdout or "") + (proc.stderr or "")


def _ffmpeg_has_encoder(bin_dir: Path, encoder: str) -> bool:
    name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    exe = bin_dir / name
    if not exe.is_file():
        return False
    return encoder in _ffmpeg_encoders_blob(exe)


def find_remotion_compositor_dir() -> Path | None:
    """Locate `@remotion/compositor-*` package dir (contains `remotion[.exe]`)."""
    env = os.environ.get("AE_REMOTION_COMPOSITOR_DIR")
    if env:
        p = Path(env)
        if (p / ("remotion.exe" if os.name == "nt" else "remotion")).is_file():
            return p.resolve()

    remotion_name = "remotion.exe" if os.name == "nt" else "remotion"
    if os.name == "nt":
        patterns = ("@remotion+compositor-win32-*/node_modules/@remotion/compositor-*",)
    elif sys.platform == "darwin":
        patterns = ("@remotion+compositor-darwin-*/node_modules/@remotion/compositor-*",)
    else:
        patterns = ("@remotion+compositor-linux-*/node_modules/@remotion/compositor-*",)

    roots = [
        framework_home() / "node_modules" / ".pnpm",
        remotion_kit_dir() / "node_modules" / ".pnpm",
        framework_home() / "node_modules",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for pattern in patterns:
            for hit in sorted(root.glob(pattern)):
                if hit.is_dir() and (hit / remotion_name).is_file():
                    return hit.resolve()
    return None


def find_nvenc_ffmpeg_bin_dir() -> Path | None:
    """Directory containing an ffmpeg that lists h264_nvenc (Windows/Linux)."""
    candidates: list[Path] = []
    # Prefer Remotion compositor ffmpeg when it has NVENC — also ships libfdk_aac
    # (Gyan full builds usually lack libfdk_aac, which Remotion requires for AAC).
    compositor = find_remotion_compositor_dir()
    if compositor is not None:
        candidates.append(compositor)
    which = shutil.which("ffmpeg")
    if which:
        candidates.append(Path(which).resolve().parent)
    local = os.environ.get("LOCALAPPDATA") or ""
    if local:
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget.is_dir():
            candidates.extend(winget.glob("Gyan.FFmpeg*/ffmpeg-*-full_build/bin"))
    env_bin = os.environ.get("AE_FFMPEG_BIN_DIR") or os.environ.get("REMOTION_FFMPEG_BINARIES")
    if env_bin:
        candidates.insert(0, Path(env_bin))

    seen: set[Path] = set()
    for d in candidates:
        try:
            d = d.resolve()
        except OSError:
            continue
        if d in seen or not d.is_dir():
            continue
        seen.add(d)
        if _ffmpeg_has_encoder(d, "h264_nvenc"):
            return d
    return None


def _link_or_copy(src: Path, dest: Path) -> None:
    """Prefer hardlink, then symlink, then copy (cross-volume safe)."""
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    try:
        os.link(src, dest)
        return
    except OSError:
        pass
    try:
        dest.symlink_to(src)
        return
    except OSError:
        pass
    shutil.copy2(src, dest)


def stage_nvenc_remotion_binaries(
    ffmpeg_bin_dir: Path,
    *,
    verbose: bool = True,
) -> Path | None:
    """Resolve a Remotion binaries dir with compositor + NVENC + libfdk_aac.

    Remotion resolves remotion/ffmpeg/ffprobe from one directory and maps AAC to
    `libfdk_aac`. Prefer the compositor package when its ffmpeg already has
    NVENC. Only overlay an external ffmpeg if it also provides libfdk_aac.
    """
    compositor = find_remotion_compositor_dir()
    if compositor is None:
        if verbose:
            print(
                "• NVENC: Remotion compositor package not found — "
                "falling back to software encode"
            )
        return None

    remotion_name = "remotion.exe" if os.name == "nt" else "remotion"
    ffmpeg_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"

    try:
        same = ffmpeg_bin_dir.resolve() == compositor.resolve()
    except OSError:
        same = False
    if same or (
        _ffmpeg_has_encoder(compositor, "h264_nvenc")
        and _ffmpeg_has_encoder(compositor, "libfdk_aac")
    ):
        if verbose:
            print(f"• NVENC: using Remotion compositor binaries → {compositor}")
        return compositor.resolve()

    src_ffmpeg = ffmpeg_bin_dir / ffmpeg_name
    src_ffprobe = ffmpeg_bin_dir / ffprobe_name
    if not src_ffmpeg.is_file():
        return None
    if not _ffmpeg_has_encoder(ffmpeg_bin_dir, "libfdk_aac"):
        if verbose:
            print(
                "• NVENC: external ffmpeg lacks libfdk_aac (required by Remotion AAC) — "
                "cannot overlay; "
                + (
                    "using compositor binaries"
                    if _ffmpeg_has_encoder(compositor, "h264_nvenc")
                    else "falling back to software encode"
                )
            )
        if _ffmpeg_has_encoder(compositor, "h264_nvenc"):
            return compositor.resolve()
        return None

    cache = framework_home() / ".ae-cache" / "remotion-nvenc-binaries"
    cache.mkdir(parents=True, exist_ok=True)
    marker = cache / ".stage-id"
    stage_id = (
        f"{compositor}:{src_ffmpeg.stat().st_mtime_ns}:"
        f"{src_ffmpeg.stat().st_size}:"
        f"{(compositor / remotion_name).stat().st_mtime_ns}"
    )
    ready = (
        marker.is_file()
        and marker.read_text(encoding="utf-8") == stage_id
        and (cache / remotion_name).is_file()
        and (cache / ffmpeg_name).is_file()
    )
    if not ready:
        for item in compositor.iterdir():
            if item.name in {ffmpeg_name, ffprobe_name}:
                continue
            if item.suffix in {".md", ".ts", ".js", ".mjs", ".json"} or item.name in {
                "README.md",
                "package.json",
                "index.js",
                "index.mjs",
                "index.d.ts",
            }:
                continue
            dest = cache / item.name
            if item.is_file():
                shutil.copy2(item, dest)
        _link_or_copy(src_ffmpeg, cache / ffmpeg_name)
        if src_ffprobe.is_file():
            _link_or_copy(src_ffprobe, cache / ffprobe_name)
        marker.write_text(stage_id, encoding="utf-8")
        if verbose:
            print(f"• NVENC: staged remotion+ffmpeg → {cache}")

    if not (cache / remotion_name).is_file() or not (cache / ffmpeg_name).is_file():
        return None
    return cache.resolve()


def remotion_render_accel_args(
    *,
    nvenc: bool = False,
    gl: str | None = None,
    verbose: bool = True,
) -> list[str]:
    """Extra `remotion render` flags for GPU encode / Chrome GL.

    NVENC only speeds *encoding* (muxing frames → mp4). Frame rasterization still
    runs in Chrome; `--gl` helps that path more on NVIDIA (`angle` on Windows).
    NVENC is useful on long encodes, not required for short drafts.
    """
    args: list[str] = []
    if gl:
        args.extend(["--gl", str(gl)])
    if not nvenc:
        return args

    ffmpeg_bin = find_nvenc_ffmpeg_bin_dir()
    if ffmpeg_bin is None:
        if verbose:
            print(
                "• NVENC requested but no h264_nvenc ffmpeg found — "
                "falling back to software encode"
            )
        return args

    bin_dir = stage_nvenc_remotion_binaries(ffmpeg_bin, verbose=verbose)
    if bin_dir is None:
        if verbose:
            print("• NVENC: no usable binaries — falling back to software encode")
        return args

    compositor = find_remotion_compositor_dir()
    use_explicit = compositor is None or bin_dir.resolve() != compositor.resolve()
    # CRF incompatible with NVENC — bitrate mode
    args.extend(["--hardware-acceleration", "if-possible", "--video-bitrate", "8M"])
    if use_explicit:
        args.extend(["--binaries-directory", str(bin_dir)])
    if verbose:
        print(f"• NVENC: binaries → {bin_dir}")
        print("• Remotion --hardware-acceleration if-possible (--video-bitrate 8M)")
    return args



def _warn_if_mg_review_stale(episode: Path) -> None:
    """Full compose renders are expensive (minutes, GB of output) — if
    cover.json's MG plan changed since the last `ae mg-review` (or no
    review has ever been run), print a loud warning instead of silently
    rendering an unreviewed overlay plan. Not a hard block: sometimes a
    full render is wanted regardless (e.g. re-rendering after a cut-only
    change), so this stays advisory, matching the rest of the pipeline's
    "confirm before" convention rather than a hard gate.
    """
    cover_path = episode / "edit" / "cover.json"
    if not cover_path.is_file():
        return
    stamp_path = episode / "edit" / "mg-review" / ".cover_sha256"
    current = hashlib.sha256(cover_path.read_bytes()).hexdigest()
    reviewed = stamp_path.read_text(encoding="utf-8").strip() if stamp_path.is_file() else None
    if reviewed == current:
        return
    reason = "no `ae mg-review` has been run yet" if reviewed is None else "cover.json changed since the last `ae mg-review`"
    print(
        f"! WARNING: {reason} — about to full-render an unreviewed MG plan.\n"
        f"  Run `ae mg-review .` and check edit/mg-review/review.html first, "
        f"or continue if you're sure.",
        file=sys.stderr,
    )


def render_compose(
    episode: Path,
    *,
    output: Path | None = None,
    nvenc: bool = False,
    gl: str | None = None,
) -> Path:
    _warn_if_mg_review_stale(episode)
    prepare_compose(episode)
    kit = remotion_kit_dir()
    props = episode / "edit" / "remotion-props.json"
    out = output or (episode / "edit" / "final.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    env = _remotion_env()
    env["AE_TIMELINE_PROPS"] = str(props)
    env["AE_EPISODE"] = str(episode.resolve())
    accel = remotion_render_accel_args(nvenc=nvenc, gl=gl)
    cmd = [
        *_remotion_cli(kit),
        "render",
        "src/index.ts",
        "AgenticTimeline",
        str(out),
        "--props",
        str(props),
        *accel,
    ]
    print(f"$ cd {kit} && {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=str(kit), env=env, check=True)
    finally:
        _clear_remotion_cache()
    cleanup_remotion_after_final()
    return out


#: All A-roll MG kinds — glass (GlassOverlays.tsx) + legacy rail (OverlayLayer).
_MG_REVIEW_KINDS = (
    "title",
    "stat",
    "lower_third",
    "tag",
    "divider",
    "quote",
    "code",
    "illustration",
    "callout",
    "chapter",
    "emphasis",
    "diagram",
    "chip",
)

#: Seconds into an overlay's fromSec where its entrance motion has settled —
#: see styles/tutorial/style.md's "Motion (exact...)" section. stat needs
#: longer (300ms count-up + 80ms delay + 260ms label fade ≈ 640ms); everything
#: else settles within ~220-280ms, so 0.6s is a safe generic hold point.
_MG_REVIEW_SETTLE_SEC = {"stat": 0.85}
_MG_REVIEW_SETTLE_DEFAULT = 0.6
#: Per-still retry count — see the comment at the retry loop in
#: render_mg_review for why this class of failure is expected to be
#: transient rather than deterministic.
_MG_REVIEW_RETRIES = 3


def cover_json_sha256(episode: Path) -> str | None:
    cover_path = episode / "edit" / "cover.json"
    if not cover_path.is_file():
        return None
    return hashlib.sha256(cover_path.read_bytes()).hexdigest()


def mg_review_stills_fresh(episode: Path) -> bool:
    """True when mg-review stills match the current cover.json."""
    digest = cover_json_sha256(episode)
    if digest is None:
        return False
    stamp_path = episode / "edit" / "mg-review" / ".cover_sha256"
    stills_dir = episode / "edit" / "mg-review" / "stills"
    if not stamp_path.is_file() or stamp_path.read_text(encoding="utf-8").strip() != digest:
        return False
    return any(stills_dir.glob("*.preview.jpg"))


def load_mg_review_preview_index(episode: Path) -> dict[str, Path]:
    """Map tile id → downscaled preview JPEG (empty when none rendered)."""
    stills_dir = episode / "edit" / "mg-review" / "stills"
    if not stills_dir.is_dir():
        return {}
    out: dict[str, Path] = {}
    for preview in stills_dir.glob("*.preview.jpg"):
        out[preview.name[: -len(".preview.jpg")]] = preview
    return out


def _mg_review_settle_frame(
    *,
    kind: str,
    from_sec: float,
    exit_start: Any,
    fps: int,
) -> int:
    settle = _MG_REVIEW_SETTLE_SEC.get(kind, _MG_REVIEW_SETTLE_DEFAULT)
    if isinstance(exit_start, (int, float)):
        settle = min(settle, max(0.05, float(exit_start) - 0.1))
    return max(0, round((from_sec + settle) * fps))


def _render_remotion_still_tile(
    *,
    kit: Path,
    props_path: Path,
    env: dict[str, str],
    gl_args: list[str],
    tile_id: str,
    frame: int,
    still_path: Path,
    preview_path: Path,
    verbose: bool,
) -> tuple[Path | None, Path | None, bool]:
    cmd = [
        *_remotion_cli(kit),
        "still",
        "src/index.ts",
        "AgenticTimeline",
        str(still_path),
        "--props",
        str(props_path),
        f"--frame={frame}",
        *gl_args,
    ]
    if verbose:
        print(f"$ cd {kit} && {' '.join(cmd)}")
    last_err: subprocess.CalledProcessError | None = None
    for attempt in range(1, _MG_REVIEW_RETRIES + 1):
        try:
            try:
                subprocess.run(cmd, cwd=str(kit), env=env, check=True)
            finally:
                _clear_remotion_cache()
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(still_path),
                    "-vf",
                    "scale=960:-1",
                    "-q:v",
                    "5",
                    str(preview_path),
                ],
                check=True,
                capture_output=True,
            )
            return still_path, preview_path, False
        except subprocess.CalledProcessError as exc:
            last_err = exc
            if verbose:
                print(
                    f"  ! {tile_id} attempt {attempt}/{_MG_REVIEW_RETRIES} "
                    f"failed (likely a transient proxy-server timeout), retrying"
                )
    if verbose:
        print(f"  x {tile_id} gave up after {_MG_REVIEW_RETRIES} attempts — {last_err}")
    return None, None, True


def _evidence_review_specs(
    cover: dict[str, Any] | None,
    edl: dict[str, Any],
    *,
    fps: int,
) -> list[dict[str, Any]]:
    from agentic_editor.cover.remap import remap_source_window

    if not cover:
        return []
    specs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ev in cover.get("events") or []:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("type") or "").lower() != "evidence_with_cam":
            continue
        src = str(ev.get("src") or "").strip()
        stem = Path(src).stem or "evidence"
        eid = f"ev-{stem}"
        if eid in seen:
            continue
        seen.add(eid)
        try:
            start = float(ev["start"])
            end = float(ev["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        mid = (start + end) / 2.0
        slices = remap_source_window(edl, mid, mid + 0.05)
        if not slices:
            continue
        from_sec = float(slices[0]["fromSec"])
        frame = max(0, round((from_sec + 0.8) * fps))
        specs.append(
            {
                "id": eid,
                "kind": "evidence",
                "fromSec": from_sec,
                "src": src,
                "note": str(ev.get("note") or "").strip(),
                "_frame": frame,
            }
        )
    return specs


def render_mg_review_tiles(
    episode: Path,
    *,
    gl: str | None = None,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Render production Remotion stills for every MG overlay + evidence hold."""
    prepare_compose(episode, verbose=verbose)
    kit = remotion_kit_dir()
    props_path = episode / "edit" / "remotion-props.json"
    timeline = json.loads(props_path.read_text(encoding="utf-8"))["timeline"]
    fps = int(timeline.get("fps") or 30)
    cover_path = episode / "edit" / "cover.json"
    cover: dict[str, Any] | None = None
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
    edl_path = episode / "edit" / "edl.json"
    edl: dict[str, Any] = {}
    if edl_path.is_file():
        edl = json.loads(edl_path.read_text(encoding="utf-8"))

    overlays = [
        ov
        for ov in (timeline.get("overlays") or [])
        if isinstance(ov, dict) and ov.get("kind") in _MG_REVIEW_KINDS
    ]
    evidence_specs = _evidence_review_specs(cover, edl, fps=fps)
    if not overlays and not evidence_specs:
        raise RuntimeError(
            "No MG overlays or evidence holds found in cover.json — nothing to review"
        )

    out_dir = episode / "edit" / "mg-review"
    stills_dir = out_dir / "stills"
    stills_dir.mkdir(parents=True, exist_ok=True)

    env = _remotion_env()
    env["AE_TIMELINE_PROPS"] = str(props_path)
    env["AE_EPISODE"] = str(episode.resolve())
    gl_args = ["--gl", str(gl)] if gl else []

    tiles: list[dict[str, Any]] = []
    render_queue: list[dict[str, Any]] = []
    for ov in overlays:
        kind = str(ov["kind"])
        from_sec = float(ov.get("fromSec") or 0.0)
        frame = _mg_review_settle_frame(
            kind=kind,
            from_sec=from_sec,
            exit_start=ov.get("exitStartSec"),
            fps=fps,
        )
        render_queue.append({**ov, "_frame": frame, "_tile_kind": kind})
    for spec in evidence_specs:
        render_queue.append(spec)

    for item in render_queue:
        tile_id = str(item["id"])
        frame = int(item["_frame"])
        kind = str(item.get("_tile_kind") or item.get("kind") or "mg")
        still_path = stills_dir / f"{tile_id}.png"
        preview_path = stills_dir / f"{tile_id}.preview.jpg"
        still, preview, failed = _render_remotion_still_tile(
            kit=kit,
            props_path=props_path,
            env=env,
            gl_args=gl_args,
            tile_id=tile_id,
            frame=frame,
            still_path=still_path,
            preview_path=preview_path,
            verbose=verbose,
        )
        if failed:
            tiles.append({**item, "_still": None, "_preview": None, "_failed": True})
            continue
        tiles.append(
            {
                **item,
                "_still": still,
                "_preview": preview,
                "_failed": False,
            }
        )

    html_path = out_dir / "review.html"
    html_path.write_text(_build_mg_review_html(tiles), encoding="utf-8")
    digest = cover_json_sha256(episode)
    if digest is not None:
        (out_dir / ".cover_sha256").write_text(digest, encoding="utf-8")

    failed = [t for t in tiles if t.get("_failed")]
    ok_count = len(tiles) - len(failed)
    if verbose:
        print(
            f"• mg-review → {html_path.relative_to(episode)} "
            f"({ok_count}/{len(tiles)} tiles rendered"
            + (f", {len(failed)} FAILED: {', '.join(t['id'] for t in failed)}" if failed else "")
            + ")"
        )
    if failed:
        raise RuntimeError(
            f"{len(failed)}/{len(tiles)} tile(s) failed to render after "
            f"{_MG_REVIEW_RETRIES} attempts each: {', '.join(t['id'] for t in failed)}. "
            f"Gallery at {html_path} still has all {len(tiles)} tiles — the {ok_count} that "
            "succeeded plus a visible FAILED placeholder for the rest. Re-run `ae mg-review` "
            "(it re-renders everything, but the retries usually clear a transient failure)."
        )
    return tiles


def ensure_mg_review_stills(
    episode: Path,
    *,
    force: bool = False,
    gl: str | None = None,
    verbose: bool = True,
) -> dict[str, Path]:
    """Ensure Remotion MG stills exist; return id → preview path index."""
    if force or not mg_review_stills_fresh(episode):
        render_mg_review_tiles(episode, gl=gl, verbose=verbose)
    return load_mg_review_preview_index(episode)


def render_mg_review(episode: Path, *, gl: str | None = None, verbose: bool = True) -> Path:
    """Render a real Remotion still per MG overlay + evidence hold + HTML gallery."""
    render_mg_review_tiles(episode, gl=gl, verbose=verbose)
    return episode / "edit" / "mg-review" / "review.html"


def _build_mg_review_html(tiles: list[dict[str, Any]]) -> str:
    import base64
    import html as _html

    rows = []
    for t in tiles:
        kind = _html.escape(str(t.get("kind") or ""))
        oid = _html.escape(str(t.get("id") or ""))
        from_sec = float(t.get("fromSec") or 0.0)
        if t.get("_failed"):
            # Visible placeholder, not a silently-missing tile — a crashed
            # render must never look the same as "nothing changed here".
            rows.append(
                f"""
      <figure class="failed">
        <div class="failbox">RENDER FAILED</div>
        <figcaption>
          <div class="meta"><span class="badge">{kind}</span><span class="id">{oid}</span></div>
          <div class="t">t={from_sec:.2f}s · frame {t['_frame']}</div>
        </figcaption>
      </figure>"""
            )
            continue
        img_b64 = base64.b64encode(t["_preview"].read_bytes()).decode("ascii")
        tone = t.get("tone")
        badges = f'<span class="badge">{kind}</span>'
        if tone:
            # b/w system: amber = dashed border (estimate/caution), else solid —
            # matches GlassOverlays.tsx's toneBorderStyle(), no color anywhere.
            border_style = "dashed" if tone == "amber" else "solid"
            badges += (
                f'<span class="badge" style="border-style:{border_style}">'
                f"{_html.escape(str(tone))}</span>"
            )
        rows.append(
            f"""
      <figure>
        <img src="data:image/jpeg;base64,{img_b64}" alt="{oid}" />
        <figcaption>
          <div class="meta">{badges}<span class="id">{oid}</span></div>
          <div class="t">t={from_sec:.2f}s · frame {t['_frame']}</div>
        </figcaption>
      </figure>"""
        )

    from datetime import datetime, timezone

    n_failed = sum(1 for t in tiles if t.get("_failed"))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    status_line = (
        f"{len(tiles) - n_failed}/{len(tiles)} rendered · {n_failed} FAILED"
        if n_failed
        else f"{len(tiles)} overlays · all rendered"
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8" />
<title>MG Review</title>
<style>
  body {{ margin:0; background:#0c0c0b; color:#f5f4f1; font-family:-apple-system,'Segoe UI',sans-serif; padding:32px; }}
  h1 {{ font-size:20px; font-weight:600; margin:0 0 4px; }}
  .status {{ font-family:ui-monospace,Menlo,monospace; font-size:12px; color:#8f8c85; margin:0 0 24px; }}
  .status.has-failures {{ color:#e0674b; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:20px; }}
  figure {{ margin:0; background:#141312; border:1px solid #333029; border-radius:8px; overflow:hidden; }}
  figure.failed {{ border-color:#e0674b; }}
  figure img {{ display:block; width:100%; height:auto; }}
  .failbox {{ aspect-ratio:16/9; display:flex; align-items:center; justify-content:center; color:#e0674b; font-weight:700; letter-spacing:.08em; font-size:13px; background:repeating-linear-gradient(45deg,#1a1211,#1a1211 10px,#241715 10px,#241715 20px); }}
  figcaption {{ padding:10px 14px; font-size:12px; }}
  .meta {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; }}
  .badge {{ font-weight:700; letter-spacing:.06em; text-transform:uppercase; font-size:10px; padding:2px 8px; border:1px solid #6b6860; color:#f5f4f1; }}
  .id {{ font-family:ui-monospace,Menlo,monospace; color:#8f8c85; }}
  .t {{ color:#8f8c85; }}
</style>
</head><body>
  <h1>MG review</h1>
  <div class="status{' has-failures' if n_failed else ''}">{status_line} · generated {generated_at}</div>
  <div class="grid">{''.join(rows)}
  </div>
</body></html>
"""


def render_draft(
    episode: Path,
    *,
    limit_sec: float = 120.0,
    output: Path | None = None,
    jpeg_quality: int = 70,
    verbose: bool = True,
    nvenc: bool = False,
    gl: str | None = None,
) -> Path:
    """Render the first ``limit_sec`` seconds using a fromSec-safe draft slice."""
    props = prepare_draft(episode, limit_sec=limit_sec, verbose=verbose)
    kit = remotion_kit_dir()
    tag = int(limit_sec) if float(limit_sec).is_integer() else limit_sec
    out = output or (episode / "edit" / "drafts" / f"draft-open-{tag}s.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    fps = int(
        json.loads(props.read_text(encoding="utf-8"))
        .get("timeline", {})
        .get("fps", 30)
    )
    last_frame = max(0, int(round(limit_sec * fps)) - 1)
    env = _remotion_env()
    env["AE_TIMELINE_PROPS"] = str(props)
    env["AE_EPISODE"] = str(episode.resolve())
    accel = remotion_render_accel_args(nvenc=nvenc, gl=gl, verbose=verbose)
    cmd = [
        *_remotion_cli(kit),
        "render",
        "src/index.ts",
        "AgenticTimeline",
        str(out),
        "--props",
        str(props),
        f"--frames=0-{last_frame}",
        f"--jpeg-quality={int(jpeg_quality)}",
        *accel,
    ]
    print(f"$ cd {kit} && {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=str(kit), env=env, check=True)
    finally:
        _clear_remotion_cache()
    return out


def npx_available() -> bool:
    try:
        _pnpm_cmd()
        return True
    except FileNotFoundError:
        return shutil.which("npx") is not None
