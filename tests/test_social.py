from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.style_load import (
    load_overlays,
    load_screen_explainer,
    load_social,
)
from agentic_editor.social import build_karaoke_captions, force_screen_stage


def test_karaoke_words_remap_through_short_edl():
    edl = {
        "sources": {"cam": "../raw/cam.mp4"},
        "ranges": [
            {"source": "cam", "start": 10.0, "end": 12.0},
            {"source": "cam", "start": 20.0, "end": 22.0},
        ],
    }
    words = [
        {"word": "Odoo", "start": 10.2, "end": 10.6},
        {"word": "gratis", "start": 10.7, "end": 11.1},
        {"word": "stok", "start": 20.1, "end": 20.5},
        {"word": "turun", "start": 20.6, "end": 21.0},
    ]

    captions = build_karaoke_captions(edl, words, max_words=2)

    assert len(captions) == 2
    assert captions[0]["text"] == "Odoo gratis"
    assert abs(captions[0]["words"][0]["start"] - 0.2) < 1e-6
    assert abs(captions[1]["words"][0]["start"] - 2.1) < 1e-6
    assert captions[1]["style"] == "karaoke"


def test_karaoke_applies_case_insensitive_word_corrections():
    edl = {
        "sources": {"cam": "../raw/cam.mp4"},
        "ranges": [{"source": "cam", "start": 0.0, "end": 2.0}],
    }
    words = [{"word": "ONKM,", "start": 0.2, "end": 0.6}]

    captions = build_karaoke_captions(
        edl,
        words,
        replacements={"onkm": "UMKM"},
    )

    assert captions[0]["text"] == "UMKM,"


def test_social_style_forces_screen_stage_by_default():
    assert load_social("social")["force_screen_with_cam"] is True


def test_social_style_ships_always_on_blinking_cta():
    cta = load_social("social")["cta"]
    assert cta["enabled"] is True
    assert cta["blink"] is True
    assert cta["anchor"] == "band_top_center"
    assert "YouTube" in cta["text"]


def test_social_letterbox_zones():
    se = load_screen_explainer("social")
    screen = se["screen"]
    pip = se["pip"]
    assert screen["presentation"] == "letterbox_landscape"
    assert se["preset"] == "social_letterbox"
    assert se["canvas"]["background"] == "#000000"
    assert "left" in pip["anchor"]
    assert pip["widthRatio"] <= 0.28
    overlays = load_overlays("social")
    # MG pinned into the top black bar.
    assert overlays["chapter"]["topCqh"] < 20
    assert overlays["emphasis"]["topCqh"] < 20
    assert overlays["callout"]["topCqh"] < 20


def test_forced_stage_never_leaves_full_cam_in_portrait():
    edl = {
        "sources": {"cam": "cam.mp4", "screen": "screen.mp4"},
        "ranges": [
            {"source": "cam", "start": 10.0, "end": 20.0, "note": "hook"},
            {"source": "cam", "start": 40.0, "end": 46.0, "note": "proof"},
        ],
    }
    cover = {
        "camera_play": {"snap_on_cuts": True, "max_hold_sec": 8},
        "events": [
            {"type": "framing", "start": 10.0, "end": 14.0, "framing": "close"},
            {"type": "screen_with_cam", "start": 40.0, "end": 46.0},
        ],
    }

    timeline = build_timeline_from_edl_and_cover(
        edl,
        force_screen_stage(cover, edl),
        width=1080,
        height=1920,
        screen_explainer=load_screen_explainer("social"),
    )

    layouts = {c["layout"] for c in timeline["clips"]}
    assert layouts == {"float_centered", "pip_corner"}
    pip = [c for c in timeline["clips"] if c["layout"] == "pip_corner"]
    assert all(c["source"] == "cam" and c["muted"] is False for c in pip)
    assert sum(c["durationSec"] for c in pip) == 16.0
