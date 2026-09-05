# Framework SFX pack (`assets/sfx/`)

**Single default pack for every style** (tutorial / evidence / social). Styles
may override volumes or MG→kind mapping in `style.md`, but they must not fork
audio files into `styles/*/sfx/`.

Dry UI / camera one-shots under cam VO. **No whoosh, riser, or swoosh.**

| Kind | File(s) | Used when |
|------|---------|-----------|
| `shutter` | `shutter.wav` | punch / framing snap / cut snap / MG chapter+diagram |
| `click` | `click_01`…`04.wav` | Screen-enter, click deixis / MG emphasis+chip |
| `paper` | `soft_tick.wav` | MG title/stat/quote/divider/illustration/code appear — crisp, not the old `paper_page.wav` rustle (too heavy/mechanical when it fires 10-15x/episode) |
| `tick` | `soft_tick.wav` | MG tag appear |
| `typing` | `typing-thock.wav` | **Opt-in only** (`sfx.typing.enabled: true`) |

Config: `pack.yaml` + `DEFAULT_SFX` in `style_load.py` (`pack: assets/sfx`).

All audio here is **real free recordings** (not synthesized tones). Provenance
and licenses: `LICENSES.md`.

### Loudness / trim guardrails

Silent or mis-trimmed one-shots (e.g. keeping only leading hush before a late
click) must not land in this pack. CI + `ae doctor` enforce:

- peak ≥ **−12 dBFS**
- onset within the first **50 ms** (no long quiet head)
- duration ≥ **30 ms**
- every `pack.yaml` file exists as 16-bit mono/stereo WAV

`sfx.<kind>.max_sec` (per-style, `style_load.DEFAULT_SFX` for the shared
default) must stay ≥ the mapped file's real duration, with margin — the
Remotion `<Sequence durationInFrames>` around each cue (`SfxLayer.tsx`) hard-
crops the `<Audio>` at that window, so a too-short `max_sec` truncates the
sound mid-decay instead of just padding trailing silence. `paper_page.wav`
is no longer referenced by default (kept on disk, still license-listed) but
would need `max_sec` ≥ ~0.47 if re-enabled.

See `agentic_editor.cover.sfx_validate` and `tests/test_sfx_pack.py`.
