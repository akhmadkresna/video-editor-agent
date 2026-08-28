# Hermes Agent / Hermes Desktop as the editing agent

Run the pipeline from a single window — [Hermes Agent](https://hermes-agent.nousresearch.com/docs)
(Nous Research), model served locally by Ollama — using the repo's own skill.
Hermes adds Routines (cron), Bot Mode, memory, and messaging on top.

## Entry points

- Skill: [`skills/video-editor/`](../../skills/video-editor/) — `SKILL.md` +
  `references/{pipeline.md,rules.md}`. Hermes-standard (`agentskills.io`) format:
  `name` / `description` / `version` frontmatter, `When to Use / Procedure /
  Pitfalls / Verification` body, progressive-disclosure references.
- Pipeline it drives: `ae ingest`, `ae edl-suggest`, `ae cut`, `ae cover`,
  `ae compose` — see [radio-edit.md](radio-edit.md), [asr-ingest.md](asr-ingest.md),
  [cover-remotion.md](cover-remotion.md).

## Register the skill (no copying)

Point Hermes at the repo's `skills/` dir in `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - "${AGENTIC_EDITOR_HOME}/skills"
  write_approval: true   # optional — confirm before the agent edits any skill
```

`/reload-skills` in chat (or restart). `skills_list()` should now show
`video-editor`. Alternative: symlink `skills/video-editor` into
`~/.hermes/skills/media/video-editor`.

`AGENTIC_EDITOR_HOME` must be exported in the environment Hermes runs in, and
`ae` must be on `PATH` (or use `uv run ae` — see the framework `README.md`).

### Telegram can act on the PC (required env)

Telegram already gets the full toolset (`hermes-telegram` = terminal +
`read_file` / `write_file` / …). If the bot “can’t read anything,” the gateway
usually started without a workspace or without `AGENTIC_EDITOR_HOME`.

Put these in Hermes’s `.env` (Windows Desktop: `%LOCALAPPDATA%\hermes\.env`)
and set `terminal.cwd` in `config.yaml`, then **restart the gateway**:

```bash
# ~/.hermes/.env  (or %LOCALAPPDATA%\hermes\.env)
AGENTIC_EDITOR_HOME=G:\AI\video-editor-agent
TERMINAL_CWD=G:\AI\episodes
TERMINAL_TIMEOUT=600
```

```yaml
# config.yaml
terminal:
  backend: local
  cwd: G:\AI\episodes   # not "." — gateway cwd is otherwise useless
  timeout: 600
```

Smoke-test from Telegram Video topic:

```
pwd
echo $env:AGENTIC_EDITOR_HOME   # PowerShell
uv run --project "$env:AGENTIC_EDITOR_HOME" ae doctor
```

Dangerous commands still ask for approval in chat — reply `yes` (or `/yolo`
for that session if you trust this personal bot). Ingest/cut can take minutes;
keep `timeout` high.

## Model — `~/.hermes/config.yaml`

Ollama has no dedicated provider; use `provider: custom` (self-hosted
OpenAI-compatible) with `base_url`:

```yaml
model:
  provider: "custom"
  model: "hermes3:8b"                 # exact tag from `ollama list`
  base_url: "http://localhost:11434/v1"
  api_key: "ollama"                   # dummy; Ollama ignores it, the field is required
  context_length: 65536              # under ~4k, tool calls fail silently
  temperature: 0.2                   # low = better tool-JSON validity on an 8B
  top_p: 0.95
```

Secrets go in `~/.hermes/.env` instead if you prefer (`OPENAI_API_KEY=ollama`).
Switch models later with `hermes model` (interactive) or
`hermes config set model <name>`. Also set `OLLAMA_CONTEXT_LENGTH=65536` on the
Ollama side and restart it — both ends need the larger window.

Hermes 4 14B (12 GB+ VRAM): `ollama pull hf.co/NousResearch/Hermes-4-14B-GGUF`,
then change `model:` to that tag.

## Use it

```
/video-editor bikin project hermes-demo
    -> ae new G:\AI\episodes\hermes-demo
    -> project.yaml + raw/ + edit/   (never freestyle mkdir)
    -> "drop raw/cam.mp4, lalu bilang footage sudah di raw"

/video-editor footage-nya sudah di raw/cam.mp4, potong jeda mikir dan
              bagian yang aku ngulang — kasih lihat rencananya dulu
    -> ae doctor -> ae ingest . -> ae edl-suggest . -> ae storyboard .
    -> "20:00 -> 13:40, 68% kept, 47 ranges, 31 think-cuts, 9 retakes dropped"
    -> edit/storyboard/index.html
    -> waits

show me storyboard / storyboard please
    -> ae storyboard .  (ae edl-suggest . first if no plan yet)

oke, terapkan
    -> ae edl-suggest . --apply -> ae cut .  ->  edit/preview.mp4

/video-editor bikin judul, deskripsi, dan chapter buat YouTube
    -> edit/shownotes.md
```

Scaffold path rules: `skills/video-editor/references/scaffold.md`. The skill
maps intent to commands; the confirm gate before `--apply` is mandatory
(`references/rules.md`). On Telegram, if the bot starts inventing folders,
reload skills (`/reload-skills`) and insist on `/video-editor` / the Video topic
so the skill loads.

## Scheduled auto-cut (Hermes Routine)

Routines live under `~/.hermes/cron/` — create them from chat, not by hand:

```
buatkan routine: setiap hari 02:00, /video-editor ingest ~/episodes/current
dan usulkan radio-edit, lalu berhenti dan tinggalkan ringkasannya — jangan apply
```

A Routine runs unattended, so it must stop at the confirm gate: it produces
`edit/edl.suggest.json` + a summary message overnight; a human does the apply in
the morning.

## MCP variant (optional, typed tools)

`skills/video-editor` uses Hermes's built-in shell tool — no MCP needed. For
structured returns (plan JSON instead of parsed stdout), add `ae serve-mcp`
(framework extra `[hermes]`) and register it:

```yaml
mcp_servers:
  video-editor:
    command: "uv"
    args: ["run", "--project", "${AGENTIC_EDITOR_HOME}", "ae", "serve-mcp"]
```

`hermes mcp configure video-editor` to scope which tools are exposed.
