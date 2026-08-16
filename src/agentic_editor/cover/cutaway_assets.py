"""Stage cutaway image assets into Remotion public/ae-media/cutaways/."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _safe_stem(raw: str) -> str:
    stem = Path(raw).stem
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)
    return (cleaned.strip("_") or "asset")[:48]


def resolve_cutaway_asset_path(episode: Path, src: str) -> Path | None:
    """Resolve an episode-relative or absolute cutaway still."""
    raw = str(src or "").strip().replace("\\", "/")
    if not raw:
        return None
    # Already staged public-relative — caller keeps as-is.
    if raw.startswith("ae-media/"):
        return None
    p = Path(raw)
    if p.is_absolute():
        return p if p.is_file() else None
    candidates = [
        episode / raw,
        episode / Path(*Path(raw).parts),
        episode / "edit" / raw,
        episode / "edit" / "cutaway_assets" / Path(raw).name,
        episode / "raw" / "cutaway_assets" / Path(raw).name,
        episode / "raw" / "evidence" / Path(raw).name,
        episode / "edit" / "evidence" / Path(raw).name,
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return None


def collect_cutaway_asset_refs(cover: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten proof/assets/backdrop image refs from cover.cutaways[]."""
    if not cover:
        return []
    refs: list[dict[str, Any]] = []
    for i, cut in enumerate(cover.get("cutaways") or []):
        if not isinstance(cut, dict):
            continue
        cid = str(cut.get("id") or f"cut-{i}")
        proof = cut.get("proof")
        if isinstance(proof, dict) and proof.get("src"):
            refs.append(
                {
                    "cutawayId": cid,
                    "field": "proof",
                    "asset": proof,
                    "role": str(proof.get("role") or "proof"),
                }
            )
        for j, asset in enumerate(cut.get("assets") or []):
            if isinstance(asset, dict) and asset.get("src"):
                refs.append(
                    {
                        "cutawayId": cid,
                        "field": f"assets[{j}]",
                        "asset": asset,
                        "role": str(asset.get("role") or "proof"),
                    }
                )
        backdrop = cut.get("backdrop")
        if (
            isinstance(backdrop, dict)
            and backdrop.get("kind") == "image"
            and backdrop.get("src")
        ):
            refs.append(
                {
                    "cutawayId": cid,
                    "field": "backdrop",
                    "asset": backdrop,
                    "role": "texture",
                }
            )
    return refs


def stage_cutaway_assets_for_remotion(
    episode: Path,
    cover: dict[str, Any] | None,
    *,
    remotion_public: Path,
    verbose: bool = False,
) -> dict[str, Any] | None:
    """Copy cutaway stills into public/ae-media/cutaways/ and rewrite cover paths.

    Returns an updated cover dict when any path changed; otherwise None.
    Already-public ``ae-media/...`` paths are left untouched.
    """
    if not cover:
        return None
    refs = collect_cutaway_asset_refs(cover)
    if not refs:
        return None

    dest_root = remotion_public / "ae-media" / "cutaways"
    dest_root.mkdir(parents=True, exist_ok=True)
    changed = False
    new_cover = dict(cover)
    new_cuts = [
        dict(c) if isinstance(c, dict) else c for c in (cover.get("cutaways") or [])
    ]
    new_cover["cutaways"] = new_cuts

    # Ensure ids so refs can match cuts without author-provided ids.
    for i, cut in enumerate(new_cuts):
        if isinstance(cut, dict) and not cut.get("id"):
            cut["id"] = f"cut-{i}"

    for ref in refs:
        asset = ref["asset"]
        src = str(asset.get("src") or "")
        if src.startswith("ae-media/"):
            continue
        resolved = resolve_cutaway_asset_path(episode, src)
        if resolved is None:
            if verbose:
                print(f"• cutaway asset missing: {src}")
            continue
        suffix = resolved.suffix.lower() or ".png"
        if suffix not in IMAGE_SUFFIXES:
            if verbose:
                print(f"• cutaway asset skipped (not image): {resolved}")
            continue
        digest = hashlib.sha1(str(resolved).encode("utf-8")).hexdigest()[:8]
        dest_name = f"{_safe_stem(resolved.name)}_{digest}{suffix}"
        dest = dest_root / dest_name
        if not dest.is_file() or dest.stat().st_size != resolved.stat().st_size:
            shutil.copy2(resolved, dest)
            if verbose:
                print(f"• staged cutaway asset → public/ae-media/cutaways/{dest_name}")
        public_rel = f"ae-media/cutaways/{dest_name}"

        def _rewrite_src(obj: dict[str, Any]) -> dict[str, Any]:
            if obj.get("src") != src:
                return obj
            out = {
                **obj,
                "src": public_rel,
            }
            if "kind" not in obj:  # asset, not backdrop
                out["provenance"] = obj.get("provenance") or src
                out["role"] = obj.get("role") or ref["role"]
            return out

        for cut in new_cuts:
            if not isinstance(cut, dict):
                continue
            # Match by id when present; also rewrite any cut that still has this src.
            if cut.get("id") and str(cut.get("id")) != ref["cutawayId"]:
                # Still allow src-based rewrite below.
                pass
            if isinstance(cut.get("proof"), dict) and cut["proof"].get("src") == src:
                cut["proof"] = _rewrite_src(cut["proof"])
                changed = True
            if isinstance(cut.get("backdrop"), dict) and cut["backdrop"].get("src") == src:
                cut["backdrop"] = _rewrite_src(cut["backdrop"])
                changed = True
            if isinstance(cut.get("assets"), list):
                assets = []
                for a in cut["assets"]:
                    if isinstance(a, dict) and a.get("src") == src:
                        assets.append(_rewrite_src(a))
                        changed = True
                    else:
                        assets.append(a)
                cut["assets"] = assets

    return new_cover if changed else None
