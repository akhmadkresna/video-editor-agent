"""HyperFrames compose helpers — materialize timeline.json as a HyperFrames
project (index.html + staged assets) and invoke the `hyperframes` CLI.

This replaces the former Remotion pipeline (`--props timeline.json` fed to a
React tree). HyperFrames has no live-props system for structural/array data,
so `agentic_editor.compose.hf_template` renders timeline.json into repeated
HTML/GSAP markup at *generation* time, once per `prepare_compose` /
`prepare_draft` call — see hf_template.py's module docstring and
MIGRATION_NOTES.md at the repo root for the full rationale.

Each episode gets its own self-contained HyperFrames project directory at
`edit/hyperframes-project/` (full copy of the `packages/hyperframes-kit`
scaffold config plus a generated `index.html` and staged `assets/`), so
concurrent episodes never collide and the composition is always in sync with
the episode's current timeline.json. `packages/hyperframes-kit` itself stays
the versioned scaffold/template (and the pnpm-workspace member Studio/CLI
scripts point at for ad-hoc use), not a shared render target.
"""

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

from agentic_editor.compose.hf_template import write_hf_composition
from agentic_editor.compose.mezzanine import resolve_compose_sources
from agentic_editor.cover import build_timeline_from_edl_and_cover, write_timeline
from agentic_editor.editor.edl import load_edl
from agentic_editor.paths import framework_home
from agentic_editor.project import load_project, resolve_source

# Absolute / drive-letter paths are not loadable inside the HyperFrames
# browser sandbox — only paths relative to the project directory.
_ABS_PATH = re.compile(r"^(?:/|[A-Za-z]:[\\/]|\\\\)")

#: Pin matches packages/hyperframes-kit/package.json's scripts.
_HF_VERSION = "0.8.46"

#: Scaffold files copied from the workspace package into every generated
#: per-episode project (everything except index.html, which is generated).
_SCAFFOLD_FILES = ("hyperframes.json", "meta.json", "package.json")


def hyperframes_kit_dir() -> Path:
    return framework_home() / "packages" / "hyperframes-kit"


def episode_hf_project_dir(episode: Path, *, tag: str | None = None) -> Path:
    """Per-episode generated HyperFrames project directory.

    `tag` gives draft slices their own isolated project dir
    (`hyperframes-project-<tag>s/`) so they don't clobber the full compose.
    """
    name = "hyperframes-project" if tag is None else f"hyperframes-project-{tag}s"
    return episode / "edit" / name


def _hf_cli() -> list[str]:
    """Prefer a hoisted local bin; fall back to `npx hyperframes@<pinned>`.

    With `node-linker=hoisted` (see repo `.npmrc`), a workspace install
    puts the `hyperframes` bin under the framework root's
    `node_modules/.bin`. Most environments (including this one) resolve it
    through `npx` instead, which auto-installs on first use — same as the
    scaffolded project's own package.json scripts.
    """
    bin_name = "hyperframes.CMD" if os.name == "nt" else "hyperframes"
    local = framework_home() / "node_modules" / ".bin" / bin_name
    if local.is_file():
        return [str(local)]
    return ["npx", "--yes", f"hyperframes@{_HF_VERSION}"]


def _wipe_dir(path: Path) -> None:
    """Best-effort delete of a file or directory tree."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
    except OSError:
        pass


def cleanup_hf_project_after_final(episode: Path, *, verbose: bool = True) -> None:
    """After a successful final render, drop the staged per-episode project.

    `edit/hyperframes-project/assets/` is a full copy of cam/screen (can be
    tens of GB). Keep it during preview / draft / mg-review iteration;
    delete it once the final file has been written.
    """
    project = episode_hf_project_dir(episode)
    assets = project / "assets"
    existed = assets.exists()
    if existed:
        _wipe_dir(assets)
    if verbose and existed:
        print(f"• cleaned staged HyperFrames media → {assets}")


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


def _copy_scaffold(project_dir: Path) -> None:
    kit = hyperframes_kit_dir()
    project_dir.mkdir(parents=True, exist_ok=True)
    for name in _SCAFFOLD_FILES:
        src = kit / name
        if src.is_file():
            shutil.copy2(src, project_dir / name)


def stage_sources_for_hyperframes(
    project_dir: Path, abs_sources: dict[str, str], *, verbose: bool = True
) -> dict[str, str]:
    """Copy episode media into `<project_dir>/assets/` for HyperFrames to serve.

    Always **copy** — never hardlink. Overwriting a hardlinked asset would
    rewrite the same inode as the episode's `raw/` master.

    HyperFrames cannot load absolute filesystem paths in the browser preview
    — only paths relative to the project directory.
    """
    assets = project_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    staged: dict[str, str] = {}
    for name, abs_path in abs_sources.items():
        src = Path(abs_path).resolve()
        if not src.is_file():
            raise FileNotFoundError(f"Source {name!r} missing: {src}")
        dest_name = f"{name}{src.suffix.lower()}"
        dest = assets / dest_name
        try:
            if dest.exists() or dest.is_symlink():
                dest.unlink()
        except OSError:
            dest = assets / f"{name}.stage{src.suffix.lower()}"
            dest_name = dest.name
        shutil.copy2(src, dest)
        if not dest.is_file():
            raise RuntimeError(f"Failed to stage source {name!r} into {dest}")
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
        staged[name] = f"assets/{dest_name}"
        if verbose:
            print(f"• staged {name} → {staged[name]} ({dest.stat().st_size} bytes)")
    return staged


def stage_sfx_for_hyperframes(
    project_dir: Path,
    timeline_sfx: list[dict[str, Any]],
    *,
    style_name: str = "tutorial",
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Copy referenced style-pack SFX into `<project_dir>/assets/sfx/` and normalize src."""
    from agentic_editor.cover.style_load import sfx_pack_dir

    if not timeline_sfx:
        return []
    pack = sfx_pack_dir(style_name)
    dest_root = project_dir / "assets" / "sfx"
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
                print(f"• staged sfx → assets/sfx/{name}")
        entry["src"] = f"assets/sfx/{name}"
        out.append(entry)
    return out


def validate_timeline_for_studio(
    timeline: dict[str, Any], project_dir: Path
) -> list[str]:
    """Return human-readable errors if the composition would show black/empty media."""
    errors: list[str] = []
    clips = timeline.get("clips") or []
    frames = int(timeline.get("durationInFrames") or 0)
    dur = float(timeline.get("durationSec") or 0)

    if not clips:
        errors.append("timeline has no clips (did you write edit/edl.json?)")
    if frames < 30 or dur < 1.0:
        errors.append(
            f"timeline too short ({dur:.2f}s / {frames} frames) — looks like empty defaults"
        )

    sources = timeline.get("sources") or {}
    for name, rel in sources.items():
        if not isinstance(rel, str) or not rel.strip():
            errors.append(f"source {name!r} is empty")
            continue
        if _ABS_PATH.match(rel) or rel.startswith("file:"):
            errors.append(
                f"source {name!r} is an absolute path ({rel!r}) — "
                "the HyperFrames project can only read project-relative assets"
            )
            continue
        if rel.startswith("http://") or rel.startswith("https://"):
            continue
        disk = project_dir / rel
        if not disk.is_file():
            errors.append(f"staged file missing for {name!r}: expected {disk}")

    index_html = project_dir / "index.html"
    if not index_html.is_file():
        errors.append(f"missing generated composition {index_html}")
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

    project_dir = episode_hf_project_dir(episode)
    _copy_scaffold(project_dir)

    cover_path = edit / "cover.json"
    cover = None
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
        from agentic_editor.cover.cutaway_assets import stage_cutaway_assets_for_hyperframes
        from agentic_editor.cover.evidence import collect_evidence_sources_from_cover

        abs_sources.update(collect_evidence_sources_from_cover(episode, cover))
        staged_cover = stage_cutaway_assets_for_hyperframes(
            episode,
            cover,
            hf_project_assets=project_dir / "assets",
            verbose=verbose,
        )
        if staged_cover is not None:
            cover = staged_cover
            # Persist rewritten project-relative paths so re-opens stay valid.
            cover_path.write_text(
                json.dumps(cover, indent=2) + "\n", encoding="utf-8"
            )

    # style: mockup — drawn-screen scenes live in edit/mockup.json (kept out
    # of cover.json so cover-suggest / overlay-suggest never clobber them).
    mockup_path = edit / "mockup.json"
    if mockup_path.is_file():
        if cover is None:
            cover = {}
        mk = json.loads(mockup_path.read_text(encoding="utf-8"))
        cover["mockups"] = mk.get("scenes") if isinstance(mk, dict) else mk

    # Prefer edit/mezzanine/* (deliverable size) over multi-GB raw masters.
    compose_sources = resolve_compose_sources(
        episode, abs_sources, cfg, verbose=verbose
    )
    staged_sources = stage_sources_for_hyperframes(
        project_dir, compose_sources, verbose=verbose
    )

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
    timeline["sfx"] = stage_sfx_for_hyperframes(
        project_dir,
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
    composition_id = re.sub(r"[^a-z0-9-]", "-", episode.name.lower()) or "episode"
    write_hf_composition(
        project_dir, timeline, composition_id=composition_id, asset_map=staged_sources
    )

    errors = validate_timeline_for_studio(timeline, project_dir)
    if errors:
        msg = "compose preflight failed:\n  - " + "\n  - ".join(errors)
        raise RuntimeError(msg)

    from agentic_editor.compose.cutaway_qa import write_cutaway_contact_plan
    from agentic_editor.compose.quality import audit_timeline_quality, format_audit

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
        print(f"• hyperframes project → {project_dir.relative_to(episode)}")
        print(f"• duration {timeline['durationSec']:.1f}s / {timeline['durationInFrames']} frames")
        print("• preflight OK (staged assets + non-empty timeline)")
    return out


def prepare_draft(
    episode: Path,
    *,
    limit_sec: float = 120.0,
    verbose: bool = True,
) -> Path:
    """Prepare compose, then write a correctly sliced draft HyperFrames project.

    Always slices via ``draft_slice.slice_timeline`` (fromSec-aware) so overlays
    are not silently dropped.
    """
    from agentic_editor.compose.draft_slice import slice_timeline
    from agentic_editor.compose.quality import audit_timeline_quality, format_audit

    prepare_compose(episode, verbose=verbose)
    full_project = episode_hf_project_dir(episode)
    timeline = json.loads((episode / "edit" / "timeline.json").read_text(encoding="utf-8"))
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

    tag = int(limit_sec) if float(limit_sec).is_integer() else limit_sec
    draft_project = episode_hf_project_dir(episode, tag=str(tag))
    _copy_scaffold(draft_project)
    # Assets already staged by prepare_compose — reuse via a fresh copy so
    # the draft project is self-contained and renderable on its own.
    src_assets = full_project / "assets"
    dest_assets = draft_project / "assets"
    if dest_assets.exists():
        _wipe_dir(dest_assets)
    if src_assets.is_dir():
        shutil.copytree(src_assets, dest_assets)
    composition_id = f"draft-{tag}s"
    write_hf_composition(draft_project, sliced, composition_id=composition_id)

    drafts = episode / "edit" / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    out = drafts / f"timeline-{tag}s.json"
    write_timeline(out, sliced)
    if verbose:
        n_ov = len(sliced.get("overlays") or [])
        n_fx = len(sliced.get("effects") or [])
        print(
            f"• draft project → {draft_project.relative_to(episode)} "
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
    project_dir = episode_hf_project_dir(episode)
    timeline = json.loads((episode / "edit" / "timeline.json").read_text(encoding="utf-8"))
    errors = validate_timeline_for_studio(timeline, project_dir)
    if errors:
        raise RuntimeError("refusing to start Studio:\n  - " + "\n  - ".join(errors))

    cmd = [*_hf_cli(), "preview"]
    print(f"$ cd {project_dir} && {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(project_dir), check=True)


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
    concurrency: int | None = None,
    jpeg_quality: int = 80,
) -> Path:
    """Render the final deliverable.

    `nvenc`/`concurrency`/`jpeg_quality` are accepted for CLI back-compat but
    only `nvenc` maps onto anything HyperFrames exposes (`render --gpu`
    turns on GPU-accelerated FFmpeg encoding automatically — there is no
    documented binaries-directory / NVENC-package staging like Remotion
    needed, see MIGRATION_NOTES.md). `gl` and per-frame concurrency /
    jpeg-quality tuning have no HyperFrames CLI equivalent and are ignored.
    """
    _warn_if_mg_review_stale(episode)
    prepare_compose(episode)
    project_dir = episode_hf_project_dir(episode)
    out = output or (episode / "edit" / "final.mp4")
    if not out.is_absolute():
        out = (episode / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        *_hf_cli(),
        "render",
        "--quality",
        "delivery",
        "--output",
        str(out),
    ]
    if nvenc:
        cmd.append("--gpu")
    print(f"$ cd {project_dir} && {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(project_dir), check=True)
    cleanup_hf_project_after_final(episode)
    return out


#: All A-roll MG kinds — see the A-Roll Text Motion System in hf_template.py.
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
    "list_cycle",
)

#: Seconds into an overlay's fromSec where its entrance motion has settled —
#: a still grabbed here shows the beat at rest, not mid-entrance.
_MG_REVIEW_SETTLE_SEC = {
    "stat": 1.10,
    "emphasis": 0.75,
    "title": 0.85,
    "quote": 0.85,
    "chapter": 0.70,
    "diagram": 1.20,
    "callout": 0.90,
    "illustration": 0.50,
    "divider": 0.70,
    "lower_third": 0.55,
    "tag": 0.70,
    "list_cycle": 0.90,
}
_MG_REVIEW_SETTLE_DEFAULT = 0.6


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
    return any(stills_dir.glob("*.png"))


def load_mg_review_preview_index(episode: Path) -> dict[str, Path]:
    """Map tile id → still PNG (empty when none rendered)."""
    stills_dir = episode / "edit" / "mg-review" / "stills"
    if not stills_dir.is_dir():
        return {}
    out: dict[str, Path] = {}
    for still in stills_dir.glob("*.png"):
        out[still.stem] = still
    return out


def _mg_review_settle_time(*, kind: str, from_sec: float, exit_start: Any) -> float:
    settle = _MG_REVIEW_SETTLE_SEC.get(kind, _MG_REVIEW_SETTLE_DEFAULT)
    if isinstance(exit_start, (int, float)):
        settle = min(settle, max(0.05, float(exit_start) - 0.1))
    return from_sec + settle


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
        specs.append(
            {
                "id": eid,
                "kind": "evidence",
                "fromSec": from_sec,
                "src": src,
                "note": str(ev.get("note") or "").strip(),
                "_at": from_sec + 0.8,
            }
        )
    return specs


def render_mg_review_tiles(
    episode: Path,
    *,
    gl: str | None = None,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Snapshot every MG overlay + evidence hold via `hyperframes snapshot --at`."""
    prepare_compose(episode, verbose=verbose)
    project_dir = episode_hf_project_dir(episode)
    timeline = json.loads((episode / "edit" / "timeline.json").read_text(encoding="utf-8"))
    cover_path = episode / "edit" / "cover.json"
    cover: dict[str, Any] | None = None
    if cover_path.is_file():
        cover = json.loads(cover_path.read_text(encoding="utf-8"))
    edl_path = episode / "edit" / "edl.json"
    edl: dict[str, Any] = {}
    if edl_path.is_file():
        edl = json.loads(edl_path.read_text(encoding="utf-8"))
    fps = int(timeline.get("fps") or 30)

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

    items: list[dict[str, Any]] = []
    for ov in overlays:
        kind = str(ov["kind"])
        at = _mg_review_settle_time(
            kind=kind, from_sec=float(ov.get("fromSec") or 0.0), exit_start=ov.get("exitStartSec")
        )
        items.append({**ov, "_at": at, "_tile_kind": kind})
    items.extend(evidence_specs)

    at_list = ",".join(f"{item['_at']:.3f}" for item in items)
    snapshot_dir = project_dir / "snapshots"
    _wipe_dir(snapshot_dir)
    cmd = [*_hf_cli(), "snapshot", "--at", at_list]
    if verbose:
        print(f"$ cd {project_dir} && {' '.join(cmd)}")
    failed_run = False
    try:
        subprocess.run(cmd, cwd=str(project_dir), check=True)
    except subprocess.CalledProcessError:
        failed_run = True

    produced = sorted(snapshot_dir.glob("*.png")) if snapshot_dir.is_dir() else []

    tiles: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        tile_id = str(item["id"])
        still_path = stills_dir / f"{tile_id}.png"
        failed = failed_run or i >= len(produced)
        if not failed:
            shutil.copy2(produced[i], still_path)
        tiles.append({**item, "_still": None if failed else still_path, "_failed": failed})

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
            f"{len(failed)}/{len(tiles)} tile(s) failed to snapshot. "
            f"Gallery at {html_path} still has all {len(tiles)} tiles — the {ok_count} that "
            "succeeded plus a visible FAILED placeholder for the rest. Re-run `ae mg-review`."
        )
    return tiles


def ensure_mg_review_stills(
    episode: Path,
    *,
    force: bool = False,
    gl: str | None = None,
    verbose: bool = True,
) -> dict[str, Path]:
    """Ensure MG review stills exist; return id → still PNG path index."""
    if force or not mg_review_stills_fresh(episode):
        render_mg_review_tiles(episode, gl=gl, verbose=verbose)
    return load_mg_review_preview_index(episode)


def render_mg_review(episode: Path, *, gl: str | None = None, verbose: bool = True) -> Path:
    """Snapshot every MG overlay + evidence hold + write an HTML gallery."""
    render_mg_review_tiles(episode, gl=gl, verbose=verbose)
    return episode / "edit" / "mg-review" / "review.html"


def _mg_motion_hint(kind: str) -> str:
    hints = {
        "emphasis": "punch scale + last-word pop + underline draw",
        "title": "punch + stagger-rise (hero 64px)",
        "quote": "punch + word stagger",
        "stat": "count-up 300ms + punch",
        "chapter": "slide Y + kicker pop + line draw",
        "diagram": "rail grow + step pop",
        "callout": "slide + value count",
        "illustration": "fade + contrast scale pair",
        "divider": "punch + rule",
        "lower_third": "calm slide",
        "tag": "slide X",
    }
    return hints.get(kind, "enter + hold")


def _build_mg_review_html(tiles: list[dict[str, Any]]) -> str:
    import base64
    import html as _html

    rows = []
    for t in tiles:
        kind = _html.escape(str(t.get("kind") or ""))
        oid = _html.escape(str(t.get("id") or ""))
        from_sec = float(t.get("fromSec") or 0.0)
        at = float(t.get("_at") or from_sec)
        if t.get("_failed"):
            rows.append(
                f"""
      <figure class="failed">
        <div class="failbox">RENDER FAILED</div>
        <figcaption>
          <div class="meta"><span class="badge">{kind}</span><span class="id">{oid}</span></div>
          <div class="t">t={from_sec:.2f}s (snapshot @{at:.2f}s)</div>
        </figcaption>
      </figure>"""
            )
            continue
        img_b64 = base64.b64encode(t["_still"].read_bytes()).decode("ascii")
        tone = t.get("tone")
        badges = f'<span class="badge">{kind}</span>'
        if tone:
            border_style = "dashed" if tone == "amber" else "solid"
            badges += (
                f'<span class="badge" style="border-style:{border_style}">'
                f"{_html.escape(str(tone))}</span>"
            )
        motion = _html.escape(_mg_motion_hint(str(t.get("kind") or "")))
        rows.append(
            f"""
      <figure>
        <img src="data:image/png;base64,{img_b64}" alt="{oid}" />
        <figcaption>
          <div class="meta">{badges}<span class="id">{oid}</span></div>
          <div class="t">t={from_sec:.2f}s (snapshot @{at:.2f}s) · motion: {motion}</div>
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
    prepare_draft(episode, limit_sec=limit_sec, verbose=verbose)
    tag = int(limit_sec) if float(limit_sec).is_integer() else limit_sec
    project_dir = episode_hf_project_dir(episode, tag=str(tag))
    out = output or (episode / "edit" / "drafts" / f"draft-open-{tag}s.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [*_hf_cli(), "render", "--quality", "draft", "--output", str(out)]
    if nvenc:
        cmd.append("--gpu")
    print(f"$ cd {project_dir} && {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(project_dir), check=True)
    return out


def npx_available() -> bool:
    return shutil.which("npx") is not None
