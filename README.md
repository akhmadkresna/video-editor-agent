# remotion-agent (Agentic Editor)

Local agentic pipeline for YouTube-style talking-head edits:

**footage → ASR → radio-edit EDL → cover (cam/screen/punch-in) → Remotion**

This repo is the **framework**. Episodes live elsewhere as thin folders (`project.yaml` + `raw/` + `edit/`).

Repo: https://github.com/akhmadkresna/remotion-agent

---

## Easy setup (paste this prompt)

Copy the block below into Cursor (or any coding agent) on a fresh machine:

```
Set up remotion-agent on this machine.

Clone https://github.com/akhmadkresna/remotion-agent.git into a sensible
dev folder (for example ~/dev/remotion-agent). That clone is the framework —
set AGENTIC_EDITOR_HOME to its absolute path and persist it in my shell
profile so new terminals keep it. Put the framework's .venv/bin on PATH
(or wire an ae alias via uv run) so the ae CLI works.

Install whatever is missing: uv, Node 20+, pnpm, and ffmpeg. On macOS also
install whisper-cpp (brew). Then from AGENTIC_EDITOR_HOME run uv sync and
pnpm install.

On macOS, download ggml-large-v3.bin into $AGENTIC_EDITOR_HOME/models/ from
https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin
(do not commit it). On Windows/Linux skip whisper-cpp —
faster-whisper from uv sync is enough (default asr.model: large → large-v3).

Symlink the Cursor skill once:
~/.cursor/skills/agentic-editor → $AGENTIC_EDITOR_HOME/skills/agentic-editor

Finish by running ae doctor and fix anything it reports missing until
ffmpeg, ffprobe, node, pnpm are OK, and either whisper.cpp + a ggml model
or faster-whisper is OK. Then briefly tell me the AGENTIC_EDITOR_HOME path
and how to create a first episode with ae new.
```

After setup, open an **episode** folder in Cursor (not only the framework), drop `raw/cam.mp4`, and ask the agent to ingest and edit. Confirm the radio-edit plan before it writes `edit/edl.json`.

---

## Local model agent (offline, no cloud)

Drive the pipeline with a **local** LLM instead of a cloud coding agent — same
`ae` commands, offline, zero per-token cost. Talk to it in plain language; it
maps intent to `ae` and waits for you before applying a cut.

- **Hermes Agent / Hermes Desktop** (recommended — one window, adds cron/Routines):
  register the repo skill via `skills.external_dirs`. See
  [`docs/catalog/features/hermes-agent.md`](docs/catalog/features/hermes-agent.md).
  Skill: [`skills/video-editor/`](skills/video-editor/).
- **OpenCode**: [`templates/opencode/README.md`](templates/opencode/README.md) ·
  [`docs/catalog/features/opencode-local.md`](docs/catalog/features/opencode-local.md).
  `ae new` scaffolds `opencode.json` + `.opencode/` into every episode.

---

## ASR backends

| `asr.backend` | Machine | Engine |
|---------------|---------|--------|
| `auto` (default) | macOS + `whisper-cli` installed | whisper.cpp |
| `auto` | no whisper.cpp, or Windows/Linux | faster-whisper |
| `whisper.cpp` / `faster-whisper` | any | force |

Default ASR language is **Indonesian** (`asr.language: id`); override per episode in `project.yaml`.

---

## Cursor workflow

- Open the **episode** folder when editing a video.
- Skill + `ae` always reach this framework via `AGENTIC_EDITOR_HOME`.
- For promotions (reusable fixes), open a multi-root workspace: episode + this repo. See [`examples/episode.code-workspace`](examples/episode.code-workspace) (edit the framework path to your clone).

---

## Commands

| Command | Purpose |
|---------|---------|
| `ae doctor` | Check deps + chosen ASR backend |
| `ae new <path>` | Scaffold episode |
| `ae ingest .` | Probe + ASR + `takes_packed.md` |
| `ae edl-suggest .` | Gap-class radio-edit proposal → `edit/edl.suggest.json` |
| `ae storyboard .` | Visual HTML plan review → `edit/storyboard/index.html` |
| `ae cut .` | EDL → `edit/preview.mp4` (enhances cam VO first) |
| `ae cover .` | EDL + cover → `timeline.json` |
| `ae voice .` | DeepFilterNet cam VO → `edit/audio/cam.voice.wav` (raw untouched) |
| `ae mezzanine .` | Deliverable proxies → `edit/mezzanine/` (muxes enhanced cam audio) |
| `ae compose . [--studio]` | Remotion preview / render |
| `ae qa .` | Cut-boundary frames in `edit/verify/` |
| `ae social . [--studio]` | Separate 1080×1920 karaoke cut from `edit/social/` |
| `ae social . --qa` | Representative portrait frames in `edit/social/verify/` |
| `ae promote-check .` | Show `edit/promotions.md` |

---

## Layout

```
src/agentic_editor/    # Python CLI + ASR + editor + cover
packages/schema/       # Zod contracts
packages/remotion-kit/ # Remotion composition
templates/project/     # ae new scaffold
skills/agentic-editor/
styles/tutorial/
docs/catalog/
models/                # ggml *.bin (gitignored — download locally)
```

---

## Hard rules (editing)

1. Confirm strategy before writing `edit/edl.json`.
2. Never cut mid-word; snap to transcript word boundaries; pad 30–200ms.
3. `ae cut` applies 30ms audio fades — do not skip.
4. Cache transcripts — never re-ASR unless source changed (`ae ingest --force`).
5. All outputs in `edit/`. Raw footage is read-only (compose **copies** into public — never hardlinks).
6. Promote reusable changes into this repo, not episode copies.
7. Heavy raw (e.g. 1440p60 multi‑GB): `ae mezzanine .` before compose — CRF16 deliverable proxies, no quality loss for YouTube 1080p.
8. Cam VO is DeepFilterNet-enhanced by default (`-D -a 12`). Cache `edit/audio/cam.voice.wav`. Opt out: `voice_enhance.enabled: false` in `project.yaml`. Do not use ffmpeg denoise/gate chains.
