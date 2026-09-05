# Naskah template — Claude Skill Lab

Fill-in-the-blank teleprompter. Copy to the episode as `edit/script.md`,
replace every `<...>`, keep the timing spine. Target **7:00**, hard cap
**~10:00**. Voice: **saya / kalian**, bahasa lisan, santai. Style pack:
`mockup` — talking head only, the screen is drawn (`ae mockup-suggest`).

Placeholders:
`<SKILL>` name · `<SUMBER>` "bawaan Claude" / GitHub URL ·
`<TUGAS>` the one real task · `<FILE>` the input file ·
`<VERDICT>` worth it / skip / worth it kalau sering `<X>`

---

## [0:00–0:30] Hook

Skill Claude minggu ini: **`<SKILL>`**.

<Satu kalimat kenapa ini menarik / bikin saya penasaran.>

Hari ini saya coba buat satu hal beneran: **`<TUGAS>`**. Kita lihat
hasilnya, dan saya kasih verdict jujur di akhir — worth it atau nggak.

---

## [0:30–1:30] Skill ini apa & dari mana

`<SKILL>` itu intinya **`<satu kalimat: skill ini ngasih Claude kemampuan apa>`**.

Ini `<SUMBER>`. <Kalau dari GitHub: tampilkan repo-nya, buka SKILL.md-nya
sebentar — "sebelum percaya, saya baca dulu isinya".>

Cara ngaktifin: `<satu baris — "tinggal diaktifin di setting" / "drop
foldernya">`. Kalau kalian belum pernah nyalain skill di Claude Desktop,
ada video setup yang saya pin — tonton itu dulu, di sini saya nggak
ulang.

Satu hal yang perlu lurus dari awal: skill itu **bukan** Claude jadi
"belajar" atau "inget kamu". **Kalian yang nulis instruksinya, Claude yang
milih** kapan dipakai. Itu aja.

---

Semua tampilan layar digambar ulang (mockup + PIP), bukan rekaman. Editor
**tidak baca naskah ini** — scene mockup ditaruh dari transkrip: dari apa
yang benar-benar kamu **ucapkan**. Jadi sebut pemicunya dengan lantang di
tempat yang tepat:

- **RepoView** (repo / SKILL.md): ".. buka **repo**-nya di **github** ..",
  ".. lihat **sumbernya** .."
- **SkillsPanel** (Settings → Skills): ".. masuk ke **settings**, bagian
  **skill** ..", ".. **aktifin skill**-nya .."
- **DiffPanel** (sebelum/sesudah): ".. **sebelumnya** begini .. **sesudah**
  dirapikan .."
- **AppWindow** (hasil kebuka di app): ".. **kebuka di** PowerPoint ..",
  ".. jadi file **pptx** / **xlsx** / **docx** .."
- **ClaudeChat** (prompt): awali dengan ".. **aku bilang** .." / ".. **aku
  ketik** .." / ".. **minta claude** .." lalu **baca prompt-nya keras** —
  kata-kata itu jadi user turn.

Kalau pemicunya cuma satu kata umum (mis. cuma "repo"), scene tetap dibuat
tapi ditandai low-confidence buat dicek pas review.

## [1:30–5:00] Demo

Oke, contohnya: **`<TUGAS>`**.

Misalnya kalian punya `<FILE / input — deskripsi singkat>`.

**Aku bilang** ke Claude — (baca keras, ini jadi user turn):

> "`<kutipan prompt>`"

<Apa yang skill ini lakukan / bagian yang berubah — sebut "**sebelumnya** ..
**sesudah** .." kalau mau DiffPanel; sebut "**kebuka di** <app>" kalau
hasilnya kebuka di pptx/xlsx/docx.>

> Isi `before`/`after` DiffPanel dan `assistant reply` ClaudeChat kamu
> lengkapi nanti di `edit/mockup.json` (highlight kata yang berubah
> dihitung otomatis dari before/after).

<Kalau ada batas yang kelihatan di sini, sebut aja — nggak wajib
"momen gagal", ini explainer.>

---

## [5:00–6:30] Jujurnya

Yang bagus:
- `<kekuatan 1>`
- `<kekuatan 2>`

Yang kurang / batasnya:
- `<kelemahan 1 — yang tadi kejadian>`
- `<caveat plan / setup>`
- `<hal yang orang kira bisa, ternyata nggak>`

Ini cocok buat kalian **kalau** `<X — kondisi konkret>`. Kalau nggak
pernah `<X>`, ya nggak usah dipasang.

---

## [6:30–7:00] Verdict + next

Verdict saya: **`<VERDICT>`**.

<Satu kalimat penutup — reframe kecil, bukan hype.>

Minggu depan kita bongkar `<skill berikutnya>`.

Pelan-pelan aja. Yang penting jalan terus.
