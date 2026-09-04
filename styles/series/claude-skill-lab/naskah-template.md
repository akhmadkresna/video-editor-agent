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

Semua tampilan layar digambar ulang (mockup + PIP), bukan rekaman. Tandai
tiap scene dengan **`[MOCKUP: <Komponen> — catatan]`** — cuma beat yang
punya cue ini yang jadi scene; sisanya full cam. Komponen:
`ClaudeChat` · `DiffPanel` · `AppWindow` · `SkillsPanel` · `RepoView`.

## [1:30–5:00] Demo

Oke, contohnya: **`<TUGAS>`**.

Misalnya kalian punya `<FILE / input — deskripsi singkat>`.

Ini yang saya ketik ke Claude:

> "`<kutipan prompt — jadi user turn>`"

`[MOCKUP: ClaudeChat — user turn = kutipan + attachment; assistant turn = skill badge + hasil. Cursor: klik kirim.]`

<Apa yang skill ini lakukan / bagian yang berubah.>

`[MOCKUP: DiffPanel — before = <input>, after = <hasil>]`
`[MOCKUP: AppWindow — app <pptx|xlsx|docx>, kalau hasilnya "kebuka di app"]`

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
