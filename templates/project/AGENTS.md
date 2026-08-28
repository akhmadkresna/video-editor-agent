# Episode agent notes

This folder is the **episode**. The framework lives in `$AGENTIC_EDITOR_HOME`.

## Always

1. Read `project.yaml` and `edit/takes_packed.md` (after ingest).
2. Run tools via `ae` (not ad-hoc ffmpeg scripts).
3. **Confirm** the radio-edit strategy with the user before writing `edit/edl.json`.
4. Snap cuts to word boundaries; pad 30–200ms; 30ms audio fades (handled by `ae cut`).
5. Outputs only under `edit/`. Never modify `raw/`.

## Commands

```bash
ae doctor
ae ingest .
ae storyboard .   # HTML plan review (after edl-suggest)
ae cut .          # needs edit/edl.json; enhances cam VO
ae voice .        # optional standalone DeepFilterNet pass
ae cover .        # needs edit/cover.json (cam/screen/punch_in)
ae mezzanine .    # 1080p30 proxies + enhanced cam audio
ae compose . --studio
ae qa .
```

## OpenCode + local model (offline agent)

This episode is also wired for [OpenCode](https://opencode.ai) driven by a local
Ollama model (see `$AGENTIC_EDITOR_HOME/templates/opencode/README.md`). You talk
to it in plain language — no need to remember command names:

> "footage-nya sudah saya taruh di raw, potong jeda dan bagian yang ngulang"
> "show me storyboard" / "storyboard please" / "tampilin storyboard"

`.opencode/agent/editor.md` maps intent like that to `ae ingest` → `ae edl-suggest` →
`ae storyboard`, summarises the plan, and **waits** for your approval before `--apply` → `ae cut`.
`opencode.json` sets the local model. `.opencode/command/{autocut,shownotes}.md`
are saved-prompt shortcuts for the same thing.

The model only orchestrates and writes text; `ae edl-suggest` / `ae cut` do the
actual cut. Always confirm the plan before `--apply`.

## Promote to framework

If you invent a reusable fix (caption style, Remotion component, ASR quirk):

1. Append a note to `edit/promotions.md`.
2. Patch files under `$AGENTIC_EDITOR_HOME` (multi-root workspace preferred).
3. Re-run preview on **this** episode.

Do not leave one-off Remotion forks inside `edit/` unless truly episode-specific.
