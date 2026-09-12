# Series: Odoo POS Tutorial

A **practical tutorial series**: Odoo SaaS (Odoo Online), Point of Sale
app, config-by-config, ordered by what the market actually searches for.
Follow-up to a standalone "sistem kasir" video that already proved this
topic draws viewers — this series goes deeper, one feature area per
episode.

Not a free-plan explainer. Not a features-dump. Each episode is **light
and easy to shoot**: one screen-recording pass through a real config,
talking-head narration, no staged multi-take demos.

```yaml
style: tutorial
series: odoo-pos-tutorial
asr:
  language: id
```

Research + full feature map + episode slate: [`research.md`](research.md).

## Positioning

- **Audience:** Indonesian UMKM owners / ops staff / freelance
  implementers looking for a real "how do I set this up" walkthrough —
  not developers, not enterprise IT.
- **Promise:** every episode, one working config by the end of it. Show
  the exact clicks, not a features slideshow.
- **Persona:** same senior-engineer-adjacent, humble voice as the rest of
  the channel. "Here's how you'd actually set this up for your toko."
- **Voice:** **saya / kalian**, bahasa lisan. English terms that read
  naturally stay English (config, session, barcode, checkout, sync).
- **Tone guardrail:** be honest about what needs extra setup (a real
  merchant/payment-provider account for automated QRIS, physical
  hardware for a real till) — don't imply everything works out of the
  box with zero friction. Say it once, plainly, then move on; don't
  dwell.
- **Setup-light rule:** every episode uses only Odoo Online (SaaS) in a
  browser. No self-hosting, no Docker, no custom code. Hardware/offline
  specifics get their own dedicated episode instead of derailing others.
- **Recording-reality rule:** the user has **no POS hardware** (no
  receipt printer, barcode scanner, cash drawer, IoT Box) and no live
  merchant/payment-provider account. Every episode must be shootable
  solo at a desk with just a browser (and optionally a phone for QR
  scanning). Never stage or fake a demo of something not actually
  running on screen — if a feature needs hardware or a merchant account
  the user doesn't have, show the config screen and say plainly it needs
  that, instead of pretending to complete it live.

## Episode spine (~8–10 min, tutorial-paced)

1. **Hook (0:00–0:30)** — name the config this episode delivers and who
   it's for ("buat kamu yang punya toko/cafe dan butuh X").
2. **Kenapa ini penting (0:30–1:30)** — one real pain point this config
   solves, plainly stated.
3. **Setup walkthrough (1:30–7:00)** — screen recording, real clicks, in
   order. Callout overlays on every setting that matters.
4. **Yang perlu diperhatikan (7:00–8:30)** — gotchas, what needs an
   external partner/hardware, what's easy to misconfigure.
5. **Wrap + next (8:30–end)** — recap what's now working, tease next
   episode's config.

## Production grammar (fixed per episode)

- **Style:** `style: tutorial` per `styles/tutorial/style.md` — cool-mist
  screen float + cam PIP when showing the browser, full cam for talking
  points.
- **Source — single pre-edited file per episode (series-specific, differs
  from the default two-track template):** the host records and does their
  own rough cut (trims dead air/mistakes) before handoff. There is **no
  separate `raw/screen.mp4`.** Every episode ships exactly one
  `raw/cam.mp4`, in one of two shapes:
  - **Cam-only** (talking-head beats, no browser on screen):
    `sources: { cam: raw/cam.mp4 }`, `composite` left off.
  - **Cam+screen baked into one frame** (OBS scene with the browser
    already composited as PIP inside the cam recording): same single
    `cam: raw/cam.mp4`, `composite.enabled: true` + `composite.baked_pip:
    true` so `ae cover` doesn't add a second PIP corner on top of the
    baked one.
  - Real screen recording (baked in via OBS), not a mockup — this series
    is about showing exact configuration steps.
- **Zoom play — "plain," full-cam-only, series default** (confirmed
  2026-09-12, supersedes the earlier flat-everywhere default): a real
  (non-flat) `camera_play`, but tuned to never sit stale above 1x —
  ```yaml
  composite:
    camera_play:
      enabled: true
      snap_on_cuts: true
      wide_on_resets: true
      home: wide      # 1.0 is the resting/reset framing
      alt: medium      # only alternate beat crops in, briefly
      max_hold_sec: 9  # forces a reset before a hold reads as static
      scales: { wide: 1.0, medium: 1.16, close: 1.32 }
  ```
  This is safe to set for the whole episode without touching the
  cam+screen sections: `cover/__init__.py`'s `broll_visual` check
  force-wides (`scale: 1.0, motion: hold`) any range tagged
  `screen_with_cam` regardless of `camera_play`, so the zoom only ever
  visibly plays on the true full-cam stretch. **Ground-truth override
  needed:** the activity+deixis probe under-detects screen presence on
  quiet UI moments (host talking without clicking) and mislabels them as
  `full_cam`, which would let the zoom crop into baked browser UI. Since
  this series' actual full-cam window is a single, known, short stretch
  (the intro hook, before the browser first appears on screen), mark
  everything from that point to the end of the kept footage as
  `screen_with_cam` explicitly in `cover.json`'s `events[]` — one range,
  not per-segment — rather than trusting the per-segment probe result.
  **After retuning `composite.camera_play` in `project.yaml`, also delete
  any stale `camera_play` key directly on `edit/cover.json`** if one
  exists from an earlier config — it no longer overrides the render
  (fixed 2026-09-12, see `promotions.md`), but a leftover copy is
  confusing for the next read of the file.
- **Overlays — full-cam-only, series default:** MG lives on the full-cam
  intro/talking-head beats only; the cam+screen config walkthrough stays
  clean (the screen itself carries the information — no `callout`/`chip`
  layered on top). Within the full-cam beats:
  - **Single short stat/phrase** (1 idea): `emphasis` or `callout`
    (`PunchWord`), clean hand-written text pulled from the real spoken
    line — never a raw ASR pull-quote fragment (auto-suggest's `quote`/
    `chapter`/`title` kinds routinely land mid-sentence; rewrite or drop).
  - **Multi-word / "topic" callout** (a contrast, a short list, a roadmap
    line — e.g. "v17 → v19", "POS → Config → Jualan"): use `kind:
    "name_drop"` with `steps: [...]` (one array entry per word/phrase),
    **not** a single `PunchWord` block with an arrow glyph joining them.
    `NameDrop` places each word around the speaker (built-in 1–4-word
    layouts), pops them in staggered, then exits together near the end of
    the overlay's window — no extra config needed beyond `steps[]`,
    `exitStartSec` is auto-computed. See
    `remotion-kit/src/components/overlay/NameDrop.tsx`.
    **`nameDropExit: "sand"` on every `name_drop` overlay — series
    default, confirmed 2026-09-12** (superseding the initial idea of
    alternating `fall`/`sand` for variety — tried both, `sand` alone read
    better across a whole episode than mixing in the punchier `fall`).
    Each letter scatters outward with a deterministic per-letter drift,
    blurring and fading, while the shot keeps a slow continuous zoom-in.
    Component default is still `fall` (gravity+spin) for back-compat with
    other series already using this kind unchanged — always set
    `nameDropExit: "sand"` explicitly per overlay in this series.
  - `diagram` only if a workflow (e.g. session-close → accounting
    posting) needs a visual, still full-cam only.
- **Radio edit:** standard `tutorial` pack settings, still runs on top of
  the host's pre-edit — `ae edl-suggest` → confirm → `ae cut`. Expect it
  to find little (filler words / small leftover pauses only, not gross
  cuts), since the rough cut is already done. Don't skip it: it's what
  applies the standard word-boundary snap + fades, and still needs
  confirmation before `edit/edl.json` is written (per house Hard Rule).
  No custom forks per episode.

## Episode slate (draft — see research.md for full rationale)

| # | Episode | Config delivered |
|---|---------|-------------------|
| 01 | Setup kasir pertama dari nol | Odoo Online signup → POS app → first session → first sale |
| 02 | Config retail | Barcode, kategori, diskon barcode, multi-outlet dasar |
| 03 | Config resto/cafe | Floor plan, kitchen display, split bill, preset switching |
| 04 | Bayar & tutup kasir tanpa pusing | Tunai + QR code payment bawaan (live, no account needed) + tutup sesi → akuntansi. Card/Xendit-automated QRIS: mentioned, not demoed. |
| 05 | Offline & apa yang butuh internet | Toggle offline/online (desk-recordable), penjelasan konseptual singkat soal hardware fisik (tidak didemokan — user belum punya) |
| 06 | Studi kasus UMKM | End-to-end toko/warung/cafe: diskon, loyalty, laporan |

## Hard rules for agents

1. Every config claim (menu path, setting name, default behavior) must
   match the live Odoo Online UI at recording time — Odoo ships point
   releases often; verify on screen, don't rely on stale research notes.
2. State plainly, once, when something needs an external partner or paid
   hardware (automated Xendit QRIS, card terminal, IoT Box) — no
   implying it's zero-setup. Don't conflate POS's generic built-in QR
   payment (manual, no account needed) with a Xendit-automated flow
   (separate Finance-level integration) — they are different features.
3. Never fake a demo of hardware or an account the user doesn't have.
   Show the config screen and narrate what it needs instead.
4. Keep each episode to one config area. If a walkthrough needs a second
   app installed beyond POS/Invoicing/Inventory, say so on screen instead
   of silently doing it off-camera.
5. Humble **saya/kalian** voice, tutorial pacing — clicks shown in real
   time or clearly sped up, never skipped silently.
6. Confirm radio-edit before `edit/edl.json`.
