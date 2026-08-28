"""Tests for evidence screenshot gather helpers."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_editor.preprod.gather import (
    _find_duplicate_captures,
    _normalize_text,
    gather_evidence,
)


def test_normalize_text_collapses_whitespace():
    assert _normalize_text("  92%   pakai\nAI  ") == "92% pakai ai"


def test_find_duplicate_captures_groups_by_sha256():
    ok = [
        {"id": "a", "sha256": "abc", "url": "https://example.com/a"},
        {"id": "b", "sha256": "abc", "url": "https://example.com/b"},
        {"id": "c", "sha256": "def", "url": "https://example.com/c"},
    ]
    groups = _find_duplicate_captures(ok)
    assert len(groups) == 1
    assert groups[0]["sha256"] == "abc"
    assert {s["id"] for s in groups[0]["shots"]} == {"a", "b"}


def test_gather_evidence_missing_plan_raises(tmp_path: Path):
    try:
        gather_evidence(tmp_path)
    except FileNotFoundError as exc:
        assert "evidence.plan.json" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_gather_evidence_missing_plan_writes_nothing_useful(tmp_path: Path):
    edit = tmp_path / "edit"
    edit.mkdir()
    (edit / "evidence.plan.json").write_text(json.dumps({"shots": []}), encoding="utf-8")
    report = gather_evidence(tmp_path)
    assert report["backend"] in {"playwright", "chrome_headless", "none"}
    assert (edit / "evidence.gather.json").is_file()
