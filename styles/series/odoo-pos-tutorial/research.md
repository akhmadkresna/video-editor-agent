# Odoo POS Tutorial — research reference

**Living doc.** Come back here before scripting each episode. Update when
Odoo ships a point release or pricing changes.

Last updated: **2026-09-11** (feasibility pass added) · Sources at bottom.

## Recording feasibility (what's actually shootable solo at a desk)

Checked against what the user actually owns/can get before scaffolding:

- **No POS hardware owned** (no receipt printer, barcode scanner, cash
  drawer, IoT Box). Eps 1/2/3/4/6 don't need any of it — barcode input
  can be typed by hand (a scanner is just a keyboard-wedge device, same
  result) or scanned with a phone camera via the Odoo mobile app.
  **Ep 5 is the one episode that assumes hardware the user doesn't
  have** — see its revised scope below.
- **Xendit sandbox is genuinely gettable**: sign up with email, verify,
  answer basic business questions → test/sandbox API keys immediately.
  No legal/business documents required for sandbox — those are only
  required to go **live**. [docs.xendit.co/getting-started/create-account]
- **But Xendit ≠ POS's QR payment method** — this was the key correction
  after checking the actual Odoo docs (see below). Don't conflate them
  on screen.

### Xendit vs. POS "QR code payment" — two different things

- **Xendit as an Odoo Payment Provider** (Finance → Payment Providers) is
  officially documented for Odoo 17/18/19. It's for **online payment
  links** (invoices, eCommerce/Website checkout) — confirmed
  automatically via webhook once Secret Key + Webhook Token are set.
  [odoo.com/documentation/19.0/applications/finance/payment_providers/xendit.html]
- **POS's built-in "QR code payment"** (Point of Sale → Configuration →
  Payment Methods → Integration: *Bank App (QR Code)*) is a **generic**
  EMV Merchant-Presented QR / SEPA QR — not a Xendit API call. The
  cashier generates the QR, the customer scans with *any* banking/
  e-wallet app, and the cashier **manually** validates the payment. No
  webhook, no automatic confirmation, no API keys needed at all.
  [odoo.com/documentation/19.0/applications/sales/point_of_sale/payment_methods/qr_code_payment.html]
- **Practical effect for ep.4**: the POS QR flow is fully desk-recordable
  and genuinely live (generate QR → scan with your own phone → mark
  paid) — no sandbox account needed for that part. If a fully automated
  QRIS-confirmed flow is wanted later, that's a *separate* Finance-level
  Xendit integration and deserves its own episode, not a rushed mention
  inside ep.4.

---

## Positioning driver: the earlier "sistem kasir" video already proved demand

A prior video touching Odoo as a kasir/POS system got strong views. This
series doubles down: **Odoo SaaS (Odoo Online), Point of Sale app,
practical setup + configuration + real use cases.** Not a free-plan
explainer — a straight tutorial series for people who want a working
till, fast.

## Why Odoo Online (SaaS), not self-hosted, for this series

- No server, no Docker, no updates to manage — sign up, pick apps, done.
  This matches the "light and easy enough to setup" brief.
- Pricing (2026, varies by country/region — reconfirm on recording day):
  **Standard** ≈ $24.90–31.10/user/month (introductory year, renews
  ~25% higher), all apps included, no Studio/multi-company/API.
  **Custom** ≈ $49–61/user/month adds Studio, multi-company, external
  API, Odoo.sh/on-prem hosting. [pricing roundups below]
- For a single-outlet UMKM/toko demo, Standard is enough — keep the
  pricing beat short and factual, don't dwell on tiers.
- Hardware note (receipt printer, barcode scanner, cash drawer, IoT Box)
  is a **real setup step**, not a free-plan gotcha — cover it in the
  dedicated hardware/offline episode, not the intro (keep ep.1 to
  "browser only, works on a laptop/tablet as-is").

## Odoo 19 POS feature map (what to demo, and in what order)

| Area | Highlights | Episode fit |
|---|---|---|
| Core setup | Install POS app, one config = one till/register, tax + payment methods, opening/closing a session | Ep 1 (fast setup) |
| New in 19 | Native dark mode, Two-Click Preset Switching (dine-in/takeout/kiosk), combo products, POS store timing (open/close hours), prep-time report, customer due-account settlement | Sprinkle across eps 1–3 as "yang baru di v19" beats |
| Shop/retail | Barcode scanning + discount-tag barcodes, categories, quotations/sales-order pickup, ship-later, multi-store sync (shared product data, per-store stock/pricelist/staff) | Ep 2 (retail config) |
| Restaurant/F&B | Floor/table plan, booking (Appointments integration), course-based kitchen tickets, kitchen display screen, bill split, tipping, eat-in vs take-out tax | Ep 3 (restaurant config) — high search demand (cafe/resto is a huge Indonesian UMKM segment) |
| Payments & closing | Cash, POS's generic QR code payment (manual scan-and-validate, no API needed — see feasibility note above), customer-account billing, session close → automatic accounting GL postings. Card terminals (Adyen/Stripe/Razorpay) and the separate Xendit *online payment provider* are name-only mentions, not live demos. | Ep 4 — fully desk-recordable now; #1 pain point in Indonesian forums is still "kok saldo kasir gak cocok" (session close beat) |
| Offline & hardware reality | POS keeps working with no internet (toggle Wi-Fi off — desk-recordable), syncs on reconnect; card payment flows and cross-store lookups need a live connection. Receipt printer/scanner/cash drawer/IoT Box setup is **not desk-recordable — user owns none of this hardware.** | Ep 5 — scope to what's actually shootable (see revised slate below); do not stage or fake a hardware demo |
| Reporting & use case | Session reports, best-seller/category reports, discounts/loyalty points, mapping a real toko/warung workflow end to end | Ep 6 (case study) |

## What Indonesian searchers actually ask (demand signals)

- "Odoo POS bisa offline gak" — yes, core sale flow works offline and
  syncs on reconnect; card/QR payment confirmation and cross-store stock
  lookups need connectivity. Say this precisely, don't oversell "100%
  offline."
- "Kasir Odoo cocok buat UMKM/toko/cafe gak" — yes, Odoo POS is used by
  Indonesian UMKM (clothing stores, cafes, retail) per case studies below;
  frame the series around a believable toko/warung/cafe persona.
- "Setup Odoo POS ribet gak" — the actual install+first-sale path is
  short (install app → one config → add products/tax/payment method →
  open session). This is the ep.1 hook: show the full path in one sitting.
- "Kasir Odoo nyambung ke akuntansi gak" — yes, session close posts
  automatically to Accounting/Inventory; this is a strong differentiator
  vs standalone kasir apps and worth its own beat in ep.4.
- "QRIS di Odoo gimana" — POS has a **generic, native** QR-payment
  method (manual: cashier generates QR, customer scans with any
  banking/e-wallet app, cashier validates) — this needs zero setup
  beyond picking "Bank App (QR Code)" as the integration, and is
  genuinely live-demoable. A **fully automated**, webhook-confirmed QRIS
  flow is a separate Xendit *Payment Provider* integration (Finance app,
  online payments) — say both exist, be precise about which one ep.4
  actually shows.
- Multi-outlet: product data is centralized, but stock/pricelist/staff
  are per-store — good "grows with your business" narrative for ep.6 or
  a closing beat in ep.2.

## Episode slate (draft — confirm before scaffolding)

1. **Setup kasir pertama dari nol** — sign up Odoo Online → install POS →
   satu config = satu kasir → produk + pajak + metode bayar → buka sesi →
   transaksi pertama. Hook: "kasir toko jadi dari nol, dalam satu duduk."
2. **Config retail** — kategori produk, barcode + barcode diskon,
   quotation/sales-order pickup, ship-later, multi-outlet dasar (data
   produk terpusat, stok/harga/staff per toko).
3. **Config resto/cafe** — floor plan meja, booking, kitchen display,
   split bill, tip, pajak dine-in vs take-away, Two-Click Preset
   Switching.
4. **Bayar & tutup kasir tanpa pusing** — tunai, QR code payment bawaan
   (live: generate QR → scan pakai HP sendiri → validasi manual, tanpa
   akun apapun), lalu tutup sesi → nyambung otomatis ke akuntansi/
   inventory. Sebut singkat bahwa kartu (Adyen/Stripe/Razorpay) dan QRIS
   otomatis-terkonfirmasi (Xendit sebagai Payment Provider di app
   Finance, bukan bagian POS) itu jalur terpisah — tidak didemokan live.
   Fully desk-recordable end to end.
5. **Offline & apa yang butuh internet** — toggle Wi-Fi off/on
   (desk-recordable) untuk tunjukkan alur jual tetap jalan offline dan
   sync pas online lagi; jelaskan bagian mana yang butuh koneksi hidup
   (validasi kartu, cross-store stock lookup). **Tidak** mendemokan
   printer struk/scanner/laci kasir/IoT Box fisik — user belum punya
   hardware itu. Tutup dengan penjelasan konseptual singkat (pakai
   foto/dokumentasi resmi) soal apa yang dibutuhkan kalau mau pasang
   hardware asli nanti.
6. **Studi kasus UMKM** — mapping alur toko/warung/cafe nyata end-to-end:
   diskon, loyalty, laporan penjualan terlaris.

Style: `tutorial` (screen recording + talking head, per
`styles/tutorial/style.md`). Keep each episode light to shoot — one
screen-recording pass per episode, no staged multi-take demos.

---

## Sources

- https://www.odoo.com/documentation/19.0/applications/sales/point_of_sale.html
- https://www.odoo.com/documentation/19.0/applications/sales/point_of_sale/shop.html
- https://www.odoo.com/documentation/19.0/applications/sales/point_of_sale/restaurant.html
- https://www.serpentcs.com/blog/odoo-pos-390/odoo-19-pos-features-what-s-new-in-point-of-sale-for-retail-restaurants-661
- https://www.odoo.com/pricing
- https://oec.sh/odoo-pricing (pricing roundup, cross-check on recording day — Odoo pricing shifts and is region-dependent)
- https://www.odoo.com/blog/business-hacks-1/cara-set-up-qris-di-odoo-1626
- https://www.proweb.co.id/articles/odoo-umkm/jurnal-pos.html
- https://journal.nurulfikri.ac.id/index.php/DBESTI/article/view/1942 (UMKM toko case study)
- https://www.kerningcode.com/blog/odoo-25/odoo-odoo-18-offline-mode-point-of-sale-and-working-offline-321
- https://www.techvaria.com/blog/odoo-pos-multi-store-retail-restaurant-guide.html
- https://www.odoo.com/documentation/19.0/applications/sales/point_of_sale/payment_methods/qr_code_payment.html (POS generic QR — manual, no API)
- https://www.odoo.com/documentation/19.0/applications/finance/payment_providers/xendit.html (Xendit as online Payment Provider — separate from POS QR)
- https://docs.xendit.co/getting-started/create-account (sandbox needs email + basic business Q&A only; documents required for live mode, not sandbox)

All pricing/partner-integration claims must be re-verified against the
live Odoo Online signup flow and current Indonesian payment-partner docs
on recording day — these move often.
