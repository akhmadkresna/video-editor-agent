from agentic_editor.cover.style_load import (
    DEFAULT_OVERLAYS,
    DEFAULT_VOICE_ENHANCE,
    load_overlays,
    load_screen_explainer,
    load_voice_enhance,
)


def test_overlays_locked_glass_with_legacy_bold_cool_mist():
    ov = load_overlays("tutorial")
    # glass is the house default (2026-08+); bold_mist tokens below still
    # style the legacy chapter/emphasis/diagram/chip/callout kinds.
    assert ov["preset"] == "glass"
    assert ov["legacyPreset"] == "bold_mist"
    assert ov["treatment"] == "bold"
    assert ov["accent"] == "#7dd3fc"
    assert ov["accentName"] == "cool_mist_sky"
    assert ov["fonts"]["display"] == "Syne"
    assert ov["dwell"]["chip_sec"] >= 3.5
    assert ov["dwell"]["emphasis_sec"] >= 2.0


def test_overlays_defaults_match_constant():
    assert load_overlays("missing-style-pack")["accent"] == DEFAULT_OVERLAYS["accent"]
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
