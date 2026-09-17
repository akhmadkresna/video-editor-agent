# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **framework** for a local, agent-driven video editor. It is not a
long-running service: there is no HTTP server, database, or Docker. "Running the app"
means running the Python `ae` CLI pipeline against an *episode* folder and rendering
(or previewing) with HyperFrames (HTML+GSAP compositions rendered via Chrome +
FFmpeg). See `README.md` for the command reference and the hard editing rules.

### Toolchain / how to invoke things
- Two package managers are used: **uv** (Python) and **pnpm** (Node ≥20). The update
  script installs `uv` (to `~/.local/bin`) and runs `uv sync --extra dev` + `pnpm install`.
  If `uv` is not on `PATH`, add `~/.local/bin` to it.
- Run the CLI as `uv run ae <cmd>` (console script defined in `pyproject.toml`). Health
  check: `uv run ae doctor` (exits non-zero only if ffmpeg/ffprobe are missing).
- Lint: `uv run ruff check .` (there is no `[tool.ruff]` config; the repo currently has
 pre-existing findings — do not treat those as environment breakage). Tests:
 `uv run pytest` (a pytest suite exists under `tests/` and passes). TS build:
 `pnpm -r run build`.

### AGENTIC_EDITOR_HOME (non-obvious)
- When you run `ae` from *inside* the framework repo, it auto-resolves the framework
  root. When you run it from an **episode folder elsewhere on disk**, you must
  `export AGENTIC_EDITOR_HOME=<abs path to this repo>` so `ae new`/templates/the
  `hyperframes-kit` scaffold resolve. Episodes are thin folders (`project.yaml` +
  `raw/` + `edit/`) that live *outside* this repo.

### Git (this framework only)
- Commit and push framework changes **directly on `main`**. Do not open a feature /
  cursor branch or PR unless the user explicitly asks for a new branch.

### First-run network downloads (cached afterward)
- `ae ingest` uses **faster-whisper**, which downloads model weights from HuggingFace on
  first use (cached in `~/.cache/huggingface`). Default tier is `asr.model: large`
  (maps to faster-whisper `large-v3` / whisper.cpp `ggml-large-v3.bin`). For quick smoke
  tests set `asr.model: tiny` in the episode `project.yaml`. An unauthenticated HF-rate
  warning is normal.
- `ae compose` (which shells out to `npx hyperframes@<pinned>`) downloads **Chrome
  Headless Shell** for HyperFrames rendering on first use (cached under npm/npx's
  own cache). Expect a one-time download.
- **Windows (G: house layout):** pnpm store lives at `G:/AI/caches/pnpm-store`, and
  the npm cache (which HyperFrames' Chrome download and `npx` package cache live
  under) is redirected there too — see `scripts/setup-hyperframes-windows.ps1`.
- `whisper.cpp` is the macOS-only ASR path; on Linux the `auto` backend is always
  `faster-whisper`, so a missing `whisper.cpp`/`ggml-*.bin` is expected and fine.

### End-to-end pipeline (the "run the app" flow)
`ae new <ep>` → drop `raw/cam.mp4` → `ae ingest <ep>` → `ae edl-suggest <ep>` →
`ae storyboard <ep>` (review `edit/storyboard/index.html`) → `ae edl-suggest <ep> --apply`
→ `ae cut <ep>` → `ae cover <ep>` → `ae compose <ep>` (renders
`edit/final.mp4`) or `ae compose <ep> --studio` (interactive HyperFrames preview server).
Always launch preview via `ae compose --studio` (it materializes the episode's
`timeline.json` into `edit/hyperframes-project/index.html`, stages media into
`edit/hyperframes-project/assets/`, and runs `npx hyperframes preview` against that
generated project); a bare `npx hyperframes preview` outside a generated project
shows an empty scaffold with no episode content.
