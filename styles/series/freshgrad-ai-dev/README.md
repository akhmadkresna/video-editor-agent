# Series: Kampus, AI, dan Masa Depan Anak IT

Talking-head series for Indonesian CS / Informatika / SI students and
fresh graduates. House video grammar stays `style: tutorial`. This folder
is the **thumbnail + series bible lock** only.

Canonical naskah (Versi 3) lives in the episode:
`edit/naskah-seri-5-video.md`. Agents must treat that file as the spine —
do not revert to the old pedagogy map (cara latihan / intent dulu /
pelatih / lengkapi semester).

| File | Role |
|------|------|
| `thumbnail.md` | Hard rules + YAML recipe (layout, colors, copy stack, export 1280×720) |

```yaml
style: tutorial
series: freshgrad-ai-dev
asr:
  language: id
```

Agents must not redesign the thumbnail. A-roll MG uses the `glass` preset
(see Production below) — thumbnail treatment is separate and unaffected.

## Positioning

- **Audience:** mahasiswa IT / Informatika / SI semester 3–8, plus fresh
  graduate.
- **Promise:** jawab keresahan soal kuliah vs industri vs AI **tanpa jualan
  takut** dan tanpa “kuliah percuma”. Kampus bikin sanggup; siap itu kerja
  di samping kuliah.
- **Persona:** senior engineer 10+ tahun. Humble, tidak menghakimi.
- **Voice (locked):** **saya / kalian** + sapaan **Teman-teman** (3–5× per
  video, jangan lebih). Bahasa lisan (`gak`, `banget`, `ngerjain`), bukan
  skripsi. Akui “saya juga sempat mikir gitu” / “saya juga pakai AI”.
  Hormati dosen: gap = siklus kurikulum vs industri, bukan males.
  Jangan roast, jangan kata *primitive* / *joki* / *hijack* / *otak kosong*
  / *kuliah percuma*.
- **Length:** **15–20 menit** (WPU niche is 18–24 min). Old 7–10 min target
  is wrong.
- **Language:** Indonesia. English that is natural on camera stays English
  (job market, deploy, review, refactor, portfolio, red flag).

## Research lock

Copy **angles / hook shape**, not wording. Do not paste source YouTube
transcripts into the teleprompter.

**Hook pattern (ID high-view):** angka mengejutkan → akui keresahan →
balik arah / jawaban **bersyarat**. Judul = pertanyaan + bantahan halus.
Sudut **kuliah/jurusan** outperforms “coding only”.

ID references that changed the plan (views as of 2026-08):

| Source | Views | Angle we copy |
|--------|------:|---------------|
| WPU — Kenapa SEKARANG waktu terbaik belajar coding | 87k | Angka → akui “ngapain belajar” → balik arah |
| WPU — Roadmap Developer 2026 | 182k | Keresahan bersama → “saya juga sempat mikir” → jawaban bersyarat |
| VoidFnc — Junior programmer bakal punah | 23k | Tuduhan halus → langsung dimaafkan → baru peringatan |
| Dea Afrizal — Belajar coding di saat AI | 117k | Engagement bait di menit pertama + “saya juga pakai” |

EN clips are **optional evidence**, not the spine. Default on-camera treatment
is an **MG quote card** (channel + short paraphrase + source on screen).
Do **not** author picture-takeover `cover.cutaways[]` on `style: tutorial`.
If the host later wants a 5–15s muted third-party clip, that is a confirmed
exception (fair use / Content ID risk; commentary on top; never replace cam
audio). Map:

| Part | Optional EN evidence |
|------|----------------------|
| 1 | Fireship ~3:20–3:46 (nobody knows the future) |
| 2 | Fireship code-as-tool + Sajjaad *context engineering* |
| 3 | PrimeTime / Matt Garman AWS + Sajjaad PHK-narrative open |
| 4 | Tina Huang security blind spot (~5:20–5:50) |
| 5 | Tina Huang vibe vs agentic (~1:20–1:50) |

**Numbers — verify on primary sources before air, show source on screen:**

- BPS Aug 2025: youth (15–24) unemployment **16.9%**
- 22–25 in AI-exposed jobs: employment **−3.8%/yr** (circulating 2026 study)
- **75%** firms: fresh grads strong on theory, weak on tools / industry std
- Junior hiring drop circulating up to **−73%** (do not treat as gospel)
- LPEM UI: informatika **mismatch** (specialist demand vs generalist campus)
- Digital sector Indonesia ~**35% YoY**
- WPU on-cam: **245k** IT layoffs, **>30%** attributed to AI

Until verified, say “angka yang beredar / yang disebut di video X / BPS
bilang…” — do not invent precision.

## Episode map (Versi 3)

| Part | Title | Thumb | Dur |
|------|-------|-------|-----|
| 1 | Kuliah IT 4 Tahun, Masih Cukup Gak Sih di 2026? | MASIH CUKUP? | 15–18 |
| 2 | Kalau Ngoding Sekarang Gampang, Kita Dibayar Buat Apa? | DIBAYAR BUAT APA? | 15–18 |
| 3 | Kenapa Lowongan Junior Makin Sedikit? (Ini Datanya) | JUNIOR -73% | 15–18 |
| 4 | 5 Hal yang Paling Dicari HRD & Tech Lead, Tapi Gak Diajarin di Kampus | 5 HAL INI | 18–20 |
| 5 | Kalau Saya Balik Jadi Mahasiswa IT di 2026, Ini yang Saya Lakuin | ROADMAP 2026 | 18–20 |

Spine per part (do not reorder back to pedagogy-only):

1. Hook 245k / BPS → bukan “kuliah percuma” → gap kurikulum vs industri
   (bukan dosen males) → 3 hal kampus yang diremehin → 4 hal kampus
   struktural gak bisa kasih → **cukup buat sanggup, gak cukup buat siap**
   → tiket stadion + latihan “kalau dipakai 1000 orang, mana yang jebol”.
2. ChatGPT-first dimaafkan → nilai pindah (kalkulator / kamera) → 4 tempat
   (tahu apa yang dibangun, nilai jawaban AI, tanggung jawab, sistem
   berantakan / context engineering) → tebak dulu 60 detik.
3. “Bukan karena kalian jelek” + data → jalur masuk nyempit → Garman talent
   pipeline → pintu dipindah (spesialis, domain, bukti, non-tech).
4. Njelasin, baca kode orang, standar industri (+ security blind spot),
   nanya sebelum ngerjain, paham uang.
5. Bukan resep; 3 prinsip; th 1–2 fondasi + AI **tutor bukan tukang**;
   th 3 sumbu teknis+domain + 5 user; th 4 magang = senior yang review;
   4 kesalahan pribadi; pohon + “saya juga masih belajar”.

Do **not** open on “kampus primitive / 90 hari roadmap / kuliah percuma”.
Do **not** dunk on lecturers. Replace `[NAMA]` only when the host supplies it.

## Production

**Picture lock:** essay talking-head. Keep `style: tutorial` (`camera_play`,
no karaoke). Do not switch the series to `style: evidence` — that pack is
for estimator screenshots.

**MG look (2026-08+):** `glass` preset — frosted overlay-on-continuous-A-roll,
teal/amber tokens (see `styles/tutorial/style.md`). Replaces the old Bold +
`#7dd3fc` left-rail look for this series starting with Part 1.

- Full cam on Parts 1–2. No screen demo. No `cover.cutaways[]`.
- Signature MG: `stat` (number + source, glass scrim). Overlay-suggest
  will not emit these — author them from `edit/evidence.md`.
- `divider` for chapters, `illustration` for lists/comparisons. `quote`
  only on thesis lines and quote cards.
- Quotes from EN/ID creators = **kartu kutipan** (`quote` kind, `kicker` =
  channel name). Default no third-party video clips (Content ID).
- Optional later: 8–12s `evidence_with_cam` of *real* BPS / Stanford /
  LPEM page screenshots. Never AI dashboards.
- Thumb accent `#facc15` is YouTube-only. In-video MG stays `glass` teal/amber.
- Sparser than Odoo demos: after overlay-suggest, delete most lexicon
  gap-fill. Audio from cam; shutter/click only; no hook music.

Episode runbook: `edit/production.md`. Number provenance:
`edit/evidence.md`.

Naskah craft (from §4): no “halo semuanya” in the first 40s; disclaimer
in ~90s; engagement bait in minute one; announce chapters; one sticky
closing analogy; sign-off **“Pelan-pelan aja, yang penting jalan terus.”**
No negative named campuses, lecturers, or clients. Swap placeholder
anecdotes (e.g. N+1 query) for the host’s real stories.

## Hard rules for agents

1. Confirm radio-edit before `edit/edl.json`.
2. No pasted YouTube transcripts. Attribute BPS / LPEM / WPU if you quote
   a number.
3. Tutorial overlays only. Audio from cam.
4. Keep the humble **saya/kalian** voice in teleprompter, titles, thumbs,
   and YouTube copy.
5. Prefer MG quote cards over third-party video clips.
