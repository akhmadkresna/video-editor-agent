"""cover.cutaways[] (cam source time) → timeline.cutaways[] (output time)."""

from agentic_editor.cover import build_timeline_from_edl_and_cover
from agentic_editor.cover.remap import build_timeline_cutaways


def _edl():
    return {
        "sources": {"cam": "../raw/cam.mp4"},
        "ranges": [
            {"source": "cam", "start": 0.0, "end": 10.0},
            {"source": "cam", "start": 100.0, "end": 130.0},
        ],
    }


def _cover():
    return {
        "camera_play": {"snap_on_cuts": False},
        "cutaways": [
            {
                "scene": "ledger_flow",
                "start": 106.0,
                "end": 120.0,
                "kicker": "Buku kas",
                "openingBalance": 1200000,
                "feeds": [
                    {"label": "Penjualan", "amount": 4850000, "at": 112.5},
                    {"label": "Pembelian", "amount": -2300000, "at": 113.7},
                ],
                "cues": {
                    "ledgerIn": 106.1,
                    "balance": 116.1,
                    "lock": 119.0,
                    "attempts": [119.4],
                },
            }
        ],
    }


def test_cutaway_remaps_to_output_time():
    cuts = build_timeline_cutaways(_edl(), _cover())
    assert len(cuts) == 1
    cut = cuts[0]
    # Keep 1 is 10s long, so source 106.0 lands at 10 + 6 = 16s out.
    assert abs(cut["fromSec"] - 16.0) < 0.01
    assert abs(cut["durationSec"] - 14.0) < 0.01
    assert cut["scene"] == "ledger_flow"
    assert cut["kicker"] == "Buku kas"


def test_cutaway_cues_become_scene_local_seconds():
    cut = build_timeline_cutaways(_edl(), _cover())[0]
    assert abs(cut["cues"]["ledgerInSec"] - 0.1) < 0.01
    assert abs(cut["cues"]["balanceSec"] - 10.1) < 0.01
    assert abs(cut["cues"]["lockSec"] - 13.0) < 0.01
    assert [round(x, 2) for x in cut["cues"]["attemptSec"]] == [13.4]
    assert [round(f["atSec"], 2) for f in cut["feeds"]] == [6.5, 7.7]


def test_cutaway_outside_keeps_is_dropped():
    cover = _cover()
    cover["cutaways"][0]["start"] = 40.0
    cover["cutaways"][0]["end"] = 55.0
    assert build_timeline_cutaways(_edl(), cover) == []


def test_unknown_scene_is_ignored():
    cover = _cover()
    cover["cutaways"][0]["scene"] = "space_lasers"
    assert build_timeline_cutaways(_edl(), cover) == []


def test_timeline_carries_cutaways():
    tl = build_timeline_from_edl_and_cover(_edl(), _cover())
    assert len(tl["cutaways"]) == 1
    # Cam clips still cover the window, so VO keeps playing under the scene.
    covering = [
        c
        for c in tl["clips"]
        if c["source"] == "cam"
        and c["fromSec"] <= 16.0
        and c["fromSec"] + c["durationSec"] >= 30.0
        and c["muted"] is False
    ]
    assert covering
