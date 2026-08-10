"""Capture real evidence screenshots from evidence.plan.json."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def gather_evidence(
    episode: Path,
    *,
    plan_path: Path | None = None,
    force: bool = False,
    timeout_ms: int = 45_000,
) -> dict[str, Any]:
    """Screenshot planned URLs into raw/evidence/. Prefer Playwright; else Chrome CDP-less.

    Returns a report dict. Never invents dashboard pixels with AI.
    """
    edit = episode / "edit"
    plan_file = plan_path or (edit / "evidence.plan.json")
    if not plan_file.is_file():
        raise FileNotFoundError(
            f"Missing {plan_file} — run: ae brief . --channel <name> first"
        )
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    shots = [s for s in (plan.get("shots") or []) if isinstance(s, dict)]
    out_dir = episode / "raw" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "gathered_at": datetime.now(timezone.utc).isoformat(),
        "backend": None,
        "ok": [],
        "skipped": [],
        "failed": [],
    }

    backend = _pick_backend()
    report["backend"] = backend["name"]
    if backend["name"] == "none":
        report["failed"].append(
            {
                "error": (
                    "No browser capture backend. Install: "
                    "uv sync --extra evidence && uv run playwright install chromium"
                )
            }
        )
        _write_provenance(edit, shots, report)
        return report

    for shot in shots:
        if shot.get("skip_gather") or (shot.get("optional") and not shot.get("url")):
            report["skipped"].append({"id": shot.get("id"), "reason": "optional/skip_gather"})
            continue
        url = str(shot.get("url") or "").strip()
        src_name = str(shot.get("src") or f"{shot.get('id')}.png")
        dest = out_dir / Path(src_name).name
        if dest.is_file() and not force:
            report["skipped"].append({"id": shot.get("id"), "reason": "exists", "path": str(dest)})
            continue
        if not url:
            report["skipped"].append({"id": shot.get("id"), "reason": "no url"})
            continue
        try:
            _capture(backend, url, dest, timeout_ms=timeout_ms)
            report["ok"].append(
                {
                    "id": shot.get("id"),
                    "src": dest.name,
                    "url": url,
                    "path": str(dest),
                    "bytes": dest.stat().st_size,
                }
            )
        except Exception as exc:  # noqa: BLE001 — surface per-shot failures
            report["failed"].append({"id": shot.get("id"), "url": url, "error": str(exc)})

    _write_provenance(edit, shots, report)
    (edit / "evidence.gather.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def _write_provenance(
    edit: Path, shots: list[dict[str, Any]], report: dict[str, Any]
) -> None:
    """Merge capture results into edit/evidence.json for QA."""
    by_id = {s.get("id"): s for s in shots}
    rows: list[dict[str, Any]] = []
    for item in report.get("ok") or []:
        meta = by_id.get(item.get("id")) or {}
        rows.append(
            {
                "id": item.get("id"),
                "src": item.get("src"),
                "url": item.get("url"),
                "captured_at": report.get("gathered_at"),
                "label": meta.get("label"),
                "note": meta.get("note"),
                "callout_value": meta.get("callout_value"),
            }
        )
    path = edit / "evidence.json"
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _pick_backend() -> dict[str, Any]:
    try:
        import playwright  # noqa: F401
        from playwright.sync_api import sync_playwright  # noqa: F401

        return {"name": "playwright"}
    except ImportError:
        pass
    chrome = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which(
        "chromium"
    ) or shutil.which("msedge")
    if chrome:
        return {"name": "chrome_headless", "bin": chrome}
    return {"name": "none"}


def _capture(backend: dict[str, Any], url: str, dest: Path, *, timeout_ms: int) -> None:
    if backend["name"] == "playwright":
        _capture_playwright(url, dest, timeout_ms=timeout_ms)
        return
    if backend["name"] == "chrome_headless":
        _capture_chrome(backend["bin"], url, dest, timeout_ms=timeout_ms)
        return
    raise RuntimeError("no capture backend")


def _capture_playwright(url: str, dest: Path, *, timeout_ms: int) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(dest), full_page=False)
        finally:
            browser.close()
    if not dest.is_file() or dest.stat().st_size < 100:
        raise RuntimeError(f"playwright screenshot empty: {dest}")


def _capture_chrome(bin_path: str, url: str, dest: Path, *, timeout_ms: int) -> None:
    # Chromium --screenshot writes to cwd as screenshot.png unless --screenshot=path (newer).
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        bin_path,
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={dest}",
        "--window-size=1440,900",
        "--hide-scrollbars",
        url,
    ]
    subprocess.run(
        cmd,
        check=True,
        timeout=max(30, timeout_ms / 1000),
        capture_output=True,
    )
    if not dest.is_file() or dest.stat().st_size < 100:
        raise RuntimeError(f"chrome screenshot empty: {dest}")
