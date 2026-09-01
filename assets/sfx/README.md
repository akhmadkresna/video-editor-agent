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
