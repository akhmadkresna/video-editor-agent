---
description: Ingest raw cam footage and propose a radio-edit (auto-cut) plan
agent: editor
---

Run the local auto-cut pipeline for this episode. Follow every step in order.
Do NOT skip the confirmation.

1. `ae doctor` — stop and tell me if ffmpeg or ffprobe is MISSING.
2. `ae ingest .` — probe + ASR. Uses the cached transcript unless `raw/` changed;
   do not pass `--force` unless I say the footage changed.
3. `ae edl-suggest .` — then read `edit/edl.suggest.json`.
4. `ae storyboard .` — open or point me at `edit/storyboard/index.html`.
5. Summarise the plan in plain language:
   - number of keep ranges
   - total keep seconds vs source seconds (and the % kept)
   - gap-class counts from `_meta.gap_classes`: breath / think / ai_wait / retake
   - anything dropped as a near-duplicate retake
6. STOP. Wait for me to reply "apply". Do not run `--apply` on your own.
7. After I confirm: `ae edl-suggest . --apply`, then `ae cut .`.
8. Tell me the path to `edit/preview.mp4` and roughly how long it is.

Never hand-edit `edit/edl.json`. Never write anything under `raw/`.
