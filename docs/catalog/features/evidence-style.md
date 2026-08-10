# Evidence production type

Additional style pack for **talking-head + real evidence stills** (channel-breakdown / estimator episodes).

Not the house default — that remains [`styles/tutorial/`](../../styles/tutorial/style.md).

## Select

```yaml
# project.yaml
style: evidence
series: ai-youtube-idr   # optional thumb lock
sources:
  cam: raw/cam.mp4
```

| Field | Role |
|-------|------|
| `style: evidence` | Video grammar: cam A-roll + `evidence` / `evidence_with_cam` cover events |
| `series: ai-youtube-idr` | Thumbnail brand lock only ([`styles/series/ai-youtube-idr/`](../../styles/series/ai-youtube-idr/)) |

## Assets

Put **real** screenshots in `raw/evidence/` (PNG/JPG/WebP). No AI-generated fake dashboards.

Optional provenance:

```json
// edit/evidence.json
[
  {
    "src": "sc-socialcounts.png",
    "url": "https://socialcounts.org/youtube-channel-analytics/...",
    "captured_at": "2026-08-10",
    "note": "last 28d revenue estimate"
  }
]
```

## Cover events

```json
{
  "type": "evidence_with_cam",
  "start": 42.0,
  "end": 48.0,
  "src": "sc-socialcounts.png",
  "layout": "float",
  "note": "SocialCounts estimate"
}
```

- `evidence` — still only (cool-mist float or full)
- `evidence_with_cam` — still + cam PIP (default for talking-head)
- Audio always from cam

## Overlays

Same Bold-mist MG as tutorial, plus **`callout`**:

```json
{
  "kind": "callout",
  "start": 42.0,
  "end": 45.5,
  "value": "Rp24 jt",
  "sourceLabel": "SocialCounts",
  "title": "last 28 days high"
}
```

## Commands

```bash
# After EDL + stills dropped:
ae evidence-suggest .
# review edit/evidence.suggest.json → confirm →
ae evidence-suggest . --apply
ae cover .
ae compose . --studio
```

## vs tutorial

| | tutorial | evidence |
|--|----------|----------|
| House default | yes | no |
| B-roll | screen recording | website/YouTube screenshots |
| Suggest | `ae cover-suggest` | `ae evidence-suggest` |
| Extra MG | — | `callout` |
