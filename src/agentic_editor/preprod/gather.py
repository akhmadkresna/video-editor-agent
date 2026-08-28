"""Capture real evidence screenshots from evidence.plan.json."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_COOKIE_DISMISS_SELECTORS = (
    "#onetrust-accept-btn-handler",
    "button#accept-cookies",
    "button.accept-cookies",
    'button:has-text("Accept all")',
    'button:has-text("Accept All")',
    'button:has-text("Accept")',
    'button:has-text("I agree")',
    'button:has-text("Terima semua")',
    'button:has-text("Terima")',
    'button:has-text("Setuju")',
    'button:has-text("Allow all")',
)


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
        "duplicates": [],
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
            _capture(backend, url, dest, shot=shot, timeout_ms=timeout_ms)
            digest = _file_sha256(dest)
            report["ok"].append(
                {
                    "id": shot.get("id"),
                    "src": dest.name,
                    "url": url,
                    "path": str(dest),
                    "bytes": dest.stat().st_size,
                    "sha256": digest,
                }
            )
        except Exception as exc:  # noqa: BLE001 — surface per-shot failures
            if force and dest.is_file():
                dest.unlink()
            report["failed"].append({"id": shot.get("id"), "url": url, "error": str(exc)})

    report["duplicates"] = _find_duplicate_captures(report.get("ok") or [])
    if report["duplicates"]:
        dup_ids = {
            item.get("id")
            for group in report["duplicates"]
            for item in group["shots"]
        }
        for group in report["duplicates"]:
            peer_ids = ", ".join(str(s.get("id")) for s in group["shots"])
            for item in group["shots"]:
                report["failed"].append(
                    {
                        "id": item.get("id"),
                        "url": item.get("url"),
                        "error": (
                            f"duplicate capture (sha256={group['sha256'][:12]}…) "
                            f"— same viewport as: {peer_ids}. "
                            "Add scroll_to_text or selector per shot."
                        ),
                    }
                )
        report["ok"] = [item for item in report.get("ok") or [] if item.get("id") not in dup_ids]

    _write_provenance(edit, shots, report)
    (edit / "evidence.gather.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _find_duplicate_captures(ok_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group captures that share the same sha256 (same viewport = bad for multi-shot URLs)."""
    by_hash: dict[str, list[dict[str, Any]]] = {}
    for item in ok_items:
        digest = str(item.get("sha256") or "")
        if not digest:
            continue
        by_hash.setdefault(digest, []).append(item)
    return [
        {"sha256": digest, "shots": items}
        for digest, items in by_hash.items()
        if len(items) > 1
    ]


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
                "sha256": item.get("sha256"),
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


def _capture(
    backend: dict[str, Any],
    url: str,
    dest: Path,
    *,
    shot: dict[str, Any],
    timeout_ms: int,
) -> None:
    if backend["name"] == "playwright":
        _capture_playwright(url, dest, shot=shot, timeout_ms=timeout_ms)
        return
    if backend["name"] == "chrome_headless":
        if shot.get("scroll_to_text") or shot.get("selector") or shot.get("must_contain"):
            raise RuntimeError(
                "scroll_to_text/selector/must_contain require Playwright "
                "(uv sync --extra evidence && uv run playwright install chromium)"
            )
        _capture_chrome(backend["bin"], url, dest, timeout_ms=timeout_ms)
        return
    raise RuntimeError("no capture backend")


def _capture_playwright(
    url: str, dest: Path, *, shot: dict[str, Any], timeout_ms: int
) -> None:
    from playwright.sync_api import sync_playwright

    wait_until = str(shot.get("wait_until") or "domcontentloaded")
    viewport = shot.get("viewport") or {"width": 1440, "height": 900}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport=viewport)
            page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            page.wait_for_timeout(int(shot.get("settle_ms") or 1200))
            if shot.get("dismiss_cookies", True):
                _try_dismiss_cookies(page)
            _prepare_viewport(page, shot, timeout_ms=timeout_ms)
            _assert_must_contain(page, shot)
            selector = str(shot.get("selector") or "").strip()
            if selector:
                loc = page.locator(selector).first
                loc.wait_for(state="visible", timeout=timeout_ms)
                loc.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                loc.screenshot(path=str(dest))
            else:
                page.screenshot(path=str(dest), full_page=bool(shot.get("full_page")))
        finally:
            browser.close()
    if not dest.is_file() or dest.stat().st_size < 100:
        raise RuntimeError(f"playwright screenshot empty: {dest}")


def _prepare_viewport(page: Any, shot: dict[str, Any], *, timeout_ms: int) -> None:
    scroll_text = str(shot.get("scroll_to_text") or "").strip()
    if scroll_text:
        _scroll_to_text(page, scroll_text, timeout_ms=timeout_ms)
        return
    anchor = str(shot.get("anchor") or shot.get("fragment") or "").strip().lstrip("#")
    if anchor:
        page.evaluate(
            """(id) => {
                const el = document.getElementById(id);
                if (el) el.scrollIntoView({ block: 'center' });
            }""",
            anchor,
        )
        page.wait_for_timeout(400)


def _scroll_to_text(page: Any, text: str, *, timeout_ms: int) -> None:
    if _scroll_to_text_js(page, text):
        return
    loc = page.get_by_text(text, exact=False).first
    loc.wait_for(state="attached", timeout=timeout_ms)
    try:
        loc.scroll_into_view_if_needed(timeout=min(timeout_ms, 15_000))
    except Exception:
        if not _scroll_to_text_js(page, text):
            raise
    page.wait_for_timeout(400)
    page.evaluate("() => window.scrollBy(0, -120)")


def _scroll_to_text_js(page: Any, text: str) -> bool:
    return bool(
        page.evaluate(
            """
            (search) => {
                const norm = (s) => s.replace(/\\s+/g, " ").trim().toLowerCase();
                const target = norm(search);
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT
                );
                let node;
                while ((node = walker.nextNode())) {
                    if (!norm(node.textContent).includes(target)) continue;
                    let el = node.parentElement;
                    while (el && el !== document.body) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 || rect.height > 0) break;
                        el = el.parentElement;
                    }
                    if (el) {
                        el.scrollIntoView({ block: "center", inline: "nearest" });
                        window.scrollBy(0, -120);
                        return true;
                    }
                }
                return false;
            }
            """,
            text,
        )
    )


def _assert_must_contain(page: Any, shot: dict[str, Any]) -> None:
    required = [str(x).strip() for x in (shot.get("must_contain") or []) if str(x).strip()]
    if not required:
        return
    body = page.inner_text("body")
    normalized = _normalize_text(body)
    missing = [token for token in required if _normalize_text(token) not in normalized]
    if missing:
        raise RuntimeError(f"page missing expected text: {', '.join(missing)}")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _try_dismiss_cookies(page: Any) -> None:
    for selector in _COOKIE_DISMISS_SELECTORS:
        try:
            btn = page.locator(selector).first
            if btn.count() and btn.is_visible():
                btn.click(timeout=1500)
                page.wait_for_timeout(400)
                return
        except Exception:  # noqa: BLE001 — best-effort cookie banners
            continue


def _capture_chrome(bin_path: str, url: str, dest: Path, *, timeout_ms: int) -> None:
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
