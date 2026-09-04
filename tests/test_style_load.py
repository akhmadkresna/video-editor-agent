from agentic_editor.cover.style_load import (
    DEFAULT_OVERLAYS,
    DEFAULT_VOICE_ENHANCE,
    load_overlays,
    load_screen_explainer,
    load_voice_enhance,
)


def test_overlays_locked_aroll_text_motion_no_accent():
    ov = load_overlays("tutorial")
    # A-Roll Text Motion System — the one house look for every kind:
    # white ink, no panel, no accent hue; surround zones + size bands.
    assert ov["preset"] == "aroll_text_motion"
    assert ov["treatment"] == "bold"
    assert ov["ink"] == "#ffffff"
    assert "accent" not in ov
    assert "accentName" not in ov
    assert ov["fonts"]["sans"] == "Plus Jakarta Sans"
    assert ov["fonts"]["mono"] == "IBM Plex Mono"
    assert ov["dwell"]["chip_sec"] >= 3.5
    assert ov["dwell"]["emphasis_sec"] >= 2.0
    assert ov["emphasis"]["sizeCqh"] >= 20
    assert "right_third" in ov["safe"]["zones"]
    assert ov["density"]["maxSecondary"] == 1
    assert ov["sizeBands"]["heroCqh"] >= 20
    # new keys inherited from DEFAULT_OVERLAYS
    assert ov["motion"]["wordStaggerMs"] == 90
    assert ov["type"]["weightHero"] == 800
    assert ov["shape"]["fillWhite12"].startswith("rgba(255,255,255")


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
