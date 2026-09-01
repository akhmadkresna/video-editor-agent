# Framework SFX pack (`assets/sfx/`)

**Single default pack for every style** (tutorial / evidence / social). Styles
may override volumes or MG→kind mapping in `style.md`, but they must not fork
audio files into `styles/*/sfx/`.

Dry UI / camera one-shots under cam VO. **No whoosh, riser, or swoosh.**

| Kind | File(s) | Used when |
|------|---------|-----------|
| `shutter` | `shutter.wav` | punch / framing snap / cut snap / MG chapter+diagram |
| `click` | `click_01`…`04.wav` | Screen-enter, click deixis / MG emphasis+chip |
| `paper` | `paper_page.wav` | MG title/stat/quote/divider/illustration/code appear |
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

See `agentic_editor.cover.sfx_validate` and `tests/test_sfx_pack.py`.
