from agentic_editor.cover.style_load import (
    DEFAULT_OVERLAYS,
    DEFAULT_VOICE_ENHANCE,
    load_overlays,
    load_screen_explainer,
    load_voice_enhance,
)


def test_overlays_locked_open_overlay_no_accent():
    ov = load_overlays("tutorial")
    # open_overlay (2026-08+, v7) is the one house look for every kind —
    # white ink, no panel, no accent color.
    assert ov["preset"] == "open_overlay"
    assert ov["treatment"] == "bold"
    assert ov["ink"] == "#ffffff"
    assert "accent" not in ov
    assert "accentName" not in ov
    assert ov["fonts"]["display"] == "Syne"
    assert ov["dwell"]["chip_sec"] >= 3.5
    assert ov["dwell"]["emphasis_sec"] >= 2.0


def test_overlays_defaults_match_constant():
    assert load_overlays("missing-style-pack")["preset"] == DEFAULT_OVERLAYS["preset"]
    assert "dwell" in DEFAULT_OVERLAYS


def test_screen_explainer_cool_mist_canvas():
    se = load_screen_explainer("tutorial")
    assert se["canvas"]["background"] == "#d9e2ec"
    assert se["preset"] == "cozy"


def test_voice_enhance_locked_deepfilternet():
    ve = load_voice_enhance("tutorial")
    assert ve["enabled"] is True
    assert ve["backend"] == "deepfilternet"
    assert ve["atten_lim_db"] == 12
    assert ve["compensate_delay"] is True
    assert DEFAULT_VOICE_ENHANCE["sources"] == ["cam"]
