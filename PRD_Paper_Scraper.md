# Product Requirements Document (PRD)
# Paper Scraper — Aplikasi Web Scraping Paper Akademik

**Versi Dokumen:** 1.0
**Tanggal:** 7 Juli 2026
**Status:** Draft untuk Development

---

## 1. Goals

### 1.1 Latar Belakang
Peneliti, mahasiswa, dan akademisi sering menghabiskan banyak waktu untuk mencari, mengumpulkan, dan merapikan referensi paper/jurnal dari berbagai sumber secara manual. Proses ini repetitif: cari keyword di satu database, salin judul/abstrak, cek duplikat, unduh PDF satu per satu, lalu rekap ke Excel untuk keperluan studi literatur.

### 1.2 Tujuan Produk
Membangun aplikasi web sederhana yang dapat:
1. Melakukan scraping metadata paper secara otomatis dari **Semantic Scholar API** dan **arXiv API** berdasarkan **keyword** dan **jumlah paper** yang diinput pengguna.
2. Menyimpan hasil scraping ke dalam **database** tanpa duplikasi judul.
3. Menyediakan riwayat scraping (per keyword dan keseluruhan).
4. Memungkinkan pengguna **mengekspor** hasil ke **CSV/Excel** dan **mengunduh PDF** paper secara massal.
5. Dapat digunakan **tanpa proses login/registrasi** sama sekali.

### 1.3 Goals Terukur (Success Metrics)
| Goal | Indikator Keberhasilan |
|---|---|
| Scraping akurat | Data yang tersimpan memiliki 5 field wajib (judul, abstrak, author, tahun, link) terisi 100% |
| Bebas duplikat | 0% paper dengan judul identik/duplikat tersimpan dobel di database |
| Kepatuhan terhadap API pihak ketiga | Tidak ada request yang terkena rate-limit block (429) karena jeda 5 detik/paper diterapkan konsisten |
| Kemudahan pakai | Pengguna baru dapat melakukan scraping pertama dalam < 1 menit tanpa dokumentasi tambahan |
| Kelengkapan ekspor | File CSV, Excel, dan ZIP PDF berhasil di-generate tanpa error untuk minimal 50 paper sekali proses |

### 1.4 Non-Goals
- Tidak membangun sistem multi-user dengan akun/login pada versi 1.0.
- Tidak melakukan analisis sitasi, ranking jurnal, atau rekomendasi paper.
- Tidak menyediakan pencarian full-text di dalam isi PDF (hanya metadata).

---

## 2. Fitur

### 2.1 Fitur Utama (Must Have)

#### F1. Input Pencarian Scraping
- Input **keyword** (bebas teks, contoh: "machine learning for healthcare").
- Input **jumlah paper** yang ingin di-scrape (angka, contoh: 20).
- Pilihan sumber data: **Semantic Scholar**, **arXiv**, atau **keduanya** (default: keduanya).
- Tombol **"Mulai Scraping"**.

#### F2. Proses Scraping Otomatis
- Sistem memanggil API Semantic Scholar dan/atau arXiv berdasarkan keyword.
- Setiap **1 paper diproses = jeda 5 detik** sebelum memproses paper berikutnya (berlaku untuk pengambilan metadata per-paper dan/atau proses pengunduhan PDF, guna menghindari pemblokiran/rate-limit dari API pihak ketiga).
- Sistem otomatis berhenti mengambil data baru ketika jumlah paper yang diminta sudah terpenuhi, atau ketika sumber data sudah tidak memiliki hasil lagi.
- Menampilkan **progress bar/status real-time** (contoh: "12/20 paper diproses...").

#### F3. Validasi Data Wajib
Sebuah hasil scraping **hanya disimpan** apabila 5 field berikut tersedia:
1. Judul (title)
2. Abstrak (abstract)
3. Author (penulis)
4. Tahun tulis/publish (year)
5. Link jurnal/paper (url)

Jika salah satu field wajib kosong dari respons API, paper tersebut **dilewati (skip)** dan tidak dihitung sebagai hasil valid.

#### F4. Filter Tahun Publikasi
- Paper dengan tahun publikasi **lebih lama dari 2020** (yaitu ≤ 2019) **tidak diikutsertakan** dalam hasil scraping. Batas paling lama yang diterima adalah tahun **2020**.

#### F5. Deteksi & Skip Duplikat
- Sebelum menyimpan paper baru, sistem mencocokkan **judul** (dinormalisasi: huruf kecil, tanpa tanda baca, tanpa spasi berlebih) terhadap paper yang sudah ada di database.
- Jika keyword yang sama di-scrape ulang dan menemukan judul yang sudah pernah tersimpan sebelumnya, paper tersebut **dilewati** (tidak membuat entri baru, tidak mengunduh ulang PDF), namun tetap dicatat sebagai "duplikat terlewati" pada ringkasan sesi.

#### F6. Penyimpanan ke Database
- Semua paper valid & non-duplikat disimpan ke **SQLite**.
- Setiap sesi scraping (1x klik "Mulai Scraping") dicatat sebagai satu **sesi riwayat**, terhubung ke keyword yang digunakan.

#### F7. Riwayat Scraping per Keyword
- Halaman/section yang menampilkan daftar **keyword** yang pernah di-scrape, beserta:
  - Tanggal & waktu scraping
  - Jumlah paper diminta vs. jumlah paper berhasil didapat
  - Jumlah duplikat yang di-skip
- Klik salah satu keyword → menampilkan seluruh paper hasil scraping dari keyword tersebut (dengan detail lengkap: judul, abstrak, author, tahun, link).

#### F8. Riwayat Seluruh Hasil Scraping
- Tabel gabungan seluruh paper dari semua sesi & semua keyword yang pernah di-scrape, dengan kolom yang sama: judul, abstrak, author, tahun, link, sumber (Semantic Scholar/arXiv), status PDF (tersedia/tidak).

#### F9. Export ke CSV
- Tombol "Export CSV" mengunduh file `.csv` berisi seluruh/kolom hasil scraping (sesuai konteks: hasil scraping terbaru, per-keyword, atau seluruh riwayat).

#### F10. Export ke Excel
- Tombol "Export Excel" mengunduh file `.xlsx` dengan struktur kolom yang sama seperti CSV, lebih rapi (header bold, lebar kolom menyesuaikan).

#### F11. Download Semua PDF
- Tombol "Download Semua PDF" akan:
  - Mengunduh file PDF dari setiap paper yang memiliki `pdf_url` valid (open access), dengan jeda 5 detik antar unduhan.
  - Mem-package seluruh PDF yang berhasil diunduh ke dalam **1 file ZIP** untuk diunduh pengguna.
  - Paper yang tidak memiliki PDF open-access akan dilewati dan dicatat dalam ringkasan (contoh: "15 dari 20 PDF berhasil diunduh").

### 2.2 Fitur Pendukung (Should Have)
- Notifikasi/alert sederhana jika keyword kosong atau jumlah paper tidak valid (≤0 atau melebihi batas maksimal yang ditentukan, misal 100 per sesi).
- Indikator sumber data pada setiap baris hasil (badge "Semantic Scholar" / "arXiv").
- Tombol "Lihat Abstrak Lengkap" (expand/collapse) karena abstrak biasanya panjang.

### 2.3 Di Luar Cakupan Fitur (Won't Have — v1)
- Login/autentikasi pengguna.
- Multi-bahasa selain Inggris (mengikuti bahasa asli metadata dari Semantic Scholar/arXiv).
- Sumber data selain Semantic Scholar & arXiv (IEEE, Scopus, PubMed, dsb).
- Edit manual data paper setelah tersimpan di database.

---

## 3. User Flow

### 3.1 Alur Utama: Melakukan Scraping Baru

```
[Pengguna membuka aplikasi web]
        |
        v
[Halaman "Paper Scraper – Pencarian" tampil]
(tanpa perlu login)
        |
        v
[Pengguna input keyword] --> [Pengguna input jumlah paper] --> [Pilih sumber: Semantic Scholar / arXiv / Keduanya]
        |
        v
[Klik "Mulai Scraping"]
        |
        v
[Sistem validasi input]
   - Keyword kosong? -> tampilkan pesan error
   - Jumlah paper tidak valid? -> tampilkan pesan error
        |
        v
[Sistem membuat sesi scraping baru & mulai proses di background]
        |
        v
[Sistem memanggil API sumber terpilih secara berurutan]
   Untuk setiap paper kandidat:
     1. Cek field wajib lengkap? Tidak -> skip
     2. Cek tahun >= 2020? Tidak -> skip
     3. Cek judul sudah ada di DB (duplikat)? Ya -> skip (tandai duplikat)
     4. Simpan ke database
     5. Tunggu 5 detik sebelum lanjut ke paper berikutnya
        |
        v
[Frontend polling status progress secara berkala]
        |
        v
[Jumlah paper valid == jumlah diminta ATAU sumber data habis]
        |
        v
[Tampilkan hasil scraping dalam tabel]
(judul, abstrak, author, tahun, link, sumber)
        |
        v
[Pengguna dapat: Export CSV | Export Excel | Download Semua PDF]
```

### 3.2 Alur Sekunder: Melihat Riwayat
```
[Pengguna berada di halaman utama]
        |
        v
[Scroll/klik ke bagian "Riwayat"]
        |
        v
[Pilih tab: "Riwayat per Keyword" atau "Riwayat Seluruh Scraping"]
        |
        v
(Per Keyword)                         (Seluruh Scraping)
   |                                        |
   v                                        v
[Daftar keyword + tanggal +          [Tabel seluruh paper
 jumlah hasil]                        dari semua sesi]
   |                                        |
   v                                        v
[Klik salah satu keyword]           [Export CSV/Excel/PDF
   |                                  langsung dari sini]
   v
[Tabel detail paper untuk
 keyword tsb + tombol export]
```

### 3.3 Alur Edge Case
- **Keyword sama di-scrape ulang** → paper baru yang unik ditambahkan, paper lama yang cocok judul dilewati, sesi baru tetap tercatat di riwayat dengan ringkasan "X paper baru, Y duplikat dilewati".
- **API sumber down/error** → sistem melanjutkan ke sumber lain (jika keduanya dipilih) dan menampilkan pesan peringatan bahwa satu sumber gagal diakses, tanpa menghentikan keseluruhan proses.
- **Jumlah paper diminta lebih besar dari hasil yang tersedia di sumber** → proses berhenti otomatis begitu sumber data habis, dengan notifikasi "Hanya ditemukan N dari M paper yang diminta".

---

## 4. UI/UX

### 4.1 Prinsip Desain
Sederhana, satu halaman utama (single-page feel), minim klik, fokus pada fungsi — sesuai kebutuhan pengguna yang ingin cepat scraping tanpa distraksi visual berlebihan.

### 4.2 Struktur Halaman: "Paper Scraper – Pencarian"

```
+-----------------------------------------------------------+
|  📄 Paper Scraper                                          |
+-----------------------------------------------------------+
|  [ Pencarian ]   [ Riwayat per Keyword ]  [ Riwayat Semua ]|
+-----------------------------------------------------------+
|                                                             |
|   Keyword:      [_____________________________]            |
|   Jumlah Paper: [______]                                    |
|   Sumber:       ( ) Semantic Scholar  ( ) arXiv  (•) Keduanya |
|                                                             |
|                [  Mulai Scraping  ]                         |
|                                                             |
|   ⏳ Progress: [██████░░░░] 12/20 paper diproses...          |
|                                                             |
+-----------------------------------------------------------+
|  Hasil Scraping (18 valid, 2 duplikat dilewati)             |
|  [Export CSV] [Export Excel] [Download Semua PDF]          |
+-----------------------------------------------------------+
| No | Judul | Author | Tahun | Sumber | Abstrak | Link | PDF |
|----|-------|--------|-------|--------|---------|------|-----|
| 1  | ...   | ...    | 2023  | S2     | [lihat] | 🔗   | ✅  |
| 2  | ...   | ...    | 2021  | arXiv  | [lihat] | 🔗   | ❌  |
+-----------------------------------------------------------+
```

### 4.3 Komponen UI Detail
- **Form Pencarian**: input text (keyword), input number (jumlah, min=1, max=100), radio/checkbox sumber, tombol submit dengan state loading (disabled + spinner saat proses berjalan).
- **Progress Indicator**: progress bar dinamis + teks status, di-refresh via polling (misal setiap 2 detik) ke endpoint status backend.
- **Tabel Hasil**: kolom judul (truncate + tooltip), abstrak (tombol expand/collapse karena panjang), author (gabungan nama dipisah koma), tahun, badge sumber berwarna, link eksternal (ikon, buka tab baru), ikon status ketersediaan PDF.
- **Tab Riwayat per Keyword**: daftar card/list per keyword (keyword, tanggal terakhir, total paper, tombol "Lihat Detail").
- **Tab Riwayat Semua**: tabel besar seluruh paper, dengan search/filter sederhana di sisi klien (opsional, filter by tahun/sumber).
- **Tombol Aksi**: konsisten diletakkan di atas tabel, disabled apabila tidak ada data untuk diekspor.

### 4.4 Responsif & Aksesibilitas
- Layout menggunakan CSS flexbox/grid sederhana agar tetap dapat digunakan di layar laptop/tablet dasar (mobile-first tidak menjadi prioritas utama, tapi tetap tidak rusak di layar kecil — tabel dapat di-scroll horizontal).
- Warna kontras cukup untuk teks & tombol, ukuran font minimal 14px untuk keterbacaan.

---

## 5. Database Overview

### 5.1 Pilihan Teknologi
SQLite (file `.db` lokal), diakses melalui `sqlite3` bawaan Python atau ORM ringan seperti SQLAlchemy.

### 5.2 Skema Tabel

#### Tabel `keywords`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| keyword_text | TEXT | Keyword asli yang diinput user |
| keyword_normalized | TEXT UNIQUE | Versi lowercase/trim untuk pencocokan |
| created_at | DATETIME | Waktu keyword pertama kali digunakan |

#### Tabel `scraping_sessions` (Riwayat Scraping)
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| keyword_id | INTEGER FK → keywords.id | |
| requested_amount | INTEGER | Jumlah paper yang diminta user |
| source_option | TEXT | 'semantic_scholar' / 'arxiv' / 'both' |
| total_found | INTEGER | Total kandidat ditemukan dari API |
| new_papers_count | INTEGER | Jumlah paper baru berhasil disimpan |
| duplicate_skipped_count | INTEGER | Jumlah dilewati karena duplikat |
| invalid_skipped_count | INTEGER | Jumlah dilewati karena field wajib kosong / tahun < 2020 |
| status | TEXT | 'running' / 'completed' / 'failed' |
| started_at | DATETIME | |
| finished_at | DATETIME (nullable) | |

#### Tabel `papers`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| title | TEXT | Judul asli |
| title_normalized | TEXT UNIQUE | Untuk deteksi duplikat (lowercase, tanpa tanda baca) |
| abstract | TEXT | |
| authors | TEXT | Disimpan sebagai string dipisah koma, atau JSON array |
| year | INTEGER | |
| source | TEXT | 'semantic_scholar' / 'arxiv' |
| external_id | TEXT | Paper ID / arXiv ID / DOI |
| paper_url | TEXT | Link ke halaman paper |
| pdf_url | TEXT (nullable) | Link PDF open-access jika tersedia |
| pdf_local_path | TEXT (nullable) | Path file PDF yang sudah diunduh secara lokal |
| pdf_downloaded | BOOLEAN | Default FALSE |
| created_at | DATETIME | |

#### Tabel `session_papers` (Relasi Many-to-Many: sesi ↔ paper)
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| session_id | INTEGER FK → scraping_sessions.id | |
| paper_id | INTEGER FK → papers.id | |
| is_duplicate | BOOLEAN | TRUE jika paper ini sebenarnya sudah ada sebelum sesi ini |

### 5.3 Alasan Desain
- Tabel `papers` terpisah dari `session_papers` memungkinkan satu paper yang sama (jika ditemukan lagi di sesi/keyword lain) **tidak disimpan dobel**, tapi tetap bisa dilacak "paper ini muncul di sesi/keyword mana saja" — mendukung fitur Riwayat per Keyword & Riwayat Seluruh Scraping tanpa duplikasi data fisik.
- `title_normalized` diberi constraint **UNIQUE** sebagai lapisan pertama pencegahan duplikat di level database, selain pengecekan di level aplikasi sebelum insert.

---

## 6. Technical Requirement

### 6.1 Tech Stack
| Layer | Teknologi |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript (Fetch API untuk komunikasi ke backend) |
| Backend | Python 3.x, Flask |
| Database | SQLite |
| Library pendukung Python | `requests` (HTTP client ke API eksternal), `feedparser` atau `xml.etree.ElementTree` (parsing Atom XML dari arXiv), `pandas` + `openpyxl` (export Excel), `csv` bawaan Python (export CSV), `python-dotenv` (kelola API key), `SQLAlchemy` (opsional, ORM) |

### 6.2 Integrasi API Eksternal

#### 6.2.1 Semantic Scholar API
- Endpoint pencarian: `GET https://api.semanticscholar.org/graph/v1/paper/search`
- Parameter: `query` (keyword), `limit`, `offset`, `fields=title,abstract,authors,year,url,openAccessPdf,externalIds`
- API key: <cite index="1-1">API key opsional dapat diminta melalui form resmi Semantic Scholar dan dikirim via email; menyertakan API key direkomendasikan sebagai best practice.</cite> Tanpa API key, request tetap bisa dilakukan namun berbagi kuota dengan seluruh pengguna publik lainnya <cite index="9-1">di mana rate limit default untuk pengguna tanpa autentikasi saat ini adalah 5.000 request per 5 menit dalam satu pool bersama</cite>. Dengan API key, <cite index="1-1">rate limit awal yang didapat adalah 1 request per detik pada seluruh endpoint</cite>.
- Implikasi teknis: karena keterbatasan ini, aplikasi **wajib** menerapkan jeda antar-request (selaras dengan requirement 5 detik/paper dari user) agar aman baik menggunakan API key maupun tanpa API key.
- Header (jika pakai API key): `x-api-key: <API_KEY>`

#### 6.2.2 arXiv API
- Endpoint: `GET http://export.arxiv.org/api/query`
- Parameter: `search_query=all:<keyword>`, `start`, `max_results`
- Tidak memerlukan API key, response berupa **Atom XML** (bukan JSON) — perlu parsing khusus (`feedparser` direkomendasikan karena Atom-compatible).
- Field yang diambil: `title`, `summary` (→ abstrak), `author/name` (bisa lebih dari satu tag), `published` (→ ambil tahun), `id` (→ link), `link[title=pdf]` (→ pdf_url).

### 6.3 Rate Limiting & Jeda Request
- Setiap kali sistem memproses **1 paper** (baik saat pengambilan metadata satuan maupun saat pengunduhan PDF), sistem **wajib menunggu 5 detik** sebelum memproses paper berikutnya.
- Implementasi: gunakan `time.sleep(5)` di dalam loop backend Python, dijalankan di **background thread** agar tidak memblokir server Flask (lihat 6.4).
- Tambahan best practice: terapkan *exponential backoff* sederhana jika menerima response HTTP 429 (Too Many Requests) dari Semantic Scholar, sesuai anjuran resmi mereka.

### 6.4 Penanganan Proses Panjang (Async/Background Job)
Karena scraping N paper dengan jeda 5 detik/paper bisa memakan waktu lama (contoh: 50 paper ≈ 250+ detik), request HTTP biasa tidak cocok (akan timeout). Pendekatan yang direkomendasikan:
1. Endpoint `POST /api/scrape` menerima keyword & jumlah, **langsung membuat record sesi** dengan status `running`, lalu menjalankan proses scraping di **background thread** Python (`threading.Thread`), dan segera mengembalikan `session_id` ke frontend.
2. Frontend melakukan **polling** ke `GET /api/scrape/status/<session_id>` setiap 2 detik untuk mendapatkan progress (jumlah diproses/total, status).
3. Setelah status `completed`, frontend mengambil hasil lengkap via `GET /api/scrape/result/<session_id>`.

> Catatan: Untuk kebutuhan skala kecil/personal (sesuai target user tanpa login), pendekatan threading sederhana sudah cukup. Jika ke depan dibutuhkan penggunaan bersamaan oleh banyak orang sekaligus, disarankan migrasi ke task queue seperti Celery + Redis.

### 6.5 Endpoint API Backend (Flask)
| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/api/scrape` | Memulai sesi scraping baru (body: keyword, jumlah, sumber) |
| GET | `/api/scrape/status/<session_id>` | Cek progress sesi scraping yang berjalan |
| GET | `/api/scrape/result/<session_id>` | Ambil hasil lengkap paper dari 1 sesi |
| GET | `/api/history/keywords` | List semua keyword + ringkasan riwayat |
| GET | `/api/history/keyword/<keyword_id>` | Detail seluruh paper dari 1 keyword |
| GET | `/api/history/all` | Seluruh paper dari seluruh riwayat |
| GET | `/api/export/csv` | Export ke CSV (query param: session_id/keyword_id/all) |
| GET | `/api/export/excel` | Export ke Excel (query param sama) |
| GET | `/api/export/pdf-zip` | Download semua PDF dalam 1 file ZIP (query param sama) |

### 6.6 Validasi & Error Handling
- Validasi input: keyword tidak boleh kosong, jumlah paper harus angka positif (>0) dan dibatasi maksimum (misal 100/sesi agar wajar dengan jeda 5 detik).
- Jika salah satu API sumber gagal diakses (timeout/error), proses tetap lanjut ke sumber lainnya (jika dipilih "keduanya") dan dicatat sebagai warning di ringkasan sesi, bukan menyebabkan seluruh proses gagal total.
- Semua exception dari pemanggilan API pihak ketiga di-*log* ke console/file log backend untuk keperluan debugging.

### 6.7 Keamanan Dasar
- API key Semantic Scholar disimpan di file `.env` (tidak di-hardcode, tidak di-commit ke repository — masuk `.gitignore`).
- Karena tanpa login, tidak ada data sensitif pengguna yang disimpan; namun tetap terapkan validasi input dasar untuk mencegah injeksi query yang tidak wajar pada parameter keyword.

---

## 7. Scope Project

### 7.1 In-Scope (v1.0)
- Scraping dari Semantic Scholar & arXiv berdasarkan keyword + jumlah.
- Validasi field wajib (judul, abstrak, author, tahun, link).
- Filter tahun publikasi (≥ 2020).
- Deteksi & skip duplikat berbasis judul.
- Penyimpanan ke SQLite.
- Riwayat scraping per keyword & riwayat seluruh scraping.
- Export CSV & Excel.
- Download seluruh PDF (yang tersedia open-access) dalam 1 ZIP.
- Jeda 5 detik per paper pada setiap request.
- Akses tanpa login sama sekali.
- UI single-page sederhana (Pencarian + Riwayat).

### 7.2 Out-of-Scope (v1.0 — Kemungkinan v2.0+)
- Sistem login/akun & isolasi data per pengguna.
- Sumber data tambahan (IEEE Xplore, Scopus, PubMed, Google Scholar, dsb).
- Pencarian/filter full-text di dalam isi PDF.
- Analisis sitasi, tren riset, atau visualisasi data (grafik, dsb).
- Retry otomatis/resume untuk sesi scraping yang gagal di tengah jalan.
- Deployment ke server produksi berskala besar (multi-user bersamaan) — arsitektur v1 dioptimalkan untuk penggunaan personal/lokal.
- Mode gelap (dark mode) atau kustomisasi tema.
- Notifikasi email/push saat scraping selesai.

### 7.3 Asumsi
- Pengguna memiliki koneksi internet stabil selama proses scraping berlangsung.
- arXiv hanya relevan untuk paper di bidang STEM (fisika, matematika, ilmu komputer, dll) — jika keyword di luar cakupan arXiv, hasil dari sumber tersebut mungkin sedikit/kosong, dan itu adalah perilaku normal, bukan bug.
- Semantic Scholar API key bersifat opsional; aplikasi tetap dapat berjalan tanpa API key dengan rate limit publik yang berlaku saat itu.

### 7.4 Batasan (Constraints)
- Maksimal jumlah paper per sesi scraping dibatasi (disarankan 100) agar waktu tunggu (dengan jeda 5 detik/paper) tetap wajar bagi pengguna (100 paper ≈ 8-9 menit).
- Hanya paper dengan PDF **open-access** yang dapat diunduh otomatis; paper di balik paywall tidak dapat diunduh sistem (keterbatasan hukum & teknis, bukan bug).

---

## 8. Tahapan Implementasi (Dari Folder Kosong hingga Siap Pakai)

### Tahap 0 — Persiapan Lingkungan
1. Install **Python 3.10+**.
2. (Opsional, direkomendasikan) Daftar **API key Semantic Scholar** melalui form resmi mereka agar mendapat rate limit lebih stabil.
3. Siapkan code editor (VS Code, dsb) dan pastikan `pip` tersedia.

### Tahap 1 — Membuat Struktur Folder Proyek
Buat struktur folder berikut dari folder kosong:

```
paper-scraper/
├── app.py                     # Entry point Flask
├── config.py                  # Konfigurasi (API key, path, dsb)
├── requirements.txt           # Daftar dependency
├── .env                        # Simpan API key (jangan di-commit)
├── .gitignore
├── database/
│   └── scraper.db             # File SQLite (dibuat otomatis saat pertama run)
├── models/
│   └── models.py               # Definisi tabel: Keyword, ScrapingSession, Paper, SessionPaper
├── services/
│   ├── semantic_scholar_service.py   # Fungsi request ke Semantic Scholar API
│   ├── arxiv_service.py              # Fungsi request & parsing arXiv API
│   ├── dedup_service.py              # Fungsi normalisasi judul & cek duplikat
│   ├── validation_service.py         # Validasi field wajib & filter tahun
│   ├── pdf_service.py                # Download PDF & buat ZIP
│   └── export_service.py             # Export CSV & Excel
├── routes/
│   ├── scraping_routes.py     # Endpoint /api/scrape, /api/scrape/status, /api/scrape/result
│   ├── history_routes.py      # Endpoint /api/history/*
│   └── export_routes.py       # Endpoint /api/export/*
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── downloads/
│   └── pdf/                    # Folder penyimpanan PDF hasil unduhan per sesi
└── exports/                     # Folder penyimpanan sementara file csv/xlsx/zip hasil export
```

### Tahap 2 — Inisialisasi Proyek & Dependency
1. Buat virtual environment: `python -m venv venv`, lalu aktifkan.
2. Buat `requirements.txt` berisi: `flask`, `requests`, `python-dotenv`, `feedparser`, `pandas`, `openpyxl`, `sqlalchemy`.
3. Install: `pip install -r requirements.txt`.
4. Isi `.env` dengan `SEMANTIC_SCHOLAR_API_KEY=` (boleh kosong jika tidak pakai key).

### Tahap 3 — Setup Database & Model
1. Definisikan model/tabel di `models/models.py` sesuai skema pada Bagian 5 (Database Overview) — tabel `keywords`, `scraping_sessions`, `papers`, `session_papers`.
2. Buat fungsi `init_db()` yang membuat file `database/scraper.db` beserta seluruh tabel jika belum ada, dipanggil otomatis saat `app.py` pertama kali dijalankan.

### Tahap 4 — Implementasi Service Layer
1. **`semantic_scholar_service.py`**: fungsi `search_papers(keyword, limit, offset)` yang memanggil endpoint `paper/search`, mengembalikan list paper mentah (judul, abstrak, author, tahun, url, pdf_url jika ada).
2. **`arxiv_service.py`**: fungsi `search_papers(keyword, start, max_results)` yang memanggil endpoint arXiv, mem-parsing Atom XML menjadi struktur data yang sama formatnya dengan hasil Semantic Scholar (agar mudah digabung).
3. **`validation_service.py`**: fungsi `is_valid(paper)` mengecek 5 field wajib terisi + tahun ≥ 2020.
4. **`dedup_service.py`**: fungsi `normalize_title(title)` dan `is_duplicate(title_normalized, db_session)` untuk cek ke tabel `papers`.
5. **`pdf_service.py`**: fungsi `download_pdf(pdf_url, save_path)` dengan jeda 5 detik antar panggilan, dan fungsi `create_zip(paper_ids)`.
6. **`export_service.py`**: fungsi `export_to_csv(papers)` dan `export_to_excel(papers)` menggunakan `pandas`.

### Tahap 5 — Implementasi Orkestrator Scraping
1. Buat fungsi utama (misal di `scraping_routes.py` atau file terpisah `orchestrator.py`) yang:
   - Menerima keyword, jumlah target, sumber pilihan.
   - Melakukan loop pengambilan data dari sumber terpilih secara bergantian/berurutan sampai jumlah valid tercapai atau sumber habis.
   - Untuk tiap kandidat paper: validasi → cek duplikat → simpan ke DB → update counter sesi → `time.sleep(5)`.
   - Update status sesi (`running` → `completed`) beserta ringkasan akhir.
2. Jalankan fungsi ini di dalam **background thread** agar endpoint `POST /api/scrape` bisa langsung merespons dengan `session_id` tanpa menunggu proses selesai.

### Tahap 6 — Implementasi Routes/Endpoint Flask
1. Daftarkan seluruh route sesuai tabel pada Bagian 6.5 menggunakan Flask Blueprint agar terstruktur (`scraping_routes`, `history_routes`, `export_routes`).
2. Hubungkan setiap route ke service layer yang relevan.
3. Pastikan response berupa JSON yang konsisten formatnya untuk dikonsumsi frontend.

### Tahap 7 — Implementasi Frontend
1. `templates/index.html`: buat struktur HTML sesuai wireframe Bagian 4.2 (form pencarian, area progress, tabel hasil, tab riwayat).
2. `static/js/main.js`:
   - Fungsi submit form → `fetch(POST /api/scrape)` → simpan `session_id`.
   - Fungsi polling → `setInterval` memanggil `GET /api/scrape/status/<id>` setiap 2 detik, update progress bar, hentikan polling saat status `completed`/`failed`.
   - Fungsi render tabel hasil dari `GET /api/scrape/result/<id>`.
   - Fungsi render tab riwayat dari `GET /api/history/keywords` dan `GET /api/history/all`.
   - Tombol export/download memanggil endpoint terkait dan memicu unduhan file (`window.location.href` atau `<a download>` dinamis).
3. `static/css/style.css`: styling sesuai prinsip desain sederhana pada Bagian 4.1 (layout flex/grid, warna netral, tabel rapi, tombol jelas).

### Tahap 8 — Integrasi & Pengujian Manual
1. Uji scraping dengan keyword umum (contoh: "artificial intelligence") jumlah kecil (5 paper) untuk memastikan alur end-to-end berjalan.
2. Uji ulang keyword yang sama untuk memverifikasi mekanisme skip duplikat bekerja.
3. Uji keyword dengan hasil sangat sedikit untuk memverifikasi sistem berhenti wajar saat sumber habis.
4. Uji export CSV, Excel, dan ZIP PDF untuk memastikan file terbentuk dengan benar dan bisa dibuka.
5. Verifikasi jeda 5 detik konsisten diterapkan (bisa dicek dari log waktu tiap request di console).

### Tahap 9 — Dokumentasi & Finalisasi
1. Buat `README.md` berisi cara instalasi, cara menjalankan (`flask run` atau `python app.py`), dan catatan penggunaan API key.
2. Pastikan `.gitignore` mencakup `venv/`, `.env`, `database/scraper.db`, `downloads/`, `exports/` agar tidak ter-commit.
3. Rapikan pesan error/validasi di frontend agar ramah pengguna non-teknis.

### Tahap 10 — Menjalankan Aplikasi
1. Aktifkan virtual environment.
2. Jalankan `python app.py` (atau `flask run` sesuai konfigurasi).
3. Buka browser ke `http://127.0.0.1:5000`.
4. Aplikasi siap digunakan tanpa proses login.

---

## Lampiran: Ringkasan Keputusan Desain Penting
| Poin | Keputusan |
|---|---|
| Autentikasi | Tidak ada login sama sekali, sesuai target user |
| Duplikat | Dicek berdasarkan judul yang dinormalisasi, unique constraint di level DB |
| Filter tahun | Paper dengan tahun < 2020 otomatis di-skip |
| Rate limit | Jeda tetap 5 detik per paper untuk seluruh request (baik metadata maupun PDF) |
| Proses panjang | Dijalankan di background thread + polling status dari frontend |
| Batas jumlah paper/sesi | Direkomendasikan maksimal 100 agar waktu proses tetap wajar |
